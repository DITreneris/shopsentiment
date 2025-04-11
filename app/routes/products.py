from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models.product import Product
from app.models.review import Review

products_bp = Blueprint('products', __name__)

@products_bp.route('/', methods=['GET'])
def get_products():
    """Get all products, optionally filtered by user_id"""
    products_db = Product.get_products_db()
    
    # Filter by user_id if provided
    user_id = request.args.get('user_id')
    if user_id:
        products = [product for product in products_db if product.get('user_id') == user_id]
    else:
        products = products_db
        
    return jsonify(products), 200

@products_bp.route('/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product by ID"""
    products_db = Product.get_products_db()
    product = Product.get_by_id(product_id, products_db)
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
        
    return jsonify(product.to_dict()), 200

@products_bp.route('/', methods=['POST'])
@login_required
def create_product():
    """Create a new product"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    platform = data.get('platform')
    product_id = data.get('product_id')
    url = data.get('url')
    
    if not platform or not product_id or not url:
        return jsonify({"error": "Platform, product_id, and URL are required"}), 400
    
    # Create product
    product = Product(
        platform=platform,
        product_id=product_id,
        url=url,
        user_id=current_user.id
    )
    
    # Save to database
    products_db = Product.get_products_db()
    products_db.append(product.to_dict())
    Product.save_products_db(products_db)
    
    return jsonify(product.to_dict()), 201

@products_bp.route('/<product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    """Update a product"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    products_db = Product.get_products_db()
    product = Product.get_by_id(product_id, products_db)
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    # Check if user owns this product
    if product.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    # Update fields
    for key, value in data.items():
        if key in ['platform', 'product_id', 'url']:
            setattr(product, key, value)
    
    # Save changes
    for i, p in enumerate(products_db):
        if p.get('id') == product_id:
            products_db[i] = product.to_dict()
            break
    
    Product.save_products_db(products_db)
    
    return jsonify(product.to_dict()), 200

@products_bp.route('/<product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    """Delete a product"""
    products_db = Product.get_products_db()
    product = Product.get_by_id(product_id, products_db)
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    # Check if user owns this product
    if product.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    # Delete the product
    products_db = [p for p in products_db if p.get('id') != product_id]
    Product.save_products_db(products_db)
    
    # Also delete related reviews
    reviews_db = Review.get_reviews_db()
    reviews_db = [r for r in reviews_db if r.get('product_id') != product_id]
    Review.save_reviews_db(reviews_db)
    
    return jsonify({"message": "Product deleted"}), 200

@products_bp.route('/<product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    """Get all reviews for a product"""
    products_db = Product.get_products_db()
    product = Product.get_by_id(product_id, products_db)
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    reviews_db = Review.get_reviews_db()
    reviews = Review.get_by_product_id(product_id, reviews_db)
    
    return jsonify([review.to_dict() for review in reviews]), 200

@products_bp.route('/<product_id>/sentiment', methods=['GET'])
def get_product_sentiment(product_id):
    """Get sentiment analysis summary for a product"""
    products_db = Product.get_products_db()
    product = Product.get_by_id(product_id, products_db)
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    reviews_db = Review.get_reviews_db()
    reviews = Review.get_by_product_id(product_id, reviews_db)
    
    if not reviews:
        return jsonify({
            "product_id": product_id,
            "sentiment_score": 0,
            "review_count": 0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0
        }), 200
    
    # Calculate sentiment metrics
    sentiment_scores = [review.sentiment for review in reviews]
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
    
    # Count positive, negative, and neutral reviews
    positive_count = sum(1 for s in sentiment_scores if s > 0.2)
    negative_count = sum(1 for s in sentiment_scores if s < -0.2)
    neutral_count = sum(1 for s in sentiment_scores if -0.2 <= s <= 0.2)
    
    return jsonify({
        "product_id": product_id,
        "sentiment_score": avg_sentiment,
        "review_count": len(reviews),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
    }), 200 