from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import json

class User(UserMixin):
    """User model for authentication and storing user-specific data"""
    
    def __init__(self, id, username, email, password_hash, created_at=None, 
                 role='user', is_active=True):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at or datetime.now().isoformat()
        self.role = role
        self.is_active = is_active
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
            'role': self.role,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            username=data.get('username'),
            email=data.get('email'),
            password_hash=data.get('password_hash'),
            created_at=data.get('created_at'),
            role=data.get('role', 'user'),
            is_active=data.get('is_active', True)
        )
    
    @classmethod
    def get_by_id(cls, user_id, users_db):
        """Retrieve a user by ID from the database."""
        for user_data in users_db:
            if user_data.get('id') == user_id:
                return cls.from_dict(user_data)
        return None
    
    @classmethod
    def get_by_email(cls, email, users_db):
        """Retrieve a user by email from the database."""
        for user_data in users_db:
            if user_data.get('email') == email:
                return cls.from_dict(user_data)
        return None
    
    @classmethod
    def get_by_username(cls, username, users_db):
        """Retrieve a user by username from the database."""
        for user_data in users_db:
            if user_data.get('username') == username:
                return cls.from_dict(user_data)
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
            INSERT INTO users (id, username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (self.id, self.username, self.email, self.password_hash, self.created_at)
        )
        conn.commit()
    
    def update(self, conn):
        """Update the user in the database"""
        conn.execute(
            '''
            UPDATE users 
            SET username = ?, email = ?, password_hash = ?, last_login = ?
            WHERE id = ?
            ''',
            (self.username, self.email, self.password_hash, self.last_login, self.id)
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
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
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
            password_hash=password_hash,
            role=role
        )
        
        # Add user to database
        users_db.append(new_user.to_dict())
        
        return new_user 