# wikipedia-scraper

Scraping and data collection are core data engineering tasks. Doing this as a team
simulates how production data pipelines are built in the real world.

This project scrapes a list of countries and their past leaders from the
[country-leaders API](https://country-leaders.onrender.com/docs), enriches each
leader with the first paragraph of their Wikipedia page, and saves everything to
`leaders.json`.

## Setup

```bash
# create and activate a virtual environment
python3 -m venv wikipedia_scraper_env
source wikipedia_scraper_env/bin/activate    # Windows: wikipedia_scraper_env\Scripts\activate

# install the dependencies
pip install -r requirements.txt
```

## Usage

Run the standalone scraper:

```bash
python3 leaders_scraper.py
```

It writes the result to `leaders.json`.

To follow the step-by-step build, open `stephane_sandbox_noteboook.ipynb`.

## How it works

- **API** — `requests` queries the `/cookie`, `/countries` and `/leaders`
  endpoints. The cookie is refreshed automatically if it expires mid-run.
- **Wikipedia** — `BeautifulSoup` parses each article. The lead paragraph is the
  first `<p>` that contains a `<b>` tag (the subject's bolded name), which works
  across languages. A reused `requests.Session` keeps the connection alive for
  speed, and a `User-Agent` header is set (Wikipedia returns `403` without one).
- **Cleanup** — regular expressions strip reference markers (`[1]`), phonetic /
  "listen" annotations, and stray whitespace.
- **Output** — the enriched dictionary is serialized to `leaders.json`.

## Files

| File | Purpose |
|------|---------|
| `leaders_scraper.py` | Stand-alone, production-ready scraper |
| `stephane_sandbox_noteboook.ipynb` | Step-by-step tutorial notebook |
| `requirements.txt` | Python dependencies |
| `leaders.json` | Generated output (git-ignored) |
