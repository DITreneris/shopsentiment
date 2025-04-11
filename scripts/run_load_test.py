#!/usr/bin/env python
"""
MongoDB Load Testing Script using Locust
Tests application performance with synthetic data at 10x production volume
"""

import os
import sys
import time
import json
import random
import logging
import statistics
from bson import ObjectId
from datetime import datetime
from locust import HttpUser, task, between, events
from dotenv import load_dotenv
from pymongo import MongoClient

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "shopsentiment")

# Global variables to track performance
query_times = {
    "get_product": [],
    "search_products": [],
    "get_reviews": [],
    "filter_reviews": [],
    "aggregate_stats": []
}

# Connect to MongoDB
client = None
db = None

def setup_mongodb():
    """Connect to MongoDB and cache some test data"""
    global client, db
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    
    # Check if we have enough data for testing
    users_count = db.users.count_documents({})
    products_count = db.products.count_documents({})
    reviews_count = db.reviews.count_documents({})
    
    logger.info(f"MongoDB connected. Available data: {users_count} users, {products_count} products, {reviews_count} reviews")
    
    if products_count < 100 or reviews_count < 10000:
        logger.warning("Insufficient test data. Consider running load_test_data_generator.py first.")

def teardown_mongodb():
    """Close MongoDB connection"""
    if client:
        client.close()
        logger.info("MongoDB connection closed")

# Register setup and teardown hooks
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("Load test starting")
    setup_mongodb()

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("Load test complete")
    
    # Print performance statistics
    logger.info("Performance Statistics:")
    for query_type, times in query_times.items():
        if times:
            avg_time = sum(times) / len(times)
            median_time = statistics.median(times)
            p95_time = sorted(times)[int(len(times) * 0.95)]
            max_time = max(times)
            min_time = min(times)
            
            logger.info(f"{query_type}:")
            logger.info(f"  Count: {len(times)}")
            logger.info(f"  Avg: {avg_time:.2f}ms")
            logger.info(f"  Median: {median_time:.2f}ms")
            logger.info(f"  P95: {p95_time:.2f}ms")
            logger.info(f"  Min: {min_time:.2f}ms")
            logger.info(f"  Max: {max_time:.2f}ms")
    
    teardown_mongodb()

class MongoDBLoadTester:
    """Class containing MongoDB query methods to test"""
    
    @staticmethod
    def get_random_product_id():
        """Get a random product ID from the database"""
        # Skip a random number of documents to get a random product
        skip_count = random.randint(0, db.products.count_documents({}) - 1)
        product = db.products.find_one({}, skip=skip_count)
        return product["_id"] if product else None
    
    @staticmethod
    def get_random_platform():
        """Get a random platform from the database"""
        platforms = db.products.distinct("platform")
        return random.choice(platforms) if platforms else None
    
    @staticmethod
    def time_query(query_type, func, *args, **kwargs):
        """Time a MongoDB query and store the result"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # Convert to milliseconds
        query_time = (end_time - start_time) * 1000
        query_times[query_type].append(query_time)
        
        return result, query_time
    
    @staticmethod
    def get_product(product_id):
        """Get a single product by ID"""
        result, query_time = MongoDBLoadTester.time_query(
            "get_product",
            db.products.find_one,
            {"_id": product_id}
        )
        return result, query_time
    
    @staticmethod
    def search_products(platform, limit=10):
        """Search products by platform"""
        result, query_time = MongoDBLoadTester.time_query(
            "search_products",
            lambda: list(db.products.find({"platform": platform}).limit(limit))
        )
        return result, query_time
    
    @staticmethod
    def get_reviews(product_id, limit=50):
        """Get reviews for a product"""
        result, query_time = MongoDBLoadTester.time_query(
            "get_reviews",
            lambda: list(db.reviews.find({"product_id": product_id}).limit(limit))
        )
        return result, query_time
    
    @staticmethod
    def filter_reviews(product_id, sentiment, min_rating=None, limit=20):
        """Filter reviews by sentiment and rating"""
        query = {"product_id": product_id, "sentiment.label": sentiment}
        
        if min_rating is not None:
            query["rating"] = {"$gte": min_rating}
        
        result, query_time = MongoDBLoadTester.time_query(
            "filter_reviews",
            lambda: list(db.reviews.find(query).limit(limit))
        )
        return result, query_time
    
    @staticmethod
    def aggregate_product_stats(platform):
        """Run an aggregation pipeline to calculate stats by platform"""
        pipeline = [
            {"$match": {"platform": platform}},
            {"$group": {
                "_id": "$platform",
                "avg_price": {"$avg": {"$toDouble": "$price"}},
                "count": {"$sum": 1},
                "avg_rating": {"$avg": "$stats.avg_rating"}
            }}
        ]
        
        result, query_time = MongoDBLoadTester.time_query(
            "aggregate_stats",
            lambda: list(db.products.aggregate(pipeline))
        )
        return result, query_time

class MongoDBUser(HttpUser):
    """Locust user class for MongoDB load testing"""
    wait_time = between(1, 3)  # Wait between 1-3 seconds between tasks
    
    def on_start(self):
        """Initialize user session"""
        self.tester = MongoDBLoadTester()
    
    @task(10)
    def get_product_task(self):
        """Get a single product (high frequency task)"""
        product_id = self.tester.get_random_product_id()
        if not product_id:
            logger.warning("No products found in database")
            return
        
        product, query_time = self.tester.get_product(product_id)
        logger.debug(f"Got product in {query_time:.2f}ms: {product['title'] if product else None}")
    
    @task(5)
    def search_products_task(self):
        """Search products by platform (medium frequency task)"""
        platform = self.tester.get_random_platform()
        if not platform:
            logger.warning("No platforms found in database")
            return
        
        products, query_time = self.tester.search_products(platform)
        logger.debug(f"Found {len(products)} products in {query_time:.2f}ms")
    
    @task(8)
    def get_reviews_task(self):
        """Get reviews for a product (high frequency task)"""
        product_id = self.tester.get_random_product_id()
        if not product_id:
            logger.warning("No products found in database")
            return
        
        reviews, query_time = self.tester.get_reviews(product_id)
        logger.debug(f"Got {len(reviews)} reviews in {query_time:.2f}ms")
    
    @task(3)
    def filter_reviews_task(self):
        """Filter reviews by sentiment and rating (medium frequency task)"""
        product_id = self.tester.get_random_product_id()
        if not product_id:
            logger.warning("No products found in database")
            return
        
        sentiment = random.choice(["positive", "neutral", "negative"])
        min_rating = random.randint(1, 5) if random.random() < 0.5 else None
        
        reviews, query_time = self.tester.filter_reviews(product_id, sentiment, min_rating)
        logger.debug(f"Filtered to {len(reviews)} reviews in {query_time:.2f}ms")
    
    @task(1)
    def aggregate_stats_task(self):
        """Run aggregation pipeline (low frequency task)"""
        platform = self.tester.get_random_platform()
        if not platform:
            logger.warning("No platforms found in database")
            return
        
        stats, query_time = self.tester.aggregate_product_stats(platform)
        logger.debug(f"Aggregated stats in {query_time:.2f}ms: {stats}")

def run_direct_test(duration=60, users=10):
    """Run test directly without Locust UI"""
    logger.info(f"Starting direct test with {users} concurrent users for {duration} seconds")
    
    setup_mongodb()
    
    start_time = time.time()
    end_time = start_time + duration
    
    tester = MongoDBLoadTester()
    
    # Run until duration is reached
    while time.time() < end_time:
        task_choice = random.random()
        
        # Simulate task distribution similar to Locust
        if task_choice < 0.4:  # 40% chance
            product_id = tester.get_random_product_id()
            if product_id:
                tester.get_product(product_id)
        
        elif task_choice < 0.6:  # 20% chance
            platform = tester.get_random_platform()
            if platform:
                tester.search_products(platform)
        
        elif task_choice < 0.9:  # 30% chance
            product_id = tester.get_random_product_id()
            if product_id:
                tester.get_reviews(product_id)
        
        elif task_choice < 0.95:  # 5% chance
            product_id = tester.get_random_product_id()
            if product_id:
                sentiment = random.choice(["positive", "neutral", "negative"])
                min_rating = random.randint(1, 5) if random.random() < 0.5 else None
                tester.filter_reviews(product_id, sentiment, min_rating)
        
        else:  # 5% chance
            platform = tester.get_random_platform()
            if platform:
                tester.aggregate_product_stats(platform)
        
        # Sleep a short time to simulate user think time
        time.sleep(random.uniform(0.1, 0.5))
    
    # Print performance statistics
    logger.info("Direct test complete. Performance Statistics:")
    for query_type, times in query_times.items():
        if times:
            avg_time = sum(times) / len(times)
            median_time = statistics.median(times)
            p95_time = sorted(times)[int(len(times) * 0.95)] if len(times) >= 20 else max(times)
            max_time = max(times)
            min_time = min(times)
            
            logger.info(f"{query_type}:")
            logger.info(f"  Count: {len(times)}")
            logger.info(f"  Avg: {avg_time:.2f}ms")
            logger.info(f"  Median: {median_time:.2f}ms")
            logger.info(f"  P95: {p95_time:.2f}ms")
            logger.info(f"  Min: {min_time:.2f}ms")
            logger.info(f"  Max: {max_time:.2f}ms")
    
    teardown_mongodb()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run MongoDB load tests")
    parser.add_argument("--direct", action="store_true", help="Run direct test without Locust UI")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds (for direct test)")
    parser.add_argument("--users", type=int, default=10, help="Number of concurrent users (for direct test)")
    
    args = parser.parse_args()
    
    if args.direct:
        run_direct_test(args.duration, args.users)
    else:
        # When running with Locust, use the following command:
        # locust -f run_load_test.py --headless -u 10 -r 1 --run-time 1m
        # Or for the web UI:
        # locust -f run_load_test.py
        logger.info("Starting Locust load test. Press Ctrl+C to stop.")
        
        # This script should be run with Locust command line as shown above
        # The Locust executor will handle the rest 