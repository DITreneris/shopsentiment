"""
Application Factory for the ShopSentiment App

Provides a factory function to create and configure a Flask application
"""

import os
import logging
import sys
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

# Database imports
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions (db instance needs to be globally accessible for models)
db = SQLAlchemy()
migrate = Migrate()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Make sure src is in the path for absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    logger.info(f"Added {parent_dir} to sys.path")

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
        #"DATABASE_PATH": os.environ.get("DATABASE_PATH", "data/shopsentiment.db"), # Old SQLite path
        "SENTIMENT_ANALYSIS_MODEL": os.environ.get("SENTIMENT_MODEL", "default"),
        # SQLAlchemy Config
        "SQLALCHEMY_DATABASE_URI": os.environ.get("DATABASE_URL", "sqlite:///default.db"), # Default to SQLite if not set
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ECHO": os.environ.get("SQLALCHEMY_ECHO", "false").lower() == "true",
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
        CORS(app)
        logger.info("CORS initialized")
    except ImportError:
        logger.warning("flask_cors not installed, CORS support disabled")
    
    # Initialize Database (SQLAlchemy)
    try:
        db.init_app(app)
        migrate.init_app(app, db)
        logger.info(f"SQLAlchemy initialized with URI: {app.config.get('SQLALCHEMY_DATABASE_URI')[:30]}...") # Log only prefix
    except Exception as e:
        logger.error(f"Failed to initialize SQLAlchemy: {str(e)}")
    
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
    except ImportError as e:
        logger.error(f"Could not import sentiment_service module: {str(e)}")
        # Continue without sentiment service - implement a dummy service instead
        app.extensions['sentiment_service'] = None
    except Exception as e:
        logger.error(f"Failed to initialize sentiment service: {str(e)}")
        # Continue without sentiment service
        app.extensions['sentiment_service'] = None
    
    # Register blueprints
    with app.app_context():
        # Import models here AFTER db is initialized and within app context
        # This ensures models are registered with SQLAlchemy correctly
        from src import models # Assuming __init__.py in models imports Product, Review
        
        try:
            # Try to import API routes first
            try:
                from src.routes.api import api_bp
                app.register_blueprint(api_bp, url_prefix='/api')
                logger.info("Registered API blueprint")
            except ImportError as e:
                logger.error(f"Could not import API routes: {str(e)}")
            except Exception as e:
                logger.error(f"Failed to register API routes: {str(e)}")
            
            # Try to import main routes
            try:
                from src.routes.main import main_bp
                app.register_blueprint(main_bp)
                logger.info("Registered main blueprint")
            except ImportError as e:
                logger.error(f"Could not import main routes: {str(e)}")
            except Exception as e:
                logger.error(f"Failed to register main routes: {str(e)}")
            
            # Register API v1 routes - direct registration approach
            try:
                logger.info("Attempting to register API v1 blueprints...")
                
                # Import API v1 blueprints directly
                from src.api.v1 import api_v1
                
                # Try importing sub-blueprints but continue if they fail
                try:
                    from src.api.v1.sentiment import sentiment_bp
                    api_v1.register_blueprint(sentiment_bp, url_prefix='/sentiment')
                    logger.info("Registered sentiment blueprint with API v1")
                except ImportError as e:
                    logger.warning(f"Could not import sentiment API: {str(e)}")
                except Exception as e:
                    logger.warning(f"Failed to register sentiment API: {str(e)}")
                
                try:
                    from src.api.v1.products import products_bp
                    api_v1.register_blueprint(products_bp, url_prefix='/products')
                    logger.info("Registered products blueprint with API v1")
                except ImportError as e:
                    logger.warning(f"Could not import products API: {str(e)}")
                except Exception as e:
                    logger.warning(f"Failed to register products API: {str(e)}")
                
                # Register the main API v1 blueprint
                app.register_blueprint(api_v1, url_prefix='/api')
                logger.info("Successfully registered API v1 blueprint")
                
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