"""
API Routes for the ShopSentiment application.
This module contains the Blueprint for API routes.
"""

import logging
from flask import Blueprint, jsonify, current_app, request

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

@api_bp.route('/health')
def get_health():
    """
    Health check endpoint.
    
    Returns:
        JSON response with health status
    """
    return jsonify({
        'status': 'healthy',
        'service': 'ShopSentiment API'
    })

@api_bp.route('/sentiment/<product_id>')
def get_sentiment(product_id):
    """
    Get sentiment data for a product.
    
    Args:
        product_id: Product ID to get sentiment for
        
    Returns:
        JSON response with sentiment data
    """
    try:
        # Try to import the mock sentiment function
        try:
            from .product_routes import get_mock_sentiment_summary
            sentiment_data = get_mock_sentiment_summary(product_id)
        except ImportError:
            # Fallback if the module isn't available
            logger.warning("product_routes module not available, using fallback mock data")
            sentiment_data = {
                "product_id": product_id,
                "sentiment_score": 0.75,
                "sentiment_label": "Positive",
                "positive_count": 150,
                "negative_count": 50,
                "neutral_count": 30,
                "total_reviews": 230
            }
            
        return jsonify(sentiment_data)
    except Exception as e:
        logger.error(f"Error getting sentiment data: {str(e)}")
        return jsonify({
            'error': 'Could not retrieve sentiment data',
            'message': str(e)
        }), 500 