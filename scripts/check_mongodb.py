#!/usr/bin/env python3
"""
Check MongoDB Connection

This script tests the MongoDB connection and prints information about all collections.
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("check_mongodb")

# Load environment variables
load_dotenv()

# Custom JSON encoder for MongoDB data types
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

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

def connect_mongodb():
    """Connect to MongoDB and test connection."""
    try:
        mongodb_uri = get_mongodb_uri()
        db_name = get_database_name()
        
        # Connect to MongoDB
        logger.info(f"Connecting to MongoDB at {mongodb_uri}")
        client = MongoClient(mongodb_uri)
        
        # Test connection
        client.admin.command('ping')
        logger.info("MongoDB connection successful!")
        
        # Get database
        db = client[db_name]
        logger.info(f"Accessing database: {db_name}")
        
        return client, db
    except Exception as e:
        logger.error(f"Cannot connect to MongoDB: {e}")
        sys.exit(1)

def check_collections(db):
    """Check all collections in the database."""
    try:
        # List collections
        collections = db.list_collection_names()
        logger.info(f"Found {len(collections)} collections: {', '.join(collections)}")
        
        # Check each collection
        for collection_name in collections:
            count = db[collection_name].count_documents({})
            logger.info(f"Collection '{collection_name}' has {count} documents")
            
            # Show sample document if collection is not empty
            if count > 0:
                sample = db[collection_name].find_one()
                json_sample = json.dumps(sample, indent=2, cls=MongoJSONEncoder)
                logger.info(f"Sample document from {collection_name}:\n{json_sample}")
    
    except Exception as e:
        logger.error(f"Error checking collections: {e}")

def check_indexes(db):
    """Check indexes for all collections."""
    try:
        for collection_name in db.list_collection_names():
            indexes = list(db[collection_name].list_indexes())
            logger.info(f"Collection '{collection_name}' has {len(indexes)} indexes:")
            
            for idx, index in enumerate(indexes):
                logger.info(f"  {idx+1}. {index['name']}: {index['key']}")
    
    except Exception as e:
        logger.error(f"Error checking indexes: {e}")

def main():
    """Main function."""
    logger.info("Starting MongoDB connection check")
    
    client, db = connect_mongodb()
    
    try:
        # Check collections
        check_collections(db)
        
        # Check indexes
        check_indexes(db)
        
        logger.info("MongoDB check completed successfully")
    finally:
        # Close MongoDB connection
        client.close()
        logger.info("MongoDB connection closed")

if __name__ == "__main__":
    main() 