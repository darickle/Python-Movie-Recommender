"""
Darick Le
Date: March-22-2025
Last Updated: March-22-2025
This module contains the user model for MongoDB.
The user model provides methods to interact with the users collection in the database with the following methods:
- Find a user by ID
- Find a user by email
- Create a new user
- Authenticate a user
- Update user preferences
- Add a movie to user's watchlist
- Remove a movie from user's watchlist
- Rate a movie
- Remove a movie rating
- Get user's watchlist
- Get user's ratings
"""

from datetime import datetime
from bson.objectid import ObjectId
import bcrypt

class User:
    collection_name = 'users'

    # Initialize the User model with the database
    def __init__(self, db):
        self.db = db
        self.collection = db[self.collection_name]
    
    # Find a user by ID in the database
    def find_by_id(self, user_id):
        # Check if user_id is a string or ObjectId
        if isinstance(user_id, str):
            try:
                return self.collection.find_one({'_id': ObjectId(user_id)})
            except:
                return None
        return None
    
    # Find a user by email in the database
    def find_by_email(self, email):
        return self.collection.find_one({'email': email})
    
    # Create a new user in the database
    def create(self, user_data):
        """Create a new user"""
        # Check if user already exists
        if self.find_by_email(user_data['email']):
            return None
        
        # Hash the password
        password = user_data['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
        # Create user object
        user = {
            'email': user_data['email'],
            'password': hashed_password,
            'name': user_data.get('name', ''),
            'preferences': user_data.get('preferences', {}),
            'watchlist': [],
            'ratings': {},
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Insert user into the database
        result = self.collection.insert_one(user)
        return result.inserted_id
    
    # Authenticate a user in the database by email and password
    def authenticate(self, email, password):
        # Find user by email
        user = self.find_by_email(email)
        if not user:
            return None
        
        # Check if the password is correct
        if bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return user
        return None
    
    # Update user preferences in the database
    def update_preferences(self, user_id, preferences):
        # Update user preferences and set updated_at timestamp
        result = self.collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'preferences': preferences,
                    'updated_at': datetime.now()
                }
            }
        )
        return result.modified_count > 0
    
    # Add a movie to user's watchlist in the database
    def add_to_watchlist(self, user_id, movie_id):
        result = self.collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$addToSet': {'watchlist': movie_id},
                '$set': {'updated_at': datetime.now()}
            }
        )
        return result.modified_count > 0
    
    # Remove a movie from user's watchlist in the database
    def remove_from_watchlist(self, user_id, movie_id):
        result = self.collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$pull': {'watchlist': movie_id},
                '$set': {'updated_at': datetime.now()}
            }
        )
        return result.modified_count > 0
    
    # Rate a movie in the database
    def rate_movie(self, user_id, movie_id, rating):
        # Validate rating (1-5)
        rating = max(1, min(5, rating))
        result = self.collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    f'ratings.{movie_id}': rating,
                    'updated_at': datetime.now()
                }
            }
        )
        return result.modified_count > 0
    
    # Remove a movie rating in the database
    def unrate_movie(self, user_id, movie_id):
        result = self.collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$unset': {f'ratings.{movie_id}': ""},
                '$set': {'updated_at': datetime.now()}
            }
        )
        return result.modified_count > 0
    
    # Get user's watchlist from the database
    def get_watchlist(self, user_id):
        user = self.find_by_id(user_id)
        if not user:
            return []
        return user.get('watchlist', [])
    
    # Get user's ratings from the database
    def get_ratings(self, user_id):
        user = self.find_by_id(user_id)
        if not user:
            return {}
        return user.get('ratings', {})