"""Track 1 - The API Client (src/api_client.py)
The API client is responsible for communicating with the country leaders API,
fetching the list of countries and their leaders, and handling cookies and
authentication as needed. It should be designed to be easily testable and
decoupled from the HTML scraping logic (Track 2). The API client should also 
handle any necessary error handling and retries, especially in the case of
expired cookies or failed requests.
"""

import re
from urllib import response
from wsgiref import headers

import requests
from bs4 import BeautifulSoup
import time


class CountryLeadersAPI:
    """Client for the country leaders API, responsible for fetching countries and leaders."""
    def __init__(self):
        self.base_url = "https://country-leaders.onrender.com"
        self.country_endpoint = "/country/{country_code}"
        self.leaders_endpoint = "/leaders"
        self.cookies_endpoint = "/cookies"
        self.session = requests.Session()

    def refresh_cookie(self):
        """Refresh the cookie by making a request to the cookies endpoint. 
        This should be called when a request fails due to an expired cookie."""
     # Check whether a valid cookie already exists
        for cookie in self.session.cookies:
            if cookie.expires and cookie.expires > time.time():
                print("Cookie is still valid.")
                return

     # No valid cookie found, request a new one
        response = self.session.get(self.base_url + self.cookies_endpoint)

        if response.status_code == 200:
            print("Cookie refreshed successfully.")
        else:
            print("Failed to refresh cookie. Status code:",response.status_code)
            

    def get_countries(self):
        """Fetch the list of countries from the API. This method should handle 
        any necessary authentication and error handling."""
        response = self.session.get(self.base_url + self.country_endpoint, cookies=self.session.cookies)
                
        if response.status_code == 200:
            countries = response.json()
        else:
            print("Failed to fetch countries. Status code:", response.status_code)
            return None
        return countries
    

    def get_leaders(self):
        """Fetch the list of leaders for each country from the API. 
        This method should handle any necessary authentication and error handling, 
        including refreshing cookies if needed."""
        countries = self.get_countries()
        if not countries:
            print("No countries available to fetch leaders.")
            return None       
   
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Wikipedia scraper exercise)"}) 
        leaders_per_country = {}
        for country in countries:
            response = self.session.get(self.leaders_endpoint,cookies=self.session.cookies, params={"country": country})
            if response.status_code != 200:  # refresh expired cookie and retry
                self.refresh_cookie()
                response = self.session.get(self.leaders_endpoint, cookies=self.session.cookies, params={"country": country})
            leaders = response.json()
        return leaders
