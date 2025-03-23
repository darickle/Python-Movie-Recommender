from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
import os
from datetime import timedelta
import bcrypt
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

# Import recommenders
from recommenders.content_based import ContentBasedRecommender
from recommenders.collaborative import CollaborativeRecommender

# Import services
from services.auth_service import register_user, login_user
from utils.validation import validate_registration_input, validate_login_input

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure JWT
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY or 'dev-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
jwt = JWTManager(app)

# Connect to MongoDB
mongo_uri = MONGO_URI or 'mongodb://localhost:27017/media_recommender'
client = MongoClient(mongo_uri)
db = client.get_database()

# Initialize recommenders
content_recommender = ContentBasedRecommender(db)
collaborative_recommender = CollaborativeRecommender(db)

# User authentication routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validate input
    validation_error = validate_registration_input(data)
    if (validation_error):
        return validation_error

    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400
    return register_user(db, username, password)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    # Validate input
    validation_error = validate_login_input(data)
    if (validation_error):
        return validation_error

    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400
    return login_user(db, username, password)

# User preference routes
@app.route('/api/preferences', methods=['GET', 'PUT'])
@jwt_required()
def user_preferences():
    user_id = get_jwt_identity()
    
    if request.method == 'GET':
        user = db.users.find_one({'_id': user_id})
        return jsonify(user.get('preferences', {})), 200
    
    if request.method == 'PUT':
        data = request.get_json()
        db.users.update_one(
            {'_id': user_id},
            {'$set': {'preferences': data}}
        )
        return jsonify({'message': 'Preferences updated successfully'}), 200

# Recommendation routes
@app.route('/api/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    user_id = get_jwt_identity()
    recommendation_type = request.args.get('type', 'hybrid')
    limit = int(request.args.get('limit', 10))
    
    if recommendation_type == 'content':
        recommendations = content_recommender.get_recommendations(user_id, limit)
    elif recommendation_type == 'collaborative':
        recommendations = collaborative_recommender.get_recommendations(user_id, limit)
    else:  # hybrid
        content_recs = content_recommender.get_recommendations(user_id, limit // 2)
        collab_recs = collaborative_recommender.get_recommendations(user_id, limit // 2)
        # Combine recommendations and remove duplicates
        recommendations = list({rec['id']: rec for rec in content_recs + collab_recs}.values())
    
    return jsonify(recommendations), 200

# Movie routes
@app.route('/api/movies', methods=['GET'])
def get_movies():
    query = {}
    title = request.args.get('title')
    genre = request.args.get('genre')
    platform = request.args.get('platform')
    
    if title:
        query['title'] = {'$regex': title, '$options': 'i'}
    if genre:
        query['genres'] = genre
    if platform:
        query['streaming_platforms'] = platform
    
    limit = int(request.args.get('limit', 20))
    skip = int(request.args.get('skip', 0))
    
    movies = list(db.movies.find(query).skip(skip).limit(limit))
    
    # Convert ObjectId to string for JSON serialization
    for movie in movies:
        movie['_id'] = str(movie['_id'])
    
    return jsonify(movies), 200

@app.route('/api/movies/<movie_id>', methods=['GET'])
def get_movie(movie_id):
    movie = db.movies.find_one({'_id': movie_id})
    if not movie:
        return jsonify({'message': 'Movie not found'}), 404
    
    movie['_id'] = str(movie['_id'])
    return jsonify(movie), 200

# User movie interaction routes
@app.route('/api/watchlist', methods=['GET', 'POST', 'DELETE'])
@jwt_required()
def watchlist():
    user_id = get_jwt_identity()
    
    if request.method == 'GET':
        user = db.users.find_one({'_id': user_id})
        watchlist_ids = user.get('watchlist', [])
        watchlist_movies = list(db.movies.find({'_id': {'$in': watchlist_ids}}))
        
        # Convert ObjectId to string for JSON serialization
        for movie in watchlist_movies:
            movie['_id'] = str(movie['_id'])
        
        return jsonify(watchlist_movies), 200
    
    if request.method == 'POST':
        data = request.get_json()
        movie_id = data['movie_id']
        
        db.users.update_one(
            {'_id': user_id},
            {'$addToSet': {'watchlist': movie_id}}
        )
        return jsonify({'message': 'Movie added to watchlist'}), 200
    
    if request.method == 'DELETE':
        data = request.get_json()
        movie_id = data['movie_id']
        
        db.users.update_one(
            {'_id': user_id},
            {'$pull': {'watchlist': movie_id}}
        )
        return jsonify({'message': 'Movie removed from watchlist'}), 200

@app.route('/api/rate', methods=['POST'])
@jwt_required()
def rate_movie():
    user_id = get_jwt_identity()
    data = request.get_json()
    movie_id = data['movie_id']
    rating = data['rating']  # Rating from 1-5
    
    # Update user ratings
    db.users.update_one(
        {'_id': user_id},
        {'$set': {f'ratings.{movie_id}': rating}}
    )
    
    # Update movie average rating
    movie = db.movies.find_one({'_id': movie_id})
    current_rating = movie.get('average_rating', 0)
    current_votes = movie.get('rating_count', 0)
    
    new_rating_count = current_votes + 1
    new_average = ((current_rating * current_votes) + rating) / new_rating_count
    
    db.movies.update_one(
        {'_id': movie_id},
        {
            '$set': {
                'average_rating': new_average,
                'rating_count': new_rating_count
            }
        }
    )
    
    # Trigger updating recommender models
    content_recommender.update_user_profile(user_id)
    collaborative_recommender.update_model()
    
    return jsonify({'message': 'Rating saved successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)