"""
API Routes for the ShopSentiment application.
This module contains the Blueprint for API routes.
"""

import logging
from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

@api_bp.route('/health')
def health():
    """Return the health status of the API."""
    return jsonify({
        'status': 'healthy',
        'service': 'ShopSentiment Analysis API'
    })

@api_bp.route('/sentiment/<product_id>')
def get_sentiment(product_id):
    """Return sentiment data for a specific product."""
    # This is a placeholder. In a real implementation, this would
    # call the sentiment service to get real data
    from src.routes.product_routes import get_mock_sentiment_summary
    
    sentiment_data = get_mock_sentiment_summary(product_id)
    return jsonify(sentiment_data) 