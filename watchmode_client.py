import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class WatchmodeClient:
    BASE_URL = "https://api.watchmode.com/v1/"
    
    def __init__(self):
        self.api_key = os.getenv("WATCHMODE_API_KEY")
        if not self.api_key:
            raise ValueError("WATCHMODE_API_KEY is not set in the environment variables.")

    def search_title(self, title):
        """Search for a title in Watchmode."""
        url = f"{self.BASE_URL}search/"
        params = {
            "apiKey": self.api_key,
            "search_field": "name",
            "search_value": title
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_title_details(self, title_id):
        """Get details for a specific title by its ID."""
        url = f"{self.BASE_URL}title/{title_id}/details/"
        params = {"apiKey": self.api_key}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
