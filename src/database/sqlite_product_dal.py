"""
SQLite Product Data Access Layer (DAL) for the ShopSentiment application.
Handles database operations related to products and reviews using SQLite.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.models.product import Product, Review, SentimentAnalysis
from src.database.sqlite_connection import get_sqlite_db

logger = logging.getLogger(__name__)


class SQLiteProductDAL:
    """Data Access Layer for Product operations using SQLite."""
    
    def __init__(self):
        """Initialize the DAL with SQLite connection."""
        self.db = get_sqlite_db()
    
    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a product by ID."""
        try:
            cursor = self.db.cursor()
            
            # Get product data
            cursor.execute(
                "SELECT id, name, description, category, price, created_at FROM products WHERE id = ?",
                (product_id,)
            )
            product_data = cursor.fetchone()
            
            if not product_data:
                return None
            
            # Convert to dictionary
            product = dict(product_data)
            
            # Get reviews for the product
            cursor.execute(
                """
                SELECT id, product_id, user_name, rating, text, sentiment_score, created_at 
                FROM reviews WHERE product_id = ?
                """,
                (product_id,)
            )
            reviews = [dict(row) for row in cursor.fetchall()]
            product["reviews"] = reviews
            
            # Calculate sentiment data
            if reviews:
                product["sentiment"] = self._calculate_product_sentiment(reviews)
            else:
                product["sentiment"] = SentimentAnalysis().dict()
                
            return product
        except Exception as e:
            logger.error(f"Error fetching product {product_id}: {str(e)}")
            return None
    
    def get_products(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve multiple products with pagination."""
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT id, name, description, category, price, created_at 
                FROM products ORDER BY created_at DESC LIMIT ? OFFSET ?
                """,
                (limit, skip)
            )
            
            products = []
            for row in cursor.fetchall():
                product = dict(row)
                
                # Get review count
                cursor.execute(
                    "SELECT COUNT(*) as count FROM reviews WHERE product_id = ?",
                    (product["id"],)
                )
                review_count = cursor.fetchone()["count"]
                
                # Get average sentiment
                if review_count > 0:
                    cursor.execute(
                        "SELECT AVG(sentiment_score) as avg_score FROM reviews WHERE product_id = ?",
                        (product["id"],)
                    )
                    avg_sentiment = cursor.fetchone()["avg_score"]
                    
                    # Add sentiment data
                    product["sentiment"] = {
                        "score": avg_sentiment,
                        "reviews_count": review_count,
                        "type": "positive" if avg_sentiment >= 0.7 else "neutral" if avg_sentiment >= 0.3 else "negative"
                    }
                else:
                    product["sentiment"] = SentimentAnalysis().dict()
                
                products.append(product)
                
            return products
        except Exception as e:
            logger.error(f"Error fetching products: {str(e)}")
            return []
    
    def search_products(self, query: str, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """Search products by text query."""
        try:
            cursor = self.db.cursor()
            search_term = f"%{query}%"
            
            cursor.execute(
                """
                SELECT id, name, description, category, price, created_at 
                FROM products 
                WHERE name LIKE ? OR description LIKE ?
                ORDER BY created_at DESC LIMIT ? OFFSET ?
                """,
                (search_term, search_term, limit, skip)
            )
            
            products = []
            for row in cursor.fetchall():
                product = dict(row)
                
                # Get review count and sentiment
                cursor.execute(
                    "SELECT COUNT(*) as count FROM reviews WHERE product_id = ?",
                    (product["id"],)
                )
                review_count = cursor.fetchone()["count"]
                
                if review_count > 0:
                    cursor.execute(
                        "SELECT AVG(sentiment_score) as avg_score FROM reviews WHERE product_id = ?",
                        (product["id"],)
                    )
                    avg_sentiment = cursor.fetchone()["avg_score"]
                    
                    # Add sentiment data
                    product["sentiment"] = {
                        "score": avg_sentiment,
                        "reviews_count": review_count,
                        "type": "positive" if avg_sentiment >= 0.7 else "neutral" if avg_sentiment >= 0.3 else "negative"
                    }
                else:
                    product["sentiment"] = SentimentAnalysis().dict()
                
                products.append(product)
                
            return products
        except Exception as e:
            logger.error(f"Error searching products with query '{query}': {str(e)}")
            return []
    
    def create_product(self, product: Product) -> Optional[int]:
        """Create a new product."""
        try:
            cursor = self.db.cursor()
            
            cursor.execute(
                """
                INSERT INTO products (name, description, category, price, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    product.name,
                    product.description,
                    product.category,
                    product.price
                )
            )
            
            self.db.commit()
            return cursor.lastrowid
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating product: {str(e)}")
            return None
    
    def update_product(self, product_id: int, product_data: Dict[str, Any]) -> bool:
        """Update a product's information."""
        try:
            cursor = self.db.cursor()
            
            # Build the update query dynamically
            update_fields = []
            params = []
            
            for field, value in product_data.items():
                if field in ["name", "description", "category", "price"]:
                    update_fields.append(f"{field} = ?")
                    params.append(value)
            
            if not update_fields:
                return False
                
            params.append(product_id)  # For the WHERE clause
            
            query = f"""
                UPDATE products 
                SET {', '.join(update_fields)} 
                WHERE id = ?
            """
            
            cursor.execute(query, params)
            self.db.commit()
            
            return cursor.rowcount > 0
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating product {product_id}: {str(e)}")
            return False
    
    def delete_product(self, product_id: int) -> bool:
        """Delete a product and its reviews."""
        try:
            cursor = self.db.cursor()
            
            # Delete reviews first (due to foreign key constraint)
            cursor.execute("DELETE FROM reviews WHERE product_id = ?", (product_id,))
            
            # Delete the product
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            self.db.commit()
            
            return cursor.rowcount > 0
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting product {product_id}: {str(e)}")
            return False
    
    def add_review(self, product_id: int, review: Review) -> bool:
        """Add a review to a product."""
        try:
            cursor = self.db.cursor()
            
            cursor.execute(
                """
                INSERT INTO reviews (product_id, user_name, rating, text, sentiment_score, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    product_id,
                    review.user_name,
                    review.rating,
                    review.text,
                    review.sentiment_score
                )
            )
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding review to product {product_id}: {str(e)}")
            return False
    
    def _calculate_product_sentiment(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate sentiment data for a product based on its reviews."""
        try:
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
            logger.error(f"Error calculating sentiment: {str(e)}")
            return SentimentAnalysis().dict() 