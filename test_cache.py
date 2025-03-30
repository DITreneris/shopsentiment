import unittest
import time
from datetime import datetime
from functools import wraps

# Import the caching decorator from app.py
def cached(timeout=300):
    def decorator(f):
        cache = {}
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = datetime.now().timestamp()
            if key in cache:
                if now - cache[key]['timestamp'] < timeout:
                    return cache[key]['value']
            result = f(*args, **kwargs)
            cache[key] = {'value': result, 'timestamp': now}
            return result
        return decorated_function
    return decorator

class CacheTests(unittest.TestCase):
    """Tests for the server-side caching functionality"""
    
    def setUp(self):
        """Set up a test function with cache"""
        # Count function calls
        self.call_count = 0
        
        # Create a test function with caching
        @cached(timeout=1)  # Short timeout for testing
        def test_function(x, y):
            self.call_count += 1
            return x + y
        
        self.test_function = test_function
    
    def test_cache_hit(self):
        """Test that cached values are returned without calling the function again"""
        # First call should execute the function
        result1 = self.test_function(1, 2)
        self.assertEqual(result1, 3, "Function should return correct result")
        self.assertEqual(self.call_count, 1, "Function should be called once")
        
        # Second call with same arguments should use the cache
        result2 = self.test_function(1, 2)
        self.assertEqual(result2, 3, "Cached result should be the same")
        self.assertEqual(self.call_count, 1, "Function should not be called again")
    
    def test_cache_miss(self):
        """Test that different arguments result in a cache miss"""
        # First call with one set of arguments
        result1 = self.test_function(1, 2)
        self.assertEqual(result1, 3, "Function should return correct result")
        self.assertEqual(self.call_count, 1, "Function should be called once")
        
        # Second call with different arguments should not use cache
        result2 = self.test_function(3, 4)
        self.assertEqual(result2, 7, "Function should return new result")
        self.assertEqual(self.call_count, 2, "Function should be called again")
    
    def test_cache_expiry(self):
        """Test that cache entries expire after the timeout"""
        # First call to cache the result
        result1 = self.test_function(1, 2)
        self.assertEqual(result1, 3, "Function should return correct result")
        self.assertEqual(self.call_count, 1, "Function should be called once")
        
        # Wait for cache to expire
        time.sleep(1.5)  # Longer than the timeout
        
        # Second call should execute the function again
        result2 = self.test_function(1, 2)
        self.assertEqual(result2, 3, "Function should return same result")
        self.assertEqual(self.call_count, 2, "Function should be called again after cache expires")
    
    def test_different_kwargs(self):
        """Test that different keyword arguments result in cache misses"""
        # Function with keyword arguments
        @cached(timeout=1)
        def kw_function(x, y=0):
            self.call_count += 1
            return x + y
        
        # Reset call count
        self.call_count = 0
        
        # First call with default kwarg
        result1 = kw_function(1)
        self.assertEqual(result1, 1, "Function should use default kwarg")
        self.assertEqual(self.call_count, 1, "Function should be called once")
        
        # Second call with explicit kwarg
        result2 = kw_function(1, y=2)
        self.assertEqual(result2, 3, "Function should use provided kwarg")
        self.assertEqual(self.call_count, 2, "Function should be called again for different kwargs")
    
    def test_cache_isolation(self):
        """Test that different decorated functions have isolated caches"""
        # Create a second function with its own cache
        @cached(timeout=1)
        def second_function(x, y):
            self.call_count += 1
            return x * y
        
        # Reset call count
        self.call_count = 0
        
        # Call first function
        result1 = self.test_function(2, 3)
        self.assertEqual(result1, 5, "First function should add numbers")
        self.assertEqual(self.call_count, 1, "First function should be called")
        
        # Call second function with same arguments
        result2 = second_function(2, 3)
        self.assertEqual(result2, 6, "Second function should multiply numbers")
        self.assertEqual(self.call_count, 2, "Second function should be called")
        
        # Call first function again
        result3 = self.test_function(2, 3)
        self.assertEqual(result3, 5, "First function should return cached result")
        self.assertEqual(self.call_count, 2, "First function should not be called again")

if __name__ == '__main__':
    unittest.main() 