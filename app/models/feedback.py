"""
Feedback model for ShopSentiment application.
"""

from datetime import datetime
from bson.objectid import ObjectId


class Feedback:
    """Feedback model representing user feedback on various entities."""
    
    def __init__(self, data=None):
        """Initialize a new Feedback object.
        
        Args:
            data (dict, optional): Dictionary with feedback data.
        """
        if data is None:
            data = {}
            
        self.id = data.get('_id', ObjectId())
        self.entity_type = data.get('entity_type', '')
        self.entity_id = data.get('entity_id', '')
        self.rating = data.get('rating', 0)
        self.comment = data.get('comment', '')
        self.user_id = data.get('user_id')
        self.tags = data.get('tags', [])
        self.created_at = data.get('created_at', datetime.now())
        self.updated_at = data.get('updated_at', datetime.now())
    
    def to_dict(self):
        """Convert feedback to dictionary.
        
        Returns:
            dict: Dictionary representation of the feedback.
        """
        return {
            '_id': self.id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'rating': self.rating,
            'comment': self.comment,
            'user_id': self.user_id,
            'tags': self.tags,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a Feedback object from a dictionary.
        
        Args:
            data (dict): Dictionary with feedback data.
            
        Returns:
            Feedback: New Feedback object.
        """
        return cls(data) 