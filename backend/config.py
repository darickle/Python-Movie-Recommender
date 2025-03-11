import os

# Database configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/media_recommender')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'media_recommender')

# API configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-here')
JWT_TOKEN_EXPIRES = int(os.environ.get('JWT_TOKEN_EXPIRES', 86400))  # 24 hours in seconds

# JustWatch API configuration
JUSTWATCH_COUNTRY = os.environ.get('JUSTWATCH_COUNTRY', 'US')

# Recommendation system configuration
CONTENT_RECOMMENDER_WEIGHT = float(os.environ.get('CONTENT_RECOMMENDER_WEIGHT', 0.5))
COLLABORATIVE_RECOMMENDER_WEIGHT = float(os.environ.get('COLLABORATIVE_RECOMMENDER_WEIGHT', 0.5))
DEFAULT_RECOMMENDATION_LIMIT = int(os.environ.get('DEFAULT_RECOMMENDATION_LIMIT', 10))

# Data refresh configuration
DATA_REFRESH_INTERVAL = int(os.environ.get('DATA_REFRESH_INTERVAL', 86400))  # 24 hours in seconds