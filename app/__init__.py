from flask import Flask
import os
import sqlite3
import nltk
from flask_login import LoginManager
import json

# Initialize Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-development')
app.config['DATABASE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reviews.db')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Specify the login route
login_manager.login_message = 'Please log in to access this page'
login_manager.login_message_category = 'error'

# Ensure the NLTK data is downloaded
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def get_users_db():
    """Load users from JSON file or create empty list if file doesn't exist"""
    users_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'users.json')
    
    if not os.path.exists(users_file):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(users_file), exist_ok=True)
        # Create empty users file
        with open(users_file, 'w') as f:
            json.dump([], f)
        return []
    
    try:
        with open(users_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

# Initialize database
def init_db():
    with app.app_context():
        conn = get_db_connection()
        
        # Create tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                product_id TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                rating FLOAT,
                date TEXT,
                sentiment FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        conn.commit()
        conn.close()

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    users_db = get_users_db()
    return User.get_by_id(user_id, users_db)

# Import routes after app is initialized to avoid circular imports
from app import routes

# Register the auth blueprint
from app.routes.auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

# Initialize the database
init_db() 