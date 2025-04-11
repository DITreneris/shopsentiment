from flask import Flask, request, jsonify
import os
import sqlite3
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import json
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-development')
app.config['DATABASE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reviews.db')

# Security Configuration
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_SECURE'] = os.environ.get('REMEMBER_COOKIE_SECURE', 'False').lower() == 'true'
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_DURATION'] = 2592000  # 30 days

# Initialize security extensions
csrf = CSRFProtect(app)

# Initialize CORS with specific settings for the frontend
CORS(app, resources={r"/*": {"origins": ["http://localhost:8000", "http://127.0.0.1:8000"]}}, supports_credentials=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Specify the login route
login_manager.login_message = 'Please log in to access this page'
login_manager.login_message_category = 'error'

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
try:
    from app import routes
except ImportError:
    logger.warning("Routes module not found or could not be imported")

# Try to register the auth blueprint
try:
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
except ImportError:
    logger.warning("Auth blueprint not found or could not be imported")

# Register products blueprint
try:
    from app.routes.products import products_bp
    app.register_blueprint(products_bp, url_prefix='/api/products')
except ImportError:
    logger.warning("Products blueprint not found or could not be imported")

# Register reviews blueprint
try:
    from app.routes.reviews import reviews_bp
    app.register_blueprint(reviews_bp, url_prefix='/api/reviews')
except ImportError:
    logger.warning("Reviews blueprint not found or could not be imported")

# Initialize the database
init_db()

# A simple route to confirm the app is working
@app.route('/health')
def health_check():
    return {'status': 'healthy'}

# A simple route for the home page
@app.route('/')
def home():
    return {'status': 'ok', 'message': 'Shop Sentiment Analysis API is running', 
            'endpoints': [
                '/api/products',
                '/api/reviews',
                '/auth/login',
                '/auth/register',
                '/auth/logout',
                '/auth/me'
            ]}

# Frontend routes - serve the SPA
@app.route('/app')
def serve_frontend():
    return app.send_static_file('frontend/index.html')

# Catch all route for SPA - redirects to the frontend app
@app.route('/frontend')
@app.route('/frontend/<path:path>')
def frontend_redirect(path=''):
    return app.send_static_file('frontend/index.html')

# Add direct auth endpoints to bypass the blueprint import issue
@app.route('/auth/login', methods=['POST'])
def auth_login():
    from werkzeug.security import check_password_hash
    from app.models.user import User
    
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    users_db = get_users_db()
    user = User.get_by_email(email, users_db)
    
    if user and user.check_password(password):
        login_user(user)
        return jsonify({"message": "Login successful", "user": user.username}), 200
    
    return jsonify({"error": "Invalid email or password"}), 401

@app.route('/auth/logout', methods=['POST'])
@login_required
def auth_logout():
    logout_user()
    return jsonify({"message": "Logout successful"}), 200

@app.route('/auth/register', methods=['POST'])
def auth_register():
    from app.models.user import User
    
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400
    
    users_db = get_users_db()
    
    if User.get_by_email(email, users_db):
        return jsonify({"error": "Email already registered"}), 400
    
    if User.get_by_username(username, users_db):
        return jsonify({"error": "Username already taken"}), 400
    
    # Create user
    user = User.create_user(username, email, password, users_db)
    
    # Save user to database
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'users.json'), 'w') as f:
        json.dump(users_db, f, indent=2)
    
    login_user(user)
    return jsonify({"message": "Registration successful", "user": user.username}), 201

@app.route('/auth/me', methods=['GET'])
@login_required
def auth_me():
    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": getattr(current_user, 'role', 'user')
    }), 200

@app.route('/auth/test', methods=['GET'])
def auth_test():
    return jsonify({"message": "Auth endpoints are working"}), 200 