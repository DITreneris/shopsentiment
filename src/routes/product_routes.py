from flask import Blueprint, render_template, request, jsonify, current_app
from datetime import datetime, timedelta
import random

# Import the Celery task
from src.tasks.scraper_tasks import scrape_amazon

from src.services.sentiment_service import create_sentiment_service

# Create a Blueprint for product routes
# Adjusted prefix to /api/v1/products for API endpoints
product_bp = Blueprint('product_api', __name__, url_prefix='/api/v1/products')

# --- Existing Mock Routes (Keep or remove based on project needs) ---
# These routes seem related to a UI/mock data setup

# @product_bp.route('/')
# def product_list():
#     # ... mock data implementation ...

# @product_bp.route('/<string:product_id>')
# def product_detail(product_id):
#     # ... mock data implementation ...

# --- API Routes --- 

@product_bp.route('/sentiment/<string:product_id>', methods=['GET'])
def product_sentiment_api(product_id):
    """
    API route to get sentiment data for a product (using service)
    """
    sentiment_service = create_sentiment_service()
    # Assuming the service uses the actual DAL
    summary = sentiment_service.get_product_sentiment_summary(product_id)
    
    if not summary:
        return jsonify({
            'error': 'Product not found or no sentiment data available'
        }), 404
    
    return jsonify(summary)

@product_bp.route('/scrape', methods=['POST'])
def trigger_amazon_scrape():
    """
    API endpoint to trigger the Amazon scraping task for a given ASIN.
    Expects JSON body: {"asin": "PRODUCT_ASIN"}
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.get_json()
    asin = data.get('asin')
    
    if not asin:
        return jsonify({"error": "Missing 'asin' in request body"}), 400
        
    if not isinstance(asin, str):
         return jsonify({"error": "'asin' must be a string"}), 400

    try:
        # Dispatch the Celery task
        # .delay() is the shortcut for .apply_async()
        task = scrape_amazon.delay(product_asin=asin)
        
        # Return the task ID so the client can check status later
        return jsonify({
            "message": f"Amazon scraping task queued for ASIN: {asin}",
            "task_id": task.id
        }), 202 # 202 Accepted indicates the request is accepted for processing
        
    except Exception as e:
        current_app.logger.error(f"Failed to queue scrape task for ASIN {asin}: {e}")
        return jsonify({"error": "Failed to queue scraping task"}), 500


# --- Mock data helpers (Keep or remove based on project needs) ---
# ... existing mock functions ...