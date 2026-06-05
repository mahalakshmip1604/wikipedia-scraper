"""Track 2 — The HTML Scraper.

A :class:`WikipediaScraper` responsible only for downloading and parsing
Wikipedia HTML documents and extracting a leader's biographical paragraph.

The class is deliberately decoupled from the API client (Track 1): it receives
a ``requests.Session`` from the parent application context and knows nothing
about cookies, country codes, or endpoints.
"""
from __future__ import annotations

import json
import logging
import re

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WikipediaScraper:
    """Download and parse Wikipedia articles to extract leaders' biographies."""

    # Wikipedia returns 403 to the default python-requests User-Agent.
    DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0 (Wikipedia scraper)"}

    def __init__(self, session: requests.Session | None = None) -> None:
        """Store the session passed from the parent context (or create one)."""
        self.session: requests.Session = session or requests.Session()
        # A fresh Session ships a "python-requests/..." User-Agent that Wikipedia
        # rejects with 403, so override it unless the parent set a custom one.
        current_ua = self.session.headers.get("User-Agent", "")
        if not current_ua or current_ua.startswith("python-requests"):
            self.session.headers["User-Agent"] = self.DEFAULT_HEADERS["User-Agent"]
        # Container the integration layer (main.py) can populate and then dump.
        self.data: dict = {}

    def fetch_html(self, url: str) -> str:
        """Safely request the raw HTML of ``url``.

        Returns the page's text on success, or an empty string on any HTTP
        error (404/500/...), timeout, or connection drop.
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as exc:
            logger.warning("Could not fetch %s: %s", url, exc)
            return ""

    def get_first_paragraph(self, html: str) -> str:
        """Return the first true biographical paragraph from raw ``html``.

        The lead paragraph bolds the subject's name in every Wikipedia language,
        so the first ``<p>`` containing a ``<b>`` tag is a reliable,
        language-agnostic match. The text is returned already cleaned.
        """
        soup = BeautifulSoup(html, "html.parser")
        for paragraph in soup.find_all("p"):
            if paragraph.find("b"):
                return self.clean_text(paragraph.get_text())
        return ""

    def clean_text(self, text: str) -> str:
        """Strip citation brackets, pronunciation cruft, and stray whitespace."""
        text = re.sub(r"\[[^\]]*\]", "", text)             # [1], [a], [citation needed]
        text = re.sub(r"\([^()]*[ⓘ/][^()]*\)", "", text)   # (listen ⓘ) / IPA ( /.../ )
        text = re.sub(r"\s*ⓘ", "", text)                   # stray listen icons
        text = re.sub(r"\s*Écouter\b", "", text)           # bare "listen" audio labels
        text = text.replace("\xa0", " ")                   # non-breaking spaces
        text = re.sub(r"\s+([,.;:])", r"\1", text)         # space before punctuation
        text = re.sub(r"\s{2,}", " ", text).strip()        # collapse whitespace
        return text

    def scrape_first_paragraph(self, url: str) -> str:
        """Convenience helper: fetch ``url`` and return its first paragraph."""
        return self.get_first_paragraph(self.fetch_html(url))

if __name__ == "__main__":
    # Quick self-test against a few articles in different languages.
    logging.basicConfig(level=logging.INFO)
    scraper = WikipediaScraper()
    for sample in (
        "https://en.wikipedia.org/wiki/Barack_Obama",
        "https://fr.wikipedia.org/wiki/Jacques_Chirac",
    ):
        print(sample)
        print(scraper.scrape_first_paragraph(sample)[:200], "\n")
