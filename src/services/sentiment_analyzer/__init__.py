"""
Sentiment Analyzer Module

This module initializes and exports the sentiment analyzer instance.
"""

import logging
from ..sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)

# Create and export a singleton instance of the SentimentAnalyzer
try:
    sentiment_analyzer = SentimentAnalyzer()
    logger.info("Initialized sentiment analyzer")
except Exception as e:
    logger.error(f"Error initializing sentiment analyzer: {str(e)}")
    # Create a minimal fallback analyzer
    class FallbackSentimentAnalyzer:
        def analyze_text(self, text):
            return {'score': 0.5, 'label': 'Neutral'}
        
    sentiment_analyzer = FallbackSentimentAnalyzer()
    logger.warning("Using fallback sentiment analyzer due to initialization error") 