from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class User(UserMixin):
    """User model for authentication and storing user-specific data"""
    
    def __init__(self, id, username, email, password_hash=None, password=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        
        if password:
            self.set_password(password)
        self.created_at = datetime.utcnow()
        self.last_login = None
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update the last login timestamp"""
        self.last_login = datetime.utcnow()
    
    @staticmethod
    def get_by_id(user_id, users_db):
        """Retrieve a user by ID from the database."""
        for user in users_db:
            if user['id'] == int(user_id):
                return User(
                    user['id'],
                    user['username'],
                    user['email'],
                    user['password_hash']
                )
        return None
    
    @staticmethod
    def get_by_email(email, users_db):
        """Retrieve a user by email from the database."""
        for user in users_db:
            if user['email'] == email:
                return User(
                    user['id'],
                    user['username'],
                    user['email'],
                    user['password_hash']
                )
        return None
    
    @staticmethod
    def get_by_username(username, users_db):
        """Retrieve a user by username from the database."""
        for user in users_db:
            if user['username'] == username:
                return User(
                    user['id'],
                    user['username'],
                    user['email'],
                    user['password_hash']
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