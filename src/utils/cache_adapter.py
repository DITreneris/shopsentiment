"""
Cache Adapter Module - Simplified version for testing

This module provides a standardized interface for caching with basic monitoring.
"""

import time
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class CacheAdapter:
    """Base class for cache adapters."""
    
    def __init__(self, namespace='default', config=None):
        self.namespace = namespace
        self.config = config or {}
        self.default_ttl = self.config.get('default_ttl', 300)
    
    def _prepare_key(self, key):
        """Format key with namespace."""
        return f"{self.namespace}:{key}" if self.namespace else key
    
    def get(self, key):
        """Get a value from the cache."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def set(self, key, value, ttl=None):
        """Set a value in the cache."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def delete(self, key):
        """Delete a value from the cache."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def exists(self, key):
        """Check if a key exists in the cache."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def clear(self):
        """Clear the cache namespace."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_many(self, keys):
        """Get multiple values from cache."""
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    def set_many(self, mapping, ttl=None):
        """Set multiple values in cache."""
        success = True
        for key, value in mapping.items():
            if not self.set(key, value, ttl):
                success = False
        return success
    
    def delete_many(self, keys):
        """Delete multiple values from cache."""
        success = True
        for key in keys:
            if not self.delete(key):
                success = False
        return success

class InMemoryCache(CacheAdapter):
    """Simple in-memory cache implementation."""
    
    def __init__(self, namespace='default', config=None):
        super().__init__(namespace, config)
        self._cache = {}
    
    def get(self, key):
        """Get a value from the in-memory cache."""
        from src.utils.cache_monitor import CacheMonitor
        
        cache_key = self._prepare_key(key)
        start_time = time.time()
        
        if cache_key in self._cache:
            # Check expiration
            if self._cache[cache_key]['expires'] > time.time() or self._cache[cache_key]['expires'] == 0:
                value = self._cache[cache_key]['value']
                duration = time.time() - start_time
                
                # Record cache hit
                monitor = CacheMonitor.get_instance()
                monitor.record_hit(key, duration)
                
                return value
                
            # Expired, remove it
            self.delete(key)
        
        # Record cache miss
        duration = time.time() - start_time
        monitor = CacheMonitor.get_instance()
        monitor.record_miss(key, duration)
        
        return None
    
    def set(self, key, value, ttl=None):
        """Set a value in the in-memory cache."""
        cache_key = self._prepare_key(key)
        ttl = ttl if ttl is not None else self.default_ttl
        expires = time.time() + ttl if ttl > 0 else 0
        
        try:
            self._cache[cache_key] = {
                'value': value,
                'expires': expires
            }
            return True
        except Exception as e:
            logger.error(f"Error setting cache key '{key}': {e}")
            return False
    
    def delete(self, key):
        """Delete a value from the in-memory cache."""
        cache_key = self._prepare_key(key)
        if cache_key in self._cache:
            del self._cache[cache_key]
            return True
        return False
    
    def exists(self, key):
        """Check if a key exists in the in-memory cache."""
        cache_key = self._prepare_key(key)
        if cache_key in self._cache:
            # Check expiration
            if self._cache[cache_key]['expires'] > time.time() or self._cache[cache_key]['expires'] == 0:
                return True
            # Expired, remove it
            self.delete(key)
        return False
    
    def clear(self):
        """Clear all values in the in-memory cache for this namespace."""
        try:
            # Only clear keys for this namespace
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(f"{self.namespace}:")]
            for k in keys_to_delete:
                del self._cache[k]
            return True
        except Exception as e:
            logger.error(f"Error clearing cache namespace '{self.namespace}': {e}")
            return False

def create_cache_adapter(adapter_type='memory', namespace='default', config=None):
    """
    Factory function to create a cache adapter instance.
    
    Args:
        adapter_type: Type of cache adapter ('memory', 'redis', etc.)
        namespace: Cache namespace
        config: Cache configuration
        
    Returns:
        CacheAdapter instance
    """
    config = config or {}
    
    if adapter_type == 'memory':
        return InMemoryCache(namespace, config)
    else:
        logger.warning(f"Unknown cache adapter type: {adapter_type}. Using memory cache instead.")
        return InMemoryCache(namespace, config) 