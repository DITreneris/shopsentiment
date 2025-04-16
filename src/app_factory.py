"""
Application Factory

This module provides a factory function to create and configure the Flask application.
"""

import os
import logging
import sys
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from flask import Flask

logger = logging.getLogger(__name__)

def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Create and configure a Flask application instance.
    
    Args:
        config: Optional dictionary with configuration values to override
        
    Returns:
        Configured Flask application
    """
    # Set template_folder to the correct location (project root/templates)
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Add config directory to path if it exists
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
    if os.path.exists(config_dir) and config_dir not in sys.path:
        sys.path.insert(0, os.path.dirname(config_dir))
        logger.info(f"Added {os.path.dirname(config_dir)} to sys.path")

    # Set default config values
    app.config.update({
        "DEBUG": os.environ.get("FLASK_DEBUG", "true").lower() == "true",
        "SECRET_KEY": os.environ.get("SECRET_KEY", "dev-key-for-shopsentiment"),
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 300,
        "DATABASE_PATH": os.environ.get("DATABASE_PATH", "data/shopsentiment.db"),
        "SENTIMENT_ANALYSIS_MODEL": os.environ.get("SENTIMENT_MODEL", "default"),
    })
    
    # Try to load default configuration
    try:
        app.config.from_object('config.default')
        logger.info("Loaded configuration from config.default")
    except ImportError as e:
        logger.warning(f"Could not load config.default: {str(e)}")
    except Exception as e:
        logger.warning(f"Error loading config.default: {str(e)}")
    
    # Try to load environment-specific configuration
    env = os.getenv('FLASK_ENV', 'development')
    try:
        app.config.from_object(f'config.{env}')
        logger.info(f"Loaded configuration for environment: {env}")
    except ImportError:
        logger.warning(f"No configuration found for environment: {env}.")
    except Exception as e:
        logger.warning(f"Error loading config.{env}: {str(e)}")
    
    # Override with any provided config values
    if config:
        app.config.update(config)
    
    # Initialize extensions
    try:
        from flask_cors import CORS
        CORS(app)
        logger.info("CORS initialized")
    except ImportError:
        logger.warning("flask_cors not installed, CORS support disabled")
    
    # Initialize cache
    try:
        from src.utils.cache_factory import get_cache_from_app_config
        cache = get_cache_from_app_config(app.config)
        app.extensions['cache'] = cache
        logger.info(f"Initialized cache: {cache.__class__.__name__}")
    except Exception as e:
        logger.error(f"Failed to initialize cache: {str(e)}")
        # Continue without cache
    
    # Initialize sentiment service
    try:
        from src.services.sentiment_service import create_sentiment_service
        db_path = app.config.get('DATABASE_PATH', 'data/shopsentiment.db')
        sentiment_model = app.config.get('SENTIMENT_ANALYSIS_MODEL', 'default')
        sentiment_service = create_sentiment_service(db_path, sentiment_model)
        app.extensions['sentiment_service'] = sentiment_service
        logger.info(f"Initialized sentiment service with model: {sentiment_model}")
    except Exception as e:
        logger.error(f"Failed to initialize sentiment service: {str(e)}")
        # Continue without sentiment service
    
    # Register blueprints
    with app.app_context():
        try:
            from src.routes.api import api_bp
            from src.routes.main import main_bp
            
            app.register_blueprint(api_bp, url_prefix='/api')
            app.register_blueprint(main_bp)
            logger.info("Registered main application blueprints")
            
            # Register API v1 routes - direct registration approach
            try:
                logger.info("Attempting to register API v1 blueprints...")
                
                # Import API v1 blueprints directly
                from src.api.v1 import api_v1
                from src.api.v1.sentiment import sentiment_bp
                from src.api.v1.products import products_bp
                
                # Register blueprints manually
                api_v1.register_blueprint(sentiment_bp, url_prefix='/sentiment')
                api_v1.register_blueprint(products_bp, url_prefix='/products')
                app.register_blueprint(api_v1, url_prefix='/api')
                
                logger.info("Successfully registered API v1 blueprints manually")
            except ImportError as e:
                logger.error(f"Could not import API v1 module: {str(e)}")
                logger.error(f"Import error details: {traceback.format_exc()}")
            except AttributeError as e:
                logger.error(f"Attribute error registering API v1 blueprints: {str(e)}")
                logger.error(f"Attribute error details: {traceback.format_exc()}")
            except Exception as e:
                logger.error(f"Failed to register API v1 blueprints: {str(e)}")
                logger.error(f"Error traceback: {traceback.format_exc()}")
        except Exception as e:
            logger.error(f"Failed to register blueprints: {str(e)}")
            # Continue without blueprints
    
    # Setup error handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        return {"error": "Not found"}, 404
    
    @app.errorhandler(500)
    def handle_server_error(e):
        logger.error(f"Internal server error: {str(e)}")
        return {"error": "Internal server error"}, 500
    
    # Add a health endpoint directly to the app
    @app.route('/health')
    def health():
        """Return the health status of the application."""
        # Check if API v1 is registered
        api_v1_registered = False
        try:
            for blueprint in app.blueprints.values():
                if blueprint.name == 'api_v1':
                    api_v1_registered = True
                    break
        except Exception as e:
            logger.error(f"Error checking API v1 registration: {str(e)}")
        
        return {
            'status': 'healthy',
            'service': 'ShopSentiment Analysis',
            'version': '1.0.0',
            'timestamp': str(datetime.now()),
            'debug': {
                'api_v1_registered': api_v1_registered,
                'registered_blueprints': list(app.blueprints.keys())
            }
        }
    
    # Setup logging
    if not app.debug:
        # Configure production logging here
        log_level = app.config.get('LOG_LEVEL', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    logger.info(f"Application initialized with environment: {env}")
    return app 