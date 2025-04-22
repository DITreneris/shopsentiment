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
    # --- TEMPORARY DEBUGGING: RAISE EXCEPTION --- 
    cache_type_debug = config.get('CACHE_TYPE', 'SimpleCache')
    redis_url_debug = config.get('CACHE_REDIS_URL')
    raise RuntimeError(f"***** CACHE FACTORY DEBUG: Entered! Type={cache_type_debug}, URL={redis_url_debug}, RedisImportOK={REDIS_AVAILABLE} *****")
    # --- END TEMPORARY DEBUGGING ---

    # --- UNCONDITIONAL ENTRY LOG --- 
    # logger.info("***** [Cache Factory] ENTERING get_cache_from_app_config *****") # Commented out for now
    # --- END UNCONDITIONAL ENTRY LOG ---
    
    # cache_type = config.get('CACHE_TYPE', 'SimpleCache') # Default to SimpleCache # Commented out
    # redis_url_from_config = config.get('CACHE_REDIS_URL') # Get potential URL # Commented out
    
    # ---> INSERT DIAGNOSTIC LOGGING HERE <---
    # logger.info(f"[Cache Factory] Input Config CACHE_TYPE: {cache_type}") # Commented out
    # logger.info(f"[Cache Factory] Redis Available (Import): {REDIS_AVAILABLE}") # Commented out
    # logger.info(f"[Cache Factory] Input Config CACHE_REDIS_URL: {redis_url_from_config}") # Commented out
    # ---> END DIAGNOSTIC LOGGING <---
    
    # --- REST OF THE FUNCTION (WILL NOT BE REACHED) ---
    # Check if the configured type is RedisCache and if Redis is available
    # ... (original code remains here but won't execute due to the raise) ...

    # Check if the configured type is RedisCache and if Redis is available
    if cache_type == 'RedisCache' and REDIS_AVAILABLE:
        # Redis-based caching
        try:
            # Get REDIS_URL from config (which should come from env var in production)
            # Use the variable already fetched
            redis_url = redis_url_from_config 
            if not redis_url:
                 logger.error("[Cache Factory] CACHE_REDIS_URL is missing in config despite CACHE_TYPE being RedisCache.")
                 raise ValueError("CACHE_REDIS_URL not found in config for RedisCache type")

            # Test the connection directly using the URL from config
            redis_client = Redis.from_url(redis_url, socket_connect_timeout=5) # Add timeout
            redis_client.ping()
            
            # Configure flask_caching with the correct type and URL
            cache_config_dict = {
                'CACHE_TYPE': 'RedisCache', # Use the correct type name for flask_caching
                'CACHE_REDIS_URL': redis_url,
                'CACHE_DEFAULT_TIMEOUT': config.get('CACHE_DEFAULT_TIMEOUT', 300)
            }
            cache = Cache(config=cache_config_dict)
            
            logger.info(f"Using Redis cache (RedisCache) at {redis_url}")
            return cache
        except Exception as e:
            # Log the specific exception and traceback when Redis fails
            logger.error(f"!!! Redis Initialization Failed: {type(e).__name__}: {str(e)} !!!", exc_info=True)
            logger.warning(f"Failed to initialize Redis cache (type RedisCache). Falling back to simple cache.")
            # Fallback logic remains the same
            if CACHE_AVAILABLE:
                # Explicitly configure SimpleCache
                return Cache(config={
                    'CACHE_TYPE': 'SimpleCache',
                    'CACHE_THRESHOLD': config.get('CACHE_THRESHOLD', 500),
                    'CACHE_DEFAULT_TIMEOUT': config.get('CACHE_DEFAULT_TIMEOUT', 300)
                })
            else:
                return SimpleCache(threshold=config.get('CACHE_THRESHOLD', 500), default_timeout=config.get('CACHE_DEFAULT_TIMEOUT', 300))
    else:
        # Simple in-memory cache or if Redis type was specified but not available
        logger.info(f"Using simple in-memory cache (type: {cache_type})")
        if CACHE_AVAILABLE:
            # Explicitly configure SimpleCache
            return Cache(config={
                'CACHE_TYPE': 'SimpleCache',
                'CACHE_THRESHOLD': config.get('CACHE_THRESHOLD', 500),
                'CACHE_DEFAULT_TIMEOUT': config.get('CACHE_DEFAULT_TIMEOUT', 300)
            })
        else:
            return SimpleCache(threshold=config.get('CACHE_THRESHOLD', 500), default_timeout=config.get('CACHE_DEFAULT_TIMEOUT', 300)) 