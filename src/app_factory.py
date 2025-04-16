"""
Application Factory

This module provides a factory function to create and configure the Flask application.
"""

import os
import logging
from typing import Dict, Any, Optional

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
    
    # Load default configuration
    app.config.from_object('config.default')
    
    # Load environment-specific configuration
    env = os.getenv('FLASK_ENV', 'development')
    try:
        app.config.from_object(f'config.{env}')
        logger.info(f"Loaded configuration for environment: {env}")
    except ImportError:
        logger.warning(f"No configuration found for environment: {env}. Using default.")
    
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
            
            logger.info("Registered application blueprints")
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