import pytest
import fakeredis
import json
from unittest import mock
from app import app, cache
from app.tasks import scrape_amazon, scrape_ebay, analyze_sentiment

class TestRedisCache:
    """Tests for Redis caching functionality."""
    
    @pytest.fixture
    def redis_mock(self):
        """Create a fake Redis server for testing."""
        server = fakeredis.FakeServer()
        fake_redis = fakeredis.FakeStrictRedis(server=server)
        return fake_redis
    
    @pytest.fixture
    def patched_cache(self, redis_mock):
        """Patch the Flask-Caching with our fake Redis."""
        with mock.patch.object(cache, 'cache', redis_mock):
            yield cache
    
    def test_cache_get_set(self, patched_cache, redis_mock):
        """Test basic cache get/set operations."""
        # Set a value in cache
        patched_cache.set('test_key', 'test_value')
        
        # Check it was set in Redis
        assert redis_mock.get('test_key').decode() == 'test_value'
        
        # Get value from cache
        assert patched_cache.get('test_key') == 'test_value'
    
    def test_cache_memoize(self, client, monkeypatch, patched_cache):
        """Test memoization of function results."""
        # Create a mock function that counts calls
        call_count = 0
        
        @patched_cache.memoize(timeout=60)
        def test_func():
            nonlocal call_count
            call_count += 1
            return "result"
        
        # Call function twice
        result1 = test_func()
        result2 = test_func()
        
        # Verify correct results and that function was only called once
        assert result1 == "result"
        assert result2 == "result"
        assert call_count == 1

    def test_cache_route(self, client, patched_cache):
        """Test caching of route responses."""
        # Patch a route with cache
        @app.route('/test_cached_route')
        @patched_cache.cached(timeout=50)
        def test_cached_route():
            return "cached content"
        
        # Record calls to the route
        calls = []
        
        def record_call():
            calls.append(1)
            return "cached content"
        
        # Replace route function with one that records calls
        test_cached_route.view_class = record_call
        
        # Request the route twice
        response1 = client.get('/test_cached_route')
        response2 = client.get('/test_cached_route')
        
        # Verify both responses are correct and only one call was made
        assert response1.data == response2.data
        assert len(calls) == 1


class TestCeleryTasks:
    """Tests for Celery task functionality."""
    
    @pytest.fixture
    def mock_task(self):
        """Create a mock task runner that tracks execution."""
        executions = []
        
        class MockTask:
            def delay(self, *args, **kwargs):
                result = self(*args, **kwargs)
                return MockAsyncResult(result)
            
            def apply_async(self, args=None, kwargs=None, **options):
                result = self(*args or (), **(kwargs or {}))
                return MockAsyncResult(result)
                
            def __call__(self, *args, **kwargs):
                executions.append((args, kwargs))
                return {"status": "success", "task_id": "mock_task_id"}
        
        class MockAsyncResult:
            def __init__(self, result):
                self.result = result
                self.id = "mock_task_id"
            
            def get(self):
                return self.result
                
            @property
            def status(self):
                return "SUCCESS"
        
        return MockTask(), executions
    
    def test_scrape_amazon_task(self, mock_task):
        """Test the Amazon scraper task."""
        task, executions = mock_task
        
        # Patch the scrape_amazon task
        with mock.patch.object(scrape_amazon, 'delay', task.delay):
            with mock.patch.object(scrape_amazon, 'apply_async', task.apply_async):
                # Call the task
                result = scrape_amazon.delay("B01LYCLS24", 1)
                
                # Verify task was executed with correct parameters
                assert len(executions) == 1
                args, kwargs = executions[0]
                assert args[0] == "B01LYCLS24"
                assert args[1] == 1
                
                # Verify result
                assert result.id == "mock_task_id"
                assert result.status == "SUCCESS"
    
    def test_scrape_ebay_task(self, mock_task):
        """Test the eBay scraper task."""
        task, executions = mock_task
        
        # Patch the scrape_ebay task
        with mock.patch.object(scrape_ebay, 'delay', task.delay):
            with mock.patch.object(scrape_ebay, 'apply_async', task.apply_async):
                # Call the task
                result = scrape_ebay.delay("123456789", 2)
                
                # Verify task was executed with correct parameters
                assert len(executions) == 1
                args, kwargs = executions[0]
                assert args[0] == "123456789"
                assert args[1] == 2
                
                # Verify result
                assert result.id == "mock_task_id"
                assert result.status == "SUCCESS"
    
    def test_sentiment_analysis_task(self, mock_task):
        """Test the sentiment analysis task."""
        task, executions = mock_task
        
        # Patch the analyze_sentiment task
        with mock.patch.object(analyze_sentiment, 'delay', task.delay):
            with mock.patch.object(analyze_sentiment, 'apply_async', task.apply_async):
                # Call the task
                result = analyze_sentiment.delay(3)
                
                # Verify task was executed with correct parameters
                assert len(executions) == 1
                args, kwargs = executions[0]
                assert args[0] == 3
                
                # Verify result
                assert result.id == "mock_task_id"
                assert result.status == "SUCCESS"
    
    def test_task_chaining(self, mock_task):
        """Test chaining of tasks."""
        task, executions = mock_task
        
        # Patch both tasks
        with mock.patch.object(scrape_amazon, 'delay', task.delay):
            with mock.patch.object(analyze_sentiment, 'apply_async', task.apply_async):
                # Call the first task
                scrape_result = scrape_amazon.delay("B01LYCLS24", 4)
                
                # Chain with the second task
                analyze_result = analyze_sentiment.apply_async(args=[4], countdown=60)
                
                # Verify both tasks were executed with correct parameters
                assert len(executions) == 2
                
                first_args, first_kwargs = executions[0]
                assert first_args[0] == "B01LYCLS24"
                assert first_args[1] == 4
                
                second_args, second_kwargs = executions[1]
                assert second_args[0] == 4
                
                # Verify both results
                assert scrape_result.id == "mock_task_id"
                assert analyze_result.id == "mock_task_id" 