"""
Darick Le
Date: March-22-2025
Last Updated: March-22-2025
Collaborative Filtering Recommender to recommend movies to users based on their ratings and similar users.
It uses the cosine similarity between users to find similar users and recommend movies that similar users liked.
This is a user-based collaborative filtering model.
"""

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
import pickle
import os
from datetime import datetime

class CollaborativeRecommender:
    def __init__(self, db):
        self.db = db
        self.user_item_matrix = None
        self.user_similarity = None
        self.movie_ids = []
        self.user_indices = {}
        self.model_path = 'models/collaborative_model.pkl'
        self.last_update = None
        
        # Load or build the model
        if os.path.exists(self.model_path):
            self.load_model()
        else:
            self.build_model()
    
    def build_model(self):
        """Build the collaborative filtering model"""
        print("Building collaborative filtering model...")
        
        # Get all users with ratings
        users = list(self.db.users.find({'ratings': {'$exists': True, '$ne': {}}}))
        if not users:
            print("No users with ratings found")
            return
        
        # Collect all movie IDs that have been rated
        all_movie_ids = set()
        for user in users:
            all_movie_ids.update(user.get('ratings', {}).keys())
        
        self.movie_ids = list(all_movie_ids)
        if not self.movie_ids:
            print("No movie ratings found")
            return
        
        # Create user-item matrix
        data = []
        for idx, user in enumerate(users):
            self.user_indices[str(user['_id'])] = idx
            ratings = user.get('ratings', {})
            for movie_id in self.movie_ids:
                if movie_id in ratings:
                    data.append([idx, self.movie_ids.index(movie_id), ratings[movie_id]])
        
        if not data:
            print("No rating data found")
            return
        
        # Convert to DataFrame
        ratings_df = pd.DataFrame(data, columns=['user_idx', 'movie_idx', 'rating'])
        
        # Create sparse matrix
        self.user_item_matrix = csr_matrix((
            ratings_df['rating'], 
            (ratings_df['user_idx'], ratings_df['movie_idx'])
        ))
        
        # Compute user similarity
        self.user_similarity = cosine_similarity(self.user_item_matrix)
        
        # Record update time
        self.last_update = datetime.now()
        
        # Save model
        self.save_model()
        
        print("Collaborative model built successfully")
    
    def save_model(self):
        """Save the model to disk"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'user_item_matrix': self.user_item_matrix,
                'user_similarity': self.user_similarity,
                'movie_ids': self.movie_ids,
                'user_indices': self.user_indices,
                'last_update': self.last_update
            }, f)
    
    def load_model(self):
        """Load the model from disk"""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.user_item_matrix = model_data['user_item_matrix']
                self.user_similarity = model_data['user_similarity']
                self.movie_ids = model_data['movie_ids']
                self.user_indices = model_data['user_indices']
                self.last_update = model_data.get('last_update', datetime.now())
            print("Collaborative model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.build_model()
    
    def update_model(self):
        """Update the model if needed"""
        # Only rebuild once per day to avoid too frequent computations
        if (self.last_update is None or 
            (datetime.now() - self.last_update).days > 0):
            self.build_model()
    
    def get_recommendations(self, user_id, limit=10):
        """
        Get collaborative filtering recommendations for a user
        
        This will:
        1. Find similar users
        2. Get movies liked by similar users
        3. Return top recommendations
        """
        # Check if model exists
        if self.user_item_matrix is None or self.user_similarity is None:
            print("Model not built yet")
            return self._get_popular_movies(limit)
        
        # Check if user is in the model
        if user_id not in self.user_indices:
            # User not in model, return popular movies
            return self._get_popular_movies(limit)
        
        # Get user index
        user_idx = self.user_indices[user_id]
        
        # Get user's ratings
        user = self.db.users.find_one({'_id': user_id})
        user_ratings = user.get('ratings', {})
        
        # Get similar users
        similar_users = self.user_similarity[user_idx]
        similar_users = list(enumerate(similar_users))
        
        # Sort by similarity (excluding self)
        similar_users = sorted(similar_users, key=lambda x: x[1], reverse=True)
        similar_users = similar_users[1:21]  # Top 20 similar users
        
        # Get recommendations from similar users
        recommendations = {}
        for sim_user_idx, similarity in similar_users:
            if similarity <= 0:
                continue
                
            # Find similar user in database
            sim_user_id = None
            for uid, idx in self.user_indices.items():
                if idx == sim_user_idx:
                    sim_user_id = uid
                    break
                    
            if not sim_user_id:
                continue
                
            # Get similar user's ratings
            sim_user = self.db.users.find_one({'_id': sim_user_id})
            sim_user_ratings = sim_user.get('ratings', {})
            
            # Add movies liked by similar user (rated 4-5) that current user hasn't rated
            for movie_id, rating in sim_user_ratings.items():
                if rating >= 4 and movie_id not in user_ratings:
                    if movie_id not in recommendations:
                        recommendations[movie_id] = 0
                    recommendations[movie_id] += similarity * rating
        
        # Sort by weighted rating
        top_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        # Get full movie data for recommendations
        result = []
        for movie_id, score in top_recommendations:
            movie = self.db.movies.find_one({'_id': movie_id})
            if movie:
                movie['_id'] = str(movie['_id'])
                movie['similarity_score'] = float(score)
                result.append(movie)
        
        # If not enough recommendations, add popular movies
        if len(result) < limit:
            popular_movies = self._get_popular_movies(limit - len(result))
            # Exclude already recommended movies
            recommended_ids = [movie['_id'] for movie in result]
            additional_recs = [movie for movie in popular_movies if movie['_id'] not in recommended_ids]
            result.extend(additional_recs)
        
        return result
    
    def _get_popular_movies(self, limit=10):
        """Get popular movies as fallback"""
        popular_movies = list(self.db.movies.find().sort('rating_count', -1).limit(limit))
        
        # Convert ObjectId to string for JSON serialization
        for movie in popular_movies:
            movie['_id'] = str(movie['_id'])
        
        return popular_movies