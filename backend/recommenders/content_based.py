import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

class ContentBasedRecommender:
    def __init__(self, db):
        self.db = db
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.cosine_sim_matrix = None
        self.movie_indices = {}
        self.model_path = 'models/content_model.pkl'
        
        # Load or build the model
        if os.path.exists(self.model_path):
            self.load_model()
        else:
            self.build_model()
    
    def build_model(self):
        """Build the content-based filtering model"""
        print("Building content-based recommendation model...")
        
        # Get all movies from database
        movies = list(self.db.movies.find({}))
        if not movies:
            print("No movies found in database")
            return
        
        # Convert to DataFrame
        movies_df = pd.DataFrame(movies)
        
        # Create a content column for TF-IDF
        movies_df['content'] = movies_df.apply(self._create_content_feature, axis=1)
        
        # Create TF-IDF matrix
        tfidf_matrix = self.vectorizer.fit_transform(movies_df['content'])
        
        # Compute cosine similarity matrix
        self.cosine_sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
        
        # Map movie IDs to matrix indices
        self.movie_indices = {str(movie['_id']): idx for idx, movie in enumerate(movies)}
        
        # Save model
        self.save_model()
        
        print("Content-based model built successfully")
    
    def _create_content_feature(self, movie):
        """Create a string representing movie content for TF-IDF"""
        features = []
        
        # Add title (weighted higher by repetition)
        features.append(movie.get('title', '') * 3)
        
        # Add overview
        features.append(movie.get('overview', ''))
        
        # Add genres
        if 'genres' in movie and movie['genres']:
            features.append(' '.join(movie['genres']))
        
        # Add directors
        if 'directors' in movie and movie['directors']:
            features.append(' '.join(movie['directors']))
        
        # Add actors
        if 'actors' in movie and movie['actors']:
            features.append(' '.join(movie['actors']))
        
        # Join all features
        return ' '.join(features).lower()
    
    def save_model(self):
        """Save the model to disk"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'cosine_sim_matrix': self.cosine_sim_matrix,
                'movie_indices': self.movie_indices,
                'vectorizer': self.vectorizer
            }, f)
    
    def load_model(self):
        """Load the model from disk"""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.cosine_sim_matrix = model_data['cosine_sim_matrix']
                self.movie_indices = model_data['movie_indices']
                self.vectorizer = model_data['vectorizer']
            print("Content-based model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.build_model()
    
    def update_user_profile(self, user_id):
        """Update user profile based on ratings"""
        # This method would be called after a user rates a movie
        # We don't actually need to update the model, just ensure
        # we have the latest movie data for recommendations
        pass
    
    def get_recommendations(self, user_id, limit=10):
        """
        Get content-based recommendations for a user
        
        This will:
        1. Get user's highly rated movies
        2. Find similar movies to those highly rated
        3. Return top recommendations
        """
        # Get user's ratings
        user = self.db.users.find_one({'_id': user_id})
        if not user or 'ratings' not in user or not user['ratings']:
            # If user has no ratings, return popular movies
            return self._get_popular_movies(limit)
        
        # Get user's highly rated movies (4-5 stars)
        liked_movie_ids = [movie_id for movie_id, rating in user['ratings'].items() if rating >= 4]
        
        if not liked_movie_ids:
            return self._get_popular_movies(limit)
        
        # Get similar movies for each liked movie
        recommendations = {}
        for movie_id in liked_movie_ids:
            if movie_id in self.movie_indices:
                similar_movies = self._get_similar_movies(movie_id)
                for rec_id, score in similar_movies:
                    if rec_id not in user['ratings'] and rec_id not in recommendations:
                        recommendations[rec_id] = score
        
        # Sort by similarity score and take top 'limit'
        top_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        # Get full movie data for recommendations
        result = []
        for movie_id, score in top_recommendations:
            movie = self.db.movies.find_one({'_id': movie_id})
            if movie:
                movie['_id'] = str(movie['_id'])
                movie['similarity_score'] = float(score)
                result.append(movie)
        
        return result
    
    def _get_similar_movies(self, movie_id):
        """Get movies similar to a given movie"""
        if movie_id not in self.movie_indices:
            return []
        
        # Get the index of the movie
        idx = self.movie_indices[movie_id]
        
        # Get similarity scores for all movies
        sim_scores = list(enumerate(self.cosine_sim_matrix[idx]))
        
        # Sort by similarity score
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Get top 20 similar movies (excluding itself)
        sim_scores = sim_scores[1:21]
        
        # Get movie ids and scores
        movie_ids = []
        for i, score in sim_scores:
            # Get the movie id for this index
            for id, index in self.movie_indices.items():
                if index == i:
                    movie_ids.append((id, score))
                    break
        
        return movie_ids
    
    def _get_popular_movies(self, limit=10):
        """Get popular movies as fallback"""
        popular_movies = list(self.db.movies.find().sort('rating_count', -1).limit(limit))
        
        # Convert ObjectId to string for JSON serialization
        for movie in popular_movies:
            movie['_id'] = str(movie['_id'])
        
        return popular_movies