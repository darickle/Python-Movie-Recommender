"""
Darick Le
Date: March-22-2025
Last Updated: March-22-2025
This module contains the movie model for MongoDB.
The movie model provides methods to interact with the movies collection in the database with the following methods:
- Find a movie by ID
- Find movies by title
- Find movies by genre
- Find movies by streaming platform
- Find popular movies
- Find recently added movies
- Find movies by release year
- Advanced search with multiple filters
- Insert or update a movie
- Get all unique genres in the database
- Get all unique streaming platforms in the database
"""

from datetime import datetime
from bson.objectid import ObjectId

class Movie:
    collection_name = 'movies'
    
    # Initialize the Movie model with the database
    def __init__(self, db):
        self.db = db
        self.collection = db[self.collection_name]
    
    # Find a movie by ID in the database
    def find_by_id(self, movie_id):
        if isinstance(movie_id, str) and len(movie_id) == 24:
            try:
                return self.collection.find_one({'_id': ObjectId(movie_id)})
            except:
                pass
        
        # Try as JustWatch ID
        return self.collection.find_one({'id': movie_id})
    
    # Find movies by title (partial match)
    def find_by_title(self, title, limit=10):
        return list(self.collection.find(
            {'title': {'$regex': title, '$options': 'i'}}
        ).limit(limit))
    
    # Find movies by genre
    def find_by_genre(self, genre, limit=10):
        return list(self.collection.find(
            {'genres': genre}
        ).limit(limit))
    
    # Find movies by streaming platform
    def find_by_platform(self, platform, limit=10):
        return list(self.collection.find(
            {'streaming_platforms': platform}
        ).limit(limit))
    
    # Find popular movies
    def find_popular(self, limit=10):
        return list(self.collection.find().sort('rating_count', -1).limit(limit))
    
    # Find recently added movies
    def find_recent(self, limit=10):
        return list(self.collection.find().sort('_id', -1).limit(limit))
    
    # Find movies by release year
    def find_by_year(self, year, limit=10):
        return list(self.collection.find(
            {'release_year': year}
        ).limit(limit))
    
    # Advanced search with multiple filters
    def advanced_search(self, query=None, genres=None, platforms=None, 
                        min_year=None, max_year=None, min_rating=None, 
                        sort_by='rating', limit=20, skip=0):
        # Build query to search movies
        search_query = {}
        
        # Apply filters
        if query:
            search_query['title'] = {'$regex': query, '$options': 'i'}
        
        # Apply genre, platform, year, and rating filters
        if genres:
            if isinstance(genres, list):
                search_query['genres'] = {'$in': genres}
            else:
                search_query['genres'] = genres
        
        # Apply streaming platform filter
        if platforms:
            if isinstance(platforms, list):
                search_query['streaming_platforms'] = {'$in': platforms}
            else:
                search_query['streaming_platforms'] = platforms
        
        # Apply release year filter
        if min_year or max_year:
            year_query = {}
            if min_year:
                year_query['$gte'] = min_year
            if max_year:
                year_query['$lte'] = max_year
            if year_query:
                search_query['release_year'] = year_query
        
        # Apply minimum rating filter
        if min_rating:
            search_query['rating'] = {'$gte': min_rating}
        
        # Determine sort order
        if sort_by == 'rating':
            sort_field = 'rating'
            sort_dir = -1
        elif sort_by == 'year_desc':
            sort_field = 'release_year'
            sort_dir = -1
        elif sort_by == 'year_asc':
            sort_field = 'release_year'
            sort_dir = 1
        elif sort_by == 'title':
            sort_field = 'title'
            sort_dir = 1
        else:
            sort_field = 'rating_count'
            sort_dir = -1
        
        # Execute query
        return list(self.collection.find(search_query)
                    .sort(sort_field, sort_dir)
                    .skip(skip)
                    .limit(limit))
    
    # Insert or update a movie in the database
    def insert_or_update(self, movie_data):
        # Check if movie exists by JustWatch ID
        existing = None
        if 'id' in movie_data:
            existing = self.collection.find_one({'id': movie_data['id']})
        
        if existing:
            # Update existing movie
            movie_data['updated_at'] = datetime.now()
            self.collection.update_one(
                {'_id': existing['_id']},
                {'$set': movie_data}
            )
            return existing['_id']
        else:
            # Insert new movie
            movie_data['created_at'] = datetime.now()
            movie_data['updated_at'] = datetime.now()
            result = self.collection.insert_one(movie_data)
            return result.inserted_id
    
    # Get all unique genres in the database
    def get_all_genres(self):
        return self.collection.distinct('genres')
    
    # Get all unique streaming platforms in the database
    def get_all_platforms(self):
        return self.collection.distinct('streaming_platforms')