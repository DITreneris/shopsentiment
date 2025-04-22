"""
API v1 Package

This package provides the API endpoints for the ShopSentiment application.
"""

import logging
import traceback
from flask import Blueprint, jsonify, current_app

logger = logging.getLogger(__name__)

# Create main API blueprint (remove internal prefix)
api_v1 = Blueprint('api_v1', __name__)

@api_v1.route('/info', methods=['GET'])
def api_info():
    """
    Get API information.
    
    Returns:
        JSON response with API information
    """
    logger.info("API v1 info endpoint called")
    return jsonify({
        'name': 'ShopSentiment API',
        'version': '1.0',
        'endpoints': [
            '/api/v1/products',
            '/api/v1/sentiment',
        ],
        'status': 'active'
    })

@api_v1.route('/status', methods=['GET'])
def api_status():
    """
    Get API status information (diagnostic endpoint).
    
    Returns:
        JSON response with API status information
    """
    logger.info("API v1 status endpoint called")
    
    # Get registered blueprints in the main app
    blueprints = []
    try:
        for name, blueprint in current_app.blueprints.items():
            blueprints.append({
                'name': name,
                'url_prefix': getattr(blueprint, 'url_prefix', None)
            })
    except Exception as e:
        logger.error(f"Error getting blueprints: {str(e)}")
    
    return jsonify({
        'status': 'active',
        'api_version': '1.0',
        'registered_blueprints': blueprints,
        'api_v1_registered': True
    })

def register_api(app):
    """
    Register API blueprints with the application.
    
    Args:
        app: Flask application instance
    """
    logger.info("Starting API v1 blueprint registration")
    
    try:
        # Import API modules
        logger.info("Importing API v1 modules")
        from src.api.v1.sentiment import sentiment_bp
        from src.api.v1.products import products_bp
        
        logger.info("Registering sentiment blueprint with API v1")
        api_v1.register_blueprint(sentiment_bp, url_prefix='/sentiment')
        
        logger.info("Registering products blueprint with API v1")
        api_v1.register_blueprint(products_bp, url_prefix='/products')
        
        logger.info("Registering API v1 blueprint with main app")
        # Apply the full prefix during registration
        app.register_blueprint(api_v1, url_prefix='/api/v1')
        
        logger.info('API v1 routes registered successfully')
        
        # Print ALL registered routes for debugging
        logger.info("--- Start Full URL Map ---")
        for rule in app.url_map.iter_rules():
            # Log all rules, not just api/v1
            logger.info(f"Registered route: {rule} | Methods: {rule.methods} | Endpoint: {rule.endpoint}")
        logger.info("--- End Full URL Map ---")
                
        return True
    except ImportError as e:
        logger.error(f"Failed to import API v1 modules: {str(e)}")
        logger.error(traceback.format_exc())
        return False
    except Exception as e:
        logger.error(f"Failed to register API v1 blueprints: {str(e)}")
        logger.error(traceback.format_exc())
        return False 