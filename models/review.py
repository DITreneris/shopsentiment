import sqlite3
import os
from datetime import datetime

class Review:
    """
    Model representing a product review in the shopsentiment system.
    """
    def __init__(self, id=None, product_id=None, author=None, rating=None, text=None, 
                 title=None, verified_purchase=False, created_at=None, updated_at=None):
        self.id = id
        self.product_id = product_id
        self.author = author
        self.rating = rating
        self.text = text
        self.title = title
        self.verified_purchase = verified_purchase
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        
        # These will be populated by the sentiment service
        self.sentiment_score = None
        self.sentiment_label = None

    @staticmethod
    def get_db_connection():
        """Get a connection to the SQLite database."""
        db_path = os.environ.get('DATABASE_PATH', 'data/shopsentiment.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def get_all_reviews(cls):
        """
        Get all reviews from the database.
        
        Returns:
            list: List of Review objects
        """
        conn = cls.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM reviews
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        reviews = []
        for row in rows:
            review = cls._row_to_review(row)
            reviews.append(review)
            
        return reviews

    @classmethod
    def get_by_id(cls, review_id):
        """
        Get a review by its ID.
        
        Args:
            review_id: The ID of the review to retrieve
            
        Returns:
            Review: Review object if found, None otherwise
        """
        conn = cls.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM reviews WHERE id = ?
        ''', (review_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        return cls._row_to_review(row)

    @classmethod
    def get_by_product_id(cls, product_id, limit=None, sentiment_label=None):
        """
        Get all reviews for a specific product.
        
        Args:
            product_id: The ID of the product to get reviews for
            limit: Optional limit on the number of reviews to return
            sentiment_label: Optional filter for reviews by sentiment label
            
        Returns:
            list: List of Review objects for the specified product
        """
        conn = cls.get_db_connection()
        cursor = conn.cursor()
        
        query = 'SELECT r.*, s.score, s.label FROM reviews r LEFT JOIN review_sentiment s ON r.id = s.review_id WHERE r.product_id = ?'
        params = [product_id]
        
        if sentiment_label:
            query += ' AND s.label = ?'
            params.append(sentiment_label)
            
        query += ' ORDER BY r.created_at DESC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        reviews = []
        for row in rows:
            review = cls._row_to_review(row)
            if 'score' in row.keys() and row['score'] is not None:
                review.sentiment_score = row['score']
            if 'label' in row.keys() and row['label'] is not None:
                review.sentiment_label = row['label']
            reviews.append(review)
            
        return reviews

    @classmethod
    def get_pending_sentiment_analysis(cls, limit=100):
        """
        Get reviews that need sentiment analysis (reviews without sentiment scores).
        
        Args:
            limit: Maximum number of reviews to retrieve
            
        Returns:
            list: List of Review objects without sentiment scores
        """
        conn = cls.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.* FROM reviews r
            LEFT JOIN review_sentiment s ON r.id = s.review_id
            WHERE s.review_id IS NULL
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        reviews = []
        for row in rows:
            reviews.append(cls._row_to_review(row))
            
        return reviews

    @classmethod
    def _row_to_review(cls, row):
        """Convert a database row to a Review object."""
        return cls(
            id=row['id'],
            product_id=row['product_id'],
            author=row['author'],
            rating=row['rating'],
            text=row['text'],
            title=row['title'],
            verified_purchase=bool(row['verified_purchase']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    def save(self):
        """
        Save the review to the database. Creates a new record if ID is None,
        otherwise updates the existing record.
        
        Returns:
            int: The ID of the saved review
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        if self.id is None:
            # Insert new review
            cursor.execute('''
                INSERT INTO reviews (product_id, author, rating, text, title, 
                                    verified_purchase, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.product_id, self.author, self.rating, self.text, 
                 self.title, self.verified_purchase, now, now))
            self.id = cursor.lastrowid
        else:
            # Update existing review
            cursor.execute('''
                UPDATE reviews
                SET product_id = ?, author = ?, rating = ?, text = ?, title = ?,
                    verified_purchase = ?, updated_at = ?
                WHERE id = ?
            ''', (self.product_id, self.author, self.rating, self.text, 
                 self.title, self.verified_purchase, now, self.id))
        
        conn.commit()
        conn.close()
        
        return self.id

    def delete(self):
        """
        Delete the review from the database.
        
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if self.id is None:
            return False
            
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM reviews WHERE id = ?', (self.id,))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0

    def to_dict(self):
        """
        Convert the review to a dictionary for JSON serialization.
        
        Returns:
            dict: Dictionary representation of the review
        """
        return {
            'id': self.id,
            'product_id': self.product_id,
            'author': self.author,
            'rating': self.rating,
            'text': self.text,
            'title': self.title,
            'verified_purchase': self.verified_purchase,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label
        } 