# 🌍 Wikipedia Scraper

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![requests](https://img.shields.io/badge/requests-2.x-orange)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-4.x-green)
![Status](https://img.shields.io/badge/status-MVP%20complete-success)

> Scrape the political leaders of every country from a REST API, enrich each one
> with the first paragraph of their Wikipedia page, and export the result to
> JSON (or CSV).

Scraping and data collection are core data engineering tasks. This project was
built as a **pair-programming exercise** to simulate how production data
pipelines are assembled in the real world: a modular, object-oriented codebase
developed across feature branches with peer-reviewed pull requests.

![data stream](https://media.giphy.com/media/13HgwGsXF0aiGY/giphy.gif)


---

## 📖 Description

The scraper builds a JSON file mapping each country to its list of past
political leaders. For every leader it fetches their Wikipedia page and extracts
the first biographical paragraph, cleaned of citation markers and noise.

Data source: the [country-leaders API](https://country-leaders.onrender.com/docs).

The code is split into two single-responsibility modules that an orchestrator
ties together:

| Layer                             | Module                                      | Responsibility                                                                                           |
| --------------------------------- | ------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Track 1 — API client**   | [`src/api_client.py`](src/api_client.py)     | `CountryLeadersAPI`: talks to the REST API, manages the session cookie, returns countries and leaders. |
| **Track 2 — HTML scraper** | [`src/html_scraper.py`](src/html_scraper.py) | `WikipediaScraper`: downloads and parses Wikipedia HTML, extracts and cleans the first paragraph.      |
| **Orchestration**           | [`main.py`](main.py)                         | Coordinates both modules end-to-end and writes the output file.                                          |

---

## 🗂️ Project structure

```text
wikipedia-scraper/
├── README.md
├── requirements.txt
├── main.py                 # MVP pipeline: API -> scraper -> leaders_data.json
├── main_optional.py        # Same pipeline + bonuses (multiprocessing, CSV, logging, CLI)
├── dev/                    # Personal sandbox notebooks (API & BeautifulSoup exploration)
│   ├── mahalakshmi_sandbox_noteboook.ipynb
│   └── stephane_sandbox_noteboook.ipynb
└── src/
    ├── __init__.py
    ├── api_client.py       # CountryLeadersAPI  (Track 1)
    └── html_scraper.py     # WikipediaScraper   (Track 2)
```

---

## ⚙️ Installation

```bash
# 1. clone the repository
git clone https://github.com/mahalakshmip1604/wikipedia-scraper.git
cd wikipedia-scraper

# 2. create and activate a virtual environment
python3 -m venv wikipedia_scraper_env
source wikipedia_scraper_env/bin/activate    # Windows: wikipedia_scraper_env\Scripts\activate

# 3. install the dependencies
pip install -r requirements.txt
```

Dependencies: `requests`, `beautifulsoup4`, `lxml`.

---

## 🚀 Usage

### Minimal pipeline (MVP)

```bash
python3 main.py
```

Writes the enriched data to `leaders_data.json`.

### Full pipeline (with bonuses)

[`main_optional.py`](main_optional.py) adds parallel scraping, a CSV exporter,
logging, and a small CLI:

```bash
python3 main_optional.py                       # -> leaders_data.json (parallel)
python3 main_optional.py --output leaders.csv  # flattened CSV export
python3 main_optional.py --no-multiprocessing  # scrape sequentially
python3 main_optional.py --workers 16          # tune the parallel worker count
```

| Flag                     | Description                                          | Default               |
| ------------------------ | ---------------------------------------------------- | --------------------- |
| `-o`, `--output`     | Output file;`.json` or `.csv` selects the format | `leaders_data.json` |
| `--no-multiprocessing` | Scrape Wikipedia pages sequentially                  | parallel on           |
| `--workers`            | Number of parallel workers                           | `8`                 |

### Sandbox notebooks

The step-by-step exploration of the API and BeautifulSoup selectors lives in
[`dev/`](dev/) — one notebook per teammate.

---

## 📦 Output

A successful run produces **136 leaders across 5 countries** (`fr`, `us`, `be`,
`ma`, `ru`). The output is a JSON object keyed by country code, each holding a
list of leader records enriched with a `first_paragraph` field.

### Schema (one leader record)

```json
{
  "id": "Q12978",
  "first_name": "Guy",
  "last_name": "Verhofstadt",
  "birth_date": "1953-04-11",
  "death_date": null,
  "place_of_birth": "Dendermonde",
  "wikipedia_url": "https://nl.wikipedia.org/wiki/Guy_Verhofstadt",
  "start_mandate": "1999-07-12",
  "end_mandate": "2008-03-20",
  "first_paragraph": "Guy Maurice Marie-Louise Verhofstadt (Dendermonde, 11 april 1953) is een Belgisch politicus voor de Open Vlaamse Liberalen en Democraten (Open Vld). Hij was premier van België van 12 juli 1999 tot 20 maart 2008 in drie regeringen..."
}
```

### Top-level shape

```json
{
  "fr": [ { "...": "..." }, ... ],
  "us": [ ... ],
  "be": [ ... ],
  "ma": [ ... ],
  "ru": [ ... ]
}
```

With `--output leaders.csv`, the same data is flattened to one row per leader,
each prefixed with its `country` code.

---

## 🔍 How it works

- **API** — `CountryLeadersAPI` queries the `/cookie`, `/countries` and
  `/leaders` endpoints through a persistent `requests.Session()`. The
  authentication cookie is refreshed automatically if it expires mid-run, with a
  single retry per request.
- **Wikipedia** — `WikipediaScraper` parses each article with `BeautifulSoup`.
  The lead paragraph is the first `<p>` containing a `<b>` tag (the subject's
  bolded name), which works across languages. A `User-Agent` header is set
  because Wikipedia returns `403` without one.
- **Cleanup** — regular expressions strip reference markers (`[1]`), phonetic /
  "listen" annotations, non-breaking spaces, and stray whitespace.
- **Error handling** — network failures, `404`/`500` responses, and dropped
  connections are caught gracefully; a failed page yields an empty paragraph
  instead of crashing the run.
- **Output** — the enriched `{country_code: [leaders]}` dictionary is serialized
  to `leaders_data.json` (or flattened to CSV).

### Pipeline overview

```text
CountryLeadersAPI.get_countries()  ─┐
CountryLeadersAPI.get_leaders(c)   ─┤→  for each leader:
                                    │     WikipediaScraper.scrape_first_paragraph(url)
                                    │       → fetch_html → get_first_paragraph → clean_text
                                    └→  map paragraph back onto the leader
                                            → save_json / save_csv
```

---

## 📚 Module reference

### `CountryLeadersAPI` — [`src/api_client.py`](src/api_client.py)

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(base_url="https://country-leaders.onrender.com")` | Creates a persistent `Session` and fetches the initial cookie. |
| `refresh_cookie` | `() -> None` | Requests a fresh authentication cookie from `/cookie`. |
| `get_countries` | `() -> list[str]` | Returns the supported country codes, retrying once if the cookie expired. |
| `get_leaders` | `(country: str) -> list[dict]` | Returns the raw list of leader records for one country. |

### `WikipediaScraper` — [`src/html_scraper.py`](src/html_scraper.py)

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(session: requests.Session \| None = None)` | Reuses a passed-in session or creates one; sets a Wikipedia-friendly `User-Agent`. |
| `fetch_html` | `(url: str) -> str` | Safely fetches raw HTML; returns `""` on any HTTP/connection error. |
| `get_first_paragraph` | `(html: str) -> str` | Extracts and cleans the first biographical paragraph from HTML. |
| `clean_text` | `(text: str) -> str` | Strips citation brackets, pronunciation cruft, and whitespace. |
| `scrape_first_paragraph` | `(url: str) -> str` | Convenience: `fetch_html` + `get_first_paragraph`. |
| `to_json_file` | `(filepath: str) -> None` | Dumps the accumulated `data` dict to JSON. |

---

## 🌐 API reference

The [country-leaders API](https://country-leaders.onrender.com/docs) exposes:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/cookie` | `GET` | Issues the authentication cookie required by the other endpoints. |
| `/countries` | `GET` | Returns the list of supported country codes. |
| `/leaders?country=<code>` | `GET` | Returns the leaders for a given country. |

> ⚠️ The API is hosted on Render's free tier and **cold-starts after inactivity**,
> so the first call of a run can take 20–50 s while the service spins up.

---

## ⚡ Performance

Measured on a full run (136 Wikipedia pages, 8 workers):

| Mode | Command | Wall time |
|------|---------|-----------|
| Parallel (default) | `python3 main_optional.py` | ~15.6 s |
| Sequential | `python3 main_optional.py --no-multiprocessing` | ~17.0 s |

The gap is modest here because most of the runtime is the API's cold-start
latency and the sequential `/leaders` calls — both shared by either mode. The
parallel scraping advantage grows with the number of leaders and on slower
networks, where the Wikipedia fetches dominate.

---

## 🖥️ Example run

```console
$ python3 main_optional.py
INFO | Cookie refreshed.
INFO | Fetched 31 leaders for 'fr'
INFO | Fetched 45 leaders for 'us'
INFO | Fetched 53 leaders for 'be'
INFO | Fetched 4 leaders for 'ma'
INFO | Fetched 3 leaders for 'ru'
INFO | Scraping 136 Wikipedia pages (parallel=True)
INFO | Wrote leaders_data.json
INFO | Done: 136 leaders across 5 countries.
```

---

## 🤝 Collaboration & Git Flow

This was a two-person project built with a protected `main` branch:

- **No direct pushes to `main`** — all work happened on descriptive feature
  branches (e.g. `feature/api-client`, `feature/html-scraper`, `step_main_mvp`).
- **Peer-reviewed pull requests** — each feature was opened as a PR and reviewed
  and approved by the partner before merging.
- **Isolated sandboxes** — early API and scraping experiments stayed in each
  teammate's own notebook under [`dev/`](dev/), keeping experimental code out of
  the production modules.

---

## 🌱 Contributing

This repo follows a lightweight Git Flow:

1. **Branch** off `main` with a descriptive name:
   `feature/<thing>`, `fix/<thing>`, or a `step-*` task branch.
2. **Commit** small, focused changes with clear messages.
3. **Open a PR** against `main` and request a review from your partner.
4. **Get one approval** and a green review before merging — never push to `main`
   directly.
5. Keep experimental work in your own `dev/` notebook, out of the `src/` modules.

---

## ✅ Features

- [X] Modular, object-oriented `src/api_client.py` and `src/html_scraper.py`
- [X] Central `main.py` controller running the pipeline end-to-end
- [X] Graceful error handling for dropped connections / missing pages
- [X] Persistent `requests.Session()` usage
- [X] **Bonus:** multiprocessing / parallel scraping (`main_optional.py`)
- [X] **Bonus:** CSV export toggle
- [X] **Bonus:** logging instead of bare `print()`

---

## 🛠️ Troubleshooting / FAQ

**The first run hangs for ~30 seconds — is it stuck?**
No. The API runs on Render's free tier and cold-starts after inactivity. The
first request wakes the service; subsequent calls are fast.

**I get a `403` when fetching Wikipedia.**
Wikipedia rejects the default `python-requests` `User-Agent`. `WikipediaScraper`
sets a browser-like `User-Agent` automatically — make sure you go through the
class rather than calling `requests.get` directly.

**`{"message": "The cookie is missing"}`.**
The authentication cookie expired or wasn't sent. The client refreshes it
automatically and retries once; if it persists, the API may be down.

**`ModuleNotFoundError: No module named 'src'`.**
Run the scripts from the project root (`python3 main.py`), not from inside
`src/`, so the package import resolves.

**Some leaders have an empty `first_paragraph`.**
That page failed to fetch (404/timeout) or had no detectable lead paragraph. By
design the pipeline logs a warning and continues instead of crashing.

---

## 👥 Authors

A pair-programming project by **Mahalakshmi P** and **Stephane van der Aa**.
