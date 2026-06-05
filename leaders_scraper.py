"""Scrape country leaders and their Wikipedia bio, then save to leaders.json.

Pipeline:
1. query the country-leaders API for the list of countries and their leaders
2. for each leader, fetch their Wikipedia page and extract the first paragraph
3. sanitize that paragraph with regular expressions
4. save the enriched data to disk as JSON

Run with:  python3 leaders_scraper.py
"""
import json
import re

import requests
from bs4 import BeautifulSoup

ROOT_URL = "https://country-leaders.onrender.com"
COOKIE_URL = ROOT_URL + "/cookie"
COUNTRIES_URL = ROOT_URL + "/countries"
LEADERS_URL = ROOT_URL + "/leaders"

# Wikipedia returns 403 to the default python-requests User-Agent.
HEADERS = {"User-Agent": "Mozilla/5.0 (Wikipedia scraper exercise)"}


def get_first_paragraph(wikipedia_url, session):
    """Return the sanitized first (lead) paragraph of a Wikipedia article."""
    print(wikipedia_url)
    soup = BeautifulSoup(session.get(wikipedia_url).text, "html.parser")

    # The lead paragraph bolds the subject's name in every language, so the
    # first <p> containing a <b> tag is a reliable, language-agnostic match.
    first_paragraph = ""
    for paragraph in soup.find_all("p"):
        if paragraph.find("b"):
            first_paragraph = paragraph.text
            break

    # Sanitize the text with a series of regular expressions.
    first_paragraph = re.sub(r"\[[^\]]*\]", "", first_paragraph)            # [1], [a], [note 2]
    first_paragraph = re.sub(r"\([^()]*[ⓘ/][^()]*\)", "", first_paragraph)  # (listen ⓘ) / IPA ( /.../ )
    first_paragraph = re.sub(r"\s*ⓘ", "", first_paragraph)             # stray listen icons
    first_paragraph = re.sub(r"\s*Écouter\b", "", first_paragraph)          # bare "listen" audio labels
    first_paragraph = first_paragraph.replace("\xa0", " ")                  # non-breaking spaces
    first_paragraph = re.sub(r"\s+([,.;:])", r"\1", first_paragraph)        # space before punctuation
    first_paragraph = re.sub(r"\s{2,}", " ", first_paragraph).strip()       # collapse whitespace
    return first_paragraph


def get_leaders():
    """Return {country_code: [leader, ...]} with each leader enriched by their bio."""
    cookies = requests.get(COOKIE_URL).cookies
    countries = requests.get(COUNTRIES_URL, cookies=cookies).json()

    # A single session reused for every Wikipedia call (keeps the TCP connection alive).
    session = requests.Session()
    session.headers.update(HEADERS)

    leaders_per_country = {}
    for country in countries:
        req = requests.get(LEADERS_URL, cookies=cookies, params={"country": country})
        # The cookie may expire mid-loop: refresh it and retry once.
        if req.status_code != 200:
            cookies = requests.get(COOKIE_URL).cookies
            req = requests.get(LEADERS_URL, cookies=cookies, params={"country": country})
        leaders = req.json()

        for leader in leaders:
            leader["first_paragraph"] = get_first_paragraph(leader["wikipedia_url"], session)
        leaders_per_country[country] = leaders

    return leaders_per_country


def save(leaders_per_country, filename="leaders.json"):
    """Save the leaders dictionary to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(leaders_per_country, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    leaders_per_country = get_leaders()
    save(leaders_per_country)
    total = sum(len(v) for v in leaders_per_country.values())
    print(f"\nSaved {total} leaders across {len(leaders_per_country)} countries to leaders.json")
