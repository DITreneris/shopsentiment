"""
ShopSentiment Application Initialization

This module initializes the ShopSentiment application with the improved
architecture, database integration, caching, and security features.
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request, g
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from src.database.connection import get_mongodb_client, close_mongodb_connection
# Import SQLite connection module for fallback
try:
    from src.database.sqlite_connection import init_sqlite_db, close_sqlite_db
except ImportError:
    # If SQLite module doesn't exist, create stub functions
    def init_sqlite_db():
        pass
    def close_sqlite_db(e=None):
        pass

from src.api.v1 import register_api
from src.web_routes import register_web_routes
from src.auth import register_auth_routes
from src.utils.security import setup_security, setup_input_validation
from src.utils.cache_factory import get_cache_from_app_config
from src.services.sentiment_analyzer import sentiment_analyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def configure_mongodb(app):
    """Configure MongoDB connection for the application."""
    try:
        with app.app_context():
            mongodb_client = get_mongodb_client()
            if mongodb_client:
                app.config['MONGODB_CLIENT'] = mongodb_client
                app.mongodb = mongodb_client
                logger.info("MongoDB connection initialized successfully")
                return True
            else:
                logger.error("Failed to initialize MongoDB client")
                return False
    except Exception as e:
        logger.error(f"Error during MongoDB configuration: {str(e)}")
        return False


def load_configuration(app):
    """Load application configuration based on environment."""
    # Configure the app based on environment
    app.config.from_object('config.default')
    
    # Determine environment
    environment = os.environ.get('FLASK_ENV', 'development')
    try:
        if environment == 'production':
            logger.info("Running in production environment")
            app.config.from_object('config.production')
        else:
            logger.info("Running in development environment")
            app.config.from_object('config.development')
    except ImportError:
        logger.warning(f"No configuration found for environment: {environment}. Using default.")


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, 
                template_folder='../templates', 
                static_folder='../static')
    
    # Load configuration
    load_configuration(app)
    
    # Override with any provided config values
    if config:
        app.config.update(config)
    
    # Fix for proxy headers
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=app.config.get('TRUSTED_PROXIES', 1))
    
    # Initialize CORS
    CORS(app)
    
    # Initialize cache
    cache = get_cache_from_app_config(app.config)
    app.extensions['cache'] = cache
    logger.info(f"Initialized cache: {cache.__class__.__name__}")
    
    # Initialize database connection based on configuration
    # Check environment variable first, then config
    use_sqlite_env = os.environ.get('USE_SQLITE', '').lower() in ('true', '1', 't', 'yes', 'y')
    use_sqlite_config = app.config.get('USE_SQLITE', False)
    use_sqlite = use_sqlite_env or use_sqlite_config
    
    logger.info(f"Database mode from environment: USE_SQLITE={use_sqlite_env}")
    logger.info(f"Database mode from config: USE_SQLITE={use_sqlite_config}")
    logger.info(f"Final database mode: USE_SQLITE={use_sqlite}")
    
    if not use_sqlite:
        # Try to configure MongoDB
        logger.info("Attempting to use MongoDB database")
        if not configure_mongodb(app):
            logger.warning("MongoDB connection failed, falling back to SQLite if available")
            use_sqlite = True
            app.config['USE_SQLITE'] = True
    
    if use_sqlite:
        # Initialize SQLite database
        try:
            with app.app_context():
                init_sqlite_db()
                logger.info("SQLite database initialized")
            # Register teardown function for SQLite
            app.teardown_appcontext(close_sqlite_db)
        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {str(e)}")
            if os.environ.get('FLASK_ENV') == 'production':
                raise
    else:
        # Register teardown function for MongoDB
        app.teardown_appcontext(close_mongodb_connection)
    
    # Register API routes
    register_api(app)
    register_web_routes(app)
    register_auth_routes(app)
    
    # Setup security features
    setup_security(app)
    setup_input_validation(app)
    
    # Add datetime.now to all template contexts
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning(f'404 error: {error}')
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Not found',
                'message': f'The requested URL {request.path} was not found'
            }), 404
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f'500 error: {error}')
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal server error',
                'message': 'The server encountered an internal error'
            }), 500
        return render_template('500.html'), 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring."""
        try:
            # Check the appropriate database connection
            use_sqlite = app.config.get('USE_SQLITE', False)
            db_status = "healthy"
            
            if use_sqlite:
                # SQLite health check is simple - if we got here, it's working
                db_type = "sqlite"
            else:
                # Check MongoDB connection
                db_type = "mongodb"
                try:
                    if hasattr(app, 'mongodb'):
                        app.mongodb.admin.command('ping')
                    else:
                        db_status = "unhealthy"
                except Exception as e:
                    logger.error(f"MongoDB health check failed: {str(e)}")
                    db_status = "unhealthy"
            
            # Check cache status
            cache_status = "healthy"
            cache_type = app.extensions.get('cache', {}).__class__.__name__
            try:
                app.extensions['cache'].set('health_check', 'ok', timeout=10)
                cache_test = app.extensions['cache'].get('health_check')
                if cache_test != 'ok':
                    cache_status = "unhealthy"
            except Exception as e:
                logger.error(f"Cache health check failed: {str(e)}")
                cache_status = "unhealthy"
            
            return jsonify({
                'status': 'healthy',
                'database': {
                    'status': db_status,
                    'type': db_type
                },
                'cache': {
                    'status': cache_status,
                    'type': cache_type
                },
                'timestamp': datetime.now().isoformat(),
                'environment': os.environ.get('FLASK_ENV', 'unknown')
            })
        except Exception as e:
            logger.error(f'Error in health check: {str(e)}')
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    logger.info(f"Application initialized with environment: {os.environ.get('FLASK_ENV', 'development')}")
    return app 