#!/usr/bin/env python3
"""
MongoDB Integration Tests

This script tests the MongoDB integration features of the ShopSentiment app.
It requires a running MongoDB instance on localhost:27017.

Usage:
    python -m tests.test_mongodb_integration
"""

import os
import sys
import unittest
import datetime
from bson.objectid import ObjectId
import pymongo
import logging
from pathlib import Path

# Add parent directory to path so we can import app modules
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mongodb_integration_test')

# Set MongoDB URI for testing
os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/'
os.environ['MONGODB_DB_NAME'] = 'shopsentiment_test'

# Now import app modules
from app.models import User, Product, Review
from app.utils.mongodb import get_db, get_collection, init_mongodb, close_db
from app import create_app

class MongoDBIntegrationTest(unittest.TestCase):
    """Test case for MongoDB integration."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        # Create Flask app with testing config
        cls.app = create_app('testing')
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        # Initialize MongoDB with app
        init_mongodb(cls.app)
        
        # Get MongoDB connection
        cls.db = get_db()
        
        # Clean up test database
        for collection in cls.db.list_collection_names():
            cls.db.drop_collection(collection)
        
        logger.info("Test environment set up")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment after all tests."""
        # Clean up test database
        client = pymongo.MongoClient(os.environ['MONGODB_URI'])
        client.drop_database(os.environ['MONGODB_DB_NAME'])
        
        # Close MongoDB connection
        close_db(None)
        
        # Remove app context
        cls.app_context.pop()
        
        logger.info("Test environment cleaned up")
    
    def setUp(self):
        """Set up before each test."""
        # Clean all collections before each test
        for collection in self.db.list_collection_names():
            self.db[collection].delete_many({})
    
    def test_user_model(self):
        """Test User model with MongoDB."""
        logger.info("Testing User model")
        
        # Create a user
        user = User(
            username="testuser",
            email="test@example.com",
            is_admin=True,
            created_at=datetime.datetime.now()
        )
        user.set_password("password123")
        
        # Save to database
        user_id = user.save()
        self.assertIsNotNone(user_id, "User ID should not be None")
        
        # Get by ID
        retrieved_user = User.get_by_id(user_id)
        self.assertIsNotNone(retrieved_user, "User should be retrieved by ID")
        self.assertEqual(retrieved_user.username, "testuser")
        self.assertEqual(retrieved_user.email, "test@example.com")
        self.assertTrue(retrieved_user.is_admin)
        
        # Get by email
        retrieved_user = User.get_by_email("test@example.com")
        self.assertIsNotNone(retrieved_user, "User should be retrieved by email")
        self.assertEqual(retrieved_user.username, "testuser")
        
        # Check password
        self.assertTrue(retrieved_user.check_password("password123"))
        self.assertFalse(retrieved_user.check_password("wrongpassword"))
        
        # Update user
        retrieved_user.username = "updateduser"
        updated_id = retrieved_user.save()
        self.assertEqual(updated_id, user_id, "User ID should not change on update")
        
        # Verify update
        updated_user = User.get_by_id(user_id)
        self.assertEqual(updated_user.username, "updateduser")
    
    def test_product_model(self):
        """Test Product model with MongoDB."""
        logger.info("Testing Product model")
        
        # Create a product
        product = Product(
            platform_id="B01ABCDEF",
            platform="amazon",
            title="Test Product",
            brand="Test Brand",
            price="29.99",
            image_url="http://example.com/image.jpg",
            url="http://amazon.com/dp/B01ABCDEF",
            created_at=datetime.datetime.now()
        )
        
        # Save to database
        product_id = product.save()
        self.assertIsNotNone(product_id, "Product ID should not be None")
        
        # Get by ID
        retrieved_product = Product.get_by_id(product_id)
        self.assertIsNotNone(retrieved_product, "Product should be retrieved by ID")
        self.assertEqual(retrieved_product.platform_id, "B01ABCDEF")
        self.assertEqual(retrieved_product.platform, "amazon")
        self.assertEqual(retrieved_product.title, "Test Product")
        
        # Get by platform ID
        retrieved_product = Product.get_by_platform_id("amazon", "B01ABCDEF")
        self.assertIsNotNone(retrieved_product, "Product should be retrieved by platform ID")
        self.assertEqual(retrieved_product.title, "Test Product")
        
        # Update product
        retrieved_product.title = "Updated Product"
        retrieved_product.price = "39.99"
        updated_id = retrieved_product.save()
        self.assertEqual(updated_id, product_id, "Product ID should not change on update")
        
        # Verify update
        updated_product = Product.get_by_id(product_id)
        self.assertEqual(updated_product.title, "Updated Product")
        self.assertEqual(updated_product.price, "39.99")
        
        # Get all products
        products = Product.get_all()
        self.assertEqual(len(products), 1, "Should retrieve all products")
    
    def test_review_model(self):
        """Test Review model with MongoDB."""
        logger.info("Testing Review model")
        
        # Create a product first
        product = Product(
            platform_id="B01ABCDEF",
            platform="amazon",
            title="Test Product",
            created_at=datetime.datetime.now()
        )
        product_id = product.save()
        
        # Create a review
        review = Review(
            product_id=product_id,
            platform_review_id="R123456",
            title="Great product",
            content="I love this product! It works great.",
            rating=5.0,
            author="TestUser",
            date=datetime.datetime.now(),
            verified_purchase=True,
            sentiment={
                'score': 0.8,
                'label': 'positive',
                'compound': 0.8,
                'pos': 0.8,
                'neg': 0.0,
                'neu': 0.2
            },
            created_at=datetime.datetime.now()
        )
        
        # Save to database
        review_id = review.save()
        self.assertIsNotNone(review_id, "Review ID should not be None")
        
        # Get by ID
        retrieved_review = Review.get_by_id(review_id)
        self.assertIsNotNone(retrieved_review, "Review should be retrieved by ID")
        self.assertEqual(retrieved_review.platform_review_id, "R123456")
        self.assertEqual(retrieved_review.content, "I love this product! It works great.")
        self.assertEqual(retrieved_review.rating, 5.0)
        
        # Get by product ID
        reviews = Review.get_by_product_id(product_id)
        self.assertEqual(len(reviews), 1, "Should retrieve reviews by product ID")
        
        # Update review
        retrieved_review.rating = 4.0
        retrieved_review.content = "Updated review content"
        updated_id = retrieved_review.save()
        self.assertEqual(updated_id, review_id, "Review ID should not change on update")
        
        # Verify update
        updated_review = Review.get_by_id(review_id)
        self.assertEqual(updated_review.rating, 4.0)
        self.assertEqual(updated_review.content, "Updated review content")
        
        # Check product stats were updated
        updated_product = Product.get_by_id(product_id)
        self.assertEqual(updated_product.stats['review_count'], 1, "Product stats should be updated")
        self.assertEqual(updated_product.stats['avg_rating'], 4.0, "Average rating should be updated")
    
    def test_mongodb_utility_functions(self):
        """Test MongoDB utility functions."""
        logger.info("Testing MongoDB utility functions")
        
        # Test get_collection
        users_collection = get_collection('users')
        self.assertIsNotNone(users_collection, "Should get users collection")
        
        products_collection = get_collection('products')
        self.assertIsNotNone(products_collection, "Should get products collection")
        
        reviews_collection = get_collection('reviews')
        self.assertIsNotNone(reviews_collection, "Should get reviews collection")
        
        # Test indexes
        indexes = list(users_collection.list_indexes())
        self.assertGreaterEqual(len(indexes), 2, "Users collection should have indexes")
        
        indexes = list(products_collection.list_indexes())
        self.assertGreaterEqual(len(indexes), 2, "Products collection should have indexes")
        
        indexes = list(reviews_collection.list_indexes())
        self.assertGreaterEqual(len(indexes), 2, "Reviews collection should have indexes")

if __name__ == '__main__':
    unittest.main() 