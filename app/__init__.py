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
# Exempt API routes from CSRF protection
csrf.exempt('auth_login')
csrf.exempt('auth_register')
csrf.exempt('auth_logout')

# Initialize CORS with specific settings for the frontend
CORS(app, resources={r"/*": {"origins": ["http://localhost:8000", "http://127.0.0.1:8000", 
                                        "https://*.herokuapp.com", "http://*.herokuapp.com",
                                        "https://salty-hamlet-05965-52206bf9d73c.herokuapp.com"],
                             "supports_credentials": True,
                             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                             "allow_headers": ["Content-Type", "Authorization"]}}, 
     supports_credentials=True)

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

# API Info endpoint
@app.route('/api')
def api_info():
    return {'status': 'ok', 'message': 'Shop Sentiment Analysis API is running', 
            'endpoints': [
                '/api/products',
                '/api/reviews',
                '/auth/login',
                '/auth/register',
                '/auth/logout',
                '/auth/me'
            ]}

# Root path now serves the frontend or API info based on environment variable
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_root(path=''):
    # Special case for API endpoints
    if path.startswith('api/') or path.startswith('auth/'):
        return api_info() if path == 'api' else None  # Let the other routes handle this
    
    # Check if we should force serving the frontend index
    force_frontend = os.environ.get('FORCE_ROOT_SERVED_INDEX', '').lower() == 'true'
    
    # If we're forcing frontend, or if this is a specific static path, serve frontend
    if force_frontend or (path != '' and os.path.exists(os.path.join(app.static_folder, 'frontend', path))):
        # For the root path when forcing frontend
        if path == '' and force_frontend:
            return app.send_static_file('frontend/index.html')
        
        # For specific static files
        if path != '' and os.path.exists(os.path.join(app.static_folder, 'frontend', path)):
            return app.send_static_file(f'frontend/{path}')
    
    # If not forcing frontend at root, serve API info at root
    if path == '' and not force_frontend:
        return api_info()
    
    # Default: serve the index.html file for any other path
    return app.send_static_file('frontend/index.html')

# Frontend routes - alternative paths
@app.route('/app', defaults={'path': ''})
@app.route('/app/<path:path>')
def serve_frontend(path=''):
    if path != '' and os.path.exists(os.path.join(app.static_folder, 'frontend', path)):
        return app.send_static_file(f'frontend/{path}')
    return app.send_static_file('frontend/index.html')

# Catch all route for SPA - redirects to the frontend app
@app.route('/frontend', defaults={'path': ''})
@app.route('/frontend/<path:path>')
def frontend_redirect(path=''):
    return app.send_static_file('frontend/index.html')

# Fix auth routes
@csrf.exempt
@app.route('/auth/login', methods=['POST', 'OPTIONS'])
def auth_login():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        return response
        
    from werkzeug.security import check_password_hash
    from app.models.user import User
    
    try:
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
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@csrf.exempt
@app.route('/auth/logout', methods=['POST', 'OPTIONS'])
@login_required
def auth_logout():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        return response
        
    logout_user()
    return jsonify({"message": "Logout successful"}), 200

@csrf.exempt
@app.route('/auth/register', methods=['POST', 'OPTIONS'])
def auth_register():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        return response
        
    from werkzeug.security import generate_password_hash
    from app.models.user import User
    
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No input data provided"}), 400
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({"error": "Username, email and password are required"}), 400
        
        users_db = get_users_db()
        
        # Check if email already exists
        if User.get_by_email(email, users_db):
            return jsonify({"error": "Email already exists"}), 400
        
        # Create new user
        from uuid import uuid4
        user_id = str(uuid4())
        new_user = {
            'id': user_id,
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password)
        }
        
        users_db.append(new_user)
        
        # Save to JSON file
        users_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'users.json')
        os.makedirs(os.path.dirname(users_file), exist_ok=True)
        with open(users_file, 'w') as f:
            json.dump(users_db, f, indent=4)
        
        return jsonify({"message": "User registered successfully", "user_id": user_id}), 201
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@csrf.exempt
@app.route('/auth/me', methods=['GET', 'OPTIONS'])
@login_required
def auth_me():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        return response
        
    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }), 200

@app.route('/auth/test', methods=['GET'])
def auth_test():
    return jsonify({"message": "Auth endpoints are working"}), 200 