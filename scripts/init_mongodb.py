#!/usr/bin/env python3
"""
MongoDB Initialization Script for ShopSentiment

This script initializes the MongoDB database for the ShopSentiment application.
It creates necessary collections and indexes for optimal performance.
"""

import os
import sys
import logging
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("init_mongodb")

def get_mongodb_uri():
    """Get MongoDB URI from environment variables."""
    return os.environ.get("MONGODB_URI", "mongodb://localhost:27017/shopsentiment")

def init_mongodb():
    """Initialize MongoDB collections and indexes."""
    try:
        # Connect to MongoDB
        client = MongoClient(get_mongodb_uri())
        db_name = get_mongodb_uri().split('/')[-1]
        db = client[db_name]
        
        logger.info(f"Connected to MongoDB database: {db_name}")
        
        # Create collections if they don't exist
        collections = ["products", "reviews", "sentiment_scores", "cache_items"]
        existing_collections = db.list_collection_names()
        
        for collection_name in collections:
            if collection_name not in existing_collections:
                db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
            else:
                logger.info(f"Collection already exists: {collection_name}")
        
        # Create indexes for products collection
        products = db.products
        products.create_index([("name", TEXT), ("description", TEXT)], 
                              name="product_text_search")
        products.create_index([("category", ASCENDING)], name="category_index")
        products.create_index([("created_at", DESCENDING)], name="product_created_index")
        logger.info("Created indexes for products collection")
        
        # Create indexes for reviews collection
        reviews = db.reviews
        reviews.create_index([("product_id", ASCENDING)], name="product_id_index")
        reviews.create_index([("sentiment_score", ASCENDING)], name="sentiment_score_index")
        reviews.create_index([("created_at", DESCENDING)], name="review_created_index")
        logger.info("Created indexes for reviews collection")
        
        # Create indexes for sentiment_scores collection
        sentiment_scores = db.sentiment_scores
        sentiment_scores.create_index([("product_id", ASCENDING)], 
                                     name="sentiment_product_id_index", unique=True)
        logger.info("Created indexes for sentiment_scores collection")
        
        # Create indexes for cache_items collection
        cache_items = db.cache_items
        cache_items.create_index([("key", ASCENDING)], name="cache_key_index", unique=True)
        cache_items.create_index([("expires_at", ASCENDING)], name="cache_expires_index")
        logger.info("Created indexes for cache_items collection")
        
        logger.info("MongoDB initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing MongoDB: {str(e)}")
        return False

def main():
    """Main function."""
    logger.info("Starting MongoDB initialization")
    
    if init_mongodb():
        logger.info("MongoDB initialization completed successfully")
        sys.exit(0)
    else:
        logger.error("MongoDB initialization failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 