import sqlite3
import json
import os
from datetime import datetime

class Product:
    """
    Model representing a product in the shopsentiment system.
    """
    def __init__(self, id=None, name=None, category=None, description=None, price=None, 
                 image_url=None, shop_name=None, shop_url=None, created_at=None, updated_at=None):
        self.id = id
        self.name = name
        self.category = category
        self.description = description
        self.price = price
        self.image_url = image_url
        self.shop_name = shop_name
        self.shop_url = shop_url
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        
        # These will be populated by the sentiment service
        self.sentiment_score = None
        self.sentiment_label = None
        self.review_count = None

    @staticmethod
    def get_db_connection():
        """Get a connection to the SQLite database."""
        db_path = os.environ.get('DATABASE_PATH', 'data/shopsentiment.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def get_all_products(cls):
        """
        Get all products from the database.
        
        Returns:
            list: List of Product objects
        """
        conn = cls.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM products
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            product = cls(
                id=row['id'],
                name=row['name'],
                category=row['category'],
                description=row['description'],
                price=row['price'],
                image_url=row['image_url'],
                shop_name=row['shop_name'],
                shop_url=row['shop_url'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            )
            products.append(product)
            
        return products

    @classmethod
    def get_by_id(cls, product_id):
        """
        Get a product by its ID.
        
        Args:
            product_id: The ID of the product to retrieve
            
        Returns:
            Product: Product object if found, None otherwise
        """
        conn = cls.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM products WHERE id = ?
        ''', (product_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        return cls(
            id=row['id'],
            name=row['name'],
            category=row['category'],
            description=row['description'],
            price=row['price'],
            image_url=row['image_url'],
            shop_name=row['shop_name'],
            shop_url=row['shop_url'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    @classmethod
    def get_by_category(cls, category):
        """
        Get all products in a specific category.
        
        Args:
            category: The category to filter by
            
        Returns:
            list: List of Product objects in the specified category
        """
        conn = cls.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM products WHERE category = ?
        ''', (category,))
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            product = cls(
                id=row['id'],
                name=row['name'],
                category=row['category'],
                description=row['description'],
                price=row['price'],
                image_url=row['image_url'],
                shop_name=row['shop_name'],
                shop_url=row['shop_url'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            )
            products.append(product)
            
        return products

    def save(self):
        """
        Save the product to the database. Creates a new record if ID is None,
        otherwise updates the existing record.
        
        Returns:
            int: The ID of the saved product
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        if self.id is None:
            # Insert new product
            cursor.execute('''
                INSERT INTO products (name, category, description, price, image_url, 
                                      shop_name, shop_url, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.name, self.category, self.description, self.price, 
                 self.image_url, self.shop_name, self.shop_url, now, now))
            self.id = cursor.lastrowid
        else:
            # Update existing product
            cursor.execute('''
                UPDATE products
                SET name = ?, category = ?, description = ?, price = ?, image_url = ?,
                    shop_name = ?, shop_url = ?, updated_at = ?
                WHERE id = ?
            ''', (self.name, self.category, self.description, self.price, 
                 self.image_url, self.shop_name, self.shop_url, now, self.id))
        
        conn.commit()
        conn.close()
        
        return self.id

    def delete(self):
        """
        Delete the product from the database.
        
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if self.id is None:
            return False
            
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM products WHERE id = ?', (self.id,))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0

    def to_dict(self):
        """
        Convert the product to a dictionary for JSON serialization.
        
        Returns:
            dict: Dictionary representation of the product
        """
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'price': self.price,
            'image_url': self.image_url,
            'shop_name': self.shop_name,
            'shop_url': self.shop_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label,
            'review_count': self.review_count
        } 