"""
Default configuration settings for the ShopSentiment application.
These settings are used in all environments unless overridden.
"""

import os

# Flask configuration
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-shopsentiment-app')
SESSION_COOKIE_SECURE = False
PREFERRED_URL_SCHEME = 'https'

# Database configuration
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'data/shopsentiment.db')

# Sentiment analysis configuration
SENTIMENT_ANALYSIS_MODEL = os.environ.get('SENTIMENT_MODEL', 'textblob')

# Caching configuration
CACHE_TYPE = 'SimpleCache'
CACHE_DEFAULT_TIMEOUT = 300

# API rate limiting
RATELIMIT_DEFAULT = "200 per day, 50 per hour"
RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')

# Logging configuration
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Flask settings
TESTING = False
TRUSTED_PROXIES = 1

# MongoDB settings
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_DB = os.environ.get('MONGODB_DB', 'shopsentiment')
MONGODB_USER = os.environ.get('MONGODB_USER')
MONGODB_PASS = os.environ.get('MONGODB_PASS')

# Application settings
MAX_REVIEWS_PER_PAGE = 20
CACHE_TIMEOUT = 300  # 5 minutes

# Logging settings
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = os.environ.get('LOG_FILE', 'app.log')

# Security settings
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Static files
STATIC_FOLDER = 'static'
TEMPLATES_FOLDER = 'templates'

# API settings
API_VERSION = 'v1'
API_PREFIX = f'/api/{API_VERSION}' 