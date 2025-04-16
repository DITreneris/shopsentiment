"""
Sentiment Analysis Service for the ShopSentiment application.
Analyzes text to determine sentiment score and type.
"""

import logging
import os
import random
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Load the appropriate sentiment analysis model based on configuration
MODEL_TYPE = os.environ.get('SENTIMENT_ANALYSIS_MODEL', 'default')


class SentimentAnalyzer:
    """Service for analyzing sentiment in text."""
    
    def __init__(self):
        """Initialize the sentiment analyzer with the appropriate model."""
        logger.info(f"Initializing SentimentAnalyzer with model type: {MODEL_TYPE}")
        
        # In a real implementation, this would load a proper machine learning model
        # For now, we're using a simple keyword-based approach for demonstration
        self.positive_words = [
            'good', 'great', 'excellent', 'amazing', 'love', 'best', 'perfect',
            'awesome', 'wonderful', 'fantastic', 'superb', 'outstanding'
        ]
        self.negative_words = [
            'bad', 'terrible', 'awful', 'hate', 'worst', 'poor', 'disappointing',
            'horrible', 'useless', 'inferior', 'mediocre', 'faulty'
        ]
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze the sentiment of the provided text.
        Returns a dictionary with sentiment score and type.
        """
        if not text:
            return {"score": 0.5, "type": "neutral"}
            
        try:
            text_lower = text.lower()
            
            # Count occurrences of positive and negative words
            positive_count = sum(1 for word in self.positive_words if word in text_lower)
            negative_count = sum(1 for word in self.negative_words if word in text_lower)
            
            # Calculate sentiment score (0 to 1)
            total = max(1, positive_count + negative_count)  # Avoid division by zero
            sentiment_score = min(1.0, max(0.0, (positive_count / total)))
            
            # Add some randomness for demonstration purposes
            if MODEL_TYPE == 'development':
                # More random for testing different scenarios
                sentiment_score = min(1.0, max(0.0, sentiment_score + random.uniform(-0.2, 0.2)))
            else:
                # Less random for production
                sentiment_score = min(1.0, max(0.0, sentiment_score + random.uniform(-0.1, 0.1)))
            
            # Determine sentiment type
            if sentiment_score >= 0.7:
                sentiment_type = 'positive'
            elif sentiment_score >= 0.3:
                sentiment_type = 'neutral'
            else:
                sentiment_type = 'negative'
                
            return {
                "score": round(sentiment_score, 2),
                "type": sentiment_type
            }
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {"score": 0.5, "type": "neutral"}


# Create a singleton instance
sentiment_analyzer = SentimentAnalyzer() 