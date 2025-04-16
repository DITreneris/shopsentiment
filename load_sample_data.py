"""
Script to load sample data into SQLite database.
Run this after starting the application with debug_app.py
"""

import os
import sqlite3
import json
import random
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample product data
SAMPLE_PRODUCTS = [
    {
        "name": "Smart Watch Pro",
        "description": "Advanced smartwatch with health monitoring and GPS",
        "category": "Electronics",
        "price": 199.99
    },
    {
        "name": "Ultra HD 4K TV",
        "description": "55-inch 4K Ultra HD Smart TV with HDR",
        "category": "Electronics",
        "price": 649.99
    },
    {
        "name": "Premium Coffee Maker",
        "description": "Programmable coffee maker with built-in grinder",
        "category": "Home & Kitchen",
        "price": 129.99
    },
    {
        "name": "Wireless Noise-Canceling Headphones",
        "description": "Premium headphones with active noise cancellation",
        "category": "Electronics",
        "price": 249.99
    },
    {
        "name": "Robot Vacuum Cleaner",
        "description": "Smart robot vacuum with mapping technology",
        "category": "Home & Kitchen",
        "price": 299.99
    }
]

# Sample review sentiments
SAMPLE_REVIEWS = [
    {
        "user_name": "JohnD",
        "text": "Absolutely love this product. It exceeded my expectations!",
        "rating": 5,
        "sentiment_score": 0.95
    },
    {
        "user_name": "SarahK",
        "text": "Good product but a bit overpriced for what you get.",
        "rating": 4,
        "sentiment_score": 0.65
    },
    {
        "user_name": "MikeR",
        "text": "Not impressed. It stopped working after just two weeks.",
        "rating": 2,
        "sentiment_score": 0.25
    },
    {
        "user_name": "EmmaL",
        "text": "Great value for money, highly recommend it.",
        "rating": 5,
        "sentiment_score": 0.85
    },
    {
        "user_name": "DavidW",
        "text": "Average product, does the job but nothing special.",
        "rating": 3,
        "sentiment_score": 0.50
    },
    {
        "user_name": "AlexB",
        "text": "Terrible customer service when I tried to return it.",
        "rating": 1,
        "sentiment_score": 0.15
    },
    {
        "user_name": "LisaM",
        "text": "Really happy with my purchase, works exactly as described.",
        "rating": 5,
        "sentiment_score": 0.90
    }
]

def get_db_connection():
    """Connect to the SQLite database."""
    conn = sqlite3.connect('shopsentiment_dev.db')
    conn.row_factory = sqlite3.Row
    return conn

def load_sample_data():
    """Load sample products and reviews into the database."""
    conn = get_db_connection()
    try:
        # Create tables if they don't exist
        conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            user_name TEXT,
            rating INTEGER,
            text TEXT,
            sentiment_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        ''')
        
        # Insert sample products
        product_ids = []
        for product in SAMPLE_PRODUCTS:
            cursor = conn.execute('''
            INSERT INTO products (name, description, category, price, created_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                product['name'],
                product['description'],
                product['category'],
                product['price'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            product_ids.append(cursor.lastrowid)
            logger.info(f"Added product: {product['name']}")
        
        # Insert sample reviews for each product
        for product_id in product_ids:
            # Add between 3-7 reviews for each product
            num_reviews = random.randint(3, 7)
            for _ in range(num_reviews):
                review = random.choice(SAMPLE_REVIEWS)
                # Set review date within the last 30 days
                days_ago = random.randint(0, 30)
                review_date = datetime.now() - timedelta(days=days_ago)
                
                conn.execute('''
                INSERT INTO reviews (product_id, user_name, rating, text, sentiment_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    product_id,
                    review['user_name'],
                    review['rating'],
                    review['text'],
                    review['sentiment_score'],
                    review_date.strftime('%Y-%m-%d %H:%M:%S')
                ))
            logger.info(f"Added {num_reviews} reviews for product ID: {product_id}")
        
        # Commit the transactions
        conn.commit()
        logger.info("Sample data loaded successfully")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading sample data: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Starting sample data load")
    load_sample_data()
    logger.info("Sample data load complete") 