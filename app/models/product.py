import uuid
from datetime import datetime
import json
import os

class Product:
    def __init__(self, id=None, platform=None, product_id=None, url=None, 
                 created_at=None, user_id=None):
        self.id = id or str(uuid.uuid4())
        self.platform = platform
        self.product_id = product_id
        self.url = url
        self.created_at = created_at or datetime.now().isoformat()
        self.user_id = user_id
    
    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'product_id': self.product_id,
            'url': self.url,
            'created_at': self.created_at,
            'user_id': self.user_id
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            platform=data.get('platform'),
            product_id=data.get('product_id'),
            url=data.get('url'),
            created_at=data.get('created_at'),
            user_id=data.get('user_id')
        )
    
    @classmethod
    def get_by_id(cls, product_id, products_db):
        for product_data in products_db:
            if product_data.get('id') == product_id:
                return cls.from_dict(product_data)
        return None
    
    @staticmethod
    def get_products_db():
        """Load products from JSON file or create empty list if file doesn't exist"""
        products_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                     '..', '..', 'data', 'products.json')
        
        if not os.path.exists(products_file):
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(products_file), exist_ok=True)
            # Create empty products file
            with open(products_file, 'w') as f:
                json.dump([], f)
            return []
        
        try:
            with open(products_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    @staticmethod
    def save_products_db(products_db):
        """Save products to JSON file"""
        products_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                     '..', '..', 'data', 'products.json')
        
        with open(products_file, 'w') as f:
            json.dump(products_db, f, indent=2) 