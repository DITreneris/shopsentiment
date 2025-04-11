#!/usr/bin/env python3
"""
Add Sample Product and Reviews to MongoDB

This script adds a sample product with reviews to the MongoDB database
for testing and demonstration purposes.
"""

import os
import sys
import logging
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('add_sample_product')

# Load environment variables from .env file
load_dotenv()

def get_mongodb_uri():
    """Get MongoDB URI from environment variables."""
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        logger.error("MongoDB URI not found in environment variables.")
        sys.exit(1)
    return mongodb_uri

def get_database_name():
    """Get database name from environment variables."""
    db_name = os.getenv('MONGODB_DB_NAME', 'shopsentiment')
    return db_name

def connect_mongodb(uri, db_name):
    """Connect to MongoDB and get database."""
    try:
        client = MongoClient(uri)
        # Test connection
        client.admin.command('ping')
        logger.info("Connected to MongoDB Atlas")
        return client, client[db_name]
    except Exception as e:
        logger.error(f"Cannot connect to MongoDB: {e}")
        sys.exit(1)

def add_sample_product(db):
    """Add a sample product to the database."""
    # Get admin user if exists
    admin_user = db.users.find_one({"username": "admin"})
    created_by = admin_user["_id"] if admin_user else None
    
    # Sample product data
    product = {
        "platform_id": "B07ZPML7NP",
        "platform": "amazon",
        "title": "Wireless Earbuds, Bluetooth 5.0 Headphones",
        "brand": "TechSonic",
        "price": "49.99",
        "image_url": "https://example.com/images/wireless_earbuds.jpg",
        "url": "https://amazon.com/dp/B07ZPML7NP",
        "created_at": datetime.now(),
        "last_updated": datetime.now(),
        "created_by": created_by,
        "stats": {
            "review_count": 5,
            "avg_rating": 4.2,
            "rating_distribution": {
                "1": 0,
                "2": 1,
                "3": 0,
                "4": 2,
                "5": 2
            },
            "sentiment_distribution": {
                "positive": 4,
                "neutral": 0,
                "negative": 1
            }
        },
        "keywords": [
            {"term": "battery life", "count": 3, "sentiment_score": 0.75},
            {"term": "sound quality", "count": 4, "sentiment_score": 0.85},
            {"term": "comfort", "count": 2, "sentiment_score": 0.92},
            {"term": "connectivity", "count": 2, "sentiment_score": 0.65},
            {"term": "price", "count": 3, "sentiment_score": 0.88}
        ]
    }
    
    # Check if product already exists
    existing_product = db.products.find_one({
        "platform": product["platform"],
        "platform_id": product["platform_id"]
    })
    
    if existing_product:
        logger.info(f"Product already exists with ID: {existing_product['_id']}")
        return existing_product["_id"]
    
    # Insert product
    result = db.products.insert_one(product)
    product_id = result.inserted_id
    logger.info(f"Added sample product with ID: {product_id}")
    return product_id

def add_sample_reviews(db, product_id):
    """Add sample reviews for the product."""
    
    # Sample reviews
    reviews = [
        {
            "product_id": product_id,
            "platform_review_id": "R12345ABC",
            "title": "Great earbuds, amazing sound quality!",
            "content": "I've been using these earbuds for about a month now and I'm very impressed. The sound quality is excellent, with deep bass and clear highs. Battery life is also great - I get about 5 hours on a single charge. Comfortable to wear for long periods too!",
            "rating": 5,
            "author": "John Smith",
            "date": datetime(2023, 12, 15),
            "verified_purchase": True,
            "sentiment": {
                "label": "positive",
                "score": 0.92,
                "compound": 0.88,
                "pos": 0.92,
                "neg": 0.0,
                "neu": 0.08
            },
            "keywords": ["sound quality", "battery life", "comfort"],
            "created_at": datetime.now()
        },
        {
            "product_id": product_id,
            "platform_review_id": "R67890DEF",
            "title": "Good value for the price",
            "content": "These earbuds offer good sound quality for the price point. The connection is stable and I haven't experienced any dropouts. Battery life could be better, but for the price I can't complain too much. Would recommend for casual listening.",
            "rating": 4,
            "author": "Sarah Jones",
            "date": datetime(2024, 1, 5),
            "verified_purchase": True,
            "sentiment": {
                "label": "positive",
                "score": 0.78,
                "compound": 0.65,
                "pos": 0.78,
                "neg": 0.05,
                "neu": 0.17
            },
            "keywords": ["sound quality", "price", "connectivity", "battery life"],
            "created_at": datetime.now()
        },
        {
            "product_id": product_id,
            "platform_review_id": "R24680GHI",
            "title": "Disappointed with the build quality",
            "content": "While the sound is decent, I'm not impressed with the build quality. The case feels cheap and one of the earbuds stopped working after just two weeks. Customer service was not helpful when I reached out about this issue.",
            "rating": 2,
            "author": "Michael Brown",
            "date": datetime(2024, 2, 10),
            "verified_purchase": True,
            "sentiment": {
                "label": "negative",
                "score": 0.32,
                "compound": -0.65,
                "pos": 0.12,
                "neg": 0.62,
                "neu": 0.26
            },
            "keywords": ["build quality", "customer service"],
            "created_at": datetime.now()
        },
        {
            "product_id": product_id,
            "platform_review_id": "R13579JKL",
            "title": "Perfect for workouts",
            "content": "These earbuds stay in place during my most intense workouts. The sound quality is great and they're comfortable to wear for long periods. The water resistance is a plus for sweaty sessions. Battery life is sufficient for my needs.",
            "rating": 5,
            "author": "Emily Wilson",
            "date": datetime(2024, 3, 1),
            "verified_purchase": True,
            "sentiment": {
                "label": "positive",
                "score": 0.90,
                "compound": 0.85,
                "pos": 0.90,
                "neg": 0.0,
                "neu": 0.10
            },
            "keywords": ["workouts", "comfort", "sound quality", "battery life"],
            "created_at": datetime.now()
        },
        {
            "product_id": product_id,
            "platform_review_id": "R97531MNO",
            "title": "Good earbuds for the price",
            "content": "I've been using these for my daily commute and they work well. The noise isolation is decent, and the connectivity with my phone is reliable. The price is very reasonable for the features. Touch controls could be more responsive though.",
            "rating": 4,
            "author": "David Lee",
            "date": datetime(2024, 3, 15),
            "verified_purchase": True,
            "sentiment": {
                "label": "positive",
                "score": 0.80,
                "compound": 0.72,
                "pos": 0.80,
                "neg": 0.05,
                "neu": 0.15
            },
            "keywords": ["price", "connectivity", "noise isolation"],
            "created_at": datetime.now()
        }
    ]
    
    # Check if reviews already exist for this product
    existing_reviews = db.reviews.count_documents({"product_id": product_id})
    if existing_reviews > 0:
        logger.info(f"Reviews already exist for product {product_id}. Found {existing_reviews} reviews.")
        return
    
    # Insert reviews
    result = db.reviews.insert_many(reviews)
    logger.info(f"Added {len(result.inserted_ids)} sample reviews")

def main():
    """Main function to add sample data."""
    logger.info("Starting to add sample data to MongoDB")
    
    mongodb_uri = get_mongodb_uri()
    db_name = get_database_name()
    
    # Connect to MongoDB
    client, db = connect_mongodb(mongodb_uri, db_name)
    
    try:
        # Add sample product
        product_id = add_sample_product(db)
        
        # Add sample reviews
        add_sample_reviews(db, product_id)
        
        logger.info("Sample data added successfully")
    finally:
        # Close connection
        client.close()
        logger.info("MongoDB connection closed")

if __name__ == "__main__":
    main() 