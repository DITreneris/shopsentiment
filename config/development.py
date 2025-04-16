"""
Development configuration settings for the ShopSentiment application.
These settings override the default configuration for development environment.
"""

from config.default import *
import os

# Flask settings
DEBUG = True
TESTING = False

# Database settings - Do not hardcode USE_SQLITE, let environment variable control it
# USE_SQLITE = False  # Should be determined by environment variables

# MongoDB settings - Atlas connection
# URI will be supplied by environment variable MONGODB_URI
MONGODB_DB = os.environ.get('MONGODB_DB', 'shopsentiment')

# Logging settings
LOG_LEVEL = 'DEBUG'

# Development-specific settings
SENTIMENT_ANALYSIS_MODEL = 'development'
CACHE_TIMEOUT = 60  # 1 minute for faster development feedback

# Security settings
SESSION_COOKIE_SECURE = False

# Cache settings
CACHE_TYPE = 'simple'
CACHE_DEFAULT_TIMEOUT = CACHE_TIMEOUT

# Development tools
EXPLAIN_TEMPLATE_LOADING = True 