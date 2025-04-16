"""
API v1 Package

This package provides the API endpoints for the ShopSentiment application.
"""

import logging
from flask import Blueprint, jsonify

# Import API modules
from src.api.v1.sentiment import sentiment_bp
from src.api.v1.products import products_bp

logger = logging.getLogger(__name__)

# Create main API blueprint
api_v1 = Blueprint('api_v1', __name__, url_prefix='/v1')

@api_v1.route('/info', methods=['GET'])
def api_info():
    """
    Get API information.
    
    Returns:
        JSON response with API information
    """
    return jsonify({
        'name': 'ShopSentiment API',
        'version': '1.0',
        'endpoints': [
            '/api/v1/products',
            '/api/v1/sentiment',
        ]
    })

def register_api(app):
    """
    Register API blueprints with the application.
    
    Args:
        app: Flask application instance
    """
    # Register blueprints
    api_v1.register_blueprint(products_bp, url_prefix='/products')
    api_v1.register_blueprint(sentiment_bp, url_prefix='/sentiment')
    
    # Register API Blueprint with app
    app.register_blueprint(api_v1, url_prefix='/api')
    
    logger.info('API v1 routes registered') 