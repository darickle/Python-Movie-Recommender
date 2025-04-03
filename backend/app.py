from flask import Flask, request, jsonify
import requests
import os
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

# WatchMode API configuration
WATCHMODE_API_KEY = config.WATCHMODE_API_KEY
WATCHMODE_BASE_URL = "https://api.watchmode.com/v1"

# Get list of available streaming services
@app.route("/api/streaming_services", methods=["GET"])
def get_streaming_services():
    # First check if we have this cached in our database
    cached_services = db.streaming_services.find_one({"type": "all_services"})
    
    if cached_services:
        return jsonify(cached_services["services"])
    
    # If not cached, fetch from WatchMode API
    url = f"{WATCHMODE_BASE_URL}/sources/?apiKey={WATCHMODE_API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        services = response.json()
        # Filter to only include subscription streaming services (not rentals)
        subscription_services = [service for service in services if service.get("type") == "sub"]
        
        # Cache in database
        db.streaming_services.insert_one({
            "type": "all_services",
            "services": subscription_services
        })
        
        return jsonify(subscription_services)
    else:
        return jsonify({"error": "Failed to fetch streaming services"}), 500

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
            "streaming_services": user.get("streaming_services", [])
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
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"streaming_services": data["streaming_services"]}}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({"message": "Streaming services updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to update streaming services: {str(e)}"}), 500

# Add a simple status endpoint to test connectivity
@app.route("/api/status", methods=["GET"])
def api_status():
    print("Status endpoint was called!")  # Add this debug line
    return jsonify({"status": "online", "message": "API is running correctly"})

# Add an OPTIONS route handler to handle preflight requests
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return '', 200

# Search for content
@app.route("/api/search", methods=["GET"])
def search_content():
    query = request.args.get("query", "")
    
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    url = f"{WATCHMODE_BASE_URL}/search/?apiKey={WATCHMODE_API_KEY}&search_field=name&search_value={query}"
    response = requests.get(url)
    
    if response.status_code == 200:
        results = response.json().get("title_results", [])
        
        # Cache results in database
        for item in results:
            db.content.update_one(
                {"id": item["id"]},
                {"$set": item},
                upsert=True
            )
        
        return jsonify(results)
    else:
        return jsonify({"error": "Failed to search content"}), 500

# Get content details with streaming availability
@app.route("/api/content/<content_id>", methods=["GET"])
def get_content_details(content_id):
    # Check if we have this cached with recent sources data
    cached_content = db.content_details.find_one({"id": content_id})
    
    # If cached and recent (within 1 day), return cached data
    if cached_content:
        return jsonify(cached_content)
    
    # Fetch details from WatchMode API
    url = f"{WATCHMODE_BASE_URL}/title/{content_id}/details/?apiKey={WATCHMODE_API_KEY}&append_to_response=sources"
    response = requests.get(url)
    
    if response.status_code == 200:
        content_details = response.json()
        
        # Cache in database
        db.content_details.update_one(
            {"id": content_id},
            {"$set": content_details},
            upsert=True
        )
        
        return jsonify(content_details)
    else:
        return jsonify({"error": "Failed to fetch content details"}), 500

# Get personalized recommendations
@app.route("/api/recommendations", methods=["GET"])
@jwt_required()
def get_recommendations():
    user_id = get_jwt_identity()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user or not user.get("streaming_services"):
        return jsonify({"error": "User streaming services not set"}), 400
    
    # Get user's streaming services
    user_services = user.get("streaming_services", [])
    
    # Fetch content for these services
    # First, get a sample of popular titles from WatchMode API to start with
    recommended_content = []
    
    # Get user's watch history and ratings if available
    user_ratings = list(db.ratings.find({"user_id": user_id}))
    
    # If user has ratings, use them for content-based recommendations
    if user_ratings:
        # Get content details for items user has rated highly
        liked_content = []
        for rating in user_ratings:
            if rating["rating"] >= 4:  # 4 or 5 star ratings
                content = db.content_details.find_one({"id": rating["content_id"]})
                if content:
                    liked_content.append(content)
        
        # Generate recommendations based on content similarity
        # This is a simplified version - in a real app, you'd want more sophisticated logic
        if liked_content:
            # Create a simplified content representation for similarity calculation
            content_data = []
            for item in liked_content:
                # Create a string of features for TF-IDF
                features = f"{item.get('title', '')} {item.get('genre_names', '')} {item.get('network_names', '')}"
                content_data.append({
                    "id": item["id"],
                    "features": features
                })
            
            # Convert to DataFrame for processing
            df = pd.DataFrame(content_data)
            
            # Create TF-IDF vectors
            tfidf = TfidfVectorizer(stop_words='english')
            tfidf_matrix = tfidf.fit_transform(df['features'])
            
            # Calculate cosine similarity
            cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
            
            # Get indices of items user has liked
            indices = df.index.tolist()
            
            # Get similar items
            similar_items = []
            for idx in indices:
                similar_indices = cosine_sim[idx].argsort()[:-6:-1]  # Top 5 similar items
                similar_items.extend([df.iloc[i]["id"] for i in similar_indices if i != idx])
            
            # Remove duplicates
            similar_items = list(set(similar_items))
            
            # Fetch details for these items
            for item_id in similar_items:
                content = db.content_details.find_one({"id": item_id})
                if content:
                    # Check if available on user's streaming services
                    sources = content.get("sources", [])
                    available_on_user_services = any(source["source_id"] in user_services for source in sources)
                    
                    if available_on_user_services:
                        recommended_content.append(content)
    
    # If we don't have enough recommendations yet, get popular content from user's services
    if len(recommended_content) < 10:
        # Get popular movies and shows available on user's streaming services
        # This would typically be fetched from the API, but we'll use a simplified approach
        # In a real app, you'd want to paginate and fetch more data
        
        url = f"{WATCHMODE_BASE_URL}/list-titles/?apiKey={WATCHMODE_API_KEY}&types=movie,show&sort_by=popularity_desc&limit=20"
        response = requests.get(url)
        
        if response.status_code == 200:
            popular_content = response.json().get("titles", [])
            
            # For each item, check streaming availability
            for item in popular_content:
                content_id = item["id"]
                details_url = f"{WATCHMODE_BASE_URL}/title/{content_id}/details/?apiKey={WATCHMODE_API_KEY}&append_to_response=sources"
                details_response = requests.get(details_url)
                
                if details_response.status_code == 200:
                    content_details = details_response.json()
                    
                    # Check if available on user's streaming services
                    sources = content_details.get("sources", [])
                    available_on_user_services = any(source["source_id"] in user_services for source in sources)
                    
                    if available_on_user_services and content_details not in recommended_content:
                        recommended_content.append(content_details)
                        
                        # Cache in database
                        db.content_details.update_one(
                            {"id": content_id},
                            {"$set": content_details},
                            upsert=True
                        )
                
                # Stop once we have enough recommendations
                if len(recommended_content) >= 20:
                    break
    
    return jsonify(recommended_content)

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

# Get trending content available on user's services
@app.route("/api/trending", methods=["GET"])
@jwt_required()
def get_trending():
    user_id = get_jwt_identity()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user or not user.get("streaming_services"):
        return jsonify({"error": "User streaming services not set"}), 400
    
    user_services = user.get("streaming_services", [])
    
    # Get trending movies and shows from WatchMode API
    url = f"{WATCHMODE_BASE_URL}/list-titles/?apiKey={WATCHMODE_API_KEY}&types=movie,show&sort_by=popularity_desc&limit=20"
    response = requests.get(url)
    
    if response.status_code == 200:
        trending_items = []
        trending_results = response.json().get("titles", [])
        
        # Check availability on user's services
        for item in trending_results:
            content_id = item["id"]
            sources_url = f"{WATCHMODE_BASE_URL}/title/{content_id}/sources/?apiKey={WATCHMODE_API_KEY}"
            sources_response = requests.get(sources_url)
            
            if sources_response.status_code == 200:
                sources = sources_response.json()
                
                # Check if available on user's services
                available_on_user_services = any(source["source_id"] in user_services for source in sources)
                
                if available_on_user_services:
                    # Get full details
                    details_url = f"{WATCHMODE_BASE_URL}/title/{content_id}/details/?apiKey={WATCHMODE_API_KEY}"
                    details_response = requests.get(details_url)
                    
                    if details_response.status_code == 200:
                        item_details = details_response.json()
                        item_details["sources"] = sources
                        trending_items.append(item_details)
                        
                        # Cache in database
                        db.content_details.update_one(
                            {"id": content_id},
                            {"$set": item_details},
                            upsert=True
                        )
            
            # Stop once we have enough items
            if len(trending_items) >= 10:
                break
        
        return jsonify(trending_items)
    else:
        return jsonify({"error": "Failed to fetch trending content"}), 500

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