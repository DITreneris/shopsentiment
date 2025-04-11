"""
MongoDB utility functions for connecting to and interacting with MongoDB Atlas.
"""
import os
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from flask import current_app, g
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from bson.objectid import ObjectId
from werkzeug.local import LocalProxy

# Configure logging
logger = logging.getLogger(__name__)

def get_db() -> Database:
    """
    Get the MongoDB database instance.
    
    Returns:
        MongoDB database instance
    """
    if 'db' not in g:
        # Get MongoDB connection details from environment variables
        mongo_uri = os.environ.get('MONGODB_URI', current_app.config.get('MONGODB_URI'))
        db_name = os.environ.get('MONGODB_DB_NAME', current_app.config.get('MONGODB_DB_NAME', 'shopsentiment'))
        
        if not mongo_uri:
            raise ValueError("MongoDB URI not set. Please set MONGODB_URI environment variable.")
        
        # Create MongoDB client and connect to database
        logger.debug(f"Connecting to MongoDB database: {db_name}")
        client = MongoClient(mongo_uri)
        g.db = client[db_name]
        
        # Initialize collections if they don't exist
        _init_collections(g.db)
        
    return g.db

# Use LocalProxy to access the database within application context
db = LocalProxy(get_db)

def _init_collections(database: Database) -> None:
    """
    Initialize collections with validation schemas if they don't exist.
    
    Args:
        database: MongoDB database instance
    """
    collections = database.list_collection_names()
    
    # Create collections with validation schemas if they don't exist
    if 'users' not in collections:
        logger.info("Creating 'users' collection with validation schema")
        database.create_collection('users')
        database.command({
            'collMod': 'users',
            'validator': {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['username', 'email', 'password_hash', 'created_at'],
                    'properties': {
                        'username': {'bsonType': 'string'},
                        'email': {'bsonType': 'string'},
                        'password_hash': {'bsonType': 'string'},
                        'created_at': {'bsonType': 'date'},
                        'last_login': {'bsonType': 'date'},
                        'settings': {'bsonType': 'object'}
                    }
                }
            }
        })
        # Create indexes for users collection
        database.users.create_index('email', unique=True)
        database.users.create_index('username', unique=True)
    
    if 'products' not in collections:
        logger.info("Creating 'products' collection with validation schema")
        database.create_collection('products')
        database.command({
            'collMod': 'products',
            'validator': {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['platform_id', 'platform', 'created_at'],
                    'properties': {
                        'platform_id': {'bsonType': 'string'},
                        'platform': {'bsonType': 'string'},
                        'title': {'bsonType': 'string'},
                        'brand': {'bsonType': 'string'},
                        'price': {'bsonType': 'string'},
                        'image_url': {'bsonType': 'string'},
                        'url': {'bsonType': 'string'},
                        'created_at': {'bsonType': 'date'},
                        'last_updated': {'bsonType': 'date'},
                        'created_by': {'bsonType': 'objectId'},
                        'stats': {'bsonType': 'object'},
                        'keywords': {'bsonType': 'array'}
                    }
                }
            }
        })
        # Create indexes for products collection
        database.products.create_index([('platform', 1), ('platform_id', 1)], unique=True)
        database.products.create_index('created_by')
        database.products.create_index([('created_at', -1)])
    
    if 'reviews' not in collections:
        logger.info("Creating 'reviews' collection with validation schema")
        database.create_collection('reviews')
        database.command({
            'collMod': 'reviews',
            'validator': {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['product_id', 'rating', 'content', 'date', 'created_at'],
                    'properties': {
                        'product_id': {'bsonType': 'objectId'},
                        'platform_review_id': {'bsonType': 'string'},
                        'title': {'bsonType': 'string'},
                        'content': {'bsonType': 'string'},
                        'rating': {'bsonType': 'int'},
                        'author': {'bsonType': 'string'},
                        'date': {'bsonType': 'date'},
                        'verified_purchase': {'bsonType': 'bool'},
                        'sentiment': {'bsonType': 'object'},
                        'keywords': {'bsonType': 'array'},
                        'created_at': {'bsonType': 'date'}
                    }
                }
            }
        })
        # Create indexes for reviews collection
        database.reviews.create_index('product_id')
        database.reviews.create_index([('product_id', 1), ('sentiment.label', 1)])
        database.reviews.create_index([('product_id', 1), ('rating', 1)])
        database.reviews.create_index([('product_id', 1), ('date', -1)])
    
    if 'feedback' not in collections:
        logger.info("Creating 'feedback' collection with validation schema")
        database.create_collection('feedback')
        database.command({
            'collMod': 'feedback',
            'validator': {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['entity_type', 'entity_id', 'rating', 'created_at'],
                    'properties': {
                        'user_id': {'bsonType': ['objectId', 'null']},
                        'entity_type': {'bsonType': 'string'},
                        'entity_id': {'bsonType': ['string', 'objectId']},
                        'rating': {'bsonType': ['int', 'double']},
                        'title': {'bsonType': ['string', 'null']},
                        'content': {'bsonType': ['string', 'null']},
                        'tags': {'bsonType': 'array'},
                        'sentiment': {'bsonType': ['double', 'null']},
                        'created_at': {'bsonType': 'date'},
                        'updated_at': {'bsonType': 'date'}
                    }
                }
            }
        })
        # Create indexes for feedback collection
        database.feedback.create_index('user_id')
        database.feedback.create_index([('entity_type', 1), ('entity_id', 1)])
        database.feedback.create_index([('created_at', -1)])
        database.feedback.create_index('rating')

def close_db(e=None) -> None:
    """
    Close MongoDB connection.
    
    Args:
        e: Error object (if any)
    """
    db_client = g.pop('db', None)
    if db_client is not None:
        client = db_client.client
        client.close()
        logger.debug("MongoDB connection closed")

def init_app(app):
    """
    Initialize MongoDB with the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Register close_db function to be called when application context ends
    app.teardown_appcontext(close_db)
    
    # Set up MongoDB configuration
    app.config.setdefault('MONGODB_URI', os.environ.get('MONGODB_URI'))
    app.config.setdefault('MONGODB_DB_NAME', os.environ.get('MONGODB_DB_NAME', 'shopsentiment'))
    
    logger.info(f"MongoDB initialized with database: {app.config.get('MONGODB_DB_NAME')}")

# Helper Functions for Database Operations

def get_collection(collection_name: str) -> Collection:
    """
    Get a MongoDB collection.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Collection object
    """
    return get_db()[collection_name]

def find_user_by_email(email: str) -> Union[Dict, None]:
    """
    Find a user by email.
    
    Args:
        email: User's email address
        
    Returns:
        User document or None if not found
    """
    return get_collection('users').find_one({'email': email})

def find_user_by_id(user_id: str) -> Union[Dict, None]:
    """
    Find a user by ID.
    
    Args:
        user_id: User's ObjectId as string
        
    Returns:
        User document or None if not found
    """
    return get_collection('users').find_one({'_id': ObjectId(user_id)})

def insert_user(user_data: Dict) -> str:
    """
    Insert a new user document.
    
    Args:
        user_data: User document
        
    Returns:
        ID of the inserted user
    """
    result = get_collection('users').insert_one(user_data)
    return str(result.inserted_id)

def find_product_by_platform_id(platform: str, platform_id: str) -> Union[Dict, None]:
    """
    Find a product by platform and platform ID.
    
    Args:
        platform: Platform name (e.g., 'amazon', 'ebay')
        platform_id: Product ID on the platform
        
    Returns:
        Product document or None if not found
    """
    return get_collection('products').find_one({
        'platform': platform,
        'platform_id': platform_id
    })

def find_product_by_id(product_id: str) -> Union[Dict, None]:
    """
    Find a product by ID.
    
    Args:
        product_id: Product's ObjectId as string
        
    Returns:
        Product document or None if not found
    """
    try:
        return get_collection('products').find_one({'_id': ObjectId(product_id)})
    except Exception as e:
        logger.error(f"Error finding product by ID: {e}")
        return None

def insert_product(product_data: Dict) -> str:
    """
    Insert a new product document.
    
    Args:
        product_data: Product document
        
    Returns:
        ID of the inserted product
    """
    result = get_collection('products').insert_one(product_data)
    return str(result.inserted_id)

def update_product(product_id: str, update_data: Dict) -> bool:
    """
    Update a product document.
    
    Args:
        product_id: Product's ObjectId as string
        update_data: Fields to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        result = get_collection('products').update_one(
            {'_id': ObjectId(product_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {e}")
        return False

def find_reviews_by_product(product_id: str, 
                           sentiment: Optional[str] = None,
                           min_rating: Optional[int] = None,
                           max_rating: Optional[int] = None,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None,
                           keyword: Optional[str] = None,
                           page: int = 1,
                           per_page: int = 20) -> List[Dict]:
    """
    Find reviews for a product with optional filters.
    
    Args:
        product_id: Product's ObjectId as string
        sentiment: Filter by sentiment (positive, negative, neutral)
        min_rating: Minimum rating (1-5)
        max_rating: Maximum rating (1-5)
        start_date: Start date for date range filter (ISO format)
        end_date: End date for date range filter (ISO format)
        keyword: Filter by keyword
        page: Page number for pagination
        per_page: Number of reviews per page
        
    Returns:
        List of review documents
    """
    query = {'product_id': ObjectId(product_id)}
    
    # Apply filters
    if sentiment:
        query['sentiment.label'] = sentiment
        
    if min_rating is not None:
        query.setdefault('rating', {})
        query['rating']['$gte'] = min_rating
        
    if max_rating is not None:
        query.setdefault('rating', {})
        query['rating']['$lte'] = max_rating
        
    if start_date:
        query.setdefault('date', {})
        query['date']['$gte'] = start_date
        
    if end_date:
        query.setdefault('date', {})
        query['date']['$lte'] = end_date
        
    if keyword:
        query['$text'] = {'$search': keyword}
    
    # Calculate skip value for pagination
    skip = (page - 1) * per_page
    
    # Execute query
    return list(get_collection('reviews')
                .find(query)
                .sort('date', -1)
                .skip(skip)
                .limit(per_page))

def count_reviews_by_product(product_id: str, 
                            sentiment: Optional[str] = None,
                            min_rating: Optional[int] = None,
                            max_rating: Optional[int] = None,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None,
                            keyword: Optional[str] = None) -> int:
    """
    Count reviews for a product with optional filters.
    
    Args:
        product_id: Product's ObjectId as string
        sentiment: Filter by sentiment (positive, negative, neutral)
        min_rating: Minimum rating (1-5)
        max_rating: Maximum rating (1-5)
        start_date: Start date for date range filter (ISO format)
        end_date: End date for date range filter (ISO format)
        keyword: Filter by keyword
        
    Returns:
        Count of matching reviews
    """
    query = {'product_id': ObjectId(product_id)}
    
    # Apply filters (same as find_reviews_by_product)
    if sentiment:
        query['sentiment.label'] = sentiment
        
    if min_rating is not None:
        query.setdefault('rating', {})
        query['rating']['$gte'] = min_rating
        
    if max_rating is not None:
        query.setdefault('rating', {})
        query['rating']['$lte'] = max_rating
        
    if start_date:
        query.setdefault('date', {})
        query['date']['$gte'] = start_date
        
    if end_date:
        query.setdefault('date', {})
        query['date']['$lte'] = end_date
        
    if keyword:
        query['$text'] = {'$search': keyword}
    
    # Execute count
    return get_collection('reviews').count_documents(query)

def insert_review(review_data: Dict) -> str:
    """
    Insert a new review document.
    
    Args:
        review_data: Review document
        
    Returns:
        ID of the inserted review
    """
    result = get_collection('reviews').insert_one(review_data)
    return str(result.inserted_id)

def insert_reviews(reviews_data: List[Dict]) -> int:
    """
    Insert multiple review documents.
    
    Args:
        reviews_data: List of review documents
        
    Returns:
        Count of inserted reviews
    """
    if not reviews_data:
        return 0
        
    result = get_collection('reviews').insert_many(reviews_data)
    return len(result.inserted_ids)

def update_review_sentiment(review_id: str, sentiment_data: Dict) -> bool:
    """
    Update sentiment analysis data for a review.
    
    Args:
        review_id: Review's ObjectId as string
        sentiment_data: Sentiment analysis data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        result = get_collection('reviews').update_one(
            {'_id': ObjectId(review_id)},
            {'$set': {'sentiment': sentiment_data}}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating review sentiment {review_id}: {e}")
        return False

def get_product_stats(product_id: str) -> Dict[str, Any]:
    """
    Get statistics for a product using MongoDB aggregation.
    
    Args:
        product_id: Product's ObjectId as string
        
    Returns:
        Dictionary with product statistics
    """
    pipeline = [
        {'$match': {'product_id': ObjectId(product_id)}},
        {'$facet': {
            'rating_distribution': [
                {'$group': {
                    '_id': '$rating',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ],
            'sentiment_distribution': [
                {'$group': {
                    '_id': '$sentiment.label',
                    'count': {'$sum': 1}
                }}
            ],
            'avg_rating': [
                {'$group': {
                    '_id': None,
                    'avg': {'$avg': '$rating'},
                    'count': {'$sum': 1}
                }}
            ],
            'top_keywords': [
                {'$unwind': '$keywords'},
                {'$group': {
                    '_id': '$keywords',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]
        }}
    ]
    
    result = list(get_collection('reviews').aggregate(pipeline))
    
    if not result:
        return {
            'rating_distribution': {},
            'sentiment_distribution': {},
            'avg_rating': 0,
            'review_count': 0,
            'top_keywords': []
        }
    
    # Process aggregation results
    stats = result[0]
    
    # Format rating distribution
    rating_dist = {str(item['_id']): item['count'] for item in stats['rating_distribution']}
    
    # Format sentiment distribution
    sentiment_dist = {item['_id']: item['count'] for item in stats['sentiment_distribution']}
    
    # Get average rating and review count
    avg_rating_data = stats['avg_rating'][0] if stats['avg_rating'] else {'avg': 0, 'count': 0}
    
    # Format top keywords
    top_keywords = [{'term': item['_id'], 'count': item['count']} for item in stats['top_keywords']]
    
    return {
        'rating_distribution': rating_dist,
        'sentiment_distribution': sentiment_dist,
        'avg_rating': round(avg_rating_data['avg'], 1) if avg_rating_data['avg'] else 0,
        'review_count': avg_rating_data['count'],
        'top_keywords': top_keywords
    }

def get_product_by_platform_id(platform: str, platform_id: str) -> Union[Dict[str, Any], None]:
    """Get a product from MongoDB by platform and platform_id"""
    try:
        product = get_collection('products').find_one({
            "platform": platform,
            "platform_id": platform_id
        })
        return product
    except Exception as e:
        logger.error(f"Error retrieving product: {e}")
        return None

def get_reviews_for_product(product_id, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get reviews for a product from MongoDB"""
    try:
        query = {"product_id": ObjectId(product_id)}
        if limit:
            reviews = list(get_collection('reviews').find(query).sort("date", -1).limit(limit))
        else:
            reviews = list(get_collection('reviews').find(query).sort("date", -1))
        return reviews
    except Exception as e:
        logger.error(f"Error retrieving reviews: {e}")
        return []

def save_product(product_data: Dict[str, Any]) -> Union[str, None]:
    """Save a product to MongoDB"""
    try:
        # Check if product already exists
        existing = get_collection('products').find_one({
            "platform": product_data["platform"],
            "platform_id": product_data["platform_id"]
        })
        
        if existing:
            # Update existing product
            get_collection('products').update_one(
                {"_id": existing["_id"]},
                {"$set": product_data}
            )
            return str(existing["_id"])
        else:
            # Insert new product
            result = get_collection('products').insert_one(product_data)
            return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error saving product: {e}")
        return None

def save_reviews(reviews: List[Dict[str, Any]], product_id) -> bool:
    """Save reviews to MongoDB"""
    try:
        if not reviews:
            return True
            
        # Add product_id to each review
        for review in reviews:
            review["product_id"] = ObjectId(product_id)
            
        # Insert reviews
        get_collection('reviews').insert_many(reviews)
        return True
    except Exception as e:
        logger.error(f"Error saving reviews: {e}")
        return False

def update_product_stats(product_id, stats: Dict[str, Any]) -> bool:
    """Update product statistics in MongoDB"""
    try:
        get_collection('products').update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"stats": stats}}
        )
        return True
    except Exception as e:
        logger.error(f"Error updating product stats: {e}")
        return False

def get_user_products(user_id) -> List[Dict[str, Any]]:
    """Get products created by a specific user"""
    try:
        products = list(get_collection('products').find({"created_by": ObjectId(user_id)}).sort("created_at", -1))
        return products
    except Exception as e:
        logger.error(f"Error retrieving user products: {e}")
        return []

# Feedback Helper Functions

def find_feedback_by_id(feedback_id: str) -> Union[Dict, None]:
    """
    Find feedback by ID.
    
    Args:
        feedback_id: Feedback ObjectId as string
        
    Returns:
        Feedback document or None if not found
    """
    try:
        return get_collection('feedback').find_one({'_id': ObjectId(feedback_id)})
    except Exception as e:
        logger.error(f"Error finding feedback by ID: {e}")
        return None

def find_feedback_by_entity(entity_type: str, entity_id: str, 
                           limit: int = 100, offset: int = 0) -> List[Dict]:
    """
    Find feedback for a specific entity.
    
    Args:
        entity_type: Type of entity (e.g., 'product', 'platform', 'app')
        entity_id: ID of the entity
        limit: Maximum number of results
        offset: Number of results to skip
        
    Returns:
        List of feedback documents
    """
    try:
        # Convert entity_id to ObjectId if it's a valid ObjectId
        if entity_id and len(entity_id) == 24 and all(c in '0123456789abcdef' for c in entity_id):
            try:
                entity_id_obj = ObjectId(entity_id)
                # Search for both string and ObjectId versions
                cursor = get_collection('feedback').find({
                    'entity_type': entity_type,
                    '$or': [{'entity_id': entity_id}, {'entity_id': entity_id_obj}]
                })
            except:
                cursor = get_collection('feedback').find({
                    'entity_type': entity_type,
                    'entity_id': entity_id
                })
        else:
            cursor = get_collection('feedback').find({
                'entity_type': entity_type,
                'entity_id': entity_id
            })
        
        return list(cursor.sort('created_at', -1).skip(offset).limit(limit))
    except Exception as e:
        logger.error(f"Error finding feedback by entity: {e}")
        return []

def find_feedback_by_user(user_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
    """
    Find feedback submitted by a specific user.
    
    Args:
        user_id: User ObjectId as string
        limit: Maximum number of results
        offset: Number of results to skip
        
    Returns:
        List of feedback documents
    """
    try:
        return list(get_collection('feedback').find({
            'user_id': ObjectId(user_id)
        }).sort('created_at', -1).skip(offset).limit(limit))
    except Exception as e:
        logger.error(f"Error finding feedback by user: {e}")
        return []

def insert_feedback(feedback_data: Dict) -> Union[str, None]:
    """
    Insert a new feedback document.
    
    Args:
        feedback_data: Feedback document
        
    Returns:
        ID of the inserted feedback or None on error
    """
    try:
        # Ensure required fields
        if 'created_at' not in feedback_data:
            feedback_data['created_at'] = datetime.now()
        if 'updated_at' not in feedback_data:
            feedback_data['updated_at'] = feedback_data['created_at']
        
        # Convert user_id to ObjectId if it exists
        if feedback_data.get('user_id') and isinstance(feedback_data['user_id'], str):
            feedback_data['user_id'] = ObjectId(feedback_data['user_id'])
        
        result = get_collection('feedback').insert_one(feedback_data)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error inserting feedback: {e}")
        return None

def update_feedback(feedback_id: str, update_data: Dict) -> bool:
    """
    Update an existing feedback document.
    
    Args:
        feedback_id: Feedback ObjectId as string
        update_data: Fields to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Always update the updated_at timestamp
        update_data['updated_at'] = datetime.now()
        
        # Convert user_id to ObjectId if it exists in the update
        if update_data.get('user_id') and isinstance(update_data['user_id'], str):
            update_data['user_id'] = ObjectId(update_data['user_id'])
        
        result = get_collection('feedback').update_one(
            {'_id': ObjectId(feedback_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating feedback: {e}")
        return False

def delete_feedback(feedback_id: str) -> bool:
    """
    Delete a feedback document.
    
    Args:
        feedback_id: Feedback ObjectId as string
        
    Returns:
        True if successful, False otherwise
    """
    try:
        result = get_collection('feedback').delete_one({'_id': ObjectId(feedback_id)})
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error deleting feedback: {e}")
        return False 