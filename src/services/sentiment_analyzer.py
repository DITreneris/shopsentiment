"""
Sentiment Analysis Service

This module provides sentiment analysis functionality with fallbacks
if NLTK is not available.
"""

import logging
import re
from typing import Dict, List, Union, Optional

# Initialize logger
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Sentiment analyzer that doesn't depend on NLTK.
    Provides basic sentiment analysis functionality using word lists.
    """
    
    def __init__(self, model_type: str = 'default'):
        """
        Initialize the sentiment analyzer.
        
        Args:
            model_type: Type of model to use (ignored in this implementation)
        """
        self.model_type = model_type.lower()
        
        # Fallback stopwords
        self.stopwords = {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
            'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him',
            'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
            'itself', 'they', 'them', 'their', 'theirs', 'themselves',
            'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
            'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
            'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while',
            'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
            'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over',
            'under', 'again', 'further', 'then', 'once', 'here', 'there',
            'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each',
            'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's',
            't', 'can', 'will', 'just', 'don', 'should', 'now'
        }
        
        # Simple positive/negative word lists
        self.positive_words = {
            'good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic',
            'wonderful', 'best', 'love', 'perfect', 'recommend', 'satisfied',
            'happy', 'helpful', 'positive', 'nice', 'quality', 'impressive',
            'well', 'liked', 'better', 'comfortable', 'enjoyable', 'beautiful',
            'worth', 'favorite', 'pleased', 'fast', 'easy', 'reliable'
        }
        
        self.negative_words = {
            'bad', 'poor', 'terrible', 'awful', 'horrible', 'worst', 'hate',
            'disappointing', 'disappointed', 'waste', 'useless', 'difficult',
            'expensive', 'cheap', 'problem', 'issues', 'broken', 'slow', 'hard',
            'negative', 'wrong', 'fail', 'failed', 'avoid', 'uncomfortable',
            'unreliable', 'mistake', 'dislike', 'overpriced', 'complaint'
        }
        
        logger.info(f"Simple sentiment analyzer initialized (fallback mode)")
    
    def analyze_text(self, text: str) -> Dict[str, Union[float, str]]:
        """
        Analyze sentiment of given text using word counting.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment score and label
        """
        if not text or not isinstance(text, str):
            logger.warning("Empty or invalid text provided to analyze_text")
            return {'score': 0, 'label': 'Neutral'}
        
        return self._analyze_with_word_count(text)
    
    def analyze(self, text: str) -> Dict[str, Union[float, str]]:
        """
        Alias for analyze_text to ensure backward compatibility.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment score and label
        """
        return self.analyze_text(text)
    
    def _analyze_with_word_count(self, text: str) -> Dict[str, Union[float, str]]:
        """
        Analyze sentiment by counting positive and negative words.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment score and label
        """
        try:
            # Convert to lowercase and split into words
            words = re.findall(r'\b\w+\b', text.lower())
            
            # Filter out stopwords
            words = [word for word in words if word not in self.stopwords]
            
            # Count positive and negative words
            positive_count = sum(1 for word in words if word in self.positive_words)
            negative_count = sum(1 for word in words if word in self.negative_words)
            total_words = len(words)
            
            # Calculate score
            if total_words > 0:
                score = (positive_count - negative_count) / total_words
            else:
                score = 0
            
            # Determine label
            if score > 0.05:
                label = 'Positive'
            elif score < -0.05:
                label = 'Negative'
            else:
                label = 'Neutral'
                
            return {
                'score': score,
                'label': label,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'total_words': total_words
            }
        except Exception as e:
            logger.error(f"Error in word count sentiment analysis: {str(e)}")
            return {
                'score': 0,
                'label': 'Neutral',
                'error': str(e)
            }

# Create a singleton instance
sentiment_analyzer = SentimentAnalyzer() 