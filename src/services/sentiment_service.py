"""
Sentiment Analysis Service

This module provides service-level functionality for analyzing and managing
product review sentiments in the ShopSentiment application.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class SentimentService:
    """Service for handling sentiment analysis operations."""
    
    def __init__(self, db_path: str, model_type: Optional[str] = None):
        """
        Initialize the sentiment service.
        
        Args:
            db_path: Path to the SQLite database
            model_type: Type of sentiment analysis model to use
        """
        self.db_path = db_path
        self.model_type = model_type
        
        # Import the sentiment analyzer here to avoid circular imports
        from src.services.sentiment_analyzer import sentiment_analyzer
        self.analyzer = sentiment_analyzer
        
        logger.info(f"Initialized sentiment service with database at {db_path}")
    
    def analyze_text(self, text: str) -> Dict[str, Union[float, str]]:
        """
        Analyze sentiment of the provided text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary containing sentiment score and label
        """
        return self.analyzer.analyze(text)
    
    def get_product_sentiment_summary(self, product_id: int) -> Optional[Dict]:
        """
        Get sentiment summary for a specific product.
        
        Args:
            product_id: ID of the product
            
        Returns:
            Dictionary containing sentiment summary or None if not found
        """
        # Mock implementation since we don't have a database yet
        if not product_id:
            return None
            
        return {
            'product_id': product_id,
            'review_count': 10,
            'average_sentiment': 0.75,
            'positive_count': 7,
            'neutral_count': 2,
            'negative_count': 1
        }
    
    def get_all_products_sentiment(self) -> List[Dict]:
        """
        Get sentiment summary for all products.
        
        Returns:
            List of dictionaries containing product sentiment summaries
        """
        # Mock implementation since we don't have a database yet
        return [
            {
                'id': 1,
                'name': 'Sample Product 1',
                'category': 'Electronics',
                'review_count': 10,
                'average_sentiment': 0.75,
                'positive_count': 7,
                'neutral_count': 2,
                'negative_count': 1
            },
            {
                'id': 2,
                'name': 'Sample Product 2',
                'category': 'Clothing',
                'review_count': 5,
                'average_sentiment': 0.4,
                'positive_count': 2,
                'neutral_count': 1,
                'negative_count': 2
            }
        ]


def create_sentiment_service(db_path: str = None, model_type: str = None) -> SentimentService:
    """
    Create a sentiment service based on configuration.
    
    Args:
        db_path: Path to the SQLite database (optional)
        model_type: Type of sentiment analysis model to use (optional)
    
    Returns:
        SentimentService instance
    """
    if db_path is None:
        # Try to get db_path from configuration
        try:
            from flask import current_app
            db_path = current_app.config.get('DATABASE_PATH', 'data/shopsentiment.db')
        except (ImportError, RuntimeError):
            # Default if config not available
            db_path = os.environ.get('DATABASE_PATH', 'data/shopsentiment.db')
    
    if model_type is None:
        # Try to get model type from configuration
        try:
            from flask import current_app
            model_type = current_app.config.get('SENTIMENT_ANALYSIS_MODEL', 'default')
        except (ImportError, RuntimeError):
            # Default if config not available
            model_type = os.environ.get('SENTIMENT_MODEL', 'default')
    
    logger.info(f"Creating sentiment service with model type: {model_type}")
    return SentimentService(db_path, model_type) 