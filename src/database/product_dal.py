"""
Product Data Access Layer (DAL) for the ShopSentiment application.
Handles database operations related to products and reviews.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult

from src.models.product import Product, Review, SentimentAnalysis
from src.database.connection import get_database

logger = logging.getLogger(__name__)


class ProductDAL:
    """Data Access Layer for Product operations."""
    
    def __init__(self):
        """Initialize the DAL with MongoDB collections."""
        db = get_database()
        self.products = db.products
        self.reviews = db.reviews
        self._ensure_indexes()
        
    def _ensure_indexes(self):
        """Create necessary indexes for product and review collections."""
        # Product indexes
        self.products.create_index("name")
        self.products.create_index([("name", "text"), ("description", "text")])
        self.products.create_index("sentiment.score")
        self.products.create_index("sentiment.reviews_count")
        
        # Review indexes
        self.reviews.create_index("product_id")
        self.reviews.create_index("sentiment_score")
        self.reviews.create_index("created_at")
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a product by ID."""
        try:
            product_data = await self.products.find_one({"_id": product_id})
            if product_data:
                # Fetch reviews for the product
                reviews_cursor = self.reviews.find({"product_id": product_id})
                reviews = await reviews_cursor.to_list(length=100)
                product_data["reviews"] = reviews
            return product_data
        except Exception as e:
            logger.error(f"Error fetching product {product_id}: {str(e)}")
            return None
    
    async def get_products(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve multiple products with pagination."""
        try:
            cursor = self.products.find().skip(skip).limit(limit).sort("created_at", -1)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error fetching products: {str(e)}")
            return []
    
    async def search_products(self, query: str, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """Search products by text query."""
        try:
            cursor = self.products.find(
                {"$text": {"$search": query}}
            ).skip(skip).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error searching products with query '{query}': {str(e)}")
            return []
    
    async def create_product(self, product: Product) -> Optional[str]:
        """Create a new product."""
        try:
            product_dict = product.dict(exclude={"reviews"})
            product_dict["_id"] = product_dict.pop("id", str(ObjectId()))
            
            result = await self.products.insert_one(product_dict)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating product: {str(e)}")
            return None
    
    async def update_product(self, product_id: str, product_data: Dict[str, Any]) -> bool:
        """Update a product's information."""
        try:
            # Remove id and created_at if present in the update data
            if "id" in product_data:
                del product_data["id"]
            if "created_at" in product_data:
                del product_data["created_at"]
            
            # Set updated_at timestamp
            product_data["updated_at"] = datetime.utcnow()
            
            result = await self.products.update_one(
                {"_id": product_id},
                {"$set": product_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating product {product_id}: {str(e)}")
            return False
    
    async def delete_product(self, product_id: str) -> bool:
        """Delete a product and its reviews."""
        try:
            # Delete the product
            product_result = await self.products.delete_one({"_id": product_id})
            
            # Delete associated reviews
            review_result = await self.reviews.delete_many({"product_id": product_id})
            
            return product_result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {str(e)}")
            return False
    
    async def add_review(self, product_id: str, review: Review) -> bool:
        """Add a review to a product and update sentiment statistics."""
        try:
            # Create review document
            review_dict = review.dict()
            review_dict["_id"] = review_dict.pop("id", str(ObjectId()))
            review_dict["product_id"] = product_id
            
            # Insert the review
            await self.reviews.insert_one(review_dict)
            
            # Update product's sentiment data
            product = await self.get_product(product_id)
            if not product:
                return False
                
            # Calculate new sentiment metrics
            new_sentiment = await self._calculate_product_sentiment(product_id)
            
            # Update the product
            await self.products.update_one(
                {"_id": product_id},
                {
                    "$set": {
                        "sentiment": new_sentiment,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return True
        except Exception as e:
            logger.error(f"Error adding review to product {product_id}: {str(e)}")
            return False
    
    async def _calculate_product_sentiment(self, product_id: str) -> Dict[str, Any]:
        """Calculate sentiment data for a product based on its reviews."""
        try:
            # Get all reviews for the product
            cursor = self.reviews.find({"product_id": product_id})
            reviews = await cursor.to_list(length=1000)
            
            if not reviews:
                return SentimentAnalysis().dict()
                
            # Calculate sentiment metrics
            total_reviews = len(reviews)
            total_sentiment = sum(review["sentiment_score"] for review in reviews)
            avg_sentiment = total_sentiment / total_reviews
            
            # Calculate sentiment distribution
            positive = sum(1 for r in reviews if r["sentiment_score"] >= 0.7) / total_reviews
            neutral = sum(1 for r in reviews if 0.3 <= r["sentiment_score"] < 0.7) / total_reviews
            negative = sum(1 for r in reviews if r["sentiment_score"] < 0.3) / total_reviews
            
            # Determine sentiment type
            if avg_sentiment >= 0.7:
                sentiment_type = "positive"
            elif avg_sentiment >= 0.3:
                sentiment_type = "neutral"
            else:
                sentiment_type = "negative"
                
            return {
                "score": avg_sentiment,
                "type": sentiment_type,
                "reviews_count": total_reviews,
                "distribution": {
                    "positive": positive,
                    "neutral": neutral,
                    "negative": negative
                }
            }
        except Exception as e:
            logger.error(f"Error calculating sentiment for product {product_id}: {str(e)}")
            return SentimentAnalysis().dict() 