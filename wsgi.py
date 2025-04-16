"""
WSGI entry point for the ShopSentiment application.

This module serves as the WSGI entry point for the application,
which is used by Gunicorn and other WSGI servers.
"""

import os
import sys
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Make sure src is in the path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Print current working directory and Python path for debugging
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    
    # Try to import from src
    from src.app_factory import create_app
    logger.info("Successfully imported app_factory")
    
    # Create application with detailed logging
    application = create_app()
    app = application  # alias for compatibility
    
    logger.info("Application initialized successfully")
except Exception as error:
    error_traceback = traceback.format_exc()
    logger.error(f"Error initializing application: {str(error)}")
    logger.error(f"Traceback: {error_traceback}")
    
    # Create a simple fallback app that shows the error
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    application = app  # alias for compatibility
    
    @app.route('/')
    def error_page():
        return jsonify({
            "error": "Application failed to initialize",
            "message": "An error occurred while initializing the application. Please check the logs for details.",
            "error_details": str(error),
            "traceback": error_traceback.split('\n')
        }), 500
    
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'unhealthy',
            'message': 'Application failed to initialize properly',
            'error': str(error)
        }), 500
    
    logger.info("Using fallback error application")

# For local development
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") != "production"
    
    logger.info(f"Starting application on port {port} with debug={debug}")
    app.run(host="0.0.0.0", port=port, debug=debug) 