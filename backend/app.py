"""
Darick Le
March 11 2025
This program is a Flask API that connects to a MongoDB database and provides endpoints for user registration
, login, and content recommendations. It includes methods to handle user preferences, streaming services,
and content search using RapidAPI. The API also implements JWT authentication for secure access to user data.
"""

from flask import Flask, request, jsonify
import http.client
import json
import os
import ssl  # Import ssl module
from flask_cors import CORS
from bson.objectid import ObjectId
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
import config  # Import config.py
from pymongo import MongoClient, IndexModel
from pymongo.server_api import ServerApi
import bcrypt  # Add bcrypt for password hashing
import certifi
from functools import wraps
import random

# Create a custom SSL context that doesn't verify certificates
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Disable SSL certificate verification for the entire application
# This is not recommended for production, but can help in development
import urllib3
urllib3.disable_warnings()

app = Flask(__name__)
# Update CORS configuration to properly handle preflight requests
CORS(app, resources={r"/*": {
    "origins": ["http://localhost:3000"], 
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}}, supports_credentials=True)

# Configuration
app.config["MONGO_URI"] = config.MONGO_URI
app.config["JWT_SECRET_KEY"] = config.JWT_SECRET_KEY
app.config["JWT_ERROR_MESSAGE_KEY"] = "error"

# Use pymongo directly
client = MongoClient(
    config.MONGO_URI,
    server_api=ServerApi('1'),
    tls=True,
    tlsCAFile=certifi.where()
)

# Replace PyMongo initialization with the new client
db = client.get_database()  # Ensure db is the correct database object

# Send a ping to confirm a successful connection
def ensure_mongo_connection():
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        return True
    except Exception as e:
        app.logger.error(f"Failed to connect to MongoDB: {e}")
        return False

# Initialize JWT after ensuring MongoDB connection
jwt = JWTManager(app)

# Helper function to validate request data
def validate_request_data(required_fields):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({"error": "Missing request data"}), 400
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
                
            return f(*args, **kwargs)
        return wrapper
    return decorator

# RapidAPI configuration
RAPIDAPI_KEY = config.RAPIDAPI_KEY
RAPIDAPI_HOST = config.RAPIDAPI_HOST

# Service ID mapping between our system and RapidAPI
SERVICE_MAPPING = {
    "203": "netflix",  # Netflix
    "26": "prime",     # Amazon Prime
    "372": "disney",   # Disney+
    "157": "hulu",     # Hulu
    "387": "hbo",      # HBO Max
    "444": "paramount", # Paramount+
    "389": "peacock",   # Peacock
    "371": "apple",     # Apple TV+
    "442": "discovery", # Discovery+
    "443": "espn"       # ESPN+
}

REVERSE_SERVICE_MAPPING = {v: k for k, v in SERVICE_MAPPING.items()}

# Helper function to create an HTTP connection with SSL context
def create_api_connection():
    return http.client.HTTPSConnection(
        RAPIDAPI_HOST,
        context=ssl_context  # Use our custom SSL context
    )

# Helper function for API requests with retry mechanism
def make_api_request(path, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            conn = create_api_connection()
            headers = {
                'x-rapidapi-key': RAPIDAPI_KEY,
                'x-rapidapi-host': RAPIDAPI_HOST
            }
            conn.request("GET", path, headers=headers)
            response = conn.getresponse()
            data = response.read().decode('utf-8')
            return json.loads(data)
        except Exception as e:
            print(f"API request failed (attempt {retries+1}/{max_retries}): {str(e)}")
            retries += 1
            if retries < max_retries:
                # Exponential backoff: wait longer between each retry
                import time
                time.sleep(2 ** retries)
        finally:
            try:
                conn.close()
            except:
                pass
    return {}

# Get list of available streaming services
@app.route("/api/streaming_services", methods=["GET"])
def get_streaming_services():
    # Define the top 10 streaming services
    TOP_STREAMING_SERVICES = [
        {"source_id": 203, "name": "Netflix", "type": "sub"},
        {"source_id": 26, "name": "Amazon Prime Video", "type": "sub"},
        {"source_id": 372, "name": "Disney+", "type": "sub"},
        {"source_id": 157, "name": "Hulu", "type": "sub"},
        {"source_id": 387, "name": "HBO Max", "type": "sub"},
        {"source_id": 444, "name": "Paramount+", "type": "sub"},
        {"source_id": 389, "name": "Peacock", "type": "sub"},
        {"source_id": 371, "name": "Apple TV+", "type": "sub"},
        {"source_id": 442, "name": "Discovery+", "type": "sub"},
        {"source_id": 443, "name": "ESPN+", "type": "sub"}
    ]
    
    return jsonify(TOP_STREAMING_SERVICES)

@app.route("/api/register", methods=["POST"])
@validate_request_data(["email", "password"])
def register():
    print("Register endpoint reached")
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        
        # Check if user already exists
        if db.users.find_one({"email": email}):
            return jsonify({"error": "User already exists"}), 400
        
        # Hash the password (store as a string)
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        
        # Create user object
        user = {
            "email": email,
            "password": hashed_password,
            "streaming_services": data.get("streaming_services", []),
            "preferences": data.get("preferences", {}),
            "created_at": pd.Timestamp.now(),
        }
        
        # Insert user into the database
        result = db.users.insert_one(user)
        user_id = str(result.inserted_id)
        
        # Create access token
        access_token = create_access_token(identity=user_id)
        
        return jsonify({"message": "User registered successfully", "token": access_token}), 201
        
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({"error": "Registration failed", "details": str(e)}), 500

@app.route("/api/login", methods=["POST"])
@validate_request_data(["email", "password"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    # Find user by email
    user = db.users.find_one({"email": email})
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Verify the password
    if not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Create JWT token
    access_token = create_access_token(identity=str(user["_id"]))
    
    return jsonify({
        "token": access_token,
        "user": {
            "email": user["email"],
            "streaming_services": user.get("streaming_services", []),
            "preferences": user.get("preferences", {})
        }
    }), 200

# Get user's streaming services
@app.route("/api/user/streaming_services", methods=["GET"])
@jwt_required()
def get_user_streaming_services():
    user_id = get_jwt_identity()
    
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({"streaming_services": user.get("streaming_services", [])}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get user streaming services: {str(e)}"}), 500

# Update user streaming services
@app.route("/api/user/streaming_services", methods=["PUT"])
@jwt_required()
@validate_request_data(["streaming_services"])
def update_streaming_services():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        # Update user's streaming services
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"streaming_services": data["streaming_services"]}}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "User not found"}), 404
            
        # Import StreamingService here to avoid cyclic imports
        try:
            from backend.utils.streaming_services import StreamingService
            StreamingService.refresh_content_for_services(data["streaming_services"])
        except ImportError:
            # Try relative import if the above fails
            try:
                from utils.streaming_services import StreamingService
                StreamingService.refresh_content_for_services(data["streaming_services"])
            except ImportError:
                # If both fail, try importing from the root level
                from streaming_services import StreamingService
                StreamingService.refresh_content_for_services(data["streaming_services"])
                
        return jsonify({"message": "Streaming services updated successfully"}), 200
    except Exception as e:
        print(f"Failed to update streaming services: {str(e)}")
        return jsonify({"error": f"Failed to update streaming services: {str(e)}"}), 500

# Update user preferences
@app.route("/api/user/preferences", methods=["PUT"])
@jwt_required()
def update_user_preferences():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'preferences' not in data:
        return jsonify({"error": "Missing preferences data"}), 400
    
    try:
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"preferences": data["preferences"]}}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({"message": "Preferences updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to update preferences: {str(e)}"}), 500

# Add a simple status endpoint to test connectivity
@app.route("/api/status", methods=["GET"])
def api_status():
    print("Status endpoint was called!")  # Add this debug line
    return jsonify({"status": "online", "message": "API is running correctly"})

# Add an OPTIONS route handler to handle preflight requests
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return '', 200

# Search for content using RapidAPI
@app.route("/api/search", methods=["GET"])
def search_content():
    query = request.args.get("query", "")
    
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    try:
        conn = create_api_connection()  # Use helper function
        
        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': RAPIDAPI_HOST
        }
        
        # Make API request to search endpoint
        req_path = f"/search/title?title={query}&country=us&show_type=all&output_language=en"
        conn.request("GET", req_path, headers=headers)
        
        res = conn.getresponse()
        data = res.read().decode('utf-8')
        
        try:
            content_data = json.loads(data)
            
            if "result" in content_data:
                results = content_data["result"]
                
                # Transform to match expected format
                transformed_results = []
                for item in results:
                    transformed_item = {
                        "id": item.get("imdbId"),
                        "title": item.get("title", ""),
                        "year": item.get("year", ""),
                        "poster_url": (item.get("posterURLs", {}).get("original") or 
                                      item.get("posterURLs", {}).get("500", "")),
                        "content_type": "movie" if item.get("type") == "movie" else "show"
                    }
                    transformed_results.append(transformed_item)
                    
                    # Cache results in database
                    db.content.update_one(
                        {"id": transformed_item["id"]},
                        {"$set": transformed_item},
                        upsert=True
                    )
                
                return jsonify(transformed_results)
            else:
                return jsonify([])
                
        except Exception as e:
            print(f"Error parsing search results: {str(e)}")
            return jsonify({"error": f"Failed to parse search results: {str(e)}"}), 500
    
    except Exception as e:
        print(f"Error searching content: {str(e)}")
        return jsonify({"error": f"Failed to search content: {str(e)}"}), 500

# Get content details with streaming availability
@app.route("/api/content/<content_id>", methods=["GET"])
@jwt_required()
def get_content_details(content_id):
    user_id = get_jwt_identity()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    user_services = user.get("streaming_services", []) if user else []
    
    # Check if we have this cached with recent sources data
    cached_content = db.content_details.find_one({"id": content_id})
    
    # If cached, return cached data
    if cached_content and cached_content.get("details_cached"):
        # Ensure we only include sources available on user's services if they have any
        if user_services and "sources" in cached_content:
            filtered_sources = [
                source for source in cached_content["sources"]
                if str(source.get("source_id", "")) in user_services
            ]
            cached_content["sources"] = filtered_sources
        
        return jsonify(cached_content)
    
    # Determine content type for API request
    content_type_check = db.content.find_one({"id": content_id})
    content_type = "movie" if content_type_check and content_type_check.get("content_type") == "movie" else "series"
    
    try:
        # Fetch from RapidAPI
        conn = create_api_connection()  # Use helper function
        
        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': RAPIDAPI_HOST
        }
        
        # Make API request
        req_path = f"/get/{content_type}/id/{content_id}?country=us"
        conn.request("GET", req_path, headers=headers)
        
        res = conn.getresponse()
        data = res.read().decode('utf-8')
        
        try:
            content_data = json.loads(data)
            
            # Transform to match expected format
            transformed_details = {
                "id": content_id,
                "title": content_data.get("title", ""),
                "year": content_data.get("year", ""),
                "runtime_minutes": content_data.get("runtime", 0),
                "us_rating": content_data.get("rating", "Not Rated"),
                "poster_url": (content_data.get("posterURLs", {}).get("original") or 
                              content_data.get("posterURLs", {}).get("500", "")),
                "plot_overview": content_data.get("overview", ""),
                "genre_names": [genre.get("name", "") for genre in content_data.get("genres", [])],
                "cast": [cast.get("name", "") for cast in content_data.get("cast", [])],
                "directors": [director.get("name", "") for director in content_data.get("directors", [])],
                "sources": [],
                "details_cached": True,
                "content_type": content_type
            }
            
            # Process streaming info
            streaming_info = content_data.get("streamingInfo", {}).get("us", {})
            for provider, info in streaming_info.items():
                source_id = REVERSE_SERVICE_MAPPING.get(provider, "")
                if source_id and (not user_services or source_id in user_services):
                    for stream_option in info:
                        transformed_details["sources"].append({
                            "source_id": source_id,
                            "name": provider,
                            "type": stream_option.get("type", ""),
                            "web_url": stream_option.get("link", "")
                        })
            
            # Cache in database
            db.content_details.update_one(
                {"id": content_id},
                {"$set": transformed_details},
                upsert=True
            )
            
            return jsonify(transformed_details)
            
        except Exception as e:
            print(f"Error parsing content details: {str(e)}")
            return jsonify({"error": f"Failed to parse content details: {str(e)}"}), 500
    
    except Exception as e:
        print(f"Error fetching content details: {str(e)}")
        return jsonify({"error": f"Failed to fetch content details: {str(e)}"}), 500

# Helper function to check if content is available on user's streaming services
def is_available_on_user_services(sources, user_services):
    if not sources or not user_services:
        return False
    
    # Convert both to strings for comparison
    user_services = [str(service_id) for service_id in user_services]
    
    for source in sources:
        source_id = str(source.get("source_id", ""))
        if source_id in user_services:
            return True
    return False

# Get personalized recommendations
@app.route("/api/recommendations", methods=["GET"])
@jwt_required()
def get_recommendations():
    user_id = get_jwt_identity()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if not user.get("streaming_services"):
        return jsonify([]), 200  # Return empty list if no streaming services
    
    # Get user's streaming services
    user_services = user.get("streaming_services", [])
    print(f"User streaming services: {user_services}")
    
    try:
        # Try to get the streaming service utility
        try:
            from backend.utils.streaming_services import StreamingService
        except ImportError:
            try:
                from utils.streaming_services import StreamingService
            except ImportError:
                from streaming_services import StreamingService
        
        # Try to get content from cache first
        cached_content = StreamingService.get_content_for_services(user_services, limit=20)
        
        if cached_content and len(cached_content) >= 10:
            print(f"Using {len(cached_content)} cached items for recommendations")
            return jsonify(cached_content)
        
        # If not enough cached content, make API requests
        # Convert our service IDs to RapidAPI service names
        rapidapi_services = []
        for service_id in user_services:
            if service_id in SERVICE_MAPPING:
                rapidapi_services.append(SERVICE_MAPPING[service_id])
        
        # If no valid services, return empty list
        if not rapidapi_services:
            return jsonify([]), 200
        
        # Choose a random service
        selected_service = random.choice(rapidapi_services)
        
        # Get user genre preferences if available
        genres = []
        if user.get("preferences") and user["preferences"].get("genres"):
            genres = user["preferences"]["genres"]
        
        # If we have genre preferences, use them
        genre_query = ""
        if genres:
            # Randomly select one genre from user preferences
            selected_genre = random.choice(genres).lower().replace(" ", "-")
            genre_query = f"&genre={selected_genre}"
        
        # Make API request for movies
        req_path = f"/search/basic?country=us&service={selected_service}&type=movie{genre_query}&page=1&language=en&sort_by=popularity"
        movie_data = make_api_request(req_path)
        recommended_movies = movie_data.get("results", [])
        
        # Make API request for TV shows
        req_path = f"/search/basic?country=us&service={selected_service}&type=series{genre_query}&page=1&language=en&sort_by=popularity"
        show_data = make_api_request(req_path)
        recommended_shows = show_data.get("results", [])
        
        # Combine and shuffle recommendations
        recommended_content = recommended_movies + recommended_shows
        random.shuffle(recommended_content)
        
        # Transform to match expected format
        transformed_recommendations = []
        for item in recommended_content[:20]:
            transformed_item = {
                "id": item.get("imdbId"),
                "title": item.get("title", ""),
                "year": item.get("year", ""),
                "runtime_minutes": item.get("runtime", 0),
                "us_rating": item.get("rating", "Not Rated"),
                "poster_url": (item.get("posterURLs", {}).get("original") or 
                              item.get("posterURLs", {}).get("500", "")),
                "plot_overview": item.get("overview", ""),
                "content_type": "movie" if item.get("type") == "movie" else "show"
            }
            transformed_recommendations.append(transformed_item)
            
            # Cache in database for future use
            db.content.update_one(
                {"id": transformed_item["id"]},
                {"$set": transformed_item},
                upsert=True
            )
        
        return jsonify(transformed_recommendations)
        
    except Exception as e:
        print(f"Error getting recommendations: {str(e)}")
        
        # Try to get content from cache as fallback
        try:
            fallback_content = list(db.content.find(
                {},  # No filter, get any content
                {"_id": 0}
            ).limit(20))
            
            if fallback_content:
                print(f"Returning {len(fallback_content)} fallback items from cache")
                return jsonify(fallback_content)
        except Exception as cache_error:
            print(f"Error retrieving fallback content: {str(cache_error)}")
            
        return jsonify({"error": f"Failed to get recommendations: {str(e)}"}), 500

# Get trending content available on user's services
@app.route("/api/trending", methods=["GET"])
@jwt_required()
def get_trending():
    user_id = get_jwt_identity()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    if not user.get("streaming_services"):
        return jsonify([]), 200  # Return empty list if no streaming services
    
    user_services = user.get("streaming_services", [])
    print(f"User streaming services for trending: {user_services}")
    
    # Convert our service IDs to RapidAPI service names
    rapidapi_services = []
    for service_id in user_services:
        if service_id in SERVICE_MAPPING:
            rapidapi_services.append(SERVICE_MAPPING[service_id])
    
    # If no valid services, return empty list
    if not rapidapi_services:
        return jsonify([]), 200
    
    # Choose a random service to get trending content from
    selected_service = random.choice(rapidapi_services)
    
    try:
        # Use our helper function for API requests
        req_path = f"/search/basic?country=us&service={selected_service}&type=movie&page=1&language=en&sort_by=popularity"
        movie_data = make_api_request(req_path)
        trending_movies = movie_data.get("results", [])
        
        req_path = f"/search/basic?country=us&service={selected_service}&type=series&page=1&language=en&sort_by=popularity"
        show_data = make_api_request(req_path)
        trending_shows = show_data.get("results", [])
        
        # Combine and shuffle trending content
        trending_content = trending_movies + trending_shows
        random.shuffle(trending_content)
        
        # Transform to match expected format
        transformed_trending = []
        for item in trending_content[:10]:
            transformed_item = {
                "id": item.get("imdbId"),
                "title": item.get("title", ""),
                "year": item.get("year", ""),
                "runtime_minutes": item.get("runtime", 0),
                "us_rating": item.get("rating", "Not Rated"),
                "poster_url": (item.get("posterURLs", {}).get("original") or 
                              item.get("posterURLs", {}).get("500", "")),
                "plot_overview": item.get("overview", ""),
                "content_type": "movie" if item.get("type") == "movie" else "show"
            }
            transformed_trending.append(transformed_item)
            
            # Cache in database for future use
            db.content.update_one(
                {"id": transformed_item["id"]},
                {"$set": transformed_item},
                upsert=True
            )
        
        # Log response for debugging
        print(f"Returning {len(transformed_trending)} trending items")
        
        return jsonify(transformed_trending)
        
    except Exception as e:
        print(f"Error getting trending content: {str(e)}")
        
        # If we get an error, try to pull from cache as a fallback
        try:
            cached_content = list(db.content.find(
                {"content_type": {"$in": ["movie", "show"]}},
                {"_id": 0}
            ).limit(10))
            
            if cached_content:
                print(f"Returning {len(cached_content)} cached items as fallback")
                return jsonify(cached_content)
        except Exception as cache_error:
            print(f"Error retrieving cached content: {str(cache_error)}")
        
        return jsonify({"error": f"Failed to get trending content: {str(e)}"}), 500

# API endpoints for the discover page
@app.route("/api/discover/categories", methods=["GET"])
@jwt_required()
def get_discover_categories():
    user_id = get_jwt_identity()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    if not user.get("streaming_services"):
        return jsonify({}), 200  # Return empty object if no streaming services
    
    # Convert service IDs to RapidAPI service names
    rapidapi_services = []
    for service_id in user.get("streaming_services", []):
        if service_id in SERVICE_MAPPING:
            rapidapi_services.append(SERVICE_MAPPING[service_id])
    
    if not rapidapi_services:
        return jsonify({}), 200  # Return empty object if no valid services
    
    # Choose a random service from the user's services
    selected_service = random.choice(rapidapi_services)
    
    # Prepare content categories
    categories = {
        "Movies": [],
        "TV Shows": [],
        "Action & Adventure": [],
        "Comedy": [],
        "Drama": [],
        "Family": []
    }
    
    try:
        conn = create_api_connection()  # Use helper function
        
        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': RAPIDAPI_HOST
        }
        
        # Get movies for the selected service
        req_path = f"/search/basic?country=us&service={selected_service}&type=movie&page=1&language=en&sort_by=popularity"
        conn.request("GET", req_path, headers=headers)
        res = conn.getresponse()
        data = res.read().decode('utf-8')
        content_data = json.loads(data)
        categories["Movies"] = transform_content_items(content_data.get("results", [])[:10])
        
        # Get TV shows for the selected service
        req_path = f"/search/basic?country=us&service={selected_service}&type=series&page=1&language=en&sort_by=popularity"
        conn.request("GET", req_path, headers=headers)
        res = conn.getresponse()
        data = res.read().decode('utf-8')
        content_data = json.loads(data)
        categories["TV Shows"] = transform_content_items(content_data.get("results", [])[:10])
        
        # Get content for specific genres
        genre_mappings = {
            "Action & Adventure": "action",
            "Comedy": "comedy",
            "Drama": "drama",
            "Family": "family"
        }
        
        for category, genre in genre_mappings.items():
            # Get movies in this genre
            req_path = f"/search/basic?country=us&service={selected_service}&type=movie&page=1&language=en&genre={genre}&sort_by=popularity"
            conn.request("GET", req_path, headers=headers)
            res = conn.getresponse()
            data = res.read().decode('utf-8')
            content_data = json.loads(data)
            movies = content_data.get("results", [])[:5]
            
            # Get shows in this genre
            req_path = f"/search/basic?country=us&service={selected_service}&type=series&page=1&language=en&genre={genre}&sort_by=popularity"
            conn.request("GET", req_path, headers=headers)
            res = conn.getresponse()
            data = res.read().decode('utf-8')
            content_data = json.loads(data)
            shows = content_data.get("results", [])[:5]
            
            # Combine movies and shows for this genre
            combined = movies + shows
            categories[category] = transform_content_items(combined)
        
        return jsonify(categories)
        
    except Exception as e:
        print(f"Error getting discover categories: {str(e)}")
        return jsonify({"error": f"Failed to get discover categories: {str(e)}"}), 500

# Helper function to transform content items from RapidAPI format to our format
def transform_content_items(items):
    transformed_items = []
    for item in items:
        transformed_item = {
            "id": item.get("imdbId"),
            "title": item.get("title", ""),
            "year": item.get("year", ""),
            "runtime_minutes": item.get("runtime", 0),
            "us_rating": item.get("rating", "Not Rated"),
            "poster_url": (item.get("posterURLs", {}).get("original") or 
                          item.get("posterURLs", {}).get("500", "")),
            "plot_overview": item.get("overview", ""),
            "content_type": "movie" if item.get("type") == "movie" else "show"
        }
        transformed_items.append(transformed_item)
        
        # Cache in database for future use
        db.content.update_one(
            {"id": transformed_item["id"]},
            {"$set": transformed_item},
            upsert=True
        )
    
    return transformed_items

@app.route("/api/discover/category/<category_name>", methods=["GET"])
@jwt_required()
def get_category_content(category_name):
    user_id = get_jwt_identity()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user or not user.get("streaming_services"):
        return jsonify({"error": "User streaming services not set"}), 400
    
    # Convert service IDs to RapidAPI service names
    rapidapi_services = []
    for service_id in user.get("streaming_services", []):
        if service_id in SERVICE_MAPPING:
            rapidapi_services.append(SERVICE_MAPPING[service_id])
    
    if not rapidapi_services:
        return jsonify({"error": "No valid streaming services configured"}), 400
    
    # Choose a random service from the user's services
    selected_service = random.choice(rapidapi_services)
    
    try:
        conn = create_api_connection()  # Use helper function
        
        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': RAPIDAPI_HOST
        }
        
        content_type = None
        genre = None
        
        # Map category name to the appropriate parameters
        if category_name.lower() == "movies":
            content_type = "movie"
        elif category_name.lower() in ["tv", "tv shows", "shows"]:
            content_type = "series"
        else:
            # Try to map category to a genre
            genre_mappings = {
                "action & adventure": "action",
                "action": "action",
                "adventure": "adventure",
                "comedy": "comedy",
                "drama": "drama",
                "family": "family",
                "sci-fi": "sci-fi",
                "thriller": "thriller",
                "horror": "horror",
                "romance": "romance",
                "documentary": "documentary",
                "animation": "animation"
            }
            genre = genre_mappings.get(category_name.lower())
            
            if not genre:
                return jsonify({"error": f"Unknown category: {category_name}"}), 400
        
        results = []
        
        # If we have a specific content type (movie or series)
        if content_type:
            req_path = f"/search/basic?country=us&service={selected_service}&type={content_type}&page=1&language=en&sort_by=popularity"
            conn.request("GET", req_path, headers=headers)
            res = conn.getresponse()
            data = res.read().decode('utf-8')
            content_data = json.loads(data)
            results = content_data.get("results", [])
        
        # If we have a specific genre
        elif genre:
            # Get movies in this genre
            req_path = f"/search/basic?country=us&service={selected_service}&type=movie&page=1&language=en&genre={genre}&sort_by=popularity"
            conn.request("GET", req_path, headers=headers)
            res = conn.getresponse()
            data = res.read().decode('utf-8')
            content_data = json.loads(data)
            movies = content_data.get("results", [])
            
            # Get shows in this genre
            req_path = f"/search/basic?country=us&service={selected_service}&type=series&page=1&language=en&genre={genre}&sort_by=popularity"
            conn.request("GET", req_path, headers=headers)
            res = conn.getresponse()
            data = res.read().decode('utf-8')
            content_data = json.loads(data)
            shows = content_data.get("results", [])
            
            # Combine movies and shows for this genre
            results = movies + shows
        
        # Transform the results to our format
        transformed_results = transform_content_items(results)
        
        return jsonify(transformed_results)
        
    except Exception as e:
        print(f"Error getting category content: {str(e)}")
        return jsonify({"error": f"Failed to get category content: {str(e)}"}), 500

# Add content to watchlist
@app.route("/api/watchlist", methods=["POST"])
@jwt_required()
def add_to_watchlist():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    watchlist_item = {
        "user_id": user_id,
        "content_id": data["content_id"],
        "added_date": pd.Timestamp.now()
    }
    
    db.watchlist.insert_one(watchlist_item)
    
    return jsonify({"message": "Added to watchlist successfully"}), 201

# Get user's watchlist
@app.route("/api/watchlist", methods=["GET"])
@jwt_required()
def get_watchlist():
    user_id = get_jwt_identity()
    
    watchlist = list(db.watchlist.find({"user_id": user_id}))
    
    # Get details for each item
    watchlist_with_details = []
    for item in watchlist:
        content = db.content_details.find_one({"id": item["content_id"]})
        if content:
            watchlist_with_details.append({
                "watchlist_id": str(item["_id"]),
                "added_date": item["added_date"],
                "content": content
            })
    
    return jsonify(watchlist_with_details)

# Add rating for content
@app.route("/api/ratings", methods=["POST"])
@jwt_required()
def add_rating():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    rating_item = {
        "user_id": user_id,
        "content_id": data["content_id"],
        "rating": data["rating"],  # 1-5 scale
        "review": data.get("review", ""),
        "date": pd.Timestamp.now()
    }
    
    # Update if exists, otherwise insert
    db.ratings.update_one(
        {"user_id": user_id, "content_id": data["content_id"]},
        {"$set": rating_item},
        upsert=True
    )
    
    return jsonify({"message": "Rating added successfully"}), 201

# Get rating for a specific content
@app.route("/api/ratings/<content_id>", methods=["GET"])
@jwt_required()
def get_rating(content_id):
    user_id = get_jwt_identity()
    
    rating = db.ratings.find_one({
        "user_id": user_id,
        "content_id": content_id
    })
    
    if not rating:
        return jsonify({"error": "Rating not found"}), 404
    
    # Convert ObjectId to string for JSON serialization
    rating["_id"] = str(rating["_id"])
    
    return jsonify(rating)

# Get current user information
@app.route("/api/user", methods=["GET"])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # Don't include password in the response
        user_data = {
            "email": user["email"],
            "streaming_services": user.get("streaming_services", []),
            "preferences": user.get("preferences", {})
        }
            
        return jsonify({"user": user_data}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get user data: {str(e)}"}), 500

# Add new endpoints for discovery preferences
@app.route("/api/discover/next", methods=["GET"])
@jwt_required()
def get_next_content():
    user_id = get_jwt_identity()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    # Get user's preferences directly from user document
    liked_content = set(user.get('liked_content', []) if user else [])
    disliked_content = set(user.get('disliked_content', []) if user else [])
    seen_content = liked_content.union(disliked_content)
    
    try:
        # Import the StreamingService class
        try:
            from backend.utils.streaming_services import StreamingService
        except ImportError:
            try:
                from utils.streaming_services import StreamingService
            except ImportError:
                from streaming_services import StreamingService
        
        # Get user's streaming services if available
        user_services = user.get("streaming_services", []) if user else []
        
        # Use our optimized method to get content fast with fallback handling
        content_item = StreamingService.get_discover_content(user_services)
        
        # Check if this content was already seen
        if content_item and content_item.get("id") in seen_content:
            # Try to get another item that hasn't been seen
            for _ in range(5):  # Try up to 5 times
                new_item = StreamingService.get_discover_content(user_services)
                if new_item and new_item.get("id") not in seen_content:
                    content_item = new_item
                    break
        
        if content_item:
            return jsonify(content_item)
        else:
            return jsonify({"error": "No content available"}), 404
            
    except Exception as e:
        print(f"Error in discover/next: {str(e)}")
        
        # Try to get any content from the db as a fallback
        try:
            fallback_content = db.content_cache.find_one(
                {"id": {"$exists": True, "$ne": "last_update"}},
                {"_id": 0}
            )
            
            if fallback_content:
                return jsonify(fallback_content)
        except Exception:
            pass
            
        return jsonify({"error": "Failed to get next content. Please try again."}), 500

@app.route("/api/discover/preference", methods=["POST"])
@jwt_required()
def record_preference():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or "content_id" not in data or "preference" not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    content_id = data["content_id"]
    preference = data["preference"]  # "like" or "dislike"
    
    try:
        # Update the user document directly
        if preference == "like":
            # Add to liked_content and remove from disliked_content if present
            db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$addToSet": {"liked_content": content_id},
                    "$pull": {"disliked_content": content_id}
                }
            )
        elif preference == "dislike":
            # Add to disliked_content and remove from liked_content if present
            db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$addToSet": {"disliked_content": content_id},
                    "$pull": {"liked_content": content_id}
                }
            )
        else:
            return jsonify({"error": "Invalid preference value"}), 400
        
        return jsonify({"message": "Preference recorded successfully"}), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add fallback API endpoint for streaming content
@app.route("/api/fallback/streaming", methods=["GET"])
@jwt_required()
def get_fallback_streaming_content():
    user_id = get_jwt_identity()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    try:
        # Get some popular genres to search for
        genres = ["action", "comedy", "drama", "thriller", "sci-fi", "romance"]
        selected_genre = random.choice(genres)
        
        conn = create_api_connection()  # Use helper function
        
        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': RAPIDAPI_HOST
        }
        
        # Get user streaming services to filter content
        user_services = user.get("streaming_services", [])
        
        # Map our service IDs to RapidAPI service names
        available_services = []
        for service_id in user_services:
            if service_id in SERVICE_MAPPING:
                available_services.append(SERVICE_MAPPING[service_id])
        
        # Default to netflix if no mapping found
        if not available_services:
            available_services = ["netflix"]
        
        # Get a random service from user's available services
        selected_service = random.choice(available_services)
        
        # Format the URL for the API request
        req_path = f"/search/basic?country=us&service={selected_service}&type=movie&genre={selected_genre}&page=1&language=en"
        
        conn.request("GET", req_path, headers=headers)
        
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        
        # Parse the JSON response
        result = json.loads(data)
        
        # Check if we got results
        if "results" in result and len(result["results"]) > 0:
            # Return a random movie from the results
            random_index = random.randint(0, min(9, len(result["results"])-1))
            return jsonify(result["results"][random_index])
        else:
            return jsonify({"error": "No content found from fallback API"}), 404
            
    except Exception as e:
        print(f"Fallback API error: {str(e)}")
        return jsonify({"error": f"Fallback API error: {str(e)}"}), 500

# Error handler for expired JWT tokens
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "Token has expired", "code": "token_expired"}), 401

# Error handler for invalid JWT tokens
@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"error": "Invalid token", "code": "invalid_token"}), 401

# Error handler for missing JWT tokens
@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({"error": "Missing authentication token", "code": "missing_token"}), 401

if __name__ == "__main__":
    if ensure_mongo_connection():
        # Make sure we're using port 5000 to match what the frontend expects
        app.run(debug=True, port=5000, host='0.0.0.0')
    else:
        print("Failed to connect to MongoDB. Exiting application.")