from flask import Flask
import os
import sqlite3
import nltk
from flask_login import LoginManager
import json
from flask_caching import Cache
from app.celery import make_celery
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from datetime import timedelta
import ssl

# Import MongoDB utilities
from app.utils.mongodb import init_app as init_mongodb

# Import Atlas Search utilities
from app.utils.atlas_search import init_app as init_atlas_search

# Initialize dashboard service after app is configured
from app.services.dashboard_service import init_dashboard_service

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

# Configure Redis cache
app.config['CACHE_TYPE'] = os.environ.get('CACHE_TYPE', 'simple')  # Default to simple cache for development
if app.config['CACHE_TYPE'] == 'redis':
    app.config['CACHE_REDIS_HOST'] = os.environ.get('REDIS_HOST', 'localhost')
    app.config['CACHE_REDIS_PORT'] = int(os.environ.get('REDIS_PORT', 6379))
    app.config['CACHE_REDIS_DB'] = int(os.environ.get('REDIS_DB', 0))
    app.config['CACHE_REDIS_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
app.config['CACHE_DEFAULT_TIMEOUT'] = int(os.environ.get('CACHE_TIMEOUT', 300))  # 5 minutes default

# Set environment variables for Heroku
is_heroku = 'DYNO' in os.environ
if is_heroku:
    # Force simple cache type if on Heroku without Redis add-on
    if not os.environ.get('REDIS_URL'):
        app.config['CACHE_TYPE'] = 'simple'
        app.config['CELERY_BROKER_URL'] = None
        app.config['CELERY_RESULT_BACKEND'] = None
        logger.warning('Redis URL not found. Using simple cache instead.')

# Celery configuration
app.config['CELERY_BROKER_URL'] = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Only initialize Celery if broker URL is set
celery = None
if app.config['CELERY_BROKER_URL']:
    try:
        celery = make_celery(app)
    except Exception as e:
        logger.error(f"Failed to initialize Celery: {e}")
        # Fallback to no Celery
        app.config['CELERY_BROKER_URL'] = None
        app.config['CELERY_RESULT_BACKEND'] = None

# Initialize security extensions
csrf = CSRFProtect(app)

# Initialize Talisman for security headers
csp = {
    'default-src': ['\'self\''],
    'script-src': ['\'self\'', '\'unsafe-inline\'', 'https://cdn.jsdelivr.net', 'https://code.jquery.com'],
    'style-src': ['\'self\'', '\'unsafe-inline\'', 'https://cdn.jsdelivr.net', 'https://fonts.googleapis.com'],
    'font-src': ['\'self\'', 'https://fonts.gstatic.com', 'https://cdn.jsdelivr.net'],
    'img-src': ['\'self\'', 'data:', 'https://cdn.jsdelivr.net'],
    'connect-src': ['\'self\'']
}

# Determine if we're in development mode
is_development = os.environ.get('FLASK_ENV', 'development') == 'development'

# Initialize Talisman with comprehensive security headers
talisman = Talisman(
    app,
    content_security_policy=csp,
    content_security_policy_nonce_in=['script-src'],
    force_https=not is_development,
    session_cookie_secure=not is_development,
    frame_options='DENY',
    frame_options_allow_from=None,
    strict_transport_security=True,
    strict_transport_security_preload=True,
    strict_transport_security_max_age=31536000,
    strict_transport_security_include_subdomains=True,
    referrer_policy='strict-origin-when-cross-origin',
    x_content_type_options='nosniff',
    x_xss_protection=True,
    feature_policy={
        'geolocation': '\'none\'',
        'microphone': '\'none\'',
        'camera': '\'none\'',
        'payment': '\'none\'',
        'usb': '\'none\''
    }
)

# Initialize Flask-Limiter for rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.environ.get('REDIS_URL', 'memory://'),
    strategy="fixed-window",
)

# Initialize cache
cache = Cache(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Specify the login route
login_manager.login_message = 'Please log in to access this page'
login_manager.login_message_category = 'error'

# Create a directory for NLTK data if it doesn't exist
nltk_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'nltk_data')
os.makedirs(nltk_data_dir, exist_ok=True)

# Set NLTK data path
nltk.data.path.append(nltk_data_dir)

# Function to download NLTK data without interactive prompts
def download_nltk_data():
    try:
        # Workaround for SSL certificate verification issues in some environments
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

        # Try to find existing data first
        try:
            nltk.data.find('vader_lexicon')
            logger.info("VADER lexicon already downloaded")
        except (LookupError, OSError):
            logger.info("Downloading VADER lexicon")
            try:
                # Download directly specifying the download dir
                nltk.download('vader_lexicon', download_dir=nltk_data_dir, quiet=True)
            except Exception as e:
                logger.error(f"Failed to download VADER lexicon: {e}")
                logger.warning("Proceeding without VADER sentiment analysis")

        try:
            nltk.data.find('tokenizers/punkt')
            logger.info("Punkt tokenizer already downloaded")
        except (LookupError, OSError):
            logger.info("Downloading Punkt tokenizer")
            try:
                # Download directly specifying the download dir
                nltk.download('punkt', download_dir=nltk_data_dir, quiet=True)
            except Exception as e:
                logger.error(f"Failed to download Punkt tokenizer: {e}")
                logger.warning("Proceeding without Punkt tokenization")
    
    except Exception as e:
        logger.error(f"Unhandled error in NLTK download: {e}")
        logger.warning("Proceeding without NLTK components")

# Download NLTK data
download_nltk_data()

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

# Initialize MongoDB
init_mongodb(app)

# Initialize Atlas Search
init_atlas_search(app)

# Register blueprints
from app.routes import main, api
app.register_blueprint(main.bp)
app.register_blueprint(api.bp, url_prefix='/api/v1')

# Register dashboard blueprint
from app.routes.dashboard import dashboard_bp
app.register_blueprint(dashboard_bp)

# Register feedback blueprint
from app.routes.feedback_routes import feedback_bp
app.register_blueprint(feedback_bp)

# Register search blueprint
from app.routes.search_routes import search_bp
app.register_blueprint(search_bp)

# Register webhook blueprint
from app.routes.webhook_routes import webhook_bp
app.register_blueprint(webhook_bp)

# Initialize dashboard service with app and cache
init_dashboard_service(app, cache)

# A simple route to confirm the app is working
@app.route('/health')
@limiter.exempt
def health_check():
    return {'status': 'healthy'}

# Additional security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Security-Policy'] = "default-src 'self'"
    response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
    response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
    response.headers['Permissions-Policy'] = 'accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()'
    response.headers['X-Download-Options'] = 'noopen'
    response.headers['X-DNS-Prefetch-Control'] = 'off'
    return response 