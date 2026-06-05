"""Phase 2 — Integration & Orchestration.

``main.py`` is the coordinator that composes the two production modules into a
single end-to-end pipeline:

1. Initialize :class:`~src.api_client.CountryLeadersAPI` and retrieve the active
   countries and their leaders.
2. Pass each discovered Wikipedia URL to the :class:`~src.html_scraper.WikipediaScraper`
   engine to parse the biography.
3. Map the scraped text back into the leader datasets and save the output.

Run with:
    python main.py                       # -> leaders_data.json
    python main.py --output leaders.csv  # flattened CSV export
    python main.py --no-multiprocessing  # disable parallel scraping
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
from concurrent.futures import ThreadPoolExecutor

import requests

from src.api_client import CountryLeadersAPI
from src.html_scraper import WikipediaScraper

logger = logging.getLogger("wikipedia_scraper")


def collect_leaders(api: CountryLeadersAPI) -> dict[str, list[dict]]:
    """Retrieve every country's leaders as ``{country_code: [leader, ...]}``."""
    leaders_per_country: dict[str, list[dict]] = {}
    for country in api.get_countries():
        leaders = api.get_leaders(country)
        leaders_per_country[country] = leaders
        logger.info("Fetched %d leaders for %r", len(leaders), country)
    return leaders_per_country


def _scrape_one(args: tuple[str, str]) -> tuple[str, str]:
    """Worker: scrape a single Wikipedia URL.

    Takes ``(leader_id, wikipedia_url)`` and returns ``(leader_id, paragraph)``.
    Each worker uses its own scraper/session so it is safe to run in parallel.
    """
    leader_id, url = args
    scraper = WikipediaScraper()
    return leader_id, scraper.scrape_first_paragraph(url)


def enrich_with_biographies(
    leaders_per_country: dict[str, list[dict]],
    *,
    use_multiprocessing: bool = True,
    max_workers: int = 8,
) -> dict[str, list[dict]]:
    """Add a ``first_paragraph`` field to every leader from their Wikipedia page."""
    # Index leaders by id so workers can map their results back regardless of order.
    by_id: dict[str, dict] = {}
    jobs: list[tuple[str, str]] = []
    for leaders in leaders_per_country.values():
        for leader in leaders:
            url = leader.get("wikipedia_url")
            if not url:
                continue
            by_id[leader["id"]] = leader
            jobs.append((leader["id"], url))

    logger.info("Scraping %d Wikipedia pages (parallel=%s)", len(jobs), use_multiprocessing)

    if use_multiprocessing:
        # I/O-bound work -> threads release the GIL while waiting on the network,
        # giving the parallel speed-up without the pickling overhead of processes.
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            results = pool.map(_scrape_one, jobs)
    else:
        session = requests.Session()
        scraper = WikipediaScraper(session=session)
        results = ((lid, scraper.scrape_first_paragraph(url)) for lid, url in jobs)

    for leader_id, paragraph in results:
        by_id[leader_id]["first_paragraph"] = paragraph

    return leaders_per_country


def save_json(data: dict[str, list[dict]], filepath: str) -> None:
    """Save the leaders dictionary to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Wrote %s", filepath)


def save_csv(data: dict[str, list[dict]], filepath: str) -> None:
    """Save the leaders as a flattened CSV (one row per leader)."""
    rows = [
        {"country": country, **leader}
        for country, leaders in data.items()
        for leader in leaders
    ]
    if not rows:
        logger.warning("No leaders to write to %s", filepath)
        return
    # Union of every key seen, so leaders with differing fields all serialize.
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Wrote %s", filepath)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape country leaders and their Wikipedia bios.")
    parser.add_argument(
        "-o", "--output",
        default="leaders_data.json",
        help="Output file. Extension .json or .csv selects the format (default: leaders_data.json).",
    )
    parser.add_argument(
        "--no-multiprocessing",
        dest="multiprocessing",
        action="store_false",
        help="Scrape Wikipedia pages sequentially instead of in parallel.",
    )
    parser.add_argument(
        "--workers", type=int, default=8,
        help="Number of parallel workers when multiprocessing is enabled (default: 8).",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    args = parse_args()

    api = CountryLeadersAPI()
    leaders_per_country = collect_leaders(api)
    enrich_with_biographies(
        leaders_per_country,
        use_multiprocessing=args.multiprocessing,
        max_workers=args.workers,
    )

    if args.output.lower().endswith(".csv"):
        save_csv(leaders_per_country, args.output)
    else:
        save_json(leaders_per_country, args.output)

    total = sum(len(v) for v in leaders_per_country.values())
    logger.info("Done: %d leaders across %d countries.", total, len(leaders_per_country))


if __name__ == "__main__":
    main()
