"""
MongoDB Atlas Search Utilities

This module provides functions to work with MongoDB Atlas Search for text search capabilities.
"""
import logging
from typing import List, Dict, Any, Optional

from bson import ObjectId
from flask import current_app, g
from pymongo.database import Database

from app.utils.mongodb import get_db

# Configure logging
logger = logging.getLogger(__name__)

def setup_search_indexes(db: Database) -> bool:
    """
    Set up MongoDB Atlas Search indexes if they don't exist.
    
    This function should be called during app initialization to ensure
    all required search indexes are created.
    
    Args:
        db: MongoDB database instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if search indexes already exist
        existing_indexes = db.command({"listSearchIndexes": "products"})
        product_search_exists = False
        
        for index in existing_indexes.get('indexes', []):
            if index.get('name') == 'product_search':
                product_search_exists = True
                logger.info("Product search index already exists")
                break
        
        # Create search index for products if it doesn't exist
        if not product_search_exists:
            logger.info("Creating product search index")
            db.command({
                "createSearchIndex": "products",
                "name": "product_search",
                "definition": {
                    "mappings": {
                        "dynamic": False,
                        "fields": {
                            "title": {
                                "type": "string",
                                "analyzer": "lucene.standard",
                                "multi": {
                                    "keywordAnalyzer": {
                                        "type": "string",
                                        "analyzer": "lucene.keyword"
                                    }
                                }
                            },
                            "brand": {
                                "type": "string",
                                "analyzer": "lucene.standard",
                                "multi": {
                                    "keywordAnalyzer": {
                                        "type": "string",
                                        "analyzer": "lucene.keyword"
                                    }
                                }
                            },
                            "keywords": {
                                "type": "string",
                                "analyzer": "lucene.standard"
                            }
                        }
                    }
                }
            })
        
        # Check if review search index exists
        existing_indexes = db.command({"listSearchIndexes": "reviews"})
        review_search_exists = False
        
        for index in existing_indexes.get('indexes', []):
            if index.get('name') == 'review_search':
                review_search_exists = True
                logger.info("Review search index already exists")
                break
        
        # Create search index for reviews if it doesn't exist
        if not review_search_exists:
            logger.info("Creating review search index")
            db.command({
                "createSearchIndex": "reviews",
                "name": "review_search",
                "definition": {
                    "mappings": {
                        "dynamic": False,
                        "fields": {
                            "title": {
                                "type": "string",
                                "analyzer": "lucene.standard"
                            },
                            "content": {
                                "type": "string",
                                "analyzer": "lucene.standard"
                            },
                            "keywords": {
                                "type": "string",
                                "analyzer": "lucene.standard"
                            },
                            "product_id": {
                                "type": "objectId"
                            },
                            "rating": {
                                "type": "number"
                            },
                            "date": {
                                "type": "date"
                            },
                            "sentiment.label": {
                                "type": "string",
                                "analyzer": "lucene.keyword"
                            },
                            "sentiment.score": {
                                "type": "number"
                            }
                        }
                    }
                }
            })
            
        # Check if feedback search index exists
        existing_indexes = db.command({"listSearchIndexes": "feedback"})
        feedback_search_exists = False
        
        for index in existing_indexes.get('indexes', []):
            if index.get('name') == 'feedback_search':
                feedback_search_exists = True
                logger.info("Feedback search index already exists")
                break
        
        # Create search index for feedback if it doesn't exist
        if not feedback_search_exists:
            logger.info("Creating feedback search index")
            db.command({
                "createSearchIndex": "feedback",
                "name": "feedback_search",
                "definition": {
                    "mappings": {
                        "dynamic": False,
                        "fields": {
                            "title": {
                                "type": "string",
                                "analyzer": "lucene.standard"
                            },
                            "content": {
                                "type": "string",
                                "analyzer": "lucene.standard"
                            },
                            "tags": {
                                "type": "string",
                                "analyzer": "lucene.standard"
                            },
                            "entity_type": {
                                "type": "string",
                                "analyzer": "lucene.keyword"
                            },
                            "entity_id": {
                                "type": "string",
                                "analyzer": "lucene.keyword"
                            },
                            "rating": {
                                "type": "number"
                            },
                            "created_at": {
                                "type": "date"
                            }
                        }
                    }
                }
            })
        
        return True
    except Exception as e:
        logger.error(f"Error setting up search indexes: {e}")
        return False

def search_products(query: str, 
                   limit: int = 10, 
                   offset: int = 0, 
                   min_score: float = 0.5) -> List[Dict[str, Any]]:
    """
    Search for products using Atlas Search.
    
    Args:
        query: Search query
        limit: Maximum number of results
        offset: Number of results to skip
        min_score: Minimum score threshold for results
        
    Returns:
        List of matching products
    """
    try:
        db = get_db()
        
        # Build search pipeline
        pipeline = [
            {
                "$search": {
                    "index": "product_search",
                    "compound": {
                        "should": [
                            {
                                "text": {
                                    "query": query,
                                    "path": ["title", "brand", "keywords"],
                                    "fuzzy": {
                                        "maxEdits": 2,
                                        "prefixLength": 3
                                    },
                                    "score": {"boost": {"value": 3}}
                                }
                            }
                        ]
                    },
                    "highlight": {
                        "path": ["title", "brand", "keywords"]
                    },
                    "score": {"boost": {"path": "stats.review_count", "undefined": 1}}
                }
            },
            {
                "$match": {
                    "score": {"$gte": min_score}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "platform": 1,
                    "platform_id": 1,
                    "title": 1,
                    "brand": 1,
                    "price": 1,
                    "image_url": 1,
                    "url": 1,
                    "stats": 1,
                    "created_at": 1,
                    "score": {"$meta": "searchScore"},
                    "highlights": {"$meta": "searchHighlights"}
                }
            },
            {"$sort": {"score": -1}},
            {"$skip": offset},
            {"$limit": limit}
        ]
        
        # Execute search
        results = list(db.products.aggregate(pipeline))
        return results
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return []

def search_reviews(query: str, 
                  product_id: Optional[str] = None,
                  sentiment: Optional[str] = None,
                  min_rating: Optional[int] = None,
                  max_rating: Optional[int] = None,
                  limit: int = 20, 
                  offset: int = 0) -> List[Dict[str, Any]]:
    """
    Search for reviews using Atlas Search.
    
    Args:
        query: Search query
        product_id: Optional product ID to filter results
        sentiment: Optional sentiment filter (positive, negative, neutral)
        min_rating: Optional minimum rating filter
        max_rating: Optional maximum rating filter
        limit: Maximum number of results
        offset: Number of results to skip
        
    Returns:
        List of matching reviews
    """
    try:
        db = get_db()
        
        # Build search pipeline
        search_stage = {
            "$search": {
                "index": "review_search",
                "compound": {
                    "must": [],
                    "should": [
                        {
                            "text": {
                                "query": query,
                                "path": ["title", "content", "keywords"],
                                "fuzzy": {
                                    "maxEdits": 2,
                                    "prefixLength": 3
                                }
                            }
                        }
                    ],
                    "filter": []
                },
                "highlight": {
                    "path": ["title", "content", "keywords"]
                }
            }
        }
        
        # Add product_id filter if provided
        if product_id:
            search_stage["$search"]["compound"]["filter"].append({
                "equals": {
                    "path": "product_id",
                    "value": ObjectId(product_id)
                }
            })
        
        # Add sentiment filter if provided
        if sentiment:
            search_stage["$search"]["compound"]["filter"].append({
                "equals": {
                    "path": "sentiment.label",
                    "value": sentiment
                }
            })
        
        # Add rating filter if provided
        if min_rating is not None or max_rating is not None:
            rating_filter = {"range": {"path": "rating"}}
            if min_rating is not None:
                rating_filter["range"]["gte"] = min_rating
            if max_rating is not None:
                rating_filter["range"]["lte"] = max_rating
            search_stage["$search"]["compound"]["filter"].append(rating_filter)
        
        pipeline = [
            search_stage,
            {
                "$project": {
                    "_id": 1,
                    "product_id": 1,
                    "title": 1,
                    "content": 1,
                    "rating": 1,
                    "author": 1,
                    "date": 1,
                    "verified_purchase": 1,
                    "sentiment": 1,
                    "keywords": 1,
                    "created_at": 1,
                    "score": {"$meta": "searchScore"},
                    "highlights": {"$meta": "searchHighlights"}
                }
            },
            {"$sort": {"score": -1, "date": -1}},
            {"$skip": offset},
            {"$limit": limit}
        ]
        
        # Execute search
        results = list(db.reviews.aggregate(pipeline))
        return results
    except Exception as e:
        logger.error(f"Error searching reviews: {e}")
        return []

def search_feedback(query: str,
                   entity_type: Optional[str] = None,
                   entity_id: Optional[str] = None,
                   min_rating: Optional[int] = None,
                   max_rating: Optional[int] = None,
                   limit: int = 20,
                   offset: int = 0) -> List[Dict[str, Any]]:
    """
    Search for feedback using Atlas Search.
    
    Args:
        query: Search query
        entity_type: Optional entity type filter
        entity_id: Optional entity ID filter
        min_rating: Optional minimum rating filter
        max_rating: Optional maximum rating filter
        limit: Maximum number of results
        offset: Number of results to skip
        
    Returns:
        List of matching feedback
    """
    try:
        db = get_db()
        
        # Build search pipeline
        search_stage = {
            "$search": {
                "index": "feedback_search",
                "compound": {
                    "must": [],
                    "should": [
                        {
                            "text": {
                                "query": query,
                                "path": ["title", "content", "tags"],
                                "fuzzy": {
                                    "maxEdits": 1,
                                    "prefixLength": 2
                                }
                            }
                        }
                    ],
                    "filter": []
                },
                "highlight": {
                    "path": ["title", "content", "tags"]
                }
            }
        }
        
        # Add entity_type filter if provided
        if entity_type:
            search_stage["$search"]["compound"]["filter"].append({
                "equals": {
                    "path": "entity_type",
                    "value": entity_type
                }
            })
        
        # Add entity_id filter if provided
        if entity_id:
            # Handle both string and ObjectId entity_id values
            if len(entity_id) == 24 and all(c in '0123456789abcdef' for c in entity_id):
                # This could be an ObjectId, so use both string and ObjectId in an OR query
                try:
                    search_stage["$search"]["compound"]["filter"].append({
                        "text": {
                            "path": "entity_id",
                            "query": entity_id
                        }
                    })
                except:
                    search_stage["$search"]["compound"]["filter"].append({
                        "equals": {
                            "path": "entity_id",
                            "value": entity_id
                        }
                    })
            else:
                search_stage["$search"]["compound"]["filter"].append({
                    "equals": {
                        "path": "entity_id",
                        "value": entity_id
                    }
                })
        
        # Add rating filter if provided
        if min_rating is not None or max_rating is not None:
            rating_filter = {"range": {"path": "rating"}}
            if min_rating is not None:
                rating_filter["range"]["gte"] = min_rating
            if max_rating is not None:
                rating_filter["range"]["lte"] = max_rating
            search_stage["$search"]["compound"]["filter"].append(rating_filter)
        
        pipeline = [
            search_stage,
            {
                "$project": {
                    "_id": 1,
                    "user_id": 1,
                    "entity_type": 1,
                    "entity_id": 1,
                    "rating": 1,
                    "title": 1,
                    "content": 1,
                    "tags": 1,
                    "sentiment": 1,
                    "created_at": 1,
                    "updated_at": 1,
                    "score": {"$meta": "searchScore"},
                    "highlights": {"$meta": "searchHighlights"}
                }
            },
            {"$sort": {"score": -1, "created_at": -1}},
            {"$skip": offset},
            {"$limit": limit}
        ]
        
        # Execute search
        results = list(db.feedback.aggregate(pipeline))
        return results
    except Exception as e:
        logger.error(f"Error searching feedback: {e}")
        return []

def init_app(app):
    """
    Initialize Atlas Search with the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Register setup function to be called after app is configured
    @app.before_first_request
    def setup_atlas_search():
        db = get_db()
        setup_search_indexes(db)
        logger.info("Atlas Search indexes initialized") 