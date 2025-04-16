"""
Cache Factory Module

This module provides functionality to create and configure caching mechanisms
based on application configuration.
"""

import logging
from typing import Dict, Any

# Try to import Redis, but have a fallback if not available
try:
    from redis import Redis
    from flask_caching import Cache
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Use flask_caching's SimpleCache instead of the deprecated werkzeug.contrib.cache
try:
    from flask_caching import Cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

logger = logging.getLogger(__name__)

class SimpleCache:
    """Simple memory cache as fallback when flask_caching is not available"""
    
    def __init__(self, threshold=500, default_timeout=300):
        self.cache = {}
        self.threshold = threshold
        self.default_timeout = default_timeout
    
    def get(self, key):
        return self.cache.get(key)
    
    def set(self, key, value, timeout=None):
        self.cache[key] = value
        return True
    
    def delete(self, key):
        if key in self.cache:
            del self.cache[key]
        return True
    
    def ping(self):
        return True

def get_cache_from_app_config(config: Dict[str, Any]) -> Any:
    """
    Create and configure a cache instance based on the application configuration.
    
    Args:
        config: Application configuration dictionary
        
    Returns:
        Configured cache instance
    """
    cache_type = config.get('CACHE_TYPE', 'simple')
    
    if cache_type == 'redis' and REDIS_AVAILABLE:
        # Redis-based caching
        try:
            redis_url = config.get('REDIS_URL', 'redis://localhost:6379/0')
            redis_client = Redis.from_url(redis_url)
            
            # Test the connection
            redis_client.ping()
            
            cache = Cache(config={
                'CACHE_TYPE': 'redis',
                'CACHE_REDIS_URL': redis_url,
                'CACHE_DEFAULT_TIMEOUT': config.get('CACHE_TIMEOUT', 300)
            })
            
            logger.info(f"Using Redis cache at {redis_url}")
            return cache
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}. Falling back to simple cache.")
            if CACHE_AVAILABLE:
                return Cache(config={
                    'CACHE_TYPE': 'SimpleCache',
                    'CACHE_THRESHOLD': config.get('CACHE_THRESHOLD', 500),
                    'CACHE_DEFAULT_TIMEOUT': config.get('CACHE_TIMEOUT', 300)
                })
            else:
                return SimpleCache(threshold=config.get('CACHE_THRESHOLD', 500), default_timeout=config.get('CACHE_TIMEOUT', 300))
    else:
        # Simple in-memory cache
        logger.info("Using simple in-memory cache")
        if CACHE_AVAILABLE:
            return Cache(config={
                'CACHE_TYPE': 'SimpleCache',
                'CACHE_THRESHOLD': config.get('CACHE_THRESHOLD', 500),
                'CACHE_DEFAULT_TIMEOUT': config.get('CACHE_TIMEOUT', 300)
            })
        else:
            return SimpleCache(threshold=config.get('CACHE_THRESHOLD', 500), default_timeout=config.get('CACHE_TIMEOUT', 300)) 