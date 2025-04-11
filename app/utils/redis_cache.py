"""
Redis Caching Utility for MongoDB Aggregation Queries
Provides optimized caching with invalidation for aggregation results
"""

import json
import logging
import hashlib
import pickle
from functools import wraps
from datetime import datetime, timedelta
from flask import current_app

logger = logging.getLogger(__name__)

# Default cache timeout (24 hours)
DEFAULT_CACHE_TIMEOUT = 60 * 60 * 24

class MongoCacheManager:
    """
    Redis cache manager for MongoDB aggregation results
    with support for automatic invalidation on data changes
    """
    
    def __init__(self, redis_client=None):
        """Initialize the cache manager"""
        self.redis = redis_client
        
    def get_redis(self):
        """Get the Redis client, either from constructor or from Flask app"""
        if self.redis:
            return self.redis
        elif hasattr(current_app, 'redis'):
            return current_app.redis
        else:
            logger.warning("Redis not available for caching")
            return None
    
    def _generate_key(self, prefix, args=None, kwargs=None):
        """Generate a unique cache key based on function arguments"""
        # Start with the prefix
        key_parts = [prefix]
        
        # Add string representation of positional args
        if args:
            for arg in args:
                if isinstance(arg, (list, dict, set)):
                    # Hash complex objects for consistent keys
                    arg_str = hashlib.md5(json.dumps(arg, sort_keys=True).encode()).hexdigest()
                else:
                    arg_str = str(arg)
                key_parts.append(arg_str)
        
        # Add string representation of keyword args
        if kwargs:
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (list, dict, set)):
                    # Hash complex objects for consistent keys
                    v_str = hashlib.md5(json.dumps(v, sort_keys=True).encode()).hexdigest()
                else:
                    v_str = str(v)
                key_parts.append(f"{k}:{v_str}")
        
        # Join all parts with a separator
        return ":".join(key_parts)
    
    def cache_aggregation(self, prefix, timeout=DEFAULT_CACHE_TIMEOUT, collections=None):
        """
        Decorator for caching MongoDB aggregation results in Redis
        
        Args:
            prefix: Cache key prefix for this function
            timeout: Cache timeout in seconds
            collections: List of MongoDB collection names that affect this result,
                         used for invalidation when collections are modified
        """
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                # Get Redis client
                redis = self.get_redis()
                if not redis:
                    # Redis not available, just execute the original function
                    return f(*args, **kwargs)
                
                # Skip cache if force_refresh is True
                force_refresh = kwargs.pop('force_refresh', False)
                
                # Generate cache key
                cache_key = self._generate_key(prefix, args, kwargs)
                
                # Try to get from cache if not forcing refresh
                if not force_refresh:
                    cached_result = redis.get(cache_key)
                    if cached_result:
                        try:
                            logger.debug(f"Cache hit for {cache_key}")
                            return pickle.loads(cached_result)
                        except Exception as e:
                            logger.warning(f"Error deserializing cached data: {e}")
                
                # Cache miss or error, execute the original function
                result = f(*args, **kwargs)
                
                # Cache the result
                try:
                    redis.setex(
                        cache_key,
                        timeout,
                        pickle.dumps(result)
                    )
                    
                    # Register this key with collections for invalidation
                    if collections:
                        for collection in collections:
                            # Add this key to the set of keys dependent on this collection
                            redis.sadd(f"collection_keys:{collection}", cache_key)
                            # Set expiration on the set to avoid unbounded growth
                            redis.expire(f"collection_keys:{collection}", timeout * 2)
                            
                    logger.debug(f"Cached result for {cache_key}")
                except Exception as e:
                    logger.warning(f"Error caching data in Redis: {e}")
                
                return result
            return wrapper
        return decorator
    
    def invalidate_collection(self, collection_name):
        """
        Invalidate all cache entries related to a specific collection
        
        Args:
            collection_name: Name of the MongoDB collection that was modified
        """
        redis = self.get_redis()
        if not redis:
            return
            
        try:
            # Get all keys dependent on this collection
            key_set = f"collection_keys:{collection_name}"
            keys = redis.smembers(key_set)
            
            if keys:
                # Delete all the keys
                redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries for collection {collection_name}")
                
                # Clean up the set itself
                redis.delete(key_set)
            else:
                logger.debug(f"No cache entries to invalidate for collection {collection_name}")
                
        except Exception as e:
            logger.warning(f"Error invalidating cache for collection {collection_name}: {e}")
    
    def register_invalidation_hooks(self, app=None):
        """
        Register hooks to automatically invalidate caches on data changes
        
        Args:
            app: Flask application instance (optional)
        """
        # This requires implementing event listeners for your MongoDB operations
        # The implementation depends on how your app manages MongoDB operations
        logger.info("Registered cache invalidation hooks")

# Create functions for common query types
mongo_cache = MongoCacheManager()

def cache_product_query(timeout=DEFAULT_CACHE_TIMEOUT):
    """Cache decorator for product queries"""
    return mongo_cache.cache_aggregation(
        prefix="product_query",
        timeout=timeout,
        collections=["products"]
    )

def cache_review_query(timeout=DEFAULT_CACHE_TIMEOUT):
    """Cache decorator for review queries"""
    return mongo_cache.cache_aggregation(
        prefix="review_query",
        timeout=timeout,
        collections=["reviews"]
    )

def cache_dashboard_stats(timeout=DEFAULT_CACHE_TIMEOUT):
    """Cache decorator for dashboard statistics"""
    return mongo_cache.cache_aggregation(
        prefix="dashboard_stats",
        timeout=timeout,
        collections=["products", "reviews"]
    )

def cache_user_data(timeout=60*60):  # 1 hour default for user data
    """Cache decorator for user data"""
    return mongo_cache.cache_aggregation(
        prefix="user_data",
        timeout=timeout,
        collections=["users"]
    )

def invalidate_on_update(collection_names):
    """
    Decorator to invalidate caches after function execution
    
    Args:
        collection_names: List of collection names affected by this operation
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            
            # Invalidate caches for all affected collections
            for collection in collection_names:
                mongo_cache.invalidate_collection(collection)
                
            return result
        return wrapper
    return decorator 