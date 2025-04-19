import requests
from pymongo import MongoClient
import certifi
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB setup
MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

# WatchMode API configuration
WATCHMODE_API_KEY = os.getenv('WATCHMODE_API_KEY')
WATCHMODE_BASE_URL = "https://api.watchmode.com/v1"

class StreamingService:
    @staticmethod
    def refresh_content_for_services(service_ids):
        """Fetch and cache content for specified streaming services."""
        try:
            # Convert service IDs to strings for consistency
            service_ids = [str(sid) for sid in service_ids]
            
            # Get current timestamp
            current_time = datetime.utcnow()
            
            # Check if we need to refresh the cache
            last_update = db.content_cache.find_one({"type": "last_update"})
            if last_update and (current_time - last_update["timestamp"]) < timedelta(hours=24):
                print("Using cached content data")
                return True
                
            print(f"Refreshing content for services: {service_ids}")
            
            # Fetch content from WatchMode API
            params = {
                "apiKey": WATCHMODE_API_KEY,
                "regions": "US",  # Assuming US region
                "source_ids": ",".join(service_ids),
                "limit": 250  # Adjust based on needs
            }
            
            # Fetch movies
            movies_url = f"{WATCHMODE_BASE_URL}/list-titles/"
            params["types"] = "movie"
            movies_response = requests.get(movies_url, params=params)
            
            # Fetch TV shows
            shows_url = f"{WATCHMODE_BASE_URL}/list-titles/"
            params["types"] = "show"
            shows_response = requests.get(shows_url, params=params)
            
            if movies_response.status_code == 200 and shows_response.status_code == 200:
                # Clear existing cache for these services
                db.content_cache.delete_many({"service_id": {"$in": service_ids}})
                
                # Process and store movies
                movies_data = movies_response.json().get("titles", [])
                for movie in movies_data:
                    movie["content_type"] = "movie"
                    movie["service_ids"] = service_ids
                    movie["cached_at"] = current_time
                    db.content_cache.update_one(
                        {"id": movie["id"]},
                        {"$set": movie},
                        upsert=True
                    )
                
                # Process and store TV shows
                shows_data = shows_response.json().get("titles", [])
                for show in shows_data:
                    show["content_type"] = "show"
                    show["service_ids"] = service_ids
                    show["cached_at"] = current_time
                    db.content_cache.update_one(
                        {"id": show["id"]},
                        {"$set": show},
                        upsert=True
                    )
                
                # Update last refresh timestamp
                db.content_cache.update_one(
                    {"type": "last_update"},
                    {"$set": {"timestamp": current_time}},
                    upsert=True
                )
                
                print(f"Successfully cached {len(movies_data)} movies and {len(shows_data)} shows")
                return True
            else:
                print(f"API Error - Movies: {movies_response.status_code}, Shows: {shows_response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error refreshing content: {str(e)}")
            return False
    
    @staticmethod
    def get_content_for_services(service_ids, content_type=None, limit=50):
        """Retrieve cached content for specified streaming services."""
        try:
            # Convert service_ids to strings
            service_ids = [str(sid) for sid in service_ids]
            
            # Build query
            query = {"service_ids": {"$in": service_ids}}
            if content_type:
                query["content_type"] = content_type
            
            # Get content from cache
            content = list(db.content_cache.find(
                query,
                {"_id": 0}  # Exclude MongoDB _id
            ).limit(limit))
            
            return content
            
        except Exception as e:
            print(f"Error retrieving content: {str(e)}")
            return []
    
    @staticmethod
    def get_content_details(content_id):
        """Get detailed information for a specific content item."""
        try:
            # First check cache
            cached_content = db.content_cache.find_one({"id": content_id}, {"_id": 0})
            
            if cached_content:
                # If we have details, return them
                if cached_content.get("details_cached"):
                    return cached_content
                
                # If not, fetch details from API
                url = f"{WATCHMODE_BASE_URL}/title/{content_id}/details/"
                params = {"apiKey": WATCHMODE_API_KEY}
                
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    details = response.json()
                    # Update cache with details
                    details["details_cached"] = True
                    db.content_cache.update_one(
                        {"id": content_id},
                        {"$set": details}
                    )
                    return details
            
            return None
            
        except Exception as e:
            print(f"Error getting content details: {str(e)}")
            return None
