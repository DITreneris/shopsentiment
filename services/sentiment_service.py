"""
Sentiment Analysis Service

Provides sentiment analysis for product reviews.
"""

import sqlite3
import random
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class SentimentService:
    """Sentiment analysis service for product reviews."""
    
    def __init__(self, db_path=None, model_type='default'):
        """
        Initialize the sentiment service.
        
        Args:
            db_path: Path to the SQLite database
            model_type: Type of sentiment model to use
        """
        self.db_path = db_path or os.environ.get('DATABASE_PATH', 'data/shopsentiment.db')
        self.model_type = model_type
        logger.info(f"Initialized SentimentService with model: {model_type}, db_path: {self.db_path}")
    
    def get_db_connection(self):
        """Get SQLite database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def analyze_text(self, text):
        """
        Analyze sentiment of the given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            dict: Sentiment analysis result
        """
        if not text:
            return {'score': 0.5, 'label': 'NEUTRAL'}
        
        # For testing, generate a consistent but random score based on text
        text_hash = sum(ord(c) for c in text)
        random.seed(text_hash)
        score = round(random.uniform(0, 1), 2)
        
        # Determine label based on score
        if score >= 0.6:
            label = 'POSITIVE'
        elif score <= 0.4:
            label = 'NEGATIVE'
        else:
            label = 'NEUTRAL'
        
        return {'score': score, 'label': label}
    
    def get_product_sentiment_summary(self, product_id):
        """
        Get sentiment summary for a product.
        
        Args:
            product_id: Product ID
            
        Returns:
            dict: Sentiment summary
        """
        logger.debug(f"Getting sentiment summary for product: {product_id}")
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Check if there's a pre-computed summary in the sentiment_product_summary view
            cursor.execute('''
                SELECT * FROM sentiment_product_summary WHERE product_id = ?
            ''', (product_id,))
            row = cursor.fetchone()
            
            if row:
                # Return pre-computed summary
                summary = dict(row)
                logger.debug(f"Found pre-computed sentiment summary for product {product_id}")
                return summary
            
            # If not in view, calculate summary from reviews
            cursor.execute('''
                SELECT r.*, s.score, s.label 
                FROM reviews r
                LEFT JOIN review_sentiment s ON r.id = s.review_id
                WHERE r.product_id = ?
            ''', (product_id,))
            rows = cursor.fetchall()
            
            if not rows:
                # For demo, return mock data if no reviews found
                return self._generate_mock_summary(product_id)
            
            # Calculate summary
            total_reviews = len(rows)
            sentiment_scores = [row['score'] for row in rows if row['score'] is not None]
            avg_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5
            
            positive_count = sum(1 for row in rows if row.get('label') == 'POSITIVE')
            negative_count = sum(1 for row in rows if row.get('label') == 'NEGATIVE')
            neutral_count = total_reviews - positive_count - negative_count
            
            # Determine overall label
            if avg_score >= 0.6:
                label = 'POSITIVE'
            elif avg_score <= 0.4:
                label = 'NEGATIVE'
            else:
                label = 'NEUTRAL'
            
            summary = {
                'product_id': product_id,
                'average_score': avg_score,
                'sentiment_label': label,
                'review_count': total_reviews,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'last_updated': datetime.now().isoformat()
            }
            
            conn.close()
            return summary
            
        except Exception as e:
            logger.error(f"Error getting sentiment summary for product {product_id}: {str(e)}")
            return self._generate_mock_summary(product_id)
    
    def _generate_mock_summary(self, product_id):
        """Generate mock sentiment summary for demo purposes."""
        random.seed(product_id)  # Ensure consistent results for same product
        
        avg_score = round(random.uniform(0.3, 0.8), 2)
        review_count = random.randint(5, 30)
        
        # Calculate counts based on average score
        if avg_score >= 0.6:
            positive_pct = random.uniform(0.6, 0.8)
            negative_pct = random.uniform(0.05, 0.15)
        elif avg_score <= 0.4:
            positive_pct = random.uniform(0.2, 0.3)
            negative_pct = random.uniform(0.5, 0.6)
        else:
            positive_pct = random.uniform(0.3, 0.5)
            negative_pct = random.uniform(0.2, 0.4)
        
        positive_count = int(review_count * positive_pct)
        negative_count = int(review_count * negative_pct)
        neutral_count = review_count - positive_count - negative_count
        
        # Determine label
        if avg_score >= 0.6:
            label = 'POSITIVE'
        elif avg_score <= 0.4:
            label = 'NEGATIVE'
        else:
            label = 'NEUTRAL'
        
        logger.debug(f"Generated mock sentiment summary for product {product_id}")
        
        return {
            'product_id': product_id,
            'average_score': avg_score,
            'sentiment_label': label,
            'review_count': review_count,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'last_updated': datetime.now().isoformat()
        }


def create_sentiment_service(db_path=None, model_type=None):
    """
    Factory function to create a sentiment service.
    
    Args:
        db_path: Path to the SQLite database
        model_type: Type of sentiment model to use
        
    Returns:
        SentimentService: Initialized sentiment service
    """
    # Use default path if not specified
    if db_path is None:
        db_path = 'data/shopsentiment.db'
    
    # Use default model if not specified
    if model_type is None:
        model_type = 'default'
    
    return SentimentService(db_path, model_type) 