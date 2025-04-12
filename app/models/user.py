from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import json

class User(UserMixin):
    """Simple User model for authentication"""
    
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            username=data.get('username'),
            email=data.get('email'),
            password_hash=data.get('password_hash')
        )
    
    @classmethod
    def get_by_id(cls, user_id, users_db):
        """Retrieve a user by ID from the database."""
        for user_data in users_db:
            if user_data.get('id') == user_id:
                return cls(
                    id=user_data.get('id'),
                    username=user_data.get('username'),
                    email=user_data.get('email'),
                    password_hash=user_data.get('password_hash')
                )
        return None
    
    @classmethod
    def get_by_email(cls, email, users_db):
        """Retrieve a user by email from the database."""
        for user_data in users_db:
            if user_data.get('email') == email:
                return cls(
                    id=user_data.get('id'),
                    username=user_data.get('username'),
                    email=user_data.get('email'),
                    password_hash=user_data.get('password_hash')
                )
        return None
    
    @classmethod
    def get_by_username(cls, username, users_db):
        """Retrieve a user by username from the database."""
        for user_data in users_db:
            if user_data.get('username') == username:
                return cls(
                    id=user_data.get('id'),
                    username=user_data.get('username'),
                    email=user_data.get('email'),
                    password_hash=user_data.get('password_hash')
                )
        return None
    
    @classmethod
    def _create_from_row(cls, row):
        """Create a User instance from a database row"""
        return cls(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash']
        )
    
    def save(self, conn):
        """Save the user to the database"""
        conn.execute(
            '''
            INSERT INTO users (id, username, email, password_hash)
            VALUES (?, ?, ?, ?)
            ''',
            (self.id, self.username, self.email, self.password_hash)
        )
        conn.commit()
    
    def update(self, conn):
        """Update the user in the database"""
        conn.execute(
            '''
            UPDATE users 
            SET username = ?, email = ?, password_hash = ?
            WHERE id = ?
            ''',
            (self.username, self.email, self.password_hash, self.id)
        )
        conn.commit()
    
    @staticmethod
    def create_table(conn):
        """Create the users table if it doesn't exist"""
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        conn.commit()
    
    @staticmethod
    def create_user(username, email, password, users_db, role='user'):
        # Create a new user
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)
        
        new_user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=password_hash
        )
        
        # Add user to database
        users_db.append(new_user.to_dict())
        
        return new_user 