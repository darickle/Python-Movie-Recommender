"""
Darick Le
March 22 2025
Streaming Services API Integration
This module integrates with the RapidAPI Streaming Availability API to fetch 
and cache content availability data for various streaming services.
"""

import http.client
import json
import ssl  # Import ssl module
from pymongo import MongoClient
import certifi
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

# Create a custom SSL context that doesn't verify certificates
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# MongoDB setup
MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

# RapidAPI configuration
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', "250f7c809bmshbd07ebdd782a896p1cf5e6jsn9767ca4b28cf")
RAPIDAPI_HOST = "streaming-availability.p.rapidapi.com"

# Service ID mapping between our system and RapidAPI
SERVICE_MAPPING = {
    "203": "netflix",  # Netflix
    "26": "prime",    # Amazon Prime
    "372": "disney",   # Disney+
    "157": "hulu",     # Hulu
    "387": "hbo",      # HBO Max
    "444": "paramount", # Paramount+
    "389": "peacock",   # Peacock
    "371": "apple",     # Apple TV+
    "442": "discovery",  # Discovery+
    "443": "espn"       # ESPN+
}

REVERSE_SERVICE_MAPPING = {v: k for k, v in SERVICE_MAPPING.items()}

# Helper function to create an HTTP connection with SSL context
def create_api_connection():
    return {
        'headers': {
            'X-RapidAPI-Key': '995e2c999cmsh5914690d2b1359ep10b499jsn0f6ec0e74ced',
            'X-RapidAPI-Host': 'streaming-availability.p.rapidapi.com',
            'Content-Type': 'application/json'
        }
    }

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
            
            # Map our service IDs to RapidAPI service names
            streaming_services = []
            for service_id in service_ids:
                if service_id in SERVICE_MAPPING:
                    streaming_services.append(SERVICE_MAPPING[service_id])
            
            if not streaming_services:
                print("No valid streaming services to query")
                return False
            
            # Create connection to RapidAPI
            conn = create_api_connection()  # Use helper function
            headers = {
                'x-rapidapi-key': RAPIDAPI_KEY,
                'x-rapidapi-host': RAPIDAPI_HOST
            }
            
            # We'll fetch both movies and shows
            # RapidAPI has different endpoints for movies and shows
            movie_results = []
            show_results = []
            
            # Fetch popular movies
            for service in streaming_services:
                req_path = f"/search/basic?country=us&service={service}&type=movie&page=1&language=en&sort_by=popularity"
                conn.request("GET", req_path, headers=headers)
                res = conn.getresponse()
                data = res.read().decode('utf-8')
                
                try:
                    content_data = json.loads(data)
                    if "results" in content_data:
                        movie_results.extend(content_data["results"])
                except Exception as e:
                    print(f"Error parsing movie results for {service}: {str(e)}")
            
            # Fetch popular TV shows
            for service in streaming_services:
                req_path = f"/search/basic?country=us&service={service}&type=series&page=1&language=en&sort_by=popularity"
                conn.request("GET", req_path, headers=headers)
                res = conn.getresponse()
                data = res.read().decode('utf-8')
                
                try:
                    content_data = json.loads(data)
                    if "results" in content_data:
                        show_results.extend(content_data["results"])
                except Exception as e:
                    print(f"Error parsing show results for {service}: {str(e)}")
            
            # Process and store movies
            for movie in movie_results:
                movie_id = movie.get("imdbId")
                if not movie_id:
                    continue
                    
                # Map RapidAPI structure to our structure
                formatted_movie = {
                    "id": movie_id,
                    "title": movie.get("title", ""),
                    "year": movie.get("year", ""),
                    "content_type": "movie",
                    "service_ids": [REVERSE_SERVICE_MAPPING.get(s, s) for s in movie.get("streamingInfo", {}).get("us", {})],
                    "poster_url": movie.get("posterURLs", {}).get("original") or movie.get("posterURLs", {}).get("500"),
                    "plot_overview": movie.get("overview", ""),
                    "cached_at": current_time
                }
                
                db.content_cache.update_one(
                    {"id": movie_id},
                    {"$set": formatted_movie},
                    upsert=True
                )
            
            # Process and store TV shows
            for show in show_results:
                show_id = show.get("imdbId")
                if not show_id:
                    continue
                    
                # Map RapidAPI structure to our structure
                formatted_show = {
                    "id": show_id,
                    "title": show.get("title", ""),
                    "year": show.get("year", ""),
                    "content_type": "show",
                    "service_ids": [REVERSE_SERVICE_MAPPING.get(s, s) for s in show.get("streamingInfo", {}).get("us", {})],
                    "poster_url": show.get("posterURLs", {}).get("original") or show.get("posterURLs", {}).get("500"),
                    "plot_overview": show.get("overview", ""),
                    "cached_at": current_time
                }
                
                db.content_cache.update_one(
                    {"id": show_id},
                    {"$set": formatted_show},
                    upsert=True
                )
            
            # Update last refresh timestamp
            db.content_cache.update_one(
                {"type": "last_update"},
                {"$set": {"timestamp": current_time}},
                upsert=True
            )
            
            print(f"Successfully cached {len(movie_results)} movies and {len(show_results)} shows")
            return True
                
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
                conn = create_api_connection()  # Use helper function
                
                headers = {
                    'x-rapidapi-key': RAPIDAPI_KEY,
                    'x-rapidapi-host': RAPIDAPI_HOST
                }
                
                # Determine content type (movie or series)
                content_type = "movie" if cached_content.get("content_type") == "movie" else "series"
                
                # Make API request
                req_path = f"/get/{content_type}/id/{content_id}?country=us"
                conn.request("GET", req_path, headers=headers)
                
                res = conn.getresponse()
                data = res.read().decode('utf-8')
                
                try:
                    details = json.loads(data)
                    
                    # Transform the response to match our expected format
                    transformed_details = {
                        "id": content_id,
                        "title": details.get("title", cached_content.get("title", "")),
                        "year": details.get("year", cached_content.get("year", "")),
                        "runtime_minutes": details.get("runtime", 0),
                        "us_rating": details.get("rating", "Not Rated"),
                        "poster_url": (details.get("posterURLs", {}).get("original") or 
                                      details.get("posterURLs", {}).get("500") or 
                                      cached_content.get("poster_url", "")),
                        "plot_overview": details.get("overview", cached_content.get("plot_overview", "")),
                        "genre_names": [genre.get("name", "") for genre in details.get("genres", [])],
                        "cast": [cast.get("name", "") for cast in details.get("cast", [])],
                        "directors": [director.get("name", "") for director in details.get("directors", [])],
                        "sources": [],
                        "details_cached": True,
                        "content_type": cached_content.get("content_type", content_type)
                    }
                    
                    # Process streaming info
                    streaming_info = details.get("streamingInfo", {}).get("us", {})
                    for provider, info in streaming_info.items():
                        source_id = REVERSE_SERVICE_MAPPING.get(provider, "")
                        if source_id:
                            for stream_option in info:
                                transformed_details["sources"].append({
                                    "source_id": source_id,
                                    "name": provider,
                                    "type": stream_option.get("type", ""),
                                    "web_url": stream_option.get("link", "")
                                })
                    
                    # Update cache with details
                    db.content_cache.update_one(
                        {"id": content_id},
                        {"$set": transformed_details},
                        upsert=True
                    )
                    
                    return transformed_details
                except Exception as e:
                    print(f"Error parsing content details: {str(e)}")
            
            return None
            
        except Exception as e:
            print(f"Error getting content details: {str(e)}")
            return None
