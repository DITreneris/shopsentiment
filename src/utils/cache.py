"""
Caching module for the ShopSentiment application.
Implements Redis-based caching for API responses and frequently accessed data.
"""

import logging
import json
import functools
from typing import Callable, Any, Dict, Optional
import redis
import os
from datetime import datetime
from flask import current_app, request

logger = logging.getLogger(__name__)

# Cache configuration from environment
CACHE_ENABLED = os.environ.get('CACHE_ENABLED', 'True').lower() == 'true'
CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', 300))  # 5 minutes default
REDIS_URL = os.environ.get('CACHE_REDIS_URL', 'redis://localhost:6379/0')

# Statistics
cache_hits = 0
cache_misses = 0

# Cache client
redis_client = None

if CACHE_ENABLED and CACHE_TYPE == 'redis':
    try:
        redis_client = redis.Redis.from_url(REDIS_URL)
        redis_client.ping()  # Test the connection
        logger.info(f"Connected to Redis cache at {REDIS_URL}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        logger.warning("Falling back to in-memory caching")
        redis_client = None


# Simple in-memory cache as fallback
memory_cache = {}


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a consistent cache key from arguments."""
    key_parts = [prefix]
    
    # Add positional args
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        elif hasattr(arg, '__dict__'):
            # For objects, use a hash of their dict
            key_parts.append(str(hash(frozenset(arg.__dict__.items()))))
        else:
            # For other types, use their string representation
            key_parts.append(str(arg))
    
    # Add keyword args, sorted by key for consistency
    for key in sorted(kwargs.keys()):
        value = kwargs[key]
        if isinstance(value, (str, int, float, bool)):
            key_parts.append(f"{key}={value}")
        else:
            key_parts.append(f"{key}={str(hash(str(value)))}")
    
    return ":".join(key_parts)


def cached(prefix: str, timeout: Optional[int] = None):
    """
    Decorator for caching function results.
    
    Args:
        prefix: Prefix for the cache key
        timeout: Cache timeout in seconds, None uses the default
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            global cache_hits, cache_misses
            
            if not CACHE_ENABLED:
                return await func(*args, **kwargs)
                
            cache_key = get_cache_key(prefix, *args, **kwargs)
            ttl = timeout if timeout is not None else CACHE_TIMEOUT
            
            # Try to get from cache
            cached_value = None
            
            if redis_client:
                # Redis cache
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    try:
                        cached_value = json.loads(cached_data)
                        logger.debug(f"Cache hit for {cache_key}")
                        cache_hits += 1
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in cache for key {cache_key}")
            else:
                # Memory cache
                if cache_key in memory_cache:
                    cached_entry = memory_cache[cache_key]
                    # Check if entry is still valid
                    if cached_entry['expires'] > datetime.now().timestamp():
                        cached_value = cached_entry['value']
                        logger.debug(f"Cache hit for {cache_key}")
                        cache_hits += 1
                    else:
                        # Expired entry
                        del memory_cache[cache_key]
            
            if cached_value is not None:
                return cached_value
                
            # Cache miss, execute the function
            logger.debug(f"Cache miss for {cache_key}")
            cache_misses += 1
            result = await func(*args, **kwargs)
            
            # Store in cache
            try:
                serialized = json.dumps(result)
                if redis_client:
                    redis_client.setex(cache_key, ttl, serialized)
                else:
                    memory_cache[cache_key] = {
                        'value': result,
                        'expires': datetime.now().timestamp() + ttl
                    }
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Could not serialize result for caching: {str(e)}")
                
            return result
            
        return wrapper
    return decorator


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics about cache usage."""
    total_requests = cache_hits + cache_misses
    hit_rate = cache_hits / total_requests if total_requests > 0 else 0
    
    stats = {
        "enabled": CACHE_ENABLED,
        "cache_type": CACHE_TYPE,
        "timeout": CACHE_TIMEOUT,
        "hits": cache_hits,
        "misses": cache_misses,
        "total_requests": total_requests,
        "hit_rate": round(hit_rate * 100, 2),
        "memory_cache_size": len(memory_cache) if redis_client is None else 0
    }
    
    # Add Redis-specific stats if available
    if redis_client:
        try:
            info = redis_client.info()
            stats["redis_info"] = {
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", "unknown"),
                "uptime_in_days": info.get("uptime_in_days", "unknown"),
                "hit_rate": info.get("keyspace_hits", 0) / (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
            }
        except Exception as e:
            logger.error(f"Error getting Redis stats: {str(e)}")
    
    return stats


def clear_cache(pattern: str = "*") -> int:
    """
    Clear cache entries matching a pattern.
    
    Args:
        pattern: Pattern to match keys (default: "*" all keys)
        
    Returns:
        Number of keys deleted
    """
    if not CACHE_ENABLED:
        return 0
        
    if redis_client:
        try:
            keys = redis_client.keys(pattern)
            if keys:
                return redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing Redis cache: {str(e)}")
            return 0
    else:
        # Memory cache
        if pattern == "*":
            count = len(memory_cache)
            memory_cache.clear()
            return count
        else:
            # Simple pattern matching
            keys_to_delete = [k for k in memory_cache.keys() if k.startswith(pattern.replace("*", ""))]
            for key in keys_to_delete:
                del memory_cache[key]
            return len(keys_to_delete)


def cached_flask(key_prefix, timeout=None):
    """
    Cache decorator for Flask routes.
    
    Args:
        key_prefix: Prefix for cache key
        timeout: Cache timeout in seconds
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip cache for non-GET requests
            if request.method != 'GET':
                return f(*args, **kwargs)
                
            # Build cache key
            cache_key = f"{key_prefix}:{request.path}"
            query_args = request.args.to_dict()
            if query_args:
                args_str = "&".join(f"{key}={value}" for key, value in sorted(query_args.items()))
                cache_key = f"{cache_key}?{args_str}"
            
            # Check if app has cache
            if not hasattr(current_app, 'extensions') or 'cache' not in current_app.extensions:
                logger.warning("Cache not available, skipping cache")
                return f(*args, **kwargs)
                
            cache = current_app.extensions['cache']
            
            # Try to get from cache
            rv = cache.get(cache_key)
            if rv:
                logger.debug(f"Cache hit for {cache_key}")
                return rv
                
            # If not in cache, call function and cache result
            logger.debug(f"Cache miss for {cache_key}")
            rv = f(*args, **kwargs)
            
            # Use default timeout if none specified
            if timeout is None:
                timeout = current_app.config.get('CACHE_TIMEOUT', 300)
                
            cache.set(cache_key, rv, timeout=timeout)
            return rv
            
        return decorated_function
    return decorator 