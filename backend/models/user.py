from datetime import datetime
from bson.objectid import ObjectId
import bcrypt

class User:
    """User model for MongoDB"""
    
    collection_name = 'users'
    
    def __init__(self, db):
        self.db = db
        self.collection = db[self.collection_name]
    
    def find_by_id(self, user_id):
        """Find a user by ID"""
        if isinstance(user_id, str):
            try:
                return self.collection.find_one({'_id': ObjectId(user_id)})
            except:
                return None
        return None
    
    def find_by_email(self, email):
        """Find a user by email"""
        return self.collection.find_one({'email': email})
    
    def create(self, user_data):
        """Create a new user"""
        # Check if user already exists
        if self.find_by_email(user_data['email']):
            return None
        
        # Hash password
        password = user_data['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Prepare user document
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
        
        # Insert user
        result = self.collection.insert_one(user)
        return result.inserted_id
    
    def authenticate(self, email, password):
        """Authenticate a user"""
        user = self.find_by_email(email)
        if not user:
            return None
        
        # Check password
        if bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return user
        
        return None
    
    def update_preferences(self, user_id, preferences):
        """Update user preferences"""
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
    
    def add_to_watchlist(self, user_id, movie_id):
        """Add a movie to user's watchlist"""
        result = self.collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$addToSet': {'watchlist': movie_id},
                '$set': {'updated_at': datetime.now()}
            }
        )
        return result.modified_count > 0
    
    def remove_from_watchlist(self, user_id, movie_id):
        """Remove a movie from user's watchlist"""
        result = self.collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$pull': {'watchlist': movie_id},
                '$set': {'updated_at': datetime.now()}
            }
        )
        return result.modified_count > 0
    
    def rate_movie(self, user_id, movie_id, rating):
        """Rate a movie"""
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
    
    def unrate_movie(self, user_id, movie_id):
        """Remove a movie rating"""
        result = self.collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$unset': {f'ratings.{movie_id}': ""},
                '$set': {'updated_at': datetime.now()}
            }
        )
        return result.modified_count > 0
    
    def get_watchlist(self, user_id):
        """Get user's watchlist"""
        user = self.find_by_id(user_id)
        if not user:
            return []
        
        return user.get('watchlist', [])
    
    def get_ratings(self, user_id):
        """Get user's ratings"""
        user = self.find_by_id(user_id)
        if not user:
            return {}
        
        return user.get('ratings', {})