"""
Search API Routes for ShopSentiment

This module provides API endpoints for searching using MongoDB Atlas Search.
"""

from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import current_user
from bson.objectid import ObjectId

from app.utils.atlas_search import (
    search_products, 
    search_reviews,
    search_feedback
)

# Create Blueprint
search_bp = Blueprint('search', __name__, url_prefix='/api/search')

@search_bp.route('/products', methods=['GET'])
def search_products_api():
    """Search for products using Atlas Search."""
    try:
        # Get query parameters
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        min_score = float(request.args.get('min_score', 0.5))
        
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400
            
        # Execute search
        results = search_products(query, limit, offset, min_score)
        
        # Format results for JSON response
        formatted_results = []
        for product in results:
            # Convert ObjectId to string
            product['_id'] = str(product['_id'])
            if product.get('created_by'):
                product['created_by'] = str(product['created_by'])
            
            formatted_results.append(product)
        
        return jsonify({
            'query': query,
            'count': len(formatted_results),
            'results': formatted_results
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error searching products: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@search_bp.route('/reviews', methods=['GET'])
def search_reviews_api():
    """Search for reviews using Atlas Search."""
    try:
        # Get query parameters
        query = request.args.get('q', '')
        product_id = request.args.get('product_id')
        sentiment = request.args.get('sentiment')
        min_rating = request.args.get('min_rating')
        max_rating = request.args.get('max_rating')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400
            
        # Convert rating parameters to integers if provided
        if min_rating is not None:
            min_rating = int(min_rating)
        if max_rating is not None:
            max_rating = int(max_rating)
            
        # Execute search
        results = search_reviews(
            query, 
            product_id, 
            sentiment, 
            min_rating, 
            max_rating, 
            limit, 
            offset
        )
        
        # Format results for JSON response
        formatted_results = []
        for review in results:
            # Convert ObjectId to string
            review['_id'] = str(review['_id'])
            review['product_id'] = str(review['product_id'])
            
            formatted_results.append(review)
        
        return jsonify({
            'query': query,
            'filters': {
                'product_id': product_id,
                'sentiment': sentiment,
                'min_rating': min_rating,
                'max_rating': max_rating
            },
            'count': len(formatted_results),
            'results': formatted_results
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error searching reviews: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@search_bp.route('/feedback', methods=['GET'])
def search_feedback_api():
    """Search for feedback using Atlas Search."""
    try:
        # Get query parameters
        query = request.args.get('q', '')
        entity_type = request.args.get('entity_type')
        entity_id = request.args.get('entity_id')
        min_rating = request.args.get('min_rating')
        max_rating = request.args.get('max_rating')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400
            
        # Convert rating parameters to integers if provided
        if min_rating is not None:
            min_rating = int(min_rating)
        if max_rating is not None:
            max_rating = int(max_rating)
            
        # Execute search
        results = search_feedback(
            query, 
            entity_type, 
            entity_id, 
            min_rating, 
            max_rating, 
            limit, 
            offset
        )
        
        # Format results for JSON response
        formatted_results = []
        for feedback in results:
            # Convert ObjectId to string
            feedback['_id'] = str(feedback['_id'])
            if feedback.get('user_id'):
                feedback['user_id'] = str(feedback['user_id'])
            
            formatted_results.append(feedback)
        
        return jsonify({
            'query': query,
            'filters': {
                'entity_type': entity_type,
                'entity_id': entity_id,
                'min_rating': min_rating,
                'max_rating': max_rating
            },
            'count': len(formatted_results),
            'results': formatted_results
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error searching feedback: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@search_bp.route('/unified', methods=['GET'])
def unified_search_api():
    """
    Unified search endpoint that searches across products, reviews, and feedback.
    Results are grouped by type and ranked by relevance.
    """
    try:
        # Get query parameters
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 5))  # Limit per entity type
        
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400
            
        # Execute searches in parallel (in a real app, we might want to use async)
        product_results = search_products(query, limit)
        review_results = search_reviews(query, limit=limit)
        feedback_results = search_feedback(query, limit=limit)
        
        # Format results
        formatted_products = []
        for product in product_results:
            product['_id'] = str(product['_id'])
            if product.get('created_by'):
                product['created_by'] = str(product['created_by'])
            formatted_products.append(product)
            
        formatted_reviews = []
        for review in review_results:
            review['_id'] = str(review['_id'])
            review['product_id'] = str(review['product_id'])
            formatted_reviews.append(review)
            
        formatted_feedback = []
        for feedback in feedback_results:
            feedback['_id'] = str(feedback['_id'])
            if feedback.get('user_id'):
                feedback['user_id'] = str(feedback['user_id'])
            formatted_feedback.append(feedback)
        
        return jsonify({
            'query': query,
            'products': {
                'count': len(formatted_products),
                'results': formatted_products
            },
            'reviews': {
                'count': len(formatted_reviews),
                'results': formatted_reviews
            },
            'feedback': {
                'count': len(formatted_feedback),
                'results': formatted_feedback
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in unified search: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@search_bp.route('/page', methods=['GET'])
def search_page():
    """Render the search page."""
    return render_template('search.html') 