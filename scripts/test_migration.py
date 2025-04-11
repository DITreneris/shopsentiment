#!/usr/bin/env python3
"""
Test script for the SQLite to MongoDB migration utility.

This script:
1. Creates a sample SQLite database with test data
2. Starts a local MongoDB instance using pymongo
3. Runs the migration script
4. Verifies the migration was successful

Usage:
    python test_migration.py
"""

import os
import sys
import sqlite3
import tempfile
import unittest
import datetime
import subprocess
import logging
from pathlib import Path
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_migration')

# Add parent directory to path so we can import the migration script
sys.path.append(str(Path(__file__).parent))
import migrate_to_mongodb

class TestMigration(unittest.TestCase):
    """Test case for SQLite to MongoDB migration."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary SQLite database
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, 'test.db')
        self.create_sqlite_database()
        
        # MongoDB connection info - using default local MongoDB
        self.mongo_uri = "mongodb://localhost:27017/"
        self.mongo_db_name = "shopsentiment_test"
        
        # Clean MongoDB database to start fresh
        try:
            import pymongo
            client = pymongo.MongoClient(self.mongo_uri)
            client.drop_database(self.mongo_db_name)
            logger.info(f"Dropped MongoDB database: {self.mongo_db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            logger.error("Make sure MongoDB is running locally on port 27017")
            sys.exit(1)
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up temporary files
        self.temp_dir.cleanup()
        
        # Clean up MongoDB test database
        try:
            import pymongo
            client = pymongo.MongoClient(self.mongo_uri)
            client.drop_database(self.mongo_db_name)
            logger.info(f"Dropped MongoDB database: {self.mongo_db_name}")
        except Exception as e:
            logger.error(f"Failed to clean up MongoDB: {e}")
    
    def create_sqlite_database(self):
        """Create a sample SQLite database with test data."""
        logger.info(f"Creating SQLite test database at {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            admin INTEGER DEFAULT 0,
            created_at TEXT,
            last_login TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            product_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            title TEXT,
            brand TEXT,
            price REAL,
            image_url TEXT,
            url TEXT,
            user_id INTEGER,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE reviews (
            id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            rating REAL,
            text TEXT,
            author TEXT,
            date TEXT,
            verified_purchase INTEGER DEFAULT 0,
            sentiment REAL,
            created_at TEXT,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        ''')
        
        # Insert test data
        now = datetime.datetime.now().isoformat()
        
        # Insert users
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, admin, created_at, last_login) VALUES (?, ?, ?, ?, ?, ?)",
            ("testuser", "test@example.com", "hash123", 1, now, now)
        )
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, admin, created_at, last_login) VALUES (?, ?, ?, ?, ?, ?)",
            ("regular_user", "user@example.com", "hash456", 0, now, now)
        )
        
        # Insert products
        cursor.execute(
            "INSERT INTO products (product_id, platform, title, brand, price, image_url, url, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("B01LYCLS24", "amazon", "Test Product 1", "TestBrand", 29.99, "http://example.com/image1.jpg", "http://amazon.com/dp/B01LYCLS24", 1, now, now)
        )
        cursor.execute(
            "INSERT INTO products (product_id, platform, title, brand, price, image_url, url, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("123456789", "ebay", "Test Product 2", "OtherBrand", 19.99, "http://example.com/image2.jpg", "http://ebay.com/itm/123456789", 1, now, now)
        )
        
        # Insert reviews
        review_texts = [
            "This product is amazing! I love it so much.",
            "Decent product but overpriced.",
            "Terrible quality, avoid at all costs!",
            "Works as expected. No issues so far.",
            "Not bad for the price, but there are better options."
        ]
        sentiments = [0.8, 0.1, -0.7, 0.4, 0.0]
        authors = ["John D.", "Jane S.", "Mike T.", "Sarah L.", "Robert K."]
        ratings = [5.0, 3.0, 1.0, 4.0, 3.0]
        
        for i, (text, sentiment, author, rating) in enumerate(zip(review_texts, sentiments, authors, ratings)):
            # Add to first product
            cursor.execute(
                "INSERT INTO reviews (product_id, rating, text, author, date, verified_purchase, sentiment, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (1, rating, text, author, now, 1 if i % 2 == 0 else 0, sentiment, now)
            )
            
            # Add to second product with slight variations
            cursor.execute(
                "INSERT INTO reviews (product_id, rating, text, author, date, verified_purchase, sentiment, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (2, rating - 0.5 if rating > 1 else rating, f"For the eBay version: {text}", author, now, 0 if i % 2 == 0 else 1, sentiment - 0.1 if sentiment > -0.9 else sentiment, now)
            )
        
        conn.commit()
        conn.close()
        logger.info("SQLite test database created successfully")
    
    def run_migration(self):
        """Run the migration script."""
        logger.info("Running migration from SQLite to MongoDB")
        
        # Using the migrate_to_mongodb module directly
        sqlite_conn = migrate_to_mongodb.connect_sqlite(self.db_path)
        mongo_db = migrate_to_mongodb.connect_mongodb(self.mongo_uri, self.mongo_db_name)
        
        # Get SQLite tables
        tables = migrate_to_mongodb.get_sqlite_tables(sqlite_conn)
        
        # Process users
        if 'users' in tables:
            users = migrate_to_mongodb.read_sqlite_table(sqlite_conn, 'users')
            mongo_users = migrate_to_mongodb.transform_user_data(users)
            user_result = migrate_to_mongodb.insert_mongodb_collection(mongo_db, 'users', mongo_users)
            user_id_mapping = migrate_to_mongodb.create_id_mapping([u['id'] for u in users], user_result)
        else:
            self.fail("No 'users' table found in SQLite database")
        
        # Process products
        if 'products' in tables:
            products = migrate_to_mongodb.read_sqlite_table(sqlite_conn, 'products')
            mongo_products = migrate_to_mongodb.transform_product_data(products, user_id_mapping)
            product_result = migrate_to_mongodb.insert_mongodb_collection(mongo_db, 'products', mongo_products)
            product_id_mapping = migrate_to_mongodb.create_id_mapping([p['id'] for p in products], product_result)
        else:
            self.fail("No 'products' table found in SQLite database")
        
        # Process reviews
        if 'reviews' in tables:
            reviews = migrate_to_mongodb.read_sqlite_table(sqlite_conn, 'reviews')
            mongo_reviews = migrate_to_mongodb.transform_review_data(reviews, product_id_mapping)
            review_result = migrate_to_mongodb.insert_mongodb_collection(mongo_db, 'reviews', mongo_reviews)
        else:
            self.fail("No 'reviews' table found in SQLite database")
        
        # Update product statistics
        migrate_to_mongodb.update_product_stats(mongo_db)
        
        # Close connections
        sqlite_conn.close()
        
        logger.info("Migration completed successfully")
    
    def verify_migration(self):
        """Verify the migration was successful."""
        logger.info("Verifying migration results")
        
        import pymongo
        client = pymongo.MongoClient(self.mongo_uri)
        db = client[self.mongo_db_name]
        
        # Check collections exist
        collections = db.list_collection_names()
        for expected_collection in ['users', 'products', 'reviews']:
            self.assertIn(expected_collection, collections, f"Collection '{expected_collection}' not found")
        
        # Check user count
        user_count = db.users.count_documents({})
        self.assertEqual(user_count, 2, f"Expected 2 users, found {user_count}")
        
        # Check admin user
        admin_user = db.users.find_one({"username": "testuser"})
        self.assertIsNotNone(admin_user, "Admin user not found")
        self.assertTrue(admin_user.get('is_admin', False), "Admin flag not set")
        
        # Check product count
        product_count = db.products.count_documents({})
        self.assertEqual(product_count, 2, f"Expected 2 products, found {product_count}")
        
        # Check amazon product
        amazon_product = db.products.find_one({"platform_id": "B01LYCLS24"})
        self.assertIsNotNone(amazon_product, "Amazon product not found")
        self.assertEqual(amazon_product.get('platform'), "amazon", "Platform is not 'amazon'")
        
        # Check review count
        review_count = db.reviews.count_documents({})
        self.assertEqual(review_count, 10, f"Expected 10 reviews, found {review_count}")
        
        # Check product stats
        for product in db.products.find({}):
            self.assertIsNotNone(product.get('stats'), "Product stats not found")
            self.assertGreater(product['stats'].get('review_count', 0), 0, "Review count not updated")
            self.assertIsNotNone(product['stats'].get('avg_rating'), "Average rating not calculated")
            self.assertIsNotNone(product['stats'].get('sentiment_distribution'), "Sentiment distribution not calculated")
        
        logger.info("Migration verification completed successfully")
    
    def test_migration(self):
        """Main test method."""
        # Run migration
        self.run_migration()
        
        # Verify results
        self.verify_migration()
        
        logger.info("Migration test completed successfully")

def main():
    """Run test as script."""
    # Check MongoDB is running
    import pymongo
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        logger.info("MongoDB is running")
    except Exception as e:
        logger.error(f"MongoDB is not available: {e}")
        logger.error("Make sure MongoDB is running locally on port 27017")
        sys.exit(1)
    
    # Run test
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

if __name__ == "__main__":
    main() 