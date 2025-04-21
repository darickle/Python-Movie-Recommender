"""
Darick Le
March 11 2025
This module handles the interaction with the RapidAPI service for streaming content.
It includes functions to refresh content, get discover content, and retrieve content details.
"""

import http.client
import json
import ssl  # Import ssl module for certificate handling
from pymongo import MongoClient
import certifi
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import random
import time  # Import for retry mechanism
import socket  # Import for setting socket timeout

# Load environment variables
load_dotenv()

# MongoDB setup
MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

# RapidAPI configuration
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', "250f7c809bmshbd07ebdd782a896p1cf5e6jsn9767ca4b28cf")
RAPIDAPI_HOST = "streaming-availability.p.rapidapi.com"

# Create a custom SSL context that doesn't verify certificates
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Set default socket timeout to prevent hanging connections
socket.setdefaulttimeout(8)  # 8 seconds timeout

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
    conn = http.client.HTTPSConnection(
        RAPIDAPI_HOST,
        context=ssl_context,  # Use our custom SSL context
        timeout=8  # 8 seconds timeout
    )
    return conn

# Helper function for API requests with retry mechanism
def make_api_request(path, max_retries=3, timeout=8):
    retries = 0
    while retries < max_retries:
        conn = None
        try:
            conn = create_api_connection()
            headers = {
                'x-rapidapi-key': RAPIDAPI_KEY,
                'x-rapidapi-host': RAPIDAPI_HOST
            }
            conn.request("GET", path, headers=headers)
            
            # Use a timeout for the response
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = conn.getresponse()
                    data = response.read().decode('utf-8')
                    return json.loads(data)
                except http.client.ResponseNotReady:
                    time.sleep(0.1)  # Small wait before retry
            
            # If we get here, the timeout was exceeded
            raise TimeoutError("Response timed out")
                
        except (socket.timeout, TimeoutError) as e:
            print(f"Timeout error (attempt {retries+1}/{max_retries}): {str(e)}")
            retries += 1
            if retries < max_retries:
                time.sleep(1)  # Wait 1 second before retry
        except Exception as e:
            print(f"API request failed (attempt {retries+1}/{max_retries}): {str(e)}")
            retries += 1
            if retries < max_retries:
                time.sleep(2 ** retries)  # Exponential backoff
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
            
    print("Max retries reached, returning cached content if available")
    return {}

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
            
            # If the user has multiple services, only refresh one at a time to avoid timeouts
            if len(service_ids) > 1:
                # Select one random service to refresh
                selected_service_id = random.choice(service_ids)
                service_ids = [selected_service_id]
                print(f"Multiple services detected. Only refreshing content for: {selected_service_id}")
                
            print(f"Refreshing content for services: {service_ids}")
            
            # Map our service IDs to RapidAPI service names
            streaming_services = []
            for service_id in service_ids:
                if service_id in SERVICE_MAPPING:
                    streaming_services.append(SERVICE_MAPPING[service_id])
            
            if not streaming_services:
                print("No valid streaming services to query")
                return False
            
            # We'll fetch both movies and shows
            movie_results = []
            show_results = []
            
            # Fetch popular movies for the top service, with lower timeout
            for service in streaming_services[:1]:  # Only use the first service
                req_path = f"/search/basic?country=us&service={service}&type=movie&page=1&language=en&sort_by=popularity"
                content_data = make_api_request(req_path, timeout=5)
                
                if "results" in content_data:
                    movie_results.extend(content_data["results"])
            
            # Process movies first to ensure we have some content
            if movie_results:
                for movie in movie_results[:20]:  # Limit to 20 movies to process quickly
                    movie_id = movie.get("imdbId")
                    if not movie_id:
                        continue
                        
                    # Extract streaming services directly from the movie data
                    movie_services = list(movie.get("streamingInfo", {}).get("us", {}).keys())
                    service_ids_for_movie = [REVERSE_SERVICE_MAPPING.get(s) for s in movie_services if s in REVERSE_SERVICE_MAPPING]
                    
                    # Map RapidAPI structure to our structure
                    formatted_movie = {
                        "id": movie_id,
                        "title": movie.get("title", ""),
                        "year": movie.get("year", ""),
                        "content_type": "movie",
                        "service_ids": service_ids_for_movie,
                        "poster_url": movie.get("posterURLs", {}).get("original") or movie.get("posterURLs", {}).get("500"),
                        "plot_overview": movie.get("overview", ""),
                        "cached_at": current_time
                    }
                    
                    db.content_cache.update_one(
                        {"id": movie_id},
                        {"$set": formatted_movie},
                        upsert=True
                    )
            
            # Now fetch shows if we have time
            if movie_results:  # Only fetch shows if we successfully got movies
                for service in streaming_services[:1]:  # Only use the first service
                    req_path = f"/search/basic?country=us&service={service}&type=series&page=1&language=en&sort_by=popularity"
                    content_data = make_api_request(req_path, timeout=5)
                    
                    if "results" in content_data:
                        show_results.extend(content_data["results"])
                
                # Process and store TV shows
                for show in show_results[:20]:  # Limit to 20 shows
                    show_id = show.get("imdbId")
                    if not show_id:
                        continue
                    
                    # Extract streaming services directly from the show data
                    show_services = list(show.get("streamingInfo", {}).get("us", {}).keys())
                    service_ids_for_show = [REVERSE_SERVICE_MAPPING.get(s) for s in show_services if s in REVERSE_SERVICE_MAPPING]
                    
                    # Map RapidAPI structure to our structure
                    formatted_show = {
                        "id": show_id,
                        "title": show.get("title", ""),
                        "year": show.get("year", ""),
                        "content_type": "show",
                        "service_ids": service_ids_for_show,
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
    def get_discover_content(user_services=None):
        """Get content for discover feature with timeout handling, ensuring both movies and shows appear."""
        try:
            # Track what we've already seen to ensure variety
            content_types_seen = []
            
            # If user has services, try to get content for them
            if (user_services and len(user_services) > 0):
                # Convert to strings
                user_services = [str(sid) for sid in user_services]
                
                # First check if we have cached content for these services
                # Try to balance movies and shows
                for content_type in ["movie", "show"]:
                    if random.choice([True, False]):  # 50% chance to choose this type first
                        cached_content = list(db.content_cache.find(
                            {
                                "service_ids": {"$in": user_services},
                                "content_type": content_type
                            },
                            {"_id": 0}
                        ).limit(50))
                        
                        if cached_content:
                            content_types_seen.append(content_type)
                            return random.choice(cached_content)
                
                # If we don't have specific content type or the random check failed, get any type
                cached_content = list(db.content_cache.find(
                    {"service_ids": {"$in": user_services}},
                    {"_id": 0}
                ).limit(100))
                
                if cached_content and len(cached_content) > 5:
                    # We have enough cached content, return a random one
                    return random.choice(cached_content)
                
                # If not enough cached content, try direct API calls for both content types
                valid_services = []
                for service_id in user_services:
                    if service_id in SERVICE_MAPPING:
                        valid_services.append(SERVICE_MAPPING[service_id])
                
                if valid_services:
                    # Select random service from user's services
                    service = random.choice(valid_services)
                    
                    # Try both content types with 50/50 chance of which to try first
                    content_types = ["movie", "series"]
                    if random.choice([True, False]):
                        content_types.reverse()
                    
                    # Try first content type
                    req_path = f"/search/basic?country=us&service={service}&type={content_types[0]}&page=1&language=en&sort_by=popularity"
                    content_data = make_api_request(req_path, max_retries=2, timeout=5)
                    
                    if "results" in content_data and content_data["results"]:
                        item = random.choice(content_data["results"])
                        
                        # Transform to our format
                        item_id = item.get("imdbId")
                        if item_id:
                            transformed_item = {
                                "id": item_id,
                                "title": item.get("title", ""),
                                "year": item.get("year", ""),
                                "content_type": "movie" if content_types[0] == "movie" else "show",
                                "runtime_minutes": item.get("runtime", 0),
                                "us_rating": item.get("rating", "Not Rated"),
                                "poster_url": (item.get("posterURLs", {}).get("original") or 
                                              item.get("posterURLs", {}).get("500", "")),
                                "plot_overview": item.get("overview", ""),
                                "service_ids": user_services,
                                "streaming_service": service
                            }
                            
                            # Cache this item
                            db.content_cache.update_one(
                                {"id": item_id},
                                {"$set": transformed_item},
                                upsert=True
                            )
                            
                            return transformed_item
                    
                    # If first content type failed, try second one
                    req_path = f"/search/basic?country=us&service={service}&type={content_types[1]}&page=1&language=en&sort_by=popularity"
                    content_data = make_api_request(req_path, max_retries=2, timeout=5)
                    
                    if "results" in content_data and content_data["results"]:
                        item = random.choice(content_data["results"])
                        
                        # Transform to our format
                        item_id = item.get("imdbId")
                        if item_id:
                            transformed_item = {
                                "id": item_id,
                                "title": item.get("title", ""),
                                "year": item.get("year", ""),
                                "content_type": "movie" if content_types[1] == "movie" else "show",
                                "runtime_minutes": item.get("runtime", 0),
                                "us_rating": item.get("rating", "Not Rated"),
                                "poster_url": (item.get("posterURLs", {}).get("original") or 
                                              item.get("posterURLs", {}).get("500", "")),
                                "plot_overview": item.get("overview", ""),
                                "service_ids": user_services,
                                "streaming_service": service
                            }
                            
                            # Cache this item
                            db.content_cache.update_one(
                                {"id": item_id},
                                {"$set": transformed_item},
                                upsert=True
                            )
                            
                            return transformed_item
            
            # If no services or API call failed, get a random item from cache
            # Try to balance movies and shows
            content_type_to_try = random.choice(["movie", "show"])
            sample_content = list(db.content_cache.find(
                {
                    "id": {"$exists": True, "$ne": "last_update"},
                    "content_type": content_type_to_try
                },
                {"_id": 0}
            ).limit(30))
            
            if sample_content:
                return random.choice(sample_content)
            
            # If specific content type search failed, try any type
            sample_content = list(db.content_cache.find(
                {"id": {"$exists": True, "$ne": "last_update"}},
                {"_id": 0}
            ).limit(30))
            
            if sample_content:
                return random.choice(sample_content)
                
            # Last resort: return one of these popular movies/shows randomly
            popular_fallbacks = [
                # Movies
                {
                    "id": "tt0111161",
                    "title": "The Shawshank Redemption",
                    "year": "1994",
                    "content_type": "movie",
                    "runtime_minutes": 142,
                    "us_rating": "R",
                    "poster_url": "https://m.media-amazon.com/images/M/MV5BNDE3ODcxYzMtY2YzZC00NmNlLWJiNDMtZDViZWM2MzIxZDYwXkEyXkFqcGdeQXVyNjAwNDUxODI@._V1_.jpg",
                    "plot_overview": "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
                    "service_ids": user_services or [],
                    "streaming_service": "netflix" if "203" in (user_services or []) else None
                },
                {
                    "id": "tt0068646",
                    "title": "The Godfather",
                    "year": "1972",
                    "content_type": "movie",
                    "runtime_minutes": 175,
                    "us_rating": "R",
                    "poster_url": "https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTYxLWJmNWYtYzZlODY3ZTk3OTFlXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_.jpg",
                    "plot_overview": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
                    "service_ids": user_services or [],
                    "streaming_service": "prime" if "26" in (user_services or []) else None
                },
                # TV Shows
                {
                    "id": "tt0944947",
                    "title": "Game of Thrones",
                    "year": "2011",
                    "content_type": "show",
                    "runtime_minutes": 60,
                    "us_rating": "TV-MA",
                    "poster_url": "https://m.media-amazon.com/images/M/MV5BYTRiNDQwYzAtMzVlZS00NTI5LWJjYjUtMzkwNTUzMWMxZTllXkEyXkFqcGdeQXVyNjIyNDgwMzM@._V1_.jpg",
                    "plot_overview": "Nine noble families fight for control over the lands of Westeros, while an ancient enemy returns after being dormant for millennia.",
                    "service_ids": user_services or [],
                    "streaming_service": "hbo" if "387" in (user_services or []) else None
                },
                {
                    "id": "tt0108778",
                    "title": "Friends",
                    "year": "1994",
                    "content_type": "show",
                    "runtime_minutes": 22,
                    "us_rating": "TV-14",
                    "poster_url": "https://m.media-amazon.com/images/M/MV5BNDVkYjU0MzctMWRmZi00NTkxLTgwZWEtOWVhYjZlYjllYmU4XkEyXkFqcGdeQXVyNTA4NzY1MzY@._V1_.jpg",
                    "plot_overview": "Follows the personal and professional lives of six twenty to thirty-something-year-old friends living in Manhattan.",
                    "service_ids": user_services or [],
                    "streaming_service": "hbo" if "387" in (user_services or []) else None
                },
                {
                    "id": "tt0455275",
                    "title": "The Office",
                    "year": "2005",
                    "content_type": "show",
                    "runtime_minutes": 22,
                    "us_rating": "TV-14",
                    "poster_url": "https://m.media-amazon.com/images/M/MV5BMDNkOTE4NDQtMTNmYi00MWE0LWE4ZTktYTc0NzhhNWIzNzJiXkEyXkFqcGdeQXVyMzQ2MDI5NjU@._V1_.jpg", 
                    "plot_overview": "A mockumentary on a group of typical office workers, where the workday consists of ego clashes, inappropriate behavior, and tedium.",
                    "service_ids": user_services or [],
                    "streaming_service": "peacock" if "389" in (user_services or []) else None
                }
            ]
            
            # Choose based on content type balance
            movies = [item for item in popular_fallbacks if item["content_type"] == "movie"]
            shows = [item for item in popular_fallbacks if item["content_type"] == "show"]
            
            if not content_types_seen:
                # If no preference yet, choose randomly between movies and shows
                if random.choice([True, False]):
                    return random.choice(movies)
                else:
                    return random.choice(shows)
            elif "movie" in content_types_seen:
                # If we've seen movies, try to return a show
                return random.choice(shows)
            else:
                # If we've seen shows, try to return a movie
                return random.choice(movies)
            
        except Exception as e:
            print(f"Error getting discover content: {str(e)}")
            # Return a random fallback content item from movies and shows
            popular_fallbacks = [
                # Movie fallbacks
                {
                    "id": "tt0111161",
                    "title": "The Shawshank Redemption",
                    "year": "1994",
                    "content_type": "movie",
                    "runtime_minutes": 142,
                    "us_rating": "R",
                    "poster_url": "https://m.media-amazon.com/images/M/MV5BNDE3ODcxYzMtY2YzZC00NmNlLWJiNDMtZDViZWM2MzIxZDYwXkEyXkFqcGdeQXVyNjAwNDUxODI@._V1_.jpg",
                    "plot_overview": "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
                    "service_ids": user_services or []
                },
                # TV Show fallbacks
                {
                    "id": "tt0944947",
                    "title": "Game of Thrones",
                    "year": "2011",
                    "content_type": "show",
                    "runtime_minutes": 60,
                    "us_rating": "TV-MA",
                    "poster_url": "https://m.media-amazon.com/images/M/MV5BYTRiNDQwYzAtMzVlZS00NTI5LWJjYjUtMzkwNTUzMWMxZTllXkEyXkFqcGdeQXVyNjIyNDgwMzM@._V1_.jpg",
                    "plot_overview": "Nine noble families fight for control over the lands of Westeros, while an ancient enemy returns after being dormant for millennia.",
                    "service_ids": user_services or []
                }
            ]
            
            # Randomly choose between movie and show
            return random.choice(popular_fallbacks)

    @staticmethod
    def get_content_for_services(service_ids, content_type=None, limit=50):
        """Retrieve cached content for specified streaming services."""
        try:
            # Convert service_ids to strings
            service_ids = [str(sid) for sid in service_ids]
            
            # If no service IDs, try to return some default content
            if not service_ids:
                # Default query with no service filter
                query = {}
                if content_type:
                    query["content_type"] = content_type
                
                # Get any cached content we have
                content = list(db.content_cache.find(
                    query,
                    {"_id": 0}  # Exclude MongoDB _id
                ).limit(limit))
                
                if content:
                    return content
                
                # If no cached content, fetch some popular content directly
                return StreamingService.get_popular_content(content_type, limit)
            
            # Build query with service IDs
            query = {"service_ids": {"$in": service_ids}}
            if content_type:
                query["content_type"] = content_type
            
            # Get content from cache
            content = list(db.content_cache.find(
                query,
                {"_id": 0}  # Exclude MongoDB _id
            ).limit(limit))
            
            # If we don't have enough content, try refreshing the cache
            if len(content) < 10:
                print(f"Not enough content in cache ({len(content)} items), refreshing...")
                StreamingService.refresh_content_for_services(service_ids)
                
                # Try again after refreshing
                content = list(db.content_cache.find(
                    query,
                    {"_id": 0}
                ).limit(limit))
                
                # If still not enough, get popular content
                if len(content) < 10:
                    popular_content = StreamingService.get_popular_content(content_type, limit - len(content))
                    content.extend(popular_content)
            
            return content
            
        except Exception as e:
            print(f"Error retrieving content: {str(e)}")
            return []
    
    @staticmethod
    def get_popular_content(content_type=None, limit=20):
        """Fetch popular content as fallback when cache is empty."""
        try:
            content_results = []
            
            # Determine content types to fetch
            content_types = []
            if content_type == "movie":
                content_types = ["movie"]
            elif content_type == "show":
                content_types = ["series"]
            else:
                content_types = ["movie", "series"]
            
            # Fetch each content type
            for ctype in content_types:
                req_path = f"/search/basic?country=us&type={ctype}&page=1&language=en&sort_by=popularity"
                data = make_api_request(req_path)
                
                if "results" in data:
                    for item in data["results"][:limit//len(content_types)]:
                        item_id = item.get("imdbId")
                        if not item_id:
                            continue
                            
                        # Transform the item
                        transformed_item = {
                            "id": item_id,
                            "title": item.get("title", ""),
                            "year": item.get("year", ""),
                            "content_type": "movie" if ctype == "movie" else "show",
                            "service_ids": [],  # No specific service since this is general popular content
                            "poster_url": (item.get("posterURLs", {}).get("original") or 
                                          item.get("posterURLs", {}).get("500")),
                            "plot_overview": item.get("overview", "")
                        }
                        
                        content_results.append(transformed_item)
            
            return content_results
            
        except Exception as e:
            print(f"Error fetching popular content: {str(e)}")
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
                # Determine content type (movie or series)
                content_type = "movie" if cached_content.get("content_type") == "movie" else "series"
                
                # Make API request
                req_path = f"/get/{content_type}/id/{content_id}?country=us"
                details = make_api_request(req_path)
                
                if details:
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
            
            # If not in cache, attempt direct lookup
            # Try as movie first
            req_path = f"/get/movie/id/{content_id}?country=us"
            movie_details = make_api_request(req_path)
            
            if movie_details and "title" in movie_details:
                # Process as movie
                return StreamingService._process_content_details(movie_details, content_id, "movie")
            
            # Try as TV series
            req_path = f"/get/series/id/{content_id}?country=us"
            show_details = make_api_request(req_path)
            
            if show_details and "title" in show_details:
                # Process as show
                return StreamingService._process_content_details(show_details, content_id, "show")
            
            return None
            
        except Exception as e:
            print(f"Error getting content details: {str(e)}")
            return None
    
    @staticmethod
    def _process_content_details(details, content_id, content_type):
        """Helper method to process API content details into our format."""
        transformed_details = {
            "id": content_id,
            "title": details.get("title", ""),
            "year": details.get("year", ""),
            "runtime_minutes": details.get("runtime", 0),
            "us_rating": details.get("rating", "Not Rated"),
            "poster_url": (details.get("posterURLs", {}).get("original") or 
                          details.get("posterURLs", {}).get("500", "")),
            "plot_overview": details.get("overview", ""),
            "genre_names": [genre.get("name", "") for genre in details.get("genres", [])],
            "cast": [cast.get("name", "") for cast in details.get("cast", [])],
            "directors": [director.get("name", "") for director in details.get("directors", [])],
            "sources": [],
            "details_cached": True,
            "content_type": content_type
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
        
        # Cache the details
        db.content_cache.update_one(
            {"id": content_id},
            {"$set": transformed_details},
            upsert=True
        )
        
        return transformed_details
