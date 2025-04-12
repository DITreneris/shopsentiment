"""Authentication module for Shop Sentiment Analysis"""
import os
import jwt
import logging
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import users

# Configure logging
logger = logging.getLogger(__name__)

# JWT settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-secret-key')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_MINUTES = 60 * 24  # 1 day

def generate_token(user_id):
    """Generate a JWT token for a user"""
    payload = {
        'exp': datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES),
        'iat': datetime.utcnow(),
        'sub': str(user_id)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token):
    """Decode a JWT token and verify it"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        logger.warning("Expired token")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None

def token_required(f):
    """Decorator to require JWT token for a route"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth = request.headers.get('Authorization')
        
        if auth and auth.startswith('Bearer '):
            token = auth.split('Bearer ')[1]
        
        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401
        
        user_id = decode_token(token)
        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Get user from database
        current_user = users.find_one({'_id': user_id})
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def register_user(username, email, password):
    """Register a new user"""
    # Check if email already exists
    if users.find_one({'email': email}):
        return None, "Email already registered"
    
    # Check if username already exists
    if users.find_one({'username': username}):
        return None, "Username already taken"
    
    # Create user
    user_id = str(uuid.uuid4())
    user = {
        '_id': user_id,
        'username': username,
        'email': email,
        'password_hash': generate_password_hash(password),
        'role': 'user',
        'is_active': True
    }
    
    users.insert_one(user)
    logger.info(f"User registered: {username}")
    
    return user, None

def authenticate_user(email, password):
    """Authenticate a user by email and password"""
    user = users.find_one({'email': email})
    
    if not user:
        logger.warning(f"Authentication failed: User not found - {email}")
        return None, "Invalid email or password"
    
    if not check_password_hash(user['password_hash'], password):
        logger.warning(f"Authentication failed: Invalid password - {email}")
        return None, "Invalid email or password"
    
    logger.info(f"User authenticated: {email}")
    return user, None 