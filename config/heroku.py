"""
Heroku-specific configuration settings for the ShopSentiment application.
These settings override the default configuration for Heroku deployment.
"""

import os
from .default import Config

class HerokuConfig(Config):
    """Heroku configuration class."""
    
    # Get environment variables set by Heroku
    MONGODB_URI = os.environ.get('MONGODB_URI')
    REDIS_URL = os.environ.get('REDIS_URL')
    
    # Flask settings
    DEBUG = False
    TESTING = False
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Logging settings - Heroku logs to stdout/stderr
    LOG_LEVEL = 'INFO'
    
    # Cache settings - Use Redis if available
    CACHE_TYPE = 'redis' if REDIS_URL else 'simple'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 3600
    
    # Performance settings
    JSONIFY_PRETTYPRINT_REGULAR = False
    JSON_SORT_KEYS = False
    
    # Static file serving
    # Heroku recommends using a CDN in production, but we'll use whitenoise for simplicity
    STATIC_ROOT = 'static'
    
    # Trusted proxy count for Heroku
    # This is important for proper IP address handling behind Heroku's load balancers
    TRUSTED_PROXIES = 1 