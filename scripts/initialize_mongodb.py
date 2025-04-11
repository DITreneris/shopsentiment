#!/usr/bin/env python3
"""
Initialize MongoDB Collections and Indexes

This script creates the necessary collections and indexes in the MongoDB database.
"""

import os
import sys
import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('initialize_mongodb')

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
    """
    Connect to MongoDB and get database.
    
    Args:
        uri: MongoDB connection URI
        db_name: Database name
        
    Returns:
        MongoDB database instance
    """
    try:
        client = MongoClient(uri)
        # Test connection
        client.admin.command('ping')
        logger.info("Connected to MongoDB Atlas")
        return client[db_name]
    except ServerSelectionTimeoutError as e:
        logger.error(f"Cannot connect to MongoDB: {e}")
        sys.exit(1)

def create_users_collection(db):
    """
    Create users collection with indexes.
    
    Args:
        db: MongoDB database instance
    """
    try:
        # Create validator for users collection
        users_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["username", "email", "password_hash"],
                "properties": {
                    "username": {
                        "bsonType": "string",
                        "description": "Username must be a string and is required"
                    },
                    "email": {
                        "bsonType": "string",
                        "description": "Email must be a string and is required"
                    },
                    "password_hash": {
                        "bsonType": "string",
                        "description": "Password hash must be a string and is required"
                    },
                    "is_admin": {
                        "bsonType": "bool",
                        "description": "Admin flag must be a boolean"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Created date must be a date"
                    },
                    "last_login": {
                        "bsonType": ["date", "null"],
                        "description": "Last login date must be a date or null"
                    },
                    "settings": {
                        "bsonType": "object",
                        "description": "User settings"
                    }
                }
            }
        }
        
        # Create users collection if it doesn't exist
        if "users" not in db.list_collection_names():
            db.create_collection("users", validator=users_validator)
            logger.info("Created 'users' collection")
        
        # Create indexes
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.users.create_index([("username", ASCENDING)], unique=True)
        logger.info("Created indexes for 'users' collection")
        
    except OperationFailure as e:
        logger.error(f"Error creating users collection: {e}")

def create_products_collection(db):
    """
    Create products collection with indexes.
    
    Args:
        db: MongoDB database instance
    """
    try:
        # Create validator for products collection
        products_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["platform_id", "platform"],
                "properties": {
                    "platform_id": {
                        "bsonType": "string",
                        "description": "Platform-specific ID must be a string and is required"
                    },
                    "platform": {
                        "bsonType": "string",
                        "description": "Platform name must be a string and is required"
                    },
                    "title": {
                        "bsonType": ["string", "null"],
                        "description": "Title must be a string"
                    },
                    "brand": {
                        "bsonType": ["string", "null"],
                        "description": "Brand must be a string"
                    },
                    "price": {
                        "bsonType": ["string", "null"],
                        "description": "Price must be a string"
                    },
                    "image_url": {
                        "bsonType": ["string", "null"],
                        "description": "Image URL must be a string"
                    },
                    "url": {
                        "bsonType": ["string", "null"],
                        "description": "URL must be a string"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Created date must be a date"
                    },
                    "last_updated": {
                        "bsonType": "date",
                        "description": "Last updated date must be a date"
                    },
                    "created_by": {
                        "bsonType": ["objectId", "null"],
                        "description": "Created by user ID"
                    },
                    "stats": {
                        "bsonType": "object",
                        "description": "Product statistics"
                    },
                    "keywords": {
                        "bsonType": "array",
                        "description": "Keywords extracted from reviews"
                    }
                }
            }
        }
        
        # Create products collection if it doesn't exist
        if "products" not in db.list_collection_names():
            db.create_collection("products", validator=products_validator)
            logger.info("Created 'products' collection")
        
        # Create indexes
        db.products.create_index([("platform", ASCENDING), ("platform_id", ASCENDING)], unique=True)
        db.products.create_index([("created_by", ASCENDING)])
        db.products.create_index([("created_at", DESCENDING)])
        logger.info("Created indexes for 'products' collection")
        
    except OperationFailure as e:
        logger.error(f"Error creating products collection: {e}")

def create_reviews_collection(db):
    """
    Create reviews collection with indexes.
    
    Args:
        db: MongoDB database instance
    """
    try:
        # Create validator for reviews collection
        reviews_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["product_id", "content"],
                "properties": {
                    "product_id": {
                        "bsonType": "objectId",
                        "description": "Product ID must be an ObjectId and is required"
                    },
                    "platform_review_id": {
                        "bsonType": ["string", "null"],
                        "description": "Platform-specific review ID"
                    },
                    "title": {
                        "bsonType": ["string", "null"],
                        "description": "Title must be a string"
                    },
                    "content": {
                        "bsonType": "string",
                        "description": "Content must be a string and is required"
                    },
                    "rating": {
                        "bsonType": ["double", "int", "null"],
                        "description": "Rating must be a number"
                    },
                    "author": {
                        "bsonType": ["string", "null"],
                        "description": "Author must be a string"
                    },
                    "date": {
                        "bsonType": ["date", "null"],
                        "description": "Date must be a date"
                    },
                    "verified_purchase": {
                        "bsonType": "bool",
                        "description": "Verified purchase flag must be a boolean"
                    },
                    "sentiment": {
                        "bsonType": ["object", "null"],
                        "description": "Sentiment analysis results"
                    },
                    "keywords": {
                        "bsonType": "array",
                        "description": "Keywords extracted from review"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Created date must be a date"
                    }
                }
            }
        }
        
        # Create reviews collection if it doesn't exist
        if "reviews" not in db.list_collection_names():
            db.create_collection("reviews", validator=reviews_validator)
            logger.info("Created 'reviews' collection")
        
        # Create indexes
        db.reviews.create_index([("product_id", ASCENDING)])
        db.reviews.create_index([("product_id", ASCENDING), ("sentiment.label", ASCENDING)])
        db.reviews.create_index([("product_id", ASCENDING), ("rating", ASCENDING)])
        db.reviews.create_index([("product_id", ASCENDING), ("date", DESCENDING)])
        logger.info("Created indexes for 'reviews' collection")
        
    except OperationFailure as e:
        logger.error(f"Error creating reviews collection: {e}")

def create_feedback_collection(db):
    """
    Create feedback collection with indexes.
    
    Args:
        db: MongoDB database instance
    """
    try:
        # Create validator for feedback collection
        feedback_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["entity_type", "entity_id", "rating", "created_at"],
                "properties": {
                    "user_id": {
                        "bsonType": ["objectId", "null"],
                        "description": "User ID who submitted the feedback"
                    },
                    "entity_type": {
                        "bsonType": "string",
                        "description": "Type of entity being rated (product, platform, app, etc.)"
                    },
                    "entity_id": {
                        "bsonType": ["string", "objectId"],
                        "description": "ID of the entity being rated"
                    },
                    "rating": {
                        "bsonType": ["int", "double"],
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Numerical rating (1-5)"
                    },
                    "title": {
                        "bsonType": ["string", "null"],
                        "description": "Feedback title/summary"
                    },
                    "content": {
                        "bsonType": ["string", "null"],
                        "description": "Detailed feedback text"
                    },
                    "tags": {
                        "bsonType": "array",
                        "description": "List of tags associated with the feedback"
                    },
                    "sentiment": {
                        "bsonType": ["double", "null"],
                        "description": "Calculated sentiment score"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Creation timestamp"
                    },
                    "updated_at": {
                        "bsonType": "date",
                        "description": "Last update timestamp"
                    }
                }
            }
        }
        
        # Create feedback collection if it doesn't exist
        if "feedback" not in db.list_collection_names():
            db.create_collection("feedback", validator=feedback_validator)
            logger.info("Created 'feedback' collection")
        
        # Create indexes
        db.feedback.create_index([("user_id", ASCENDING)])
        db.feedback.create_index([("entity_type", ASCENDING), ("entity_id", ASCENDING)])
        db.feedback.create_index([("created_at", DESCENDING)])
        db.feedback.create_index([("rating", ASCENDING)])
        logger.info("Created indexes for 'feedback' collection")
        
    except OperationFailure as e:
        logger.error(f"Error creating feedback collection: {e}")

def create_admin_user(db):
    """
    Create an admin user if no users exist.
    
    Args:
        db: MongoDB database instance
    """
    from werkzeug.security import generate_password_hash
    from datetime import datetime
    
    # Check if users collection exists and is empty
    if "users" in db.list_collection_names() and db.users.count_documents({}) == 0:
        try:
            # Create admin user
            admin_user = {
                "username": "admin",
                "email": "admin@example.com",
                "password_hash": generate_password_hash("admin123"),  # Change this password in production!
                "is_admin": True,
                "created_at": datetime.now(),
                "last_login": None,
                "settings": {
                    "theme": "light"
                }
            }
            
            result = db.users.insert_one(admin_user)
            logger.info(f"Created admin user with ID: {result.inserted_id}")
            
            # Print credentials for the user
            logger.info("Admin user credentials:")
            logger.info("  Username: admin")
            logger.info("  Email: admin@example.com")
            logger.info("  Password: admin123")
            logger.info("IMPORTANT: Change these credentials in a production environment!")
            
        except OperationFailure as e:
            logger.error(f"Error creating admin user: {e}")

def main():
    """Main function to initialize MongoDB database."""
    mongodb_uri = get_mongodb_uri()
    db_name = get_database_name()
    
    logger.info(f"Initializing MongoDB database: {db_name}")
    
    # Connect to MongoDB
    db = connect_mongodb(mongodb_uri, db_name)
    
    # Create collections and indexes
    create_users_collection(db)
    create_products_collection(db)
    create_reviews_collection(db)
    create_feedback_collection(db)
    
    # Create admin user
    create_admin_user(db)
    
    logger.info("MongoDB initialization completed successfully")

if __name__ == "__main__":
    main() 