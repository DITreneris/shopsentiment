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

# Cache settings - Explicitly configure for Redis in production
# The cache_factory will handle fallback if URL is missing or connection fails
CACHE_TYPE = 'RedisCache'
CACHE_REDIS_URL = os.environ.get('REDIS_URL') # Will be None if env var not set
CACHE_DEFAULT_TIMEOUT = CACHE_TIMEOUT # Use production timeout

# Performance settings
JSONIFY_PRETTYPRINT_REGULAR = False
JSON_SORT_KEYS = False

# Rate limiting
RATELIMIT_DEFAULT = "1000 per day;100 per hour"

# Error handling
PROPAGATE_EXCEPTIONS = False 