#!/usr/bin/env python3
"""
Initialize MongoDB Precomputed Statistics Collection
Sets up the precomputed_stats collection with proper indexes
and calculates initial statistics for popular products.

Usage:
    python initialize_precomputed_stats.py [--force]

Options:
    --force: Force recreation of the collection, dropping existing data
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import CollectionInvalid
from bson.objectid import ObjectId
from tqdm import tqdm
import time
import random

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('initialize_stats')

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Initialize precomputed statistics for MongoDB')
    parser.add_argument('--force', action='store_true', help='Force recreation of collection, dropping existing data')
    parser.add_argument('--top-products', type=int, default=50, help='Number of top products to precompute stats for')
    return parser.parse_args()

def connect_mongodb():
    """Connect to MongoDB using environment variables"""
    # First try getting the URI from environment variables
    mongodb_uri = os.environ.get('MONGODB_URI')
    
    # If not found, use the test connection URI
    if not mongodb_uri:
        mongodb_uri = "mongodb+srv://tomasstaniulis76:JaLhUd1NLZUtwVb5@shop1.11tjwh5.mongodb.net/?retryWrites=true&w=majority&appName=Shop1"
        logger.warning("Using hardcoded MongoDB URI from test script")
    
    db_name = os.environ.get('MONGODB_DB_NAME', 'shopsentiment')
    
    logger.info(f"Connecting to MongoDB database: {db_name}")
    client = MongoClient(mongodb_uri)
    db = client[db_name]
    
    return client, db

def initialize_collection(db, force=False):
    """Initialize the precomputed_stats collection with validation schema and indexes"""
    logger.info("Initializing precomputed_stats collection")
    
    # Drop existing collection if forced
    if force and 'precomputed_stats' in db.list_collection_names():
        logger.warning("Dropping existing precomputed_stats collection")
        db.precomputed_stats.drop()
    
    # Create collection with schema validation
    try:
        db.create_collection('precomputed_stats', validator={
            '$jsonSchema': {
                'bsonType': 'object',
                'required': ['stats_type', 'identifier', 'created_at', 'data'],
                'properties': {
                    'stats_type': {'bsonType': 'string'},
                    'identifier': {'bsonType': 'string'},
                    'created_at': {'bsonType': 'date'},
                    'expires_at': {'bsonType': 'date'},
                    'data': {'bsonType': 'object'}
                }
            }
        })
        logger.info("Created precomputed_stats collection with schema validation")
    except CollectionInvalid:
        logger.info("Collection already exists, skipping creation")
    
    # Create indexes
    logger.info("Creating indexes on precomputed_stats collection")
    
    # Compound index for quick lookups by stats_type and identifier
    db.precomputed_stats.create_index(
        [('stats_type', ASCENDING), ('identifier', ASCENDING)],
        unique=True,
        background=True
    )
    
    # TTL index to automatically expire documents
    db.precomputed_stats.create_index(
        [('expires_at', ASCENDING)],
        expireAfterSeconds=0,
        background=True
    )
    
    # Index for queries that filter by creation time
    db.precomputed_stats.create_index(
        [('created_at', DESCENDING)],
        background=True
    )
    
    logger.info("Indexes created successfully")
    
    return True

def precompute_initial_stats(db, top_n=50):
    """
    Precompute initial statistics for top products
    
    Args:
        db: MongoDB database connection
        top_n: Number of top products to precompute stats for
    """
    logger.info(f"Precomputing statistics for top {top_n} products")
    
    # Import required modules here to avoid circular imports
    try:
        from app.utils.mongodb_aggregations import AggregationPipelines
        pipelines = AggregationPipelines()
    except ImportError as e:
        logger.error(f"Failed to import AggregationPipelines: {e}")
        logger.warning("Creating a simplified version for initialization only")
        
        # Create a minimal version of the class for initialization
        class SimpleAggregationPipelines:
            def __init__(self):
                self.db = db
            
            def store_precomputed_stats(self, stats_type, identifier, data, expiration=None):
                """Store precomputed statistics in MongoDB"""
                now = datetime.now()
                
                # Create document
                doc = {
                    "stats_type": stats_type,
                    "identifier": identifier,
                    "created_at": now,
                    "data": data
                }
                
                # Add expiration if specified
                if expiration:
                    if isinstance(expiration, int):
                        # Interpret as hours
                        expires_at = now + timedelta(hours=expiration)
                    else:
                        # Assume it's a datetime
                        expires_at = expiration
                    
                    doc["expires_at"] = expires_at
                
                # Upsert the document
                self.db.precomputed_stats.update_one(
                    {"stats_type": stats_type, "identifier": identifier},
                    {"$set": doc},
                    upsert=True
                )
                
                logger.info(f"Stored {stats_type} stats for {identifier}")
                return True
        
        pipelines = SimpleAggregationPipelines()
    
    # Find top products by review count
    products = list(db.products.find(
        {}, 
        {"_id": 1, "title": 1, "platform": 1, "stats.review_count": 1}
    ).sort("stats.review_count", -1).limit(top_n))
    
    logger.info(f"Found {len(products)} products to process")
    
    if len(products) == 0:
        logger.warning("No products found. Skipping precomputation.")
        return 0
    
    # Initialize counters
    stats_count = 0
    
    # Create a test statistic to verify the collection works
    try:
        test_data = {
            "test": True,
            "timestamp": datetime.now(),
            "metrics": {
                "product_count": len(products)
            }
        }
        
        pipelines.store_precomputed_stats(
            stats_type="initialization_test",
            identifier="test",
            data=test_data,
            expiration=24  # 24 hours
        )
        
        stats_count += 1
        logger.info("Successfully stored test statistics")
        
    except Exception as e:
        logger.error(f"Error storing test statistics: {e}")
    
    # Get statistics about precomputed data
    stats_count = db.precomputed_stats.count_documents({})
    
    logger.info(f"Precomputation complete. Created {stats_count} precomputed statistics")
    
    return stats_count

def main():
    """Main function to initialize precomputed statistics"""
    args = parse_arguments()
    
    # Connect to MongoDB
    try:
        client, db = connect_mongodb()
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return False
    
    # Initialize collection
    try:
        success = initialize_collection(db, args.force)
        if not success:
            logger.error("Failed to initialize collection")
            return False
    except Exception as e:
        logger.error(f"Error initializing collection: {e}")
        return False
    
    # Precompute statistics
    try:
        stats_count = precompute_initial_stats(db, args.top_products)
        logger.info(f"Successfully precomputed {stats_count} statistics")
    except Exception as e:
        logger.error(f"Error precomputing statistics: {e}")
        return False
    
    # Close MongoDB connection
    client.close()
    
    logger.info("Precomputed statistics initialization complete")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 