#!/usr/bin/env python3
"""
Heroku Connection Testing Script for ShopSentiment

This script tests the connection to a deployed Heroku app and verifies
that MongoDB, Redis, and the application are working correctly.
"""

import os
import sys
import logging
import requests
import time
import json
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_heroku_connection")

def get_app_url(app_name):
    """Get the URL for the Heroku app."""
    if not app_name:
        return None
    
    return f"https://{app_name}.herokuapp.com"

def test_app_connection(app_url):
    """Test basic connection to the app."""
    try:
        logger.info(f"Testing connection to {app_url}...")
        response = requests.get(app_url, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Successfully connected to the app. Status code: {response.status_code}")
            return True
        else:
            logger.error(f"Failed to connect to the app. Status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"Error connecting to the app: {str(e)}")
        return False

def test_health_endpoint(app_url):
    """Test the health endpoint to verify component status."""
    try:
        health_url = f"{app_url}/health"
        logger.info(f"Testing health endpoint at {health_url}...")
        
        response = requests.get(health_url, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Health endpoint returned status code: {response.status_code}")
            return False
        
        try:
            health_data = response.json()
            logger.info(f"Health endpoint response: {json.dumps(health_data, indent=2)}")
            
            # Check overall status
            if health_data.get('status') != 'healthy':
                logger.error(f"Application status is not healthy: {health_data.get('status')}")
                return False
            
            # Check database status
            db_status = health_data.get('database', {}).get('status')
            if db_status != 'healthy':
                logger.error(f"Database status is not healthy: {db_status}")
                return False
            
            # Check cache status
            cache_status = health_data.get('cache', {}).get('status')
            if cache_status != 'healthy':
                logger.error(f"Cache status is not healthy: {cache_status}")
                return False
            
            logger.info("All components are healthy according to the health endpoint")
            return True
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing health endpoint response: {str(e)}")
            return False
    except requests.RequestException as e:
        logger.error(f"Error accessing health endpoint: {str(e)}")
        return False

def test_api_endpoint(app_url):
    """Test API endpoint to verify API functionality."""
    try:
        api_url = f"{app_url}/api/v1/info"
        logger.info(f"Testing API endpoint at {api_url}...")
        
        response = requests.get(api_url, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"API endpoint returned status code: {response.status_code}")
            return False
        
        try:
            api_data = response.json()
            logger.info(f"API response: {json.dumps(api_data, indent=2)}")
            
            # Check if the API version information is present
            if 'version' not in api_data:
                logger.error("API response missing version information")
                return False
            
            logger.info(f"API endpoint is working correctly. Version: {api_data.get('version')}")
            return True
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing API response: {str(e)}")
            return False
    except requests.RequestException as e:
        logger.error(f"Error accessing API endpoint: {str(e)}")
        return False

def main():
    """Main function to test Heroku connection."""
    logger.info("Starting Heroku connection test")
    
    # Get app name from command-line argument or prompt
    if len(sys.argv) > 1:
        app_name = sys.argv[1]
    else:
        app_name = input("Enter Heroku app name: ").strip()
    
    if not app_name:
        logger.error("App name not provided. Exiting.")
        sys.exit(1)
    
    app_url = get_app_url(app_name)
    if not app_url:
        logger.error("Failed to determine app URL. Exiting.")
        sys.exit(1)
    
    # Test basic connection
    if not test_app_connection(app_url):
        logger.error("Basic connection test failed. Exiting.")
        sys.exit(1)
    
    # Test health endpoint
    if not test_health_endpoint(app_url):
        logger.warning("Health endpoint test failed.")
    
    # Test API endpoint
    if not test_api_endpoint(app_url):
        logger.warning("API endpoint test failed.")
    
    logger.info("Heroku connection tests completed")

if __name__ == "__main__":
    main() 