"""
Production configuration settings for the ShopSentiment application.
These settings override the default configuration for production environment.
"""

from config.default import *

# Flask settings
DEBUG = False
TESTING = False

# MongoDB settings
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_DB = os.environ.get('MONGODB_DB', 'shopsentiment')

# Security settings
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Logging settings
LOG_LEVEL = 'INFO'
LOG_FILE = '/var/log/shopsentiment/app.log'

# Production-specific settings
SENTIMENT_ANALYSIS_MODEL = 'production'
CACHE_TIMEOUT = 3600  # 1 hour for production

# Cache settings - Determine type based on REDIS_URL
REDIS_URL_ENV = os.environ.get('REDIS_URL')
if REDIS_URL_ENV:
    CACHE_TYPE = 'RedisCache'  # Use RedisCache from flask_caching
    CACHE_REDIS_URL = REDIS_URL_ENV
    CACHE_DEFAULT_TIMEOUT = CACHE_TIMEOUT
else:
    CACHE_TYPE = 'SimpleCache'  # Fallback to SimpleCache
    CACHE_DEFAULT_TIMEOUT = 300 # Or keep CACHE_TIMEOUT if preferred for SimpleCache too

# Performance settings
JSONIFY_PRETTYPRINT_REGULAR = False
JSON_SORT_KEYS = False

# Rate limiting
RATELIMIT_DEFAULT = "1000 per day;100 per hour"

# Error handling
PROPAGATE_EXCEPTIONS = False 