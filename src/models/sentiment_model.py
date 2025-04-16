"""
Sentiment Analysis Model for Product Reviews

This module provides functionality to analyze sentiment in product reviews
using natural language processing techniques.
"""

import logging
import os
import re
import sqlite3
from typing import Dict, List, Tuple, Union, Optional

# Initialize logger
logger = logging.getLogger(__name__)

# Try to load NLTK libraries but provide fallbacks if missing
nltk_available = True
try:
    from textblob import TextBlob
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.sentiment.vader import SentimentIntensityAnalyzer

    # Check if required NLTK data is available
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        logger.warning("NLTK data not available. Using fallback sentiment analysis.")
        nltk_available = False
except ImportError:
    logger.warning("NLTK or TextBlob not available. Using fallback sentiment analysis.")
    nltk_available = False

class SentimentAnalyzer:
    """
    Sentiment analyzer for product reviews.
    
    Analyzes sentiment in text using NLTK and TextBlob, or falls back
    to a simple word-based approach if NLTK is not available.
    """
    
    def __init__(self, model_type: str = 'default'):
        """
        Initialize the sentiment analyzer.
        
        Args:
            model_type: Type of model to use ('vader', 'textblob', or 'default')
        """
        self.model_type = model_type.lower()
        self.vader_analyzer = None
        
        # Initialize analyzers if NLTK is available
        if nltk_available:
            if self.model_type in ('vader', 'default'):
                try:
                    self.vader_analyzer = SentimentIntensityAnalyzer()
                except Exception as e:
                    logger.error(f"Error initializing VADER: {str(e)}")
                    
            # Common English stopwords to exclude from analysis
            try:
                self.stopwords = set(stopwords.words('english'))
            except Exception:
                # Fallback stopwords if NLTK corpus not available
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
        else:
            # Fallback stopwords if NLTK not available
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
            
        # Simple positive/negative word lists for fallback
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
        
        logger.info(f"Sentiment analyzer initialized with model type: {model_type}")
        if not nltk_available:
            logger.warning("Using fallback word-based sentiment analysis")
    
    def analyze_text(self, text: str) -> Dict[str, Union[float, str]]:
        """
        Analyze sentiment of given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment score and label
        """
        if not text or not isinstance(text, str):
            logger.warning("Empty or invalid text provided to analyze_text")
            return {'score': 0, 'label': 'Neutral'}
        
        # Use VADER if available and selected
        if nltk_available and self.vader_analyzer and self.model_type in ('vader', 'default'):
            try:
                return self._analyze_with_vader(text)
            except Exception as e:
                logger.error(f"VADER analysis error: {str(e)}")
                # Fall back to TextBlob
        
        # Use TextBlob if available and VADER failed or not selected
        if nltk_available and self.model_type in ('textblob', 'default'):
            try:
                return self._analyze_with_textblob(text)
            except Exception as e:
                logger.error(f"TextBlob analysis error: {str(e)}")
                # Fall back to word count method
        
        # Fallback to simple word count method
        return self._analyze_with_word_count(text)
    
    def _analyze_with_vader(self, text: str) -> Dict[str, Union[float, str]]:
        """
        Analyze sentiment using VADER.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment score and label
        """
        scores = self.vader_analyzer.polarity_scores(text)
        compound = scores['compound']
        
        if compound >= 0.05:
            label = 'Positive'
        elif compound <= -0.05:
            label = 'Negative'
        else:
            label = 'Neutral'
        
        return {
            'score': compound,
            'label': label,
            'positive': scores['pos'],
            'negative': scores['neg'],
            'neutral': scores['neu']
        }
    
    def _analyze_with_textblob(self, text: str) -> Dict[str, Union[float, str]]:
        """
        Analyze sentiment using TextBlob.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment score and label
        """
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
        if polarity > 0.1:
            label = 'Positive'
        elif polarity < -0.1:
            label = 'Negative'
        else:
            label = 'Neutral'
        
        return {
            'score': polarity,
            'label': label,
            'subjectivity': blob.sentiment.subjectivity
        }
    
    def _analyze_with_word_count(self, text: str) -> Dict[str, Union[float, str]]:
        """
        Analyze sentiment by counting positive and negative words.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment score and label
        """
        # Convert to lowercase and split into words
        if not nltk_available:
            # Simple tokenization
            words = re.findall(r'\b\w+\b', text.lower())
        else:
            try:
                # NLTK tokenization if available
                words = word_tokenize(text.lower())
            except Exception:
                # Fallback to simple tokenization
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

def create_sentiment_analyzer(model_type: Optional[str] = None) -> SentimentAnalyzer:
    """
    Create a sentiment analyzer based on configuration.
    
    Args:
        model_type: Type of sentiment analysis model to use
                   (defaults to configuration if None)
    
    Returns:
        SentimentAnalyzer instance
    """
    if model_type is None:
        # Try to get model type from configuration
        try:
            from config import config
            model_type = getattr(config, 'SENTIMENT_ANALYSIS_MODEL', 'textblob')
        except (ImportError, AttributeError):
            model_type = 'textblob'
    
    logger.info(f"Creating sentiment analyzer with model type: {model_type}")
    return SentimentAnalyzer(model_type) 