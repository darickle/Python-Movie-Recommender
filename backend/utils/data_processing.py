"""
Darick Le
March 11 2025
Data Processing Module
This module contains functions to preprocess movie data, extract features,
normalize features, and create user feature vectors for the movie recommendation system.
It includes functions to handle missing values, encode categories,
normalize numerical features, and calculate similarity scores between user preferences
and movie features.
"""

import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import MinMaxScaler

def preprocess_movie_data(movies):
    """
    Preprocess movie data for recommendation system
    
    Args:
        movies: List of movie documents from MongoDB
        
    Returns:
        pandas.DataFrame: Processed movie data
    """
    # Convert to DataFrame
    df = pd.DataFrame(movies)
    
    # Fill missing values
    df['overview'] = df['overview'].fillna('')
    df['release_year'] = df['release_year'].fillna(0).astype(int)
    df['runtime'] = df['runtime'].fillna(0).astype(int)
    
    # Handle missing arrays
    df['genres'] = df['genres'].apply(lambda x: x if isinstance(x, list) else [])
    df['actors'] = df['actors'].apply(lambda x: x if isinstance(x, list) else [])
    df['directors'] = df['directors'].apply(lambda x: x if isinstance(x, list) else [])
    df['streaming_platforms'] = df['streaming_platforms'].apply(lambda x: x if isinstance(x, list) else [])
    
    # Convert ratings to float
    df['rating'] = df['rating'].fillna(0).astype(float)
    
    return df

def extract_features(df):
    """
    Extract features from movie data for content-based filtering
    
    Args:
        df: DataFrame with movie data
        
    Returns:
        pandas.DataFrame: Feature matrix
    """
    # Create feature vectors
    features = {}
    
    # One-hot encode genres
    all_genres = []
    for genres in df['genres']:
        all_genres.extend(genres)
    unique_genres = list(set(all_genres))
    
    for genre in unique_genres:
        features[f'genre_{genre}'] = df['genres'].apply(lambda x: 1 if genre in x else 0)
    
    # Create year features (by decade)
    df['decade'] = (df['release_year'] // 10) * 10
    decades = df['decade'].unique()
    for decade in decades:
        if decade > 0:  # Skip missing values
            features[f'decade_{decade}'] = (df['decade'] == decade).astype(int)
    
    # Runtime features (short/medium/long)
    features['short_film'] = (df['runtime'] < 90).astype(int)
    features['medium_film'] = ((df['runtime'] >= 90) & (df['runtime'] <= 150)).astype(int)
    features['long_film'] = (df['runtime'] > 150).astype(int)
    
    # Create feature DataFrame
    feature_df = pd.DataFrame(features, index=df.index)
    
    return feature_df

def normalize_features(feature_df):
    """
    Normalize features for recommendation
    
    Args:
        feature_df: DataFrame with extracted features
        
    Returns:
        numpy.ndarray: Normalized feature matrix
    """
    # Scale features
    scaler = MinMaxScaler()
    normalized_features = scaler.fit_transform(feature_df)
    
    return normalized_features

def user_feature_vector(user_preferences, all_features):
    """
    Create feature vector for a user based on preferences
    
    Args:
        user_preferences: Dictionary of user preferences
        all_features: DataFrame with all possible features
        
    Returns:
        numpy.ndarray: User feature vector
    """
    # Create empty feature vector
    user_vector = np.zeros(len(all_features.columns))
    
    # Fill in genre preferences
    genres = user_preferences.get('genres', [])
    for genre in genres:
        if f'genre_{genre}' in all_features.columns:
            idx = all_features.columns.get_loc(f'genre_{genre}')
            user_vector[idx] = 1
    
    # Fill in year preferences
    preferred_decades = user_preferences.get('decades', [])
    for decade in preferred_decades:
        if f'decade_{decade}' in all_features.columns:
            idx = all_features.columns.get_loc(f'decade_{decade}')
            user_vector[idx] = 1
    
    # Fill in runtime preferences
    runtime_pref = user_preferences.get('runtime', 'any')
    if runtime_pref == 'short':
        idx = all_features.columns.get_loc('short_film')
        user_vector[idx] = 1
    elif runtime_pref == 'medium':
        idx = all_features.columns.get_loc('medium_film')
        user_vector[idx] = 1
    elif runtime_pref == 'long':
        idx = all_features.columns.get_loc('long_film')
        user_vector[idx] = 1
    
    return user_vector

def calculate_similarity(user_vector, item_features):
    """
    Calculate similarity between user vector and item features
    
    Args:
        user_vector: User preference vector
        item_features: Item feature matrix
        
    Returns:
        numpy.ndarray: Similarity scores
    """
    # Calculate cosine similarity
    # Reshape user vector for broadcasting
    user_vector = user_vector.reshape(1, -1)
    
    # Calculate dot product
    dot_product = np.dot(user_vector, item_features.T)[0]
    
    # Calculate magnitudes
    user_magnitude = np.sqrt(np.sum(user_vector**2))
    item_magnitudes = np.sqrt(np.sum(item_features**2, axis=1))
    
    # Calculate cosine similarity
    similarities = dot_product / (user_magnitude * item_magnitudes)
    
    return similarities

def process_user_ratings(user_ratings, movie_ids):
    """
    Process user ratings into a vector
    
    Args:
        user_ratings: Dictionary of user ratings
        movie_ids: List of all movie IDs
        
    Returns:
        numpy.ndarray: User rating vector
    """
    # Create vector of zeros
    rating_vector = np.zeros(len(movie_ids))
    
    # Fill in ratings
    for movie_id, rating in user_ratings.items():
        if movie_id in movie_ids:
            idx = movie_ids.index(movie_id)
            rating_vector[idx] = rating
    
    return rating_vector