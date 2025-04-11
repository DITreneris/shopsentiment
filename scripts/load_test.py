#!/usr/bin/env python3
"""
Load Testing Script for ShopSentiment

This script uses Locust to perform load testing on the ShopSentiment application
with production-scale data. It simulates multiple users accessing dashboard features
to identify performance bottlenecks.
"""

import os
import random
import json
import logging
from datetime import datetime
from locust import HttpUser, task, between, events, constant_pacing
from bson import ObjectId

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='load_test_results.log'
)
logger = logging.getLogger('load_test')

# Load test configuration
TEST_CONFIG = {
    "target_host": os.environ.get("TARGET_HOST", "http://localhost:5000"),
    "min_wait": 1,  # Minimum wait time between tasks in seconds
    "max_wait": 5,  # Maximum wait time between tasks in seconds
    "test_duration": 300,  # Test duration in seconds (5 minutes)
    "users": 50,  # Number of concurrent users
    "spawn_rate": 10,  # Users spawned per second
    "cache_enabled": True,  # Whether Redis cache is enabled
    "precomputed_stats_enabled": True,  # Whether precomputed MongoDB stats are enabled
    "test_name": f"full_load_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
}

# Global counters for metrics
METRICS = {
    "dashboard_views": 0,
    "sentiment_trend_requests": 0,
    "rating_distribution_requests": 0,
    "keyword_sentiment_requests": 0,
    "product_comparison_requests": 0,
    "api_errors": 0,
    "cached_responses": 0,
    "uncached_responses": 0
}

# Sample product IDs for testing (these would be loaded from the database in a real scenario)
SAMPLE_PRODUCT_IDS = [
    "607f1f77bcf86cd799439011",
    "607f1f77bcf86cd799439012",
    "607f1f77bcf86cd799439013",
    "607f1f77bcf86cd799439014",
    "607f1f77bcf86cd799439015",
    "607f1f77bcf86cd799439016",
    "607f1f77bcf86cd799439017",
    "607f1f77bcf86cd799439018",
    "607f1f77bcf86cd799439019",
    "607f1f77bcf86cd799439020"
]

# Load test data generator
class DataGenerator:
    """Generates test data for load testing"""
    
    @staticmethod
    def get_random_product_id():
        """Get a random product ID from the sample list"""
        return random.choice(SAMPLE_PRODUCT_IDS)
    
    @staticmethod
    def get_random_product_ids(count=2):
        """Get random product IDs for comparison"""
        return random.sample(SAMPLE_PRODUCT_IDS, min(count, len(SAMPLE_PRODUCT_IDS)))
    
    @staticmethod
    def get_random_days():
        """Get a random number of days for trend analysis"""
        return random.choice([30, 60, 90, 180, 365])
    
    @staticmethod
    def get_random_interval():
        """Get a random interval for trend analysis"""
        return random.choice(['day', 'week', 'month'])
    
    @staticmethod
    def get_random_platform():
        """Get a random platform for filtering"""
        return random.choice(['amazon', 'ebay', 'walmart', None])
    
    @staticmethod
    def get_random_min_count():
        """Get a random minimum count for keyword filtering"""
        return random.choice([5, 10, 25, 50])

# Custom events for test metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts"""
    logger.info(f"Starting load test: {TEST_CONFIG['test_name']}")
    logger.info(f"Configuration: {json.dumps(TEST_CONFIG, indent=2)}")
    
    # Reset metrics
    for key in METRICS:
        METRICS[key] = 0

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops"""
    logger.info(f"Load test completed: {TEST_CONFIG['test_name']}")
    logger.info(f"Metrics: {json.dumps(METRICS, indent=2)}")
    
    # Calculate cache hit rate
    total_requests = METRICS["cached_responses"] + METRICS["uncached_responses"]
    cache_hit_rate = (METRICS["cached_responses"] / total_requests) * 100 if total_requests > 0 else 0
    
    logger.info(f"Cache hit rate: {cache_hit_rate:.2f}%")
    logger.info(f"API errors: {METRICS['api_errors']}")

# Locust user class
class DashboardUser(HttpUser):
    """
    Simulates a user accessing the dashboard features
    
    This user will randomly request different dashboard endpoints to
    measure the performance under load.
    """
    wait_time = between(TEST_CONFIG["min_wait"], TEST_CONFIG["max_wait"])
    
    def on_start(self):
        """Setup before starting tests"""
        # Log in (if authentication is required)
        self.client.post("/login", {
            "username": "testuser",
            "password": "testpassword"
        })
        
    @task(20)
    def view_dashboard(self):
        """View the main dashboard"""
        with self.client.get("/dashboard", catch_response=True) as response:
            if response.status_code == 200:
                METRICS["dashboard_views"] += 1
            else:
                METRICS["api_errors"] += 1
                response.failure(f"Failed to load dashboard: {response.status_code}")
    
    @task(15)
    def get_sentiment_trend(self):
        """Get sentiment trend data for a random product"""
        product_id = DataGenerator.get_random_product_id()
        days = DataGenerator.get_random_days()
        interval = DataGenerator.get_random_interval()
        
        url = f"/api/dashboard/sentiment-trend?product_id={product_id}&days={days}&interval={interval}"
        
        with self.client.get(url, catch_response=True) as response:
            if response.status_code == 200:
                METRICS["sentiment_trend_requests"] += 1
                
                # Check if response was cached
                if 'X-Cache' in response.headers and response.headers['X-Cache'] == 'HIT':
                    METRICS["cached_responses"] += 1
                else:
                    METRICS["uncached_responses"] += 1
            else:
                METRICS["api_errors"] += 1
                response.failure(f"Failed to get sentiment trend: {response.status_code}")
    
    @task(10)
    def get_rating_distribution(self):
        """Get rating distribution data"""
        platform = DataGenerator.get_random_platform()
        days = DataGenerator.get_random_days()
        
        url = f"/api/dashboard/rating-distribution?days={days}"
        if platform:
            url += f"&platform={platform}"
        
        with self.client.get(url, catch_response=True) as response:
            if response.status_code == 200:
                METRICS["rating_distribution_requests"] += 1
                
                # Check if response was cached
                if 'X-Cache' in response.headers and response.headers['X-Cache'] == 'HIT':
                    METRICS["cached_responses"] += 1
                else:
                    METRICS["uncached_responses"] += 1
            else:
                METRICS["api_errors"] += 1
                response.failure(f"Failed to get rating distribution: {response.status_code}")
    
    @task(8)
    def get_keyword_sentiment(self):
        """Get keyword sentiment data"""
        min_count = DataGenerator.get_random_min_count()
        
        url = f"/api/dashboard/keyword-sentiment?min_count={min_count}"
        
        with self.client.get(url, catch_response=True) as response:
            if response.status_code == 200:
                METRICS["keyword_sentiment_requests"] += 1
                
                # Check if response was cached
                if 'X-Cache' in response.headers and response.headers['X-Cache'] == 'HIT':
                    METRICS["cached_responses"] += 1
                else:
                    METRICS["uncached_responses"] += 1
            else:
                METRICS["api_errors"] += 1
                response.failure(f"Failed to get keyword sentiment: {response.status_code}")
    
    @task(5)
    def get_product_comparison(self):
        """Get product comparison data"""
        product_ids = DataGenerator.get_random_product_ids(2)
        product_ids_str = ",".join(product_ids)
        
        url = f"/api/dashboard/product-comparison?product_ids={product_ids_str}"
        
        with self.client.get(url, catch_response=True) as response:
            if response.status_code == 200:
                METRICS["product_comparison_requests"] += 1
                
                # Check if response was cached
                if 'X-Cache' in response.headers and response.headers['X-Cache'] == 'HIT':
                    METRICS["cached_responses"] += 1
                else:
                    METRICS["uncached_responses"] += 1
            else:
                METRICS["api_errors"] += 1
                response.failure(f"Failed to get product comparison: {response.status_code}")

# Performance test class with constant pacing
class PerformanceTestUser(HttpUser):
    """
    Simulates a user performing intensive operations in a controlled sequence
    
    This user helps measure performance degradation over time by executing
    the same sequence of operations repeatedly.
    """
    wait_time = constant_pacing(10)  # Execute tasks every 10 seconds
    
    def on_start(self):
        """Setup before starting tests"""
        # Log in (if authentication is required)
        self.client.post("/login", {
            "username": "testuser",
            "password": "testpassword"
        })
    
    @task
    def performance_test_sequence(self):
        """Execute a fixed sequence of operations"""
        # 1. View dashboard
        with self.client.get("/dashboard", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to load dashboard: {response.status_code}")
                return
        
        # 2. Get sentiment trend for a specific product
        product_id = SAMPLE_PRODUCT_IDS[0]  # Use the same product each time
        with self.client.get(f"/api/dashboard/sentiment-trend?product_id={product_id}&days=90&interval=day", 
                            catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get sentiment trend: {response.status_code}")
                return
        
        # 3. Get rating distribution
        with self.client.get("/api/dashboard/rating-distribution?days=90", 
                            catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get rating distribution: {response.status_code}")
                return
        
        # 4. Get keyword sentiment
        with self.client.get("/api/dashboard/keyword-sentiment?min_count=10", 
                            catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get keyword sentiment: {response.status_code}")
                return
        
        # 5. Get product comparison
        product_ids = ",".join(SAMPLE_PRODUCT_IDS[:2])  # Use the same products each time
        with self.client.get(f"/api/dashboard/product-comparison?product_ids={product_ids}", 
                            catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get product comparison: {response.status_code}")
                return

if __name__ == "__main__":
    # This script is meant to be run by Locust, not directly
    print("This script should be run using the Locust command line interface:")
    print("locust -f load_test.py --host=http://localhost:5000 --users=50 --spawn-rate=10 --run-time=5m")
    print("\nFor headless mode:")
    print("locust -f load_test.py --host=http://localhost:5000 --users=50 --spawn-rate=10 --run-time=5m --headless --csv=results") 