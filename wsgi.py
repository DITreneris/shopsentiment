#!/usr/bin/env python
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info("Starting application")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")

try:
    # Import the Flask app
    logger.info("Importing Flask app")
    from app import app
    
    # Log successful import
    logger.info("Flask app successfully imported")
except Exception as e:
    # Log the error
    logger.error(f"Error importing Flask app: {e}", exc_info=True)
    raise

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    logger.info(f"Running app on port {port}")
    app.run(host='0.0.0.0', port=port) 