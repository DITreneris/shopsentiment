"""
Redis Cache Adapter

This module provides a Redis-based cache implementation for the ShopSentiment application.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

try:
    import redis
    from redis.exceptions import RedisError
except ImportError:
    redis = None
    RedisError = Exception

from src.utils.cache_adapter import CacheAdapter
from src.utils.cache_monitor import monitored_cache

logger = logging.getLogger(__name__)


class RedisCache(CacheAdapter):
    """
    Redis-based cache implementation.
    
    This adapter provides a distributed caching mechanism using Redis,
    suitable for production deployments and multi-server environments.
    """
    
    def __init__(self, namespace: str = "default", config: Optional[Dict[str, Any]] = None):
        """
        Initialize Redis cache adapter.
        
        Args:
            namespace: Cache namespace for prefixing keys
            config: Redis configuration options including:
                - host: Redis server hostname (default: localhost)
                - port: Redis server port (default: 6379)
                - db: Redis database number (default: 0)
                - password: Redis password (default: None)
                - socket_timeout: Socket timeout in seconds (default: 5)
                - default_ttl: Default TTL for cache entries (default: 300)
        """
        super().__init__(namespace, config)
        
        if redis is None:
            raise ImportError("Redis package is required. Install with 'pip install redis'.")
        
        self.config = config or {}
        self._client = self._create_redis_client()
        logger.debug(f"Initialized Redis cache with namespace '{namespace}'")
    
    def _create_redis_client(self) -> 'redis.Redis':
        """Create and configure Redis client."""
        try:
            client = redis.Redis(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 6379),
                db=self.config.get('db', 0),
                password=self.config.get('password'),
                socket_timeout=self.config.get('socket_timeout', 5),
                decode_responses=False  # We handle our own serialization
            )
            # Test connection
            client.ping()
            return client
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _serialize(self, value: Any) -> bytes:
        """
        Serialize value for storage in Redis.
        
        Args:
            value: Python object to serialize
            
        Returns:
            Serialized value as bytes
            
        Raises:
            ValueError: If serialization fails
        """
        try:
            return json.dumps(value).encode('utf-8')
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize value: {e}")
            raise ValueError(f"Unable to serialize value: {e}")
    
    def _deserialize(self, value: Optional[bytes]) -> Any:
        """
        Deserialize value from Redis.
        
        Args:
            value: Serialized value as bytes
            
        Returns:
            Deserialized Python object or None
            
        Raises:
            ValueError: If deserialization fails
        """
        if value is None:
            return None
        
        try:
            return json.loads(value.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.error(f"Failed to deserialize value: {e}")
            return None
    
    @monitored_cache
    def get(self, key: str) -> Any:
        """
        Get a value from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        cache_key = self._prepare_key(key)
        try:
            value = self._client.get(cache_key)
            return self._deserialize(value)
        except RedisError as e:
            logger.error(f"Redis error getting key '{key}': {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in Redis.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None for default)
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._prepare_key(key)
        ttl = ttl if ttl is not None else self.default_ttl
        
        try:
            serialized = self._serialize(value)
            if ttl > 0:
                result = self._client.setex(cache_key, ttl, serialized)
            else:
                result = self._client.set(cache_key, serialized)
            return bool(result)
        except (ValueError, RedisError) as e:
            logger.error(f"Redis error setting key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._prepare_key(key)
        try:
            result = self._client.delete(cache_key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis error deleting key '{key}': {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        cache_key = self._prepare_key(key)
        try:
            return bool(self._client.exists(cache_key))
        except RedisError as e:
            logger.error(f"Redis error checking existence of key '{key}': {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all values in the Redis cache for this namespace.
        
        Returns:
            True if successful, False otherwise
        """
        pattern = f"{self.namespace}:*"
        try:
            keys = self._client.keys(pattern)
            if keys:
                result = self._client.delete(*keys)
                return True
            return True  # No keys to delete is still successful
        except RedisError as e:
            logger.error(f"Redis error clearing namespace '{self.namespace}': {e}")
            return False
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from Redis efficiently.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary mapping keys to values
        """
        if not keys:
            return {}
        
        cache_keys = [self._prepare_key(k) for k in keys]
        try:
            # MGET is more efficient than multiple GET operations
            values = self._client.mget(cache_keys)
            result = {}
            
            for i, key in enumerate(keys):
                value = self._deserialize(values[i])
                if value is not None:
                    result[key] = value
            
            return result
        except RedisError as e:
            logger.error(f"Redis error getting multiple keys: {e}")
            # Fall back to individual gets
            return super().get_many(keys)
    
    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set multiple values in Redis efficiently.
        
        Args:
            mapping: Dictionary mapping keys to values
            ttl: Time-to-live in seconds (None for default)
            
        Returns:
            True if all operations successful, False otherwise
        """
        if not mapping:
            return True
        
        ttl = ttl if ttl is not None else self.default_ttl
        pipeline = self._client.pipeline()
        
        try:
            for key, value in mapping.items():
                cache_key = self._prepare_key(key)
                serialized = self._serialize(value)
                
                if ttl > 0:
                    pipeline.setex(cache_key, ttl, serialized)
                else:
                    pipeline.set(cache_key, serialized)
            
            pipeline.execute()
            return True
        except (ValueError, RedisError) as e:
            logger.error(f"Redis error setting multiple keys: {e}")
            # Fall back to individual sets
            return super().set_many(mapping, ttl)
    
    def delete_many(self, keys: List[str]) -> bool:
        """
        Delete multiple values from Redis efficiently.
        
        Args:
            keys: List of cache keys
            
        Returns:
            True if all operations successful, False otherwise
        """
        if not keys:
            return True
        
        cache_keys = [self._prepare_key(k) for k in keys]
        try:
            self._client.delete(*cache_keys)
            return True
        except RedisError as e:
            logger.error(f"Redis error deleting multiple keys: {e}")
            # Fall back to individual deletes
            return super().delete_many(keys)
    
    def get_ttl(self, key: str) -> Optional[int]:
        """
        Get the remaining time-to-live for a key in seconds.
        
        Args:
            key: Cache key
            
        Returns:
            Remaining TTL in seconds, None if key doesn't exist,
            or -1 if key exists but has no expiration
        """
        cache_key = self._prepare_key(key)
        try:
            ttl = self._client.ttl(cache_key)
            # Redis returns -2 if key doesn't exist, -1 if no expiry
            if ttl == -2:
                return None
            return ttl
        except RedisError as e:
            logger.error(f"Redis error getting TTL for key '{key}': {e}")
            return None 