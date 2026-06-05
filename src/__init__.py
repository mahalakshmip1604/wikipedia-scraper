"""Wikipedia scraper package: API client (Track 1) and HTML scraper (Track 2)."""

from src.api_client import CountryLeadersAPI
from src.html_scraper import WikipediaScraper

__all__ = ["CountryLeadersAPI", "WikipediaScraper"]
