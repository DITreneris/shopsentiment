"""
Redis Fallback Utility

This module provides a fallback mechanism for Redis caching services.
When Redis is unavailable, it provides in-memory caching or graceful degradation.
"""

import time
import logging
import json
import threading
import functools
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Callable, Union, List, Tuple
try:
    from redis.exceptions import RedisError, ConnectionError
except ImportError:
    # Define fallback exception classes if redis is not installed
    class RedisError(Exception):
        pass
    class ConnectionError(Exception):
        pass

logger = logging.getLogger(__name__)

# In-memory cache as fallback when Redis is unavailable
class InMemoryCache:
    """
    Simple in-memory cache implementation for use when Redis is unavailable.
    Provides basic TTL functionality and thread-safe operations.
    """
    def __init__(self, max_size: int = 1000):
        """Initialize the in-memory cache with a maximum size"""
        self._cache: Dict[str, Tuple[Any, float]] = {}  # {key: (value, expiry_timestamp)}
        self._lock = threading.RLock()
        self._max_size = max_size
        self._last_cleanup = time.time()
        self._cleanup_interval = 60  # seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache, returning None if expired or not found"""
        with self._lock:
            # Check if cleanup is needed
            self._maybe_cleanup()
            
            if key not in self._cache:
                return None
            
            value, expiry = self._cache[key]
            if expiry and time.time() > expiry:
                # Value has expired
                del self._cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: Any, expiry_seconds: Optional[int] = None) -> None:
        """Set a value in the cache with optional expiry time in seconds"""
        with self._lock:
            # Enforce maximum cache size
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_oldest()
            
            # Calculate expiry timestamp
            expiry = time.time() + expiry_seconds if expiry_seconds is not None else None
            
            # Store value and expiry
            self._cache[key] = (value, expiry)
    
    def delete(self, key: str) -> None:
        """Delete a key from the cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def _evict_oldest(self) -> None:
        """Evict the oldest entry when cache is full"""
        if not self._cache:
            return
        
        # Find the oldest entry (min expiry time or just any if no expiry)
        oldest_key = None
        oldest_time = float('inf')
        
        for key, (_, expiry) in self._cache.items():
            if expiry is None:
                # Items with no expiry are candidates for eviction
                oldest_key = key
                break
            elif expiry < oldest_time:
                oldest_key = key
                oldest_time = expiry
        
        if oldest_key:
            del self._cache[oldest_key]
    
    def _maybe_cleanup(self) -> None:
        """Periodically clean up expired entries"""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        self._last_cleanup = now
        expired_keys = []
        
        for key, (_, expiry) in self._cache.items():
            if expiry and now > expiry:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all entries from the cache"""
        with self._lock:
            self._cache.clear()
    
    def info(self) -> Dict[str, Any]:
        """Get information about the cache state"""
        with self._lock:
            now = time.time()
            active_count = 0
            expired_count = 0
            
            for _, expiry in self._cache.values():
                if expiry is None or now <= expiry:
                    active_count += 1
                else:
                    expired_count += 1
            
            return {
                "active_keys": active_count,
                "expired_keys": expired_count,
                "total_keys": len(self._cache),
                "max_size": self._max_size,
                "last_cleanup": datetime.fromtimestamp(self._last_cleanup).isoformat()
            }

# Global in-memory cache instance
_memory_cache = InMemoryCache()

class RedisFallback:
    """
    Provides fallback mechanisms for Redis operations.
    
    When Redis is unavailable, this class:
    1. Logs the failure
    2. Uses in-memory cache as fallback if appropriate
    3. Implements circuit breaker to avoid hammering Redis when it's down
    4. Provides status of Redis availability
    """
    def __init__(self, redis_client = None):
        """Initialize with optional Redis client"""
        self.redis_client = redis_client
        self.use_memory_cache = True
        self._circuit_open = False
        self._last_failure = 0
        self._failure_count = 0
        self._retry_interval = 30  # seconds before retrying Redis after failure
        self._max_failures = 3     # number of failures before opening circuit
        self._memory_cache = _memory_cache
        
        # Check if Redis is not configured at all
        if redis_client is None:
            logger.warning("Redis client not provided, using in-memory cache only")
            self._circuit_open = True
    
    def set_redis_client(self, redis_client) -> None:
        """Update the Redis client"""
        self.redis_client = redis_client
        # Reset circuit state when client changes
        self._circuit_open = False
        self._failure_count = 0
    
    def is_redis_available(self) -> bool:
        """Check if Redis is available"""
        if self._circuit_open:
            now = time.time()
            if now - self._last_failure >= self._retry_interval:
                # Try to close the circuit and test Redis
                self._circuit_open = False
                logger.info("Circuit breaker reset, trying Redis again")
            else:
                return False
        
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            # If we get here, Redis is available
            self._failure_count = 0
            return True
        except (RedisError, ConnectionError, AttributeError) as e:
            self._handle_failure(e)
            return False
    
    def _handle_failure(self, exception) -> None:
        """Handle Redis failure and update circuit breaker state"""
        self._last_failure = time.time()
        self._failure_count += 1
        
        if self._failure_count >= self._max_failures:
            if not self._circuit_open:
                logger.warning(f"Circuit breaker opened after {self._failure_count} Redis failures")
                self._circuit_open = True
        
        logger.warning(f"Redis operation failed: {str(exception)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value with Redis -> memory fallback"""
        # Try Redis first if available
        if self.is_redis_available():
            try:
                value = self.redis_client.get(key)
                if value:
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value.decode() if isinstance(value, bytes) else value
            except (RedisError, ConnectionError) as e:
                self._handle_failure(e)
                # Fall through to memory cache
        
        # Fall back to memory cache
        if self.use_memory_cache:
            return self._memory_cache.get(key)
        
        return default
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set a value with Redis -> memory fallback"""
        success = False
        
        # Try to serialize if not a string
        if not isinstance(value, (str, bytes)):
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                serialized = str(value)
        else:
            serialized = value
        
        # Try Redis first if available
        if self.is_redis_available():
            try:
                if ex:
                    self.redis_client.setex(key, ex, serialized)
                else:
                    self.redis_client.set(key, serialized)
                success = True
            except (RedisError, ConnectionError) as e:
                self._handle_failure(e)
                # Fall through to memory cache
        
        # Fall back to memory cache
        if self.use_memory_cache:
            self._memory_cache.set(key, value, ex)
            success = True
        
        return success
    
    def delete(self, key: str) -> bool:
        """Delete a value with Redis -> memory fallback"""
        success = False
        
        # Try Redis first if available
        if self.is_redis_available():
            try:
                self.redis_client.delete(key)
                success = True
            except (RedisError, ConnectionError) as e:
                self._handle_failure(e)
                # Fall through to memory cache
        
        # Fall back to memory cache
        if self.use_memory_cache:
            self._memory_cache.delete(key)
            success = True
        
        return success
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about fallback state"""
        info = {
            "redis_available": self.is_redis_available(),
            "circuit_breaker_status": "open" if self._circuit_open else "closed",
            "failure_count": self._failure_count,
            "memory_cache_enabled": self.use_memory_cache,
            "memory_cache_info": self._memory_cache.info() if self.use_memory_cache else None
        }
        
        # Add Redis info if available
        if info["redis_available"]:
            try:
                redis_info = self.redis_client.info()
                info["redis_info"] = {
                    "redis_version": redis_info.get("redis_version"),
                    "connected_clients": redis_info.get("connected_clients"),
                    "used_memory_human": redis_info.get("used_memory_human"),
                    "uptime_in_seconds": redis_info.get("uptime_in_seconds")
                }
            except (RedisError, ConnectionError) as e:
                self._handle_failure(e)
                info["redis_available"] = False
        
        return info

# Global instance for easy access
redis_fallback = RedisFallback()

def with_redis_fallback(func):
    """
    Decorator to add Redis fallback to functions that use Redis.
    If Redis fails, it will use in-memory cache or gracefully return a default value.
    
    Usage:
    @with_redis_fallback
    def my_function(redis_client, ...):
        # Function that uses Redis
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (RedisError, ConnectionError) as e:
            logger.warning(f"Redis error in {func.__name__}: {str(e)}")
            
            # Check if we can extract the key from args or kwargs
            key = None
            if len(args) > 1 and isinstance(args[1], str):
                key = args[1]
            elif 'key' in kwargs:
                key = kwargs['key']
            
            # Use in-memory cache if key is available
            if key and redis_fallback.use_memory_cache:
                # See if we're getting or setting
                if 'get' in func.__name__.lower():
                    return redis_fallback._memory_cache.get(key)
                elif 'set' in func.__name__.lower() and len(args) > 2:
                    value = args[2]
                    ex = kwargs.get('ex', None)
                    redis_fallback._memory_cache.set(key, value, ex)
                    return True
            
            # Last resort - return a sensible default
            if 'default' in kwargs:
                return kwargs['default']
            return None
    
    return wrapper 