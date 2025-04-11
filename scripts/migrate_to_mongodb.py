#!/usr/bin/env python3
"""
Script to migrate data from SQLite database to MongoDB.

This script:
1. Connects to the SQLite database
2. Connects to MongoDB Atlas
3. Reads data from SQLite tables
4. Transforms the data to MongoDB document format
5. Imports the data into MongoDB collections

Usage:
    python migrate_to_mongodb.py --sqlite-path=data/shopsentiment.db --mongo-uri=mongodb+srv://...
"""

import os
import sys
import argparse
import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import pymongo
from pymongo.errors import BulkWriteError
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migration.log')
    ]
)
logger = logging.getLogger('migrate_to_mongodb')

def connect_sqlite(db_path: str) -> sqlite3.Connection:
    """
    Connect to SQLite database.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        SQLite connection
    """
    logger.info(f"Connecting to SQLite database: {db_path}")
    if not os.path.exists(db_path):
        logger.error(f"SQLite database file not found: {db_path}")
        sys.exit(1)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to SQLite database: {e}")
        sys.exit(1)

def connect_mongodb(mongo_uri: str, db_name: str = 'shopsentiment') -> pymongo.database.Database:
    """
    Connect to MongoDB Atlas.
    
    Args:
        mongo_uri: MongoDB connection URI
        db_name: MongoDB database name
        
    Returns:
        MongoDB database instance
    """
    logger.info(f"Connecting to MongoDB database: {db_name}")
    try:
        client = pymongo.MongoClient(mongo_uri)
        # Test connection
        client.admin.command('ping')
        logger.info("MongoDB connection successful")
        return client[db_name]
    except pymongo.errors.ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)

def get_sqlite_tables(conn: sqlite3.Connection) -> List[str]:
    """
    Get list of tables in SQLite database.
    
    Args:
        conn: SQLite connection
        
    Returns:
        List of table names
    """
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cursor.fetchall()]
    cursor.close()
    
    # Filter out SQLite system tables
    tables = [t for t in tables if not t.startswith('sqlite_')]
    logger.info(f"Found SQLite tables: {', '.join(tables)}")
    return tables

def get_table_schema(conn: sqlite3.Connection, table_name: str) -> List[Dict[str, str]]:
    """
    Get schema information for a SQLite table.
    
    Args:
        conn: SQLite connection
        table_name: Table name
        
    Returns:
        List of column information dictionaries
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    return columns

def read_sqlite_table(conn: sqlite3.Connection, table_name: str) -> List[Dict[str, Any]]:
    """
    Read all rows from a SQLite table.
    
    Args:
        conn: SQLite connection
        table_name: Table name
        
    Returns:
        List of row dictionaries
    """
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    
    logger.info(f"Read {len(rows)} rows from table '{table_name}'")
    return rows

def transform_user_data(sqlite_users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform user data from SQLite format to MongoDB format.
    
    Args:
        sqlite_users: List of user dictionaries from SQLite
        
    Returns:
        List of user documents for MongoDB
    """
    mongo_users = []
    
    for user in sqlite_users:
        # Create MongoDB document
        mongo_user = {
            "username": user.get('username', ''),
            "email": user.get('email', ''),
            "password_hash": user.get('password_hash', ''),
            "created_at": datetime.fromisoformat(user.get('created_at')) if user.get('created_at') else datetime.now(),
            "last_login": datetime.fromisoformat(user.get('last_login')) if user.get('last_login') else None,
            "settings": {
                "theme": "light"
            }
        }
        
        # Add optional fields if present
        if user.get('admin') == 1:
            mongo_user['is_admin'] = True
        
        mongo_users.append(mongo_user)
    
    return mongo_users

def transform_product_data(sqlite_products: List[Dict[str, Any]], user_id_mapping: Dict[int, str]) -> List[Dict[str, Any]]:
    """
    Transform product data from SQLite format to MongoDB format.
    
    Args:
        sqlite_products: List of product dictionaries from SQLite
        user_id_mapping: Mapping of SQLite user IDs to MongoDB ObjectIDs
        
    Returns:
        List of product documents for MongoDB
    """
    from bson.objectid import ObjectId
    
    mongo_products = []
    
    for product in sqlite_products:
        # Create MongoDB document
        mongo_product = {
            "platform_id": product.get('product_id', ''),
            "platform": product.get('platform', 'unknown').lower(),
            "title": product.get('title', ''),
            "brand": product.get('brand', ''),
            "price": str(product.get('price', '0.00')),
            "image_url": product.get('image_url', ''),
            "url": product.get('url', ''),
            "created_at": datetime.fromisoformat(product.get('created_at')) if product.get('created_at') else datetime.now(),
            "last_updated": datetime.fromisoformat(product.get('updated_at')) if product.get('updated_at') else datetime.now(),
            "stats": {
                "review_count": 0,
                "avg_rating": 0,
                "rating_distribution": {},
                "sentiment_distribution": {}
            },
            "keywords": []
        }
        
        # Map user ID if available
        if product.get('user_id') and product.get('user_id') in user_id_mapping:
            mongo_product['created_by'] = ObjectId(user_id_mapping[product.get('user_id')])
        
        mongo_products.append(mongo_product)
    
    return mongo_products

def transform_review_data(sqlite_reviews: List[Dict[str, Any]], product_id_mapping: Dict[int, str]) -> List[Dict[str, Any]]:
    """
    Transform review data from SQLite format to MongoDB format.
    
    Args:
        sqlite_reviews: List of review dictionaries from SQLite
        product_id_mapping: Mapping of SQLite product IDs to MongoDB ObjectIDs
        
    Returns:
        List of review documents for MongoDB
    """
    from bson.objectid import ObjectId
    
    mongo_reviews = []
    
    for review in sqlite_reviews:
        # Skip if product ID is not in mapping
        if review.get('product_id') not in product_id_mapping:
            continue
            
        # Determine sentiment label based on sentiment score
        sentiment_score = float(review.get('sentiment', 0))
        if sentiment_score >= 0.05:
            sentiment_label = 'positive'
        elif sentiment_score <= -0.05:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        # Parse keywords from text (basic implementation)
        keywords = []
        if review.get('text'):
            # Extract simple keywords (this is a simplistic approach)
            # In a real implementation, you'd use proper NLP techniques
            words = review.get('text', '').lower().split()
            # Remove duplicates and very short words
            keywords = list(set([w for w in words if len(w) > 3 and w.isalpha()]))[:10]
        
        # Create MongoDB document
        mongo_review = {
            "product_id": ObjectId(product_id_mapping[review.get('product_id')]),
            "platform_review_id": str(review.get('id')),
            "title": "",  # SQLite schema might not have title
            "content": review.get('text', ''),
            "rating": float(review.get('rating', 0)),
            "author": review.get('author', 'Anonymous'),
            "date": datetime.fromisoformat(review.get('date')) if review.get('date') else datetime.now(),
            "verified_purchase": bool(review.get('verified_purchase', 0)),
            "sentiment": {
                "label": sentiment_label,
                "score": sentiment_score,
                "compound": sentiment_score,
                "pos": max(0, sentiment_score) if sentiment_score > 0 else 0,
                "neg": abs(min(0, sentiment_score)) if sentiment_score < 0 else 0,
                "neu": 1 - abs(sentiment_score) if abs(sentiment_score) < 1 else 0
            },
            "keywords": keywords,
            "created_at": datetime.fromisoformat(review.get('created_at')) if review.get('created_at') else datetime.now()
        }
        
        mongo_reviews.append(mongo_review)
    
    return mongo_reviews

def insert_mongodb_collection(db: pymongo.database.Database, collection_name: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Insert documents into MongoDB collection.
    
    Args:
        db: MongoDB database instance
        collection_name: Collection name
        documents: List of documents to insert
        
    Returns:
        Dictionary with insertion results
    """
    if not documents:
        logger.warning(f"No documents to insert into collection '{collection_name}'")
        return {"inserted": 0}
    
    try:
        result = db[collection_name].insert_many(documents)
        logger.info(f"Inserted {len(result.inserted_ids)} documents into collection '{collection_name}'")
        return {"inserted": len(result.inserted_ids), "ids": [str(id) for id in result.inserted_ids]}
    except BulkWriteError as e:
        logger.error(f"Bulk write error when inserting into '{collection_name}': {e.details}")
        return {"inserted": len(e.details.get('writeErrors', [])), "errors": len(e.details.get('writeErrors', []))}
    except Exception as e:
        logger.error(f"Error inserting into collection '{collection_name}': {e}")
        return {"inserted": 0, "error": str(e)}

def create_id_mapping(original_ids: List[int], inserted_result: Dict[str, Any]) -> Dict[int, str]:
    """
    Create mapping between original IDs and new MongoDB ObjectIDs.
    
    Args:
        original_ids: List of original IDs from SQLite
        inserted_result: Result dictionary from insert_mongodb_collection
        
    Returns:
        Dictionary mapping original IDs to new MongoDB ObjectIDs
    """
    if len(original_ids) != len(inserted_result.get('ids', [])):
        logger.warning("ID count mismatch when creating ID mapping")
        # Handle partial success by mapping only available IDs
        return {original_ids[i]: inserted_result['ids'][i] for i in range(min(len(original_ids), len(inserted_result.get('ids', []))))}
    
    return {original_ids[i]: inserted_result['ids'][i] for i in range(len(original_ids))}

def update_product_stats(db: pymongo.database.Database) -> None:
    """
    Update product statistics based on review data.
    
    Args:
        db: MongoDB database instance
    """
    logger.info("Updating product statistics...")
    
    # Get all products
    products = list(db.products.find({}))
    
    for product in tqdm(products, desc="Updating product stats"):
        product_id = product['_id']
        
        # Count reviews
        review_count = db.reviews.count_documents({'product_id': product_id})
        
        if review_count == 0:
            continue
            
        # Calculate average rating
        pipeline = [
            {'$match': {'product_id': product_id}},
            {'$group': {'_id': None, 'avg_rating': {'$avg': '$rating'}}}
        ]
        avg_result = list(db.reviews.aggregate(pipeline))
        avg_rating = avg_result[0]['avg_rating'] if avg_result else 0
        
        # Calculate rating distribution
        pipeline = [
            {'$match': {'product_id': product_id}},
            {'$group': {'_id': '$rating', 'count': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]
        rating_dist = {str(int(item['_id'])): item['count'] for item in db.reviews.aggregate(pipeline)}
        
        # Calculate sentiment distribution
        pipeline = [
            {'$match': {'product_id': product_id}},
            {'$group': {'_id': '$sentiment.label', 'count': {'$sum': 1}}}
        ]
        sentiment_dist = {item['_id']: item['count'] for item in db.reviews.aggregate(pipeline)}
        
        # Extract top keywords
        pipeline = [
            {'$match': {'product_id': product_id}},
            {'$unwind': '$keywords'},
            {'$group': {'_id': '$keywords', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        keywords = [{'term': item['_id'], 'count': item['count']} for item in db.reviews.aggregate(pipeline)]
        
        # Update product
        db.products.update_one(
            {'_id': product_id},
            {'$set': {
                'stats.review_count': review_count,
                'stats.avg_rating': round(avg_rating, 1),
                'stats.rating_distribution': rating_dist,
                'stats.sentiment_distribution': sentiment_dist,
                'keywords': keywords,
                'last_updated': datetime.now()
            }}
        )
    
    logger.info(f"Updated statistics for {len(products)} products")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Migrate data from SQLite to MongoDB')
    parser.add_argument('--sqlite-path', required=True, help='Path to SQLite database')
    parser.add_argument('--mongo-uri', required=True, help='MongoDB connection URI')
    parser.add_argument('--mongo-db', default='shopsentiment', help='MongoDB database name')
    args = parser.parse_args()
    
    # Connect to databases
    sqlite_conn = connect_sqlite(args.sqlite_path)
    mongo_db = connect_mongodb(args.mongo_uri, args.mongo_db)
    
    # Get SQLite tables
    tables = get_sqlite_tables(sqlite_conn)
    
    # Process users
    if 'users' in tables:
        logger.info("Processing users...")
        users = read_sqlite_table(sqlite_conn, 'users')
        mongo_users = transform_user_data(users)
        user_result = insert_mongodb_collection(mongo_db, 'users', mongo_users)
        user_id_mapping = create_id_mapping([u['id'] for u in users], user_result)
    else:
        logger.warning("No 'users' table found in SQLite database")
        user_id_mapping = {}
    
    # Process products
    if 'products' in tables:
        logger.info("Processing products...")
        products = read_sqlite_table(sqlite_conn, 'products')
        mongo_products = transform_product_data(products, user_id_mapping)
        product_result = insert_mongodb_collection(mongo_db, 'products', mongo_products)
        product_id_mapping = create_id_mapping([p['id'] for p in products], product_result)
    else:
        logger.warning("No 'products' table found in SQLite database")
        product_id_mapping = {}
    
    # Process reviews
    if 'reviews' in tables:
        logger.info("Processing reviews...")
        reviews = read_sqlite_table(sqlite_conn, 'reviews')
        mongo_reviews = transform_review_data(reviews, product_id_mapping)
        review_result = insert_mongodb_collection(mongo_db, 'reviews', mongo_reviews)
    else:
        logger.warning("No 'reviews' table found in SQLite database")
    
    # Update product statistics
    update_product_stats(mongo_db)
    
    # Close connections
    sqlite_conn.close()
    
    logger.info("Migration completed successfully")

if __name__ == '__main__':
    main() 