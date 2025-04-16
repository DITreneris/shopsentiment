#!/usr/bin/env python3
"""
SQLite Initialization Script for ShopSentiment

This script initializes the SQLite database for the ShopSentiment application.
It creates necessary tables and indexes for optimal performance.
"""

import os
import sys
import logging
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("init_sqlite")

def get_db_path():
    """Get SQLite database path from environment variables."""
    return os.environ.get("DATABASE_PATH", "data/shopsentiment.db")

def ensure_db_directory():
    """Ensure the directory for the database file exists."""
    db_path = get_db_path()
    db_dir = os.path.dirname(db_path)
    
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        logger.info(f"Created directory for database: {db_dir}")

def init_sqlite():
    """Initialize SQLite database tables and indexes."""
    try:
        # Ensure database directory exists
        ensure_db_directory()
        
        # Connect to SQLite database
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info(f"Connected to SQLite database: {db_path}")
        
        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                description TEXT,
                price REAL,
                image_url TEXT,
                shop_name TEXT,
                shop_url TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        logger.info("Created products table")
        
        # Create reviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                author TEXT,
                rating INTEGER,
                text TEXT,
                title TEXT,
                verified_purchase INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )
        ''')
        logger.info("Created reviews table")
        
        # Create review_sentiment table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_sentiment (
                review_id INTEGER PRIMARY KEY,
                score REAL NOT NULL,
                label TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (review_id) REFERENCES reviews (id) ON DELETE CASCADE
            )
        ''')
        logger.info("Created review_sentiment table")
        
        # Create sentiment_product_summary view
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS sentiment_product_summary AS
            SELECT 
                r.product_id,
                AVG(s.score) as average_score,
                CASE 
                    WHEN AVG(s.score) >= 0.6 THEN 'POSITIVE'
                    WHEN AVG(s.score) <= 0.4 THEN 'NEGATIVE'
                    ELSE 'NEUTRAL'
                END as sentiment_label,
                COUNT(r.id) as review_count,
                SUM(CASE WHEN s.label = 'POSITIVE' THEN 1 ELSE 0 END) as positive_count,
                SUM(CASE WHEN s.label = 'NEGATIVE' THEN 1 ELSE 0 END) as negative_count,
                SUM(CASE WHEN s.label = 'NEUTRAL' THEN 1 ELSE 0 END) as neutral_count,
                MAX(r.updated_at) as last_updated
            FROM reviews r
            LEFT JOIN review_sentiment s ON r.id = s.review_id
            GROUP BY r.product_id
        ''')
        logger.info("Created sentiment_product_summary view")
        
        # Create cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_items (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at TEXT
            )
        ''')
        logger.info("Created cache_items table")
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category ON products (category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_created_at ON products (created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews (product_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews (created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache_items (expires_at)')
        logger.info("Created database indexes")
        
        # Enable foreign keys
        cursor.execute('PRAGMA foreign_keys = ON')
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info("SQLite initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing SQLite database: {str(e)}")
        return False

def main():
    """Main function."""
    logger.info("Starting SQLite initialization")
    
    if init_sqlite():
        logger.info("SQLite initialization completed successfully")
        sys.exit(0)
    else:
        logger.error("SQLite initialization failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 