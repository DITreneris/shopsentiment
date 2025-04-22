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

# Setup NLTK data (REMOVED - Application uses fallback analyzer)
# try:
#     import nltk
#     nltk_data_dir = os.environ.get('NLTK_DATA', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nltk_data'))
#     
#     # Create the directory if it doesn't exist
#     os.makedirs(nltk_data_dir, exist_ok=True)
#     
#     # Add to NLTK's search path
#     nltk.data.path.append(nltk_data_dir)
#     
#     # Disable interactive downloads
#     os.environ['NLTK_DOWNLOADER_INTERACTIVE'] = '0'
#     
#     # Define required packages
#     required_packages = ['vader_lexicon', 'punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']
#     missing_packages = []
#     
#     # Check which packages are missing
#     for package in required_packages:
#         try:
#             nltk.data.find(f'tokenizers/{package}')
#             logger.info(f"NLTK package '{package}' is available")
#         except LookupError:
#             missing_packages.append(package)
#     
#     if missing_packages:
#         logger.warning(f"Missing NLTK packages: {', '.join(missing_packages)}")
#         logger.warning("Application will use fallback sentiment analyzer")
#     else:
#         logger.info("All required NLTK packages are available")
#         
# except ImportError:
#     logger.warning("NLTK not available. Will use fallback sentiment analyzer.")
# except Exception as e:
#     logger.error(f"Error setting up NLTK: {str(e)}")

error_details = None
error_traceback = None

try:
    # Make sure src is in the path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Print current working directory and Python path for debugging
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    
    # Try to import from src (where create_app now resides)
    from src import create_app
    logger.info("Successfully imported create_app from src")
    
    # Create application with detailed logging
    application = create_app()
    app = application  # alias for compatibility
    
    logger.info("Application initialized successfully")
except Exception as e:
    error_details = str(e)
    error_traceback = traceback.format_exc()
    logger.error(f"Error initializing application: {error_details}")
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
            "error_details": error_details,
            "traceback": error_traceback.split('\n') if error_traceback else []
        }), 500
    
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'unhealthy',
            'message': 'Application failed to initialize properly',
            'error': error_details
        }), 500
    
    logger.info("Using fallback error application")

# For local development
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") != "production"
    
    logger.info(f"Starting application on port {port} with debug={debug}")
    app.run(host="0.0.0.0", port=port, debug=debug) 