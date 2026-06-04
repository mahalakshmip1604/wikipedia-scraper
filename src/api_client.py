import re
from urllib import response
from wsgiref import headers

import requests
from bs4 import BeautifulSoup
import time
# comment
class CountryLeadersAPI:
    def __init__(self):
        self.base_url = "https://country-leaders.onrender.com"
        self.country_endpoint = "/country/{country_code}"
        self.leaders_endpoint = "/leaders"
        cookies_endpoint = "/cookies"
        self.session = requests.Session()

    def refresh_cookie(self):
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
        response = self.session.get(self.base_url + self.country_endpoint, cookies=self.session.cookies)
                
        if response.status_code == 200:
            countries = response.json()
        else:
            print("Failed to fetch countries. Status code:", response.status_code)
            return None
        return countries
    

    def get_leaders(self):
        countries = self.get_countries()
        if not countries:
            print("No countries available to fetch leaders.")
            return None       
   
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Wikipedia scraper exercise)"}) 
        leaders_per_country = {}
        for country in countries:
            req = self.session.get(self.leaders_endpoint, params={"country": country})
            if req.status_code != 200:  # refresh expired cookie and retry
                self.refresh_cookie()
                req = self.session.get(self.leaders_endpoint, params={"country": country})
                leaders = req.json()
                leaders_per_country[country] = leaders
            return leaders_per_country

        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to fetch leaders. Status code:", response.status_code)
            return None
    
