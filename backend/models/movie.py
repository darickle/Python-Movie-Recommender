from datetime import datetime
from bson.objectid import ObjectId

class Movie:
    """Movie model for MongoDB"""
    
    collection_name = 'movies'
    
    def __init__(self, db):
        self.db = db
        self.collection = db[self.collection_name]
    
    def find_by_id(self, movie_id):
        """Find a movie by ID"""
        if isinstance(movie_id, str) and len(movie_id) == 24:
            # If it's a valid ObjectId string
            try:
                return self.collection.find_one({'_id': ObjectId(movie_id)})
            except:
                pass
        
        # Try as JustWatch ID
        return self.collection.find_one({'id': movie_id})
    
    def find_by_title(self, title, limit=10):
        """Find movies by title (partial match)"""
        return list(self.collection.find(
            {'title': {'$regex': title, '$options': 'i'}}
        ).limit(limit))
    
    def find_by_genre(self, genre, limit=10):
        """Find movies by genre"""
        return list(self.collection.find(
            {'genres': genre}
        ).limit(limit))
    
    def find_by_platform(self, platform, limit=10):
        """Find movies by streaming platform"""
        return list(self.collection.find(
            {'streaming_platforms': platform}
        ).limit(limit))
    
    def find_popular(self, limit=10):
        """Find popular movies"""
        return list(self.collection.find().sort('rating_count', -1).limit(limit))
    
    def find_recent(self, limit=10):
        """Find recently added movies"""
        return list(self.collection.find().sort('_id', -1).limit(limit))
    
    def find_by_year(self, year, limit=10):
        """Find movies by release year"""
        return list(self.collection.find(
            {'release_year': year}
        ).limit(limit))
    
    def advanced_search(self, query=None, genres=None, platforms=None, 
                        min_year=None, max_year=None, min_rating=None, 
                        sort_by='rating', limit=20, skip=0):
        """Advanced search with multiple filters"""
        # Build query
        search_query = {}
        
        if query:
            search_query['title'] = {'$regex': query, '$options': 'i'}
        
        if genres:
            if isinstance(genres, list):
                search_query['genres'] = {'$in': genres}
            else:
                search_query['genres'] = genres
        
        if platforms:
            if isinstance(platforms, list):
                search_query['streaming_platforms'] = {'$in': platforms}
            else:
                search_query['streaming_platforms'] = platforms
        
        if min_year or max_year:
            year_query = {}
            if min_year:
                year_query['$gte'] = min_year
            if max_year:
                year_query['$lte'] = max_year
            if year_query:
                search_query['release_year'] = year_query
        
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
    
    def insert_or_update(self, movie_data):
        """Insert or update a movie"""
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
    
    def get_all_genres(self):
        """Get all unique genres in the database"""
        return self.collection.distinct('genres')
    
    def get_all_platforms(self):
        """Get all unique streaming platforms in the database"""
        return self.collection.distinct('streaming_platforms')