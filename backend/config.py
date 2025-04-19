import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/media_recommender')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'media_recommender')

# API configuration
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '250f7c809bmshbd07ebdd782a896p1cf5e6jsn9767ca4b28cf')
RAPIDAPI_HOST = os.environ.get('RAPIDAPI_HOST', 'streaming-availability.p.rapidapi.com')

# Recommendation system configuration
CONTENT_RECOMMENDER_WEIGHT = float(os.environ.get('CONTENT_RECOMMENDER_WEIGHT', 0.5))
COLLABORATIVE_RECOMMENDER_WEIGHT = float(os.environ.get('COLLABORATIVE_RECOMMENDER_WEIGHT', 0.5))
DEFAULT_RECOMMENDATION_LIMIT = int(os.environ.get('DEFAULT_RECOMMENDATION_LIMIT', 10))

# Data refresh configuration
DATA_REFRESH_INTERVAL = int(os.environ.get('DATA_REFRESH_INTERVAL', 86400))  # 24 hours in seconds

# JWT configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default-secret-key')