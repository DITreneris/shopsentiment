import uuid
from datetime import datetime
import json
import os
import re

class Review:
    def __init__(self, id=None, product_id=None, text=None, rating=None, date=None,
                 sentiment=None, created_at=None):
        self.id = id or str(uuid.uuid4())
        self.product_id = product_id
        self.text = text
        self.rating = rating
        self.date = date
        self.sentiment = sentiment or self.analyze_sentiment()
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'text': self.text,
            'rating': self.rating,
            'date': self.date,
            'sentiment': self.sentiment,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            product_id=data.get('product_id'),
            text=data.get('text'),
            rating=data.get('rating'),
            date=data.get('date'),
            sentiment=data.get('sentiment'),
            created_at=data.get('created_at')
        )
    
    @classmethod
    def get_by_id(cls, review_id, reviews_db):
        for review_data in reviews_db:
            if review_data.get('id') == review_id:
                return cls.from_dict(review_data)
        return None
    
    @classmethod
    def get_by_product_id(cls, product_id, reviews_db):
        reviews = []
        for review_data in reviews_db:
            if review_data.get('product_id') == product_id:
                reviews.append(cls.from_dict(review_data))
        return reviews
    
    def analyze_sentiment(self):
        """
        Simple rule-based sentiment analysis
        Returns a sentiment score between -1 (negative) and 1 (positive)
        """
        if not self.text:
            return 0.0
            
        # Convert text to lowercase for easier processing
        text = self.text.lower()
        
        # Basic positive and negative word lists
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic',
            'wonderful', 'best', 'love', 'happy', 'satisfied', 'recommend',
            'like', 'perfect', 'enjoy', 'comfortable', 'pleased', 'quality',
            'positive', 'fast', 'reliable', 'helpful', 'exceptional', 'favorite',
            'impressive'
        ]
        
        negative_words = [
            'bad', 'terrible', 'horrible', 'awful', 'poor', 'worst',
            'hate', 'disappointing', 'disappointed', 'waste', 'problem',
            'issue', 'defective', 'negative', 'slow', 'unreliable', 'broken',
            'useless', 'complaint', 'avoid', 'unhappy', 'overpriced', 'expensive',
            'difficult', 'faulty'
        ]
        
        # Count positive and negative words
        positive_count = sum(1 for word in re.findall(r'\b\w+\b', text) if word in positive_words)
        negative_count = sum(1 for word in re.findall(r'\b\w+\b', text) if word in negative_words)
        
        # If rating is available, incorporate it into sentiment calculation
        rating_factor = 0
        if self.rating is not None:
            try:
                # Convert rating to a scale from -1 to 1
                # Assuming rating is on a scale of 1-5
                rating_factor = (float(self.rating) - 3) / 2
            except (ValueError, TypeError):
                # If rating can't be converted, ignore it
                pass
        
        # Calculate sentiment score, incorporating both text analysis and rating
        if positive_count == 0 and negative_count == 0:
            # If no sentiment words found, use rating only (if available)
            return rating_factor
        else:
            # Combine word-based sentiment with rating factor
            text_sentiment = (positive_count - negative_count) / (positive_count + negative_count)
            if rating_factor != 0:
                # Weight: 70% text analysis, 30% rating
                return 0.7 * text_sentiment + 0.3 * rating_factor
            else:
                return text_sentiment
    
    @staticmethod
    def get_reviews_db():
        """Load reviews from JSON file or create empty list if file doesn't exist"""
        reviews_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    '..', '..', 'data', 'reviews.json')
        
        if not os.path.exists(reviews_file):
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(reviews_file), exist_ok=True)
            # Create empty reviews file
            with open(reviews_file, 'w') as f:
                json.dump([], f)
            return []
        
        try:
            with open(reviews_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    @staticmethod
    def save_reviews_db(reviews_db):
        """Save reviews to JSON file"""
        reviews_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    '..', '..', 'data', 'reviews.json')
        
        with open(reviews_file, 'w') as f:
            json.dump(reviews_db, f, indent=2) 