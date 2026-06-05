"""main2.py — minimal MVP pipeline (no optional features).

Instantiate the API client to get the leaders, instantiate the HTML scraper to
get each leader's Wikipedia first paragraph, then write the combined result to
a JSON file. Run with: python main2.py
"""
from asyncio.log import logger
import json
import logging

from src.api_client import CountryLeadersAPI
from src.html_scraper import WikipediaScraper
logger = logging.getLogger(__name__)
OUTPUT_FILE = "leaders_data.json"


def main():
    api = CountryLeadersAPI()
    scraper = WikipediaScraper(session=api.session)
    
    leaders_per_country = {}
    countries = api.get_countries()

    if not countries:
        logger.error("No countries available to fetch leaders.")
        raise RuntimeError("API returned empty country list")
    
    for country in countries:
        leaders = api.get_leaders(country)
        for leader in leaders:
            leader["first_paragraph"] = scraper.scrape_first_paragraph(leader["wikipedia_url"])
        leaders_per_country[country] = leaders

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(leaders_per_country, f, ensure_ascii=False, indent=2)
    print(f"Saved leaders to {OUTPUT_FILE}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
    
