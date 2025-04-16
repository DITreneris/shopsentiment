#!/usr/bin/env python3
"""
MongoDB Database Initialization Script for ShopSentiment

This script initializes the MongoDB database with sample data for development
and testing purposes. It creates collections, indexes, and inserts mock data.
"""

import os
import sys
import json
import logging
from datetime import datetime
from bson import ObjectId

# Add the parent directory to the Python path to import the application modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import get_mongodb_client, get_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_indexes(db):
    """Create necessary indexes for collections."""
    logger.info("Creating indexes...")
    
    # Product indexes
    db.products.create_index("name")
    db.products.create_index([("name", "text"), ("description", "text")])
    db.products.create_index("sentiment.score")
    db.products.create_index("sentiment.reviews_count")
    
    # Review indexes
    db.reviews.create_index("product_id")
    db.reviews.create_index("sentiment_score")
    db.reviews.create_index("created_at")
    
    logger.info("Indexes created successfully")


def insert_sample_data(db):
    """Insert sample data for development and testing."""
    logger.info("Inserting sample data...")
    
    # Check if products already exist
    if db.products.count_documents({}) > 0:
        logger.info("Sample data already exists. Skipping insertion.")
        return
    
    # Sample products
    products = [
        {
            "_id": "1",
            "name": "Smart Watch Pro",
            "description": "Advanced smartwatch with health monitoring features",
            "price": 199.99,
            "category": "Electronics",
            "sentiment": {
                "score": 0.85,
                "type": "positive",
                "reviews_count": 2,
                "distribution": {
                    "positive": 0.75,
                    "neutral": 0.25,
                    "negative": 0.0
                }
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": "2",
            "name": "Wireless Earbuds",
            "description": "Premium wireless earbuds with noise cancellation",
            "price": 149.99,
            "category": "Electronics",
            "sentiment": {
                "score": 0.72,
                "type": "positive",
                "reviews_count": 2,
                "distribution": {
                    "positive": 0.5,
                    "neutral": 0.5,
                    "negative": 0.0
                }
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": "3",
            "name": "Organic Cotton T-Shirt",
            "description": "Eco-friendly cotton t-shirt, great for everyday wear",
            "price": 29.99,
            "category": "Clothing",
            "sentiment": {
                "score": 0.65,
                "type": "neutral",
                "reviews_count": 2,
                "distribution": {
                    "positive": 0.5,
                    "neutral": 0.0,
                    "negative": 0.5
                }
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    # Sample reviews
    reviews = [
        {
            "_id": "101",
            "product_id": "1",
            "text": "Love this watch! The health features are amazing.",
            "rating": 5.0,
            "sentiment_score": 0.92,
            "user": "User1234",
            "date": "2023-10-15",
            "created_at": datetime.utcnow()
        },
        {
            "_id": "102",
            "product_id": "1",
            "text": "Good product, but battery life could be better.",
            "rating": 4.0,
            "sentiment_score": 0.72,
            "user": "User5678",
            "date": "2023-10-10",
            "created_at": datetime.utcnow()
        },
        {
            "_id": "103",
            "product_id": "2",
            "text": "These earbuds are amazing! Great sound quality.",
            "rating": 5.0,
            "sentiment_score": 0.95,
            "user": "User2468",
            "date": "2023-09-25",
            "created_at": datetime.utcnow()
        },
        {
            "_id": "104",
            "product_id": "2",
            "text": "They're okay. Not the best fit for my ears.",
            "rating": 3.0,
            "sentiment_score": 0.50,
            "user": "User1357",
            "date": "2023-09-18",
            "created_at": datetime.utcnow()
        },
        {
            "_id": "105",
            "product_id": "3",
            "text": "Nice shirt, good quality material.",
            "rating": 4.0,
            "sentiment_score": 0.80,
            "user": "User7890",
            "date": "2023-08-15",
            "created_at": datetime.utcnow()
        },
        {
            "_id": "106",
            "product_id": "3",
            "text": "Disappointed with the fit. Too small for me.",
            "rating": 2.0,
            "sentiment_score": 0.20,
            "user": "User3456",
            "date": "2023-08-10",
            "created_at": datetime.utcnow()
        }
    ]
    
    # Insert data
    db.products.insert_many(products)
    db.reviews.insert_many(reviews)
    
    logger.info(f"Inserted {len(products)} products and {len(reviews)} reviews")


def main():
    """Main function to initialize the database."""
    try:
        logger.info("Starting database initialization...")
        
        # Get MongoDB connection
        client = get_mongodb_client()
        db = get_database()
        
        # Create indexes
        create_indexes(db)
        
        # Insert sample data
        insert_sample_data(db)
        
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 