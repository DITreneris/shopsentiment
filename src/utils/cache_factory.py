"""
Cache Factory Module

This module provides functionality to create and configure caching mechanisms
based on application configuration.
"""

import logging
import os # Import os to check environment variables
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
    # --- REVERTED DEBUGGING --- 
    # cache_type_debug = config.get('CACHE_TYPE', 'SimpleCache')
    # redis_url_debug = config.get('CACHE_REDIS_URL')
    # raise RuntimeError(f"***** CACHE FACTORY DEBUG: Entered! Type={cache_type_debug}, URL={redis_url_debug}, RedisImportOK={REDIS_AVAILABLE} *****")
    # --- END REVERTED DEBUGGING ---

    # --- UNCONDITIONAL ENTRY LOG --- 
    logger.info("***** [Cache Factory] ENTERING get_cache_from_app_config *****") # Re-enabled
    # --- END UNCONDITIONAL ENTRY LOG ---
    
    cache_type = config.get('CACHE_TYPE', 'SimpleCache') # Default to SimpleCache # Re-enabled
    redis_url_from_config = config.get('CACHE_REDIS_URL') # Get potential URL # Re-enabled
    
    # ---> INSERT DIAGNOSTIC LOGGING HERE <---
    logger.info(f"[Cache Factory] Input Config CACHE_TYPE: {cache_type}") # Re-enabled
    logger.info(f"[Cache Factory] Redis Available (Import): {REDIS_AVAILABLE}") # Re-enabled
    logger.info(f"[Cache Factory] Input Config CACHE_REDIS_URL: {redis_url_from_config}") # Re-enabled
    # ---> END DIAGNOSTIC LOGGING <---
    
    # --- REST OF THE FUNCTION (Now reachable again) ---
    # Check if the configured type is RedisCache and if Redis is available
    if cache_type == 'RedisCache' and REDIS_AVAILABLE:
        # Redis-based caching
        try:
            # Use the variable already fetched
            redis_url = redis_url_from_config 
            if not redis_url:
                logger.error("[Cache Factory] CACHE_REDIS_URL is missing in config despite CACHE_TYPE being RedisCache.")
                raise ValueError("CACHE_REDIS_URL not found in config for RedisCache type")
            
            # Prepare Redis connection options
            redis_connect_options = {
                'socket_connect_timeout': 5
            }
            # If using SSL (rediss://), disable certificate verification ONLY for local dev
            is_production = os.environ.get('FLASK_ENV') == 'production'
            if redis_url.startswith('rediss://') and not is_production:
                logger.warning("[Cache Factory] Non-production env with 'rediss://'. Disabling SSL certificate verification.")
                redis_connect_options['ssl_cert_reqs'] = None
            elif redis_url.startswith('rediss://') and is_production:
                logger.info("[Cache Factory] Production env with 'rediss://'. Using default SSL certificate verification.")
                # Explicitly do *not* set ssl_cert_reqs=None in production
            
            # Test the connection directly using the URL from config and options
            redis_client = Redis.from_url(redis_url, **redis_connect_options) 
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
        # Add specific log why Redis wasn't chosen
        if cache_type == 'RedisCache' and not REDIS_AVAILABLE:
            logger.warning(f"CACHE_TYPE is RedisCache but Redis library import failed (REDIS_AVAILABLE=False). Falling back to SimpleCache.")
        elif cache_type != 'RedisCache':
             logger.info(f"CACHE_TYPE is '{cache_type}', not 'RedisCache'. Using simple in-memory cache.")
        else:
            logger.info(f"Using simple in-memory cache (type: {cache_type}). Condition: cache_type == 'RedisCache' and REDIS_AVAILABLE was False.")
            
        if CACHE_AVAILABLE:
            # Explicitly configure SimpleCache
            return Cache(config={
                'CACHE_TYPE': 'SimpleCache',
                'CACHE_THRESHOLD': config.get('CACHE_THRESHOLD', 500),
                'CACHE_DEFAULT_TIMEOUT': config.get('CACHE_DEFAULT_TIMEOUT', 300)
            })
        else:
            return SimpleCache(threshold=config.get('CACHE_THRESHOLD', 500), default_timeout=config.get('CACHE_DEFAULT_TIMEOUT', 300)) 