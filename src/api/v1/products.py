"""
Product API endpoints for the ShopSentiment application.
Provides routes for accessing and manipulating product data.
"""

import logging
from typing import Dict, Any, List, Optional
from flask import Blueprint, jsonify, request, current_app
from pydantic import ValidationError

from src.models.product import Product, Review
from src.database.product_dal import ProductDAL
from src.database.sqlite_product_dal import SQLiteProductDAL  # Import the SQLite DAL
from src.utils.cache import cached
from src.database.connection import get_database

logger = logging.getLogger(__name__)

# Create a Blueprint for the products API
products_bp = Blueprint('products_api', __name__)

# Initialize the ProductDAL
product_dal = None

# Initialize flag to track if DAL has been set up
dal_setup_complete = False

@products_bp.before_app_request
def setup_dal():
    """Setup the data access layer before the first request."""
    global product_dal, dal_setup_complete
    
    # Only run setup once
    if dal_setup_complete:
        return
    
    # Determine which DAL to use
    use_sqlite = current_app.config.get('USE_SQLITE', False)
    
    if use_sqlite:
        # Use SQLite DAL
        logger.info("Using SQLite database for products")
        product_dal = SQLiteProductDAL()
    else:
        # Try MongoDB DAL first, fall back to SQLite if needed
        try:
            logger.info("Attempting to connect to MongoDB database")
            # Get the MongoDB connection; assume get_database() raises error or returns None on failure
            db = get_database()
            
            # Check if connection succeeded (add a more specific check if needed)
            if db is None:
                raise ConnectionError("Failed to get MongoDB database connection.")
                
            # If connection is successful, instantiate the MongoDB DAL
            product_dal = ProductDAL() # Now instantiated only if db connection is ok
            logger.info("Successfully connected to MongoDB and initialized ProductDAL")
            
        except Exception as e:
            logger.warning(f"Failed to initialize MongoDB connection or DAL: {str(e)}")
            logger.warning("Falling back to SQLite database for products")
            product_dal = SQLiteProductDAL()
            # Ensure the config reflects the fallback state if it wasn't already set
            current_app.config['USE_SQLITE'] = True
    
    dal_setup_complete = True


@products_bp.route('', methods=['GET'])
@cached("products:list")
async def get_products():
    """Get a list of all products."""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 10
            
        # Calculate skip value for pagination
        skip = (page - 1) * limit
        
        # Get products from the database
        products = await product_dal.get_products(skip, limit)
        
        return jsonify({
            'products': products,
            'count': len(products),
            'page': page,
            'limit': limit
        })
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve products'
        }), 500


@products_bp.route('/<product_id>', methods=['GET'])
@cached("products:detail")
async def get_product(product_id):
    """Get detailed information about a specific product."""
    try:
        # Get product from the database
        product = await product_dal.get_product(product_id)
        
        if not product:
            return jsonify({
                'error': 'Not found',
                'message': f'Product with ID {product_id} not found'
            }), 404
            
        return jsonify(product)
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': f'Failed to retrieve product {product_id}'
        }), 500


@products_bp.route('', methods=['POST'])
async def create_product():
    """Create a new product."""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Bad request',
                'message': 'Missing request body'
            }), 400
            
        # Validate product data
        try:
            product = Product(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation error',
                'message': str(e)
            }), 400
            
        # Create product in the database
        product_id = await product_dal.create_product(product)
        
        if not product_id:
            return jsonify({
                'error': 'Internal server error',
                'message': 'Failed to create product'
            }), 500
            
        # Return the created product
        return jsonify({
            'id': product_id,
            'message': 'Product created successfully'
        }), 201
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to create product'
        }), 500


@products_bp.route('/<product_id>', methods=['PUT'])
async def update_product(product_id):
    """Update an existing product."""
    try:
        # Check if product exists
        product = await product_dal.get_product(product_id)
        if not product:
            return jsonify({
                'error': 'Not found',
                'message': f'Product with ID {product_id} not found'
            }), 404
            
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Bad request',
                'message': 'Missing request body'
            }), 400
            
        # Update product in the database
        success = await product_dal.update_product(product_id, data)
        
        if not success:
            return jsonify({
                'error': 'Internal server error',
                'message': 'Failed to update product'
            }), 500
            
        return jsonify({
            'message': 'Product updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': f'Failed to update product {product_id}'
        }), 500


@products_bp.route('/<product_id>', methods=['DELETE'])
async def delete_product(product_id):
    """Delete a product."""
    try:
        # Check if product exists
        product = await product_dal.get_product(product_id)
        if not product:
            return jsonify({
                'error': 'Not found',
                'message': f'Product with ID {product_id} not found'
            }), 404
            
        # Delete product from the database
        success = await product_dal.delete_product(product_id)
        
        if not success:
            return jsonify({
                'error': 'Internal server error',
                'message': 'Failed to delete product'
            }), 500
            
        return jsonify({
            'message': 'Product deleted successfully'
        })
    except Exception as e:
        logger.error(f"Error deleting product {product_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': f'Failed to delete product {product_id}'
        }), 500


@products_bp.route('/<product_id>/reviews', methods=['POST'])
async def add_review(product_id):
    """Add a review to a product."""
    try:
        # Get the analyzer from the app context
        sentiment_service = current_app.extensions.get('sentiment_service')
        if not sentiment_service or not hasattr(sentiment_service, 'analyzer'):
            logger.error("Sentiment service or analyzer not available in app context.")
            return jsonify({'error': 'Service unavailable', 'message': 'Sentiment analysis service is not configured.'}), 503

        analyzer = sentiment_service.analyzer

        # Check if product exists
        product = await product_dal.get_product(product_id)
        if not product:
            return jsonify({
                'error': 'Not found',
                'message': f'Product with ID {product_id} not found'
            }), 404

        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Bad request',
                'message': 'Missing request body'
            }), 400

        # Validate review data
        try:
            review = Review(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation error',
                'message': str(e)
            }), 400

        # Analyze sentiment of the review text
        sentiment_result = analyzer.analyze_text(review.text)
        review.sentiment = sentiment_result.get('label', 'Neutral') # Store label
        review.sentiment_score = sentiment_result.get('score', 0.0) # Store score

        # Add review to the database
        success = await product_dal.add_review(product_id, review)

        if not success:
            return jsonify({
                'error': 'Internal server error',
                'message': 'Failed to add review'
            }), 500

        return jsonify({
            'message': 'Review added successfully',
            'sentiment': review.sentiment,
            'score': review.sentiment_score
        }), 201
    except Exception as e:
        logger.error(f"Error adding review to product {product_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to add review'
        }), 500


@products_bp.route('/search', methods=['GET'])
@cached("products:search")
async def search_products():
    """Search products by text query."""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({
                'error': 'Bad request',
                'message': 'Missing query parameter "q"'
            }), 400
            
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 10
            
        # Calculate skip value for pagination
        skip = (page - 1) * limit
        
        # Search products
        products = await product_dal.search_products(query, skip, limit)
        
        return jsonify({
            'products': products,
            'count': len(products),
            'query': query,
            'page': page,
            'limit': limit
        })
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to search products'
        }), 500 