"""
Unit tests for the cache module.
"""

import pytest
import os
import sys
import time
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path to import the application modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.utils.cache as cache_module
from src.utils.cache import cached, get_cache_key, get_cache_stats, clear_cache


class TestCacheKey:
    """Test cases for cache key generation."""

    def test_get_cache_key_with_simple_args(self):
        """Test generating a cache key with simple arguments."""
        # Execute
        key = get_cache_key("test", 123, "abc", True)
        
        # Assert
        assert key == "test:123:abc:True"

    def test_get_cache_key_with_kwargs(self):
        """Test generating a cache key with keyword arguments."""
        # Execute
        key = get_cache_key("test", user_id=123, name="john")
        
        # Assert
        assert key == "test:name=john:user_id=123"  # Note: sorted by key name

    def test_get_cache_key_with_mixed_args(self):
        """Test generating a cache key with mixed positional and keyword arguments."""
        # Execute
        key = get_cache_key("test", 123, "abc", name="john")
        
        # Assert
        assert key == "test:123:abc:name=john"

    def test_get_cache_key_with_object(self):
        """Test generating a cache key with an object argument."""
        # Execute
        class TestObject:
            def __init__(self):
                self.id = 123
                self.name = "test"
        
        obj = TestObject()
        key = get_cache_key("test", obj)
        
        # Assert
        assert "test:" in key
        assert "TestObject" in key or "hash" in key.lower()


class TestCacheDecorator:
    """Test cases for the cached decorator."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # Default to cache miss
        mock_redis.setex.return_value = True
        return mock_redis

    @pytest.fixture
    def setup_cache_module(self, mock_redis):
        """Setup the cache module with test settings."""
        # Save original values
        original_cache_enabled = cache_module.CACHE_ENABLED
        original_redis_client = cache_module.redis_client
        original_memory_cache = cache_module.memory_cache
        original_cache_hits = cache_module.cache_hits
        original_cache_misses = cache_module.cache_misses
        
        # Set test values
        cache_module.CACHE_ENABLED = True
        cache_module.redis_client = mock_redis
        cache_module.memory_cache = {}
        cache_module.cache_hits = 0
        cache_module.cache_misses = 0
        
        yield
        
        # Restore original values
        cache_module.CACHE_ENABLED = original_cache_enabled
        cache_module.redis_client = original_redis_client
        cache_module.memory_cache = original_memory_cache
        cache_module.cache_hits = original_cache_hits
        cache_module.cache_misses = original_cache_misses

    @pytest.mark.asyncio
    async def test_cached_function_cache_miss(self, setup_cache_module, mock_redis):
        """Test cached function with a cache miss."""
        # Setup
        mock_redis.get.return_value = None  # Cache miss
        
        # Define a test function
        counter = 0
        
        @cached("test")
        async def test_function(arg1, arg2):
            nonlocal counter
            counter += 1
            return f"{arg1}:{arg2}:{counter}"
        
        # Execute
        result1 = await test_function("a", "b")
        
        # Assert
        assert result1 == "a:b:1"
        assert counter == 1
        assert cache_module.cache_hits == 0
        assert cache_module.cache_misses == 1
        mock_redis.get.assert_called_once()
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_cached_function_cache_hit(self, setup_cache_module, mock_redis):
        """Test cached function with a cache hit."""
        # Setup
        import json
        cached_value = json.dumps("cached_result")
        mock_redis.get.return_value = cached_value  # Cache hit
        
        # Define a test function
        counter = 0
        
        @cached("test")
        async def test_function(arg1, arg2):
            nonlocal counter
            counter += 1
            return f"{arg1}:{arg2}:{counter}"
        
        # Execute
        result = await test_function("a", "b")
        
        # Assert
        assert result == "cached_result"
        assert counter == 0  # Function should not be called
        assert cache_module.cache_hits == 1
        assert cache_module.cache_misses == 0
        mock_redis.get.assert_called_once()
        mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_cached_function_with_timeout(self, setup_cache_module, mock_redis):
        """Test cached function with a custom timeout."""
        # Setup
        mock_redis.get.return_value = None  # Cache miss
        
        # Define a test function
        @cached("test", timeout=60)
        async def test_function():
            return "result"
        
        # Execute
        await test_function()
        
        # Assert - check if the correct timeout was used
        mock_redis.setex.assert_called_once()
        args, kwargs = mock_redis.setex.call_args
        assert args[1] == 60  # Should use the provided timeout

    @pytest.mark.asyncio
    async def test_cached_function_memory_cache(self, setup_cache_module):
        """Test cached function with memory cache."""
        # Setup
        cache_module.redis_client = None  # Disable Redis to use memory cache
        
        # Define a test function
        counter = 0
        
        @cached("test")
        async def test_function():
            nonlocal counter
            counter += 1
            return f"result:{counter}"
        
        # Execute - first call should be a miss
        result1 = await test_function()
        
        # Second call should be a hit
        result2 = await test_function()
        
        # Assert
        assert result1 == "result:1"
        assert result2 == "result:1"  # Should return cached result
        assert counter == 1  # Function should only be called once
        assert cache_module.cache_hits == 1
        assert cache_module.cache_misses == 1
        assert len(cache_module.memory_cache) == 1


class TestCacheStats:
    """Test cases for cache statistics."""

    @pytest.fixture
    def setup_cache_module(self):
        """Setup the cache module with test settings."""
        # Save original values
        original_cache_enabled = cache_module.CACHE_ENABLED
        original_redis_client = cache_module.redis_client
        original_memory_cache = cache_module.memory_cache
        original_cache_hits = cache_module.cache_hits
        original_cache_misses = cache_module.cache_misses
        
        # Set test values
        cache_module.CACHE_ENABLED = True
        cache_module.redis_client = None  # Use memory cache
        cache_module.memory_cache = {}
        cache_module.cache_hits = 10
        cache_module.cache_misses = 5
        
        yield
        
        # Restore original values
        cache_module.CACHE_ENABLED = original_cache_enabled
        cache_module.redis_client = original_redis_client
        cache_module.memory_cache = original_memory_cache
        cache_module.cache_hits = original_cache_hits
        cache_module.cache_misses = original_cache_misses

    def test_get_cache_stats(self, setup_cache_module):
        """Test getting cache statistics."""
        # Add some items to memory cache
        cache_module.memory_cache = {
            "key1": {"value": "value1", "expires": time.time() + 3600},
            "key2": {"value": "value2", "expires": time.time() + 3600}
        }
        
        # Execute
        stats = get_cache_stats()
        
        # Assert
        assert stats["enabled"] is True
        assert stats["hits"] == 10
        assert stats["misses"] == 5
        assert stats["total_requests"] == 15
        assert stats["hit_rate"] == round((10 / 15) * 100, 2)
        assert stats["memory_cache_size"] == 2

    def test_clear_cache(self, setup_cache_module):
        """Test clearing the cache."""
        # Add some items to memory cache
        cache_module.memory_cache = {
            "prefix1:key1": {"value": "value1", "expires": time.time() + 3600},
            "prefix1:key2": {"value": "value2", "expires": time.time() + 3600},
            "prefix2:key3": {"value": "value3", "expires": time.time() + 3600}
        }
        
        # Execute - clear specific prefix
        count1 = clear_cache("prefix1:*")
        
        # Assert
        assert count1 == 2
        assert "prefix1:key1" not in cache_module.memory_cache
        assert "prefix1:key2" not in cache_module.memory_cache
        assert "prefix2:key3" in cache_module.memory_cache
        
        # Execute - clear all
        count2 = clear_cache()
        
        # Assert
        assert count2 == 1
        assert len(cache_module.memory_cache) == 0 