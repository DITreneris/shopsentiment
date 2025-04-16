#!/usr/bin/env python3
"""
Test script for running the application in a Heroku-like environment locally.

This script sets up environment variables similar to Heroku and runs the application.
"""

import os
import subprocess
import sys
import time
import requests
import logging
import signal
import random
import socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_free_port():
    """Find an available port to run the test server."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def setup_heroku_environment():
    """Set up environment variables to simulate Heroku."""
    env = os.environ.copy()
    
    # Heroku environment variables
    env['DYNO'] = f'web.{random.randint(1, 10)}'
    env['PORT'] = str(find_free_port())
    env['WEB_CONCURRENCY'] = '2'
    env['FLASK_ENV'] = 'production'
    env['FLASK_APP'] = 'app.py'
    env['LOG_LEVEL'] = 'INFO'
    env['SECRET_KEY'] = 'test-secret-key'
    
    # MongoDB and Redis
    # For local testing, you can use localhost or a test instance
    env['MONGODB_URI'] = 'mongodb://localhost:27017/shopsentiment_test'
    env['REDIS_URL'] = 'redis://localhost:6379/0'
    
    return env

def start_application(env):
    """Start the application using gunicorn like Heroku would."""
    command = [
        'gunicorn',
        '--config', 'gunicorn_config.py',
        '--log-level', 'debug',
        'wsgi:application'
    ]
    
    logger.info(f"Starting application on port {env['PORT']}")
    process = subprocess.Popen(command, env=env)
    return process, int(env['PORT'])

def test_application(port):
    """Test the application endpoints."""
    base_url = f"http://localhost:{port}"
    max_retries = 5
    retry_delay = 2
    
    # Wait for the application to start
    logger.info("Waiting for application to start...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health")
            if response.status_code == 200:
                logger.info("Application is running!")
                break
        except requests.exceptions.ConnectionError:
            if i < max_retries - 1:
                logger.info(f"Connection failed, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Failed to connect to the application after multiple retries")
                return False
    
    # Test health endpoint
    logger.info("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        data = response.json()
        logger.info(f"Health endpoint response: {data}")
        if response.status_code != 200 or data.get('status') != 'healthy':
            logger.error("Health check failed")
            return False
    except Exception as e:
        logger.error(f"Error testing health endpoint: {str(e)}")
        return False
    
    # Test home page
    logger.info("Testing home page...")
    try:
        response = requests.get(base_url)
        if response.status_code != 200:
            logger.error(f"Home page check failed with status code {response.status_code}")
            return False
        logger.info("Home page loaded successfully")
    except Exception as e:
        logger.error(f"Error testing home page: {str(e)}")
        return False
    
    # Test API endpoint
    logger.info("Testing API endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/products")
        if response.status_code != 200:
            logger.error(f"API check failed with status code {response.status_code}")
            return False
        data = response.json()
        logger.info(f"API response: {data}")
        if 'products' not in data:
            logger.error("API response format is incorrect")
            return False
        logger.info("API endpoint working correctly")
    except Exception as e:
        logger.error(f"Error testing API endpoint: {str(e)}")
        return False
    
    # Test sentiment analysis
    logger.info("Testing sentiment analysis...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/analyze",
            json={"text": "This is a great product!"}
        )
        if response.status_code != 200:
            logger.error(f"Sentiment analysis failed with status code {response.status_code}")
            return False
        data = response.json()
        logger.info(f"Sentiment analysis response: {data}")
        if 'sentiment' not in data:
            logger.error("Sentiment analysis response format is incorrect")
            return False
        logger.info("Sentiment analysis working correctly")
    except Exception as e:
        logger.error(f"Error testing sentiment analysis: {str(e)}")
        return False
    
    logger.info("All tests passed!")
    return True

def main():
    """Main function to run the tests."""
    logger.info("Setting up Heroku-like environment...")
    env = setup_heroku_environment()
    
    process = None
    try:
        process, port = start_application(env)
        
        # Wait for application to start
        time.sleep(3)
        
        # Run tests
        success = test_application(port)
        
        if success:
            logger.info("✅ Application is ready for Heroku deployment!")
            return 0
        else:
            logger.error("❌ Some tests failed. Review the logs and fix issues before deploying.")
            return 1
    finally:
        # Cleanup
        if process:
            logger.info("Shutting down application...")
            process.send_signal(signal.SIGTERM)
            process.wait()

if __name__ == "__main__":
    sys.exit(main()) 