#!/usr/bin/env python3
"""
Start ShopSentiment Application

This script starts the ShopSentiment application with MongoDB integration.
It handles the necessary setup and environment checks before launching the app.
"""

import os
import sys
import subprocess
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("start_app")

def check_environment():
    """Check if the environment is properly set up."""
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        logger.error("Python 3.7 or higher is required")
        sys.exit(1)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        logger.error(".env file not found. Please create one based on .env.example")
        sys.exit(1)
    
    # Load environment variables
    load_dotenv()
    
    # Check MongoDB URI
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        logger.warning("MONGODB_URI not found in .env file. Using SQLite as fallback.")
    else:
        logger.info("MongoDB configuration found.")
    
    # Check FLASK_APP
    flask_app = os.getenv('FLASK_APP')
    if not flask_app:
        logger.warning("FLASK_APP not set in .env file. Setting to 'app.py'")
        os.environ['FLASK_APP'] = 'app.py'
    
    logger.info("Environment checks completed successfully.")
    return True

def verify_mongodb_setup():
    """Verify MongoDB is properly set up."""
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        return False
    
    try:
        logger.info("Testing MongoDB connection...")
        result = subprocess.run(
            [sys.executable, 'scripts/test_mongodb_connection.py'],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("MongoDB connection successful.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"MongoDB connection failed: {e.stderr}")
        return False

def initialize_mongodb_if_needed():
    """Initialize MongoDB if needed."""
    if not verify_mongodb_setup():
        logger.warning("Skipping MongoDB initialization.")
        return
    
    try:
        # Check if collections exist by listing MongoDB data
        logger.info("Checking if MongoDB collections exist...")
        result = subprocess.run(
            [sys.executable, 'scripts/list_mongodb_data.py'],
            check=False,  # Don't exit if command fails
            capture_output=True,
            text=True
        )
        
        # If "Found 0 users" or error in output, initialize MongoDB
        if "Found 0 users" in result.stdout or "error" in result.stderr.lower():
            logger.info("No users found. Initializing MongoDB...")
            subprocess.run(
                [sys.executable, 'scripts/initialize_mongodb.py'],
                check=True
            )
            
            # Add sample product
            logger.info("Adding sample product...")
            subprocess.run(
                [sys.executable, 'scripts/add_sample_product.py'],
                check=True
            )
        else:
            logger.info("MongoDB collections already exist. Skipping initialization.")
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error initializing MongoDB: {e}")
        sys.exit(1)

def check_nltk_data():
    """Check if NLTK data is available and download if needed."""
    try:
        logger.info("Checking NLTK data...")
        import nltk
        
        # List of required NLTK data packages
        required_packages = ['vader_lexicon', 'punkt', 'stopwords']
        
        # Check each package and download if not available
        for package in required_packages:
            try:
                nltk.data.find(f'tokenizers/{package}')
                logger.info(f"NLTK package '{package}' is available.")
            except LookupError:
                logger.info(f"Downloading NLTK package '{package}'...")
                nltk.download(package)
    
    except Exception as e:
        logger.error(f"Error checking NLTK data: {e}")
        sys.exit(1)

def start_flask_app():
    """Start the Flask application."""
    logger.info("Starting Flask application...")
    
    # Determine environment
    flask_env = os.getenv('FLASK_ENV', 'development')
    debug_mode = flask_env == 'development'
    
    # Import app after environment setup
    from app import app
    
    # Get host and port from environment or use defaults
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    
    logger.info(f"Running in {flask_env} mode on {host}:{port}")
    app.run(host=host, port=port, debug=debug_mode)

def main():
    """Main function to start the application."""
    logger.info("Starting ShopSentiment application")
    
    # Check environment
    check_environment()
    
    # Check NLTK data
    check_nltk_data()
    
    # Initialize MongoDB if needed
    initialize_mongodb_if_needed()
    
    # Start Flask application
    start_flask_app()

if __name__ == "__main__":
    main() 