import requests
import json
import time
from datetime import datetime

class JustWatchAPI:
    def __init__(self, country='US'):
        self.base_url = 'https://apis.justwatch.com/content'
        self.country = country
        self.platform_map = self._get_platform_map()
    
    def _get_platform_map(self):
        """Get mapping of provider IDs to names"""
        try:
            url = f"{self.base_url}/providers/locale/{self.country.lower()}"
            response = requests.get(url)
            providers = response.json()
            
            return {provider['id']: provider['clear_name'] for provider in providers}
        except Exception as e:
            print(f"Error getting providers: {e}")
            # Fallback with common providers
            return {
                8: "Netflix",
                9: "Amazon Prime Video",
                2: "Apple iTunes",
                3: "Google Play Movies",
                10: "Amazon Video",
                15: "Hulu",
                283: "Crunchyroll",
                337: "Disney Plus",
                350: "Apple TV Plus",
                386: "HBO Max",
                387: "Peacock",
                444: "Paramount Plus"
            }
    
    def search_movies(self, query, page=1, page_size=20):
        """Search for movies by title"""
        try:
            url = f"{self.base_url}/titles/{self.country.lower()}/popular"
            payload = {
                "body": json.dumps({
                    "page": page,
                    "page_size": page_size,
                    "query": query,
                    "content_types": ["movie"]
                })
            }
            
            response = requests.get(url, params=payload)
            data = response.json()
            
            return self._process_results(data.get('items', []))
        except Exception as e:
            print(f"Error searching movies: {e}")
            return []
    
    def search_shows(self, query, page=1, page_size=20):
        """Search for TV shows by title"""
        try:
            url = f"{self.base_url}/titles/{self.country.lower()}/popular"
            payload = {
                "body": json.dumps({
                    "page": page,
                    "page_size": page_size,
                    "query": query,
                    "content_types": ["show"]
                })
            }
            
            response = requests.get(url, params=payload)
            data = response.json()
            
            return self._process_results(data.get('items', []))
        except Exception as e:
            print(f"Error searching shows: {e}")
            return []
    
    def get_title_details(self, title_id):
        """Get detailed information about a title"""
        try:
            url = f"{self.base_url}/titles/movie/{title_id}/locale/{self.country.lower()}"
            response = requests.get(url)
            data = response.json()
            
            return self._process_title_details(data)
        except Exception as e:
            print(f"Error getting title details: {e}")
            return None
    
    def get_popular_titles(self, content_type='movie', page=1, page_size=20):
        """Get popular movies or shows"""
        try:
            url = f"{self.base_url}/titles/{self.country.lower()}/popular"
            payload = {
                "body": json.dumps({
                    "page": page,
                    "page_size": page_size,
                    "content_types": [content_type]
                })
            }
            
            response = requests.get(url, params=payload)
            data = response.json()
            
            return self._process_results(data.get('items', []))
        except Exception as e:
            print(f"Error getting popular titles: {e}")
            return []
    
    def _process_results(self, items):
        """Process search results into standardized format"""
        results = []
        
        for item in items:
            # Extract basic info
            title_data = {
                'id': item.get('id'),
                'title': item.get('title'),
                'object_type': item.get('object_type'),
                'release_year': item.get('original_release_year'),
                'poster': self._get_best_poster(item.get('poster', {})),
                'genres': self._extract_genres(item.get('genre_ids', [])),
                'streaming_platforms': self._extract_platforms(item.get('offers', []))
            }
            
            results.append(title_data)
        
        return results
    
    def _process_title_details(self, data):
        """Process title details into standardized format"""
        if not data:
            return None
        
        # Extract cast and crew
        actors = []
        directors = []
        for credit in data.get('credits', []):
            if credit.get('role') == 'ACTOR':
                actors.append(credit.get('name'))
            elif credit.get('role') == 'DIRECTOR':
                directors.append(credit.get('name'))
        
        # Create detailed title data
        title_data = {
            'id': data.get('id'),
            'title': data.get('title'),
            'object_type': data.get('object_type'),
            'release_year': data.get('original_release_year'),
            'poster': self._get_best_poster(data.get('poster', {})),
            'backdrop': self._get_best_poster(data.get('backdrop', {})),
            'genres': self._extract_genres(data.get('genre_ids', [])),
            'runtime': data.get('runtime'),
            'overview': data.get('short_description'),
            'actors': actors[:10],  # Limit to top 10 actors
            'directors': directors,
            'rating': data.get('scoring', {}).get('imdb', {}).get('value'),
            'streaming_platforms': self._extract_platforms(data.get('offers', []))
        }
        
        return title_data
    
    def _get_best_poster(self, poster_data):
        """Get the best quality poster URL"""
        if not poster_data:
            return None
        
        url_base = poster_data.get('url_base')
        if not url_base:
            return None
        
        # Try to get a reasonably sized poster
        for size in ['s718', 's592', 's342', 's166']:
            if size in poster_data.get('urls', []):
                return f"{url_base}{size}.jpg"
        
        # Fallback to any available size
        if poster_data.get('urls'):
            return f"{url_base}{poster_data['urls'][0]}.jpg"
        
        return None
    
    def _extract_genres(self, genre_ids):
        """Convert genre IDs to genre names"""
        # Pre-defined genre mapping
        genre_map = {
            1: "Action",
            2: "Animation",
            3: "Comedy",
            4: "Crime",
            5: "Documentary",
            6: "Drama",
            7: "Fantasy",
            8: "History",
            9: "Horror",
            10: "Family",
            11: "Music",
            12: "Mystery",
            13: "Romance",
            14: "Science Fiction",
            15: "Sport",
            16: "Thriller",
            17: "War",
            18: "Western",
            19: "Biography",
            20: "Adventure",
            21: "Reality",
            22: "Game Show",
            23: "News",
            24: "Talk Show"
        }
        
        return [genre_map.get(gid, "Unknown") for gid in genre_ids if gid in genre_map]
    
    def _extract_platforms(self, offers):
        """Extract streaming platform information from offers"""
        platforms = set()
        
        for offer in offers:
            # Only include streaming offers (not rental/purchase)
            if offer.get('monetization_type') == 'flatrate':
                provider_id = offer.get('provider_id')
                if provider_id in self.platform_map:
                    platforms.add(self.platform_map[provider_id])
        
        return list(platforms)
    
    def refresh_data(self, db):
        """Refresh movie/show data in the database"""
        # This method would be used to update the movie database with 
        # the latest information from JustWatch
        # Typically would be run as a scheduled task
        
        # Get popular movies
        for page in range(1, 6):  # Get first 5 pages
            movies = self.get_popular_titles('movie', page, 20)
            for movie_data in movies:
                # Get full details
                movie_id = movie_data.get('id')
                if movie_id:
                    details = self.get_title_details(movie_id)
                    if details:
                        # Update or insert movie
                        db.movies.update_one(
                            {'id': movie_id},
                            {'$set': details},
                            upsert=True
                        )
                        
                # Avoid rate limiting
                time.sleep(0.5)
            
            # Avoid rate limiting
            time.sleep(2)
        
        print(f"Database refreshed at {datetime.now()}")