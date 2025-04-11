#!/usr/bin/env python3
"""
List MongoDB Data

This script lists all products and reviews from the MongoDB database.
"""

import os
import sys
import json
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
logger = logging.getLogger('list_mongodb_data')

# Load environment variables from .env file
load_dotenv()

# Custom JSON encoder for MongoDB data types
class MongoEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(MongoEncoder, self).default(obj)

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

def list_users(db):
    """List all users."""
    users = list(db.users.find())
    logger.info(f"Found {len(users)} users:")
    
    for i, user in enumerate(users, 1):
        print(f"\n--- User {i} ---")
        print(f"ID: {user['_id']}")
        print(f"Username: {user['username']}")
        print(f"Email: {user['email']}")
        print(f"Admin: {user.get('is_admin', False)}")
        print(f"Created: {user.get('created_at')}")
        print(f"Last login: {user.get('last_login')}")
    
    print("\n")

def list_products(db):
    """List all products."""
    products = list(db.products.find())
    logger.info(f"Found {len(products)} products:")
    
    for i, product in enumerate(products, 1):
        print(f"\n--- Product {i} ---")
        print(f"ID: {product['_id']}")
        print(f"Platform: {product['platform']}")
        print(f"Platform ID: {product['platform_id']}")
        print(f"Title: {product.get('title', 'N/A')}")
        print(f"Brand: {product.get('brand', 'N/A')}")
        print(f"Price: {product.get('price', 'N/A')}")
        
        # Display stats
        stats = product.get('stats', {})
        print(f"Review count: {stats.get('review_count', 0)}")
        print(f"Average rating: {stats.get('avg_rating', 0)}")
        
        # Display sentiment distribution
        sentiment_dist = stats.get('sentiment_distribution', {})
        print(f"Sentiment: Positive: {sentiment_dist.get('positive', 0)}, "
              f"Neutral: {sentiment_dist.get('neutral', 0)}, "
              f"Negative: {sentiment_dist.get('negative', 0)}")
        
        # Display top keywords
        keywords = product.get('keywords', [])
        if keywords:
            print("Top keywords:")
            for kw in keywords[:3]:  # Display top 3 keywords
                print(f"  - {kw['term']} (count: {kw['count']}, sentiment: {kw['sentiment_score']:.2f})")
    
    print("\n")

def list_reviews(db):
    """List all reviews."""
    reviews = list(db.reviews.find())
    logger.info(f"Found {len(reviews)} reviews:")
    
    for i, review in enumerate(reviews, 1):
        print(f"\n--- Review {i} ---")
        print(f"ID: {review['_id']}")
        print(f"Product ID: {review['product_id']}")
        print(f"Title: {review.get('title', 'N/A')}")
        
        # Truncate long content
        content = review.get('content', '')
        if len(content) > 100:
            content = content[:97] + "..."
        print(f"Content: {content}")
        
        print(f"Rating: {review.get('rating', 'N/A')}")
        print(f"Author: {review.get('author', 'N/A')}")
        print(f"Date: {review.get('date')}")
        
        # Display sentiment
        sentiment = review.get('sentiment', {})
        label = sentiment.get('label', 'N/A')
        score = sentiment.get('score', 0)
        print(f"Sentiment: {label} ({score:.2f})")
        
        # Display keywords
        keywords = review.get('keywords', [])
        if keywords:
            print(f"Keywords: {', '.join(keywords)}")
    
    print("\n")

def main():
    """Main function to list MongoDB data."""
    logger.info("Starting to list MongoDB data")
    
    mongodb_uri = get_mongodb_uri()
    db_name = get_database_name()
    
    # Connect to MongoDB
    client, db = connect_mongodb(mongodb_uri, db_name)
    
    try:
        # List collections
        collections = db.list_collection_names()
        logger.info(f"Collections in database: {', '.join(collections)}")
        
        # List users
        list_users(db)
        
        # List products
        list_products(db)
        
        # List reviews
        list_reviews(db)
        
        logger.info("Finished listing MongoDB data")
    finally:
        # Close connection
        client.close()
        logger.info("MongoDB connection closed")

if __name__ == "__main__":
    main() 