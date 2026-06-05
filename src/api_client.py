"""Track 1 — The API Client.

A :class:`CountryLeadersAPI` responsible only for communicating with the
``country-leaders`` REST API: managing the session cookie and returning the
list of supported countries and their leaders.

The class is deliberately decoupled from the HTML scraping (Track 2): it knows
about endpoints and cookies, but nothing about Wikipedia or BeautifulSoup.
"""
from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)


class CountryLeadersAPI:
    """Client for the country-leaders REST API."""

    def __init__(self, base_url: str = "https://country-leaders.onrender.com") -> None:
        self.base_url: str = base_url
        self.country_endpoint: str = "/countries"
        self.leaders_endpoint: str = "/leaders"
        self.cookies_endpoint: str = "/cookie"
        # A single persistent session keeps the TCP connection alive and carries
        # the authentication cookie across every request.
        self.session: requests.Session = requests.Session()
        self.refresh_cookie()

    def refresh_cookie(self) -> None:
        """Fetch a fresh authentication cookie from the API.

        Callers handle expiry by retrying once on a non-200 response, so this
        always requests a new cookie rather than trying to validate the old one.
        """
        response = self.session.get(self.base_url + self.cookies_endpoint, timeout=10)
        response.raise_for_status()
        logger.info("Cookie refreshed.")

    def get_countries(self) -> list[str]:
        """Return the list of supported country codes (e.g. ``["fr", "be", ...]``)."""
        response = self.session.get(self.base_url + self.country_endpoint, timeout=10)
        if response.status_code != 200:
            # The cookie may have expired; refresh once and retry.
            self.refresh_cookie()
            response = self.session.get(self.base_url + self.country_endpoint, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_leaders(self, country: str) -> list[dict]:
        """Return the raw JSON list of leaders for ``country``."""
        response = self.session.get(
            self.base_url + self.leaders_endpoint,
            params={"country": country},
            timeout=10,
        )
        if response.status_code != 200:
            # The cookie may expire mid-loop: refresh it and retry once.
            self.refresh_cookie()
            response = self.session.get(
                self.base_url + self.leaders_endpoint,
                params={"country": country},
                timeout=10,
            )
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    api = CountryLeadersAPI()
    countries = api.get_countries()
    print("Countries:", countries)
    print("Leaders in", countries[0], "->", len(api.get_leaders(countries[0])))
