"""
API Routes Verification Script

This script verifies that the API v1 routes are properly registered
and accessible in the application.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the API routes verification."""
    try:
        logger.info("Starting API routes verification")
        
        # Make sure src is in the path
        sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
        
        # Import the application factory (now from src/__init__.py)
        from src import create_app
        
        # Create the application
        app = create_app()
        
        # Check registered blueprints
        logger.info("Registered blueprints:")
        for name, blueprint in app.blueprints.items():
            logger.info(f"  - {name} (url_prefix: {blueprint.url_prefix})")
        
        # Check if API v1 is registered
        api_v1_registered = False
        for name, blueprint in app.blueprints.items():
            if name == 'api_v1':
                api_v1_registered = True
                break
        
        if api_v1_registered:
            logger.info("API v1 blueprint is registered")
        else:
            logger.error("API v1 blueprint is NOT registered")
        
        # Check API v1 routes
        logger.info("Registered routes:")
        for rule in app.url_map.iter_rules():
            if 'api/v1' in str(rule):
                logger.info(f"  - {rule}")
        
        logger.info("API routes verification completed")
        
    except Exception as e:
        logger.error(f"Error during API routes verification: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 