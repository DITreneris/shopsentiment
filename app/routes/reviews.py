from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models.product import Product
from app.models.review import Review

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/', methods=['GET'])
def get_reviews():
    """Get all reviews, optionally filtered by product_id"""
    reviews_db = Review.get_reviews_db()
    
    # Filter by product_id if provided
    product_id = request.args.get('product_id')
    if product_id:
        reviews = [review for review in reviews_db if review.get('product_id') == product_id]
    else:
        reviews = reviews_db
        
    return jsonify(reviews), 200

@reviews_bp.route('/<review_id>', methods=['GET'])
def get_review(review_id):
    """Get a specific review by ID"""
    reviews_db = Review.get_reviews_db()
    review = Review.get_by_id(review_id, reviews_db)
    
    if not review:
        return jsonify({"error": "Review not found"}), 404
        
    return jsonify(review.to_dict()), 200

@reviews_bp.route('/', methods=['POST'])
@login_required
def create_review():
    """Create a new review"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    product_id = data.get('product_id')
    text = data.get('text')
    
    if not product_id or not text:
        return jsonify({"error": "Product ID and text are required"}), 400
    
    # Verify product exists
    products_db = Product.get_products_db()
    product = Product.get_by_id(product_id, products_db)
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    # Create review
    review = Review(
        product_id=product_id,
        text=text,
        rating=data.get('rating'),
        date=data.get('date')
    )
    
    # Save to database
    reviews_db = Review.get_reviews_db()
    reviews_db.append(review.to_dict())
    Review.save_reviews_db(reviews_db)
    
    return jsonify(review.to_dict()), 201

@reviews_bp.route('/<review_id>', methods=['PUT'])
@login_required
def update_review(review_id):
    """Update a review"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    reviews_db = Review.get_reviews_db()
    review = Review.get_by_id(review_id, reviews_db)
    
    if not review:
        return jsonify({"error": "Review not found"}), 404
    
    # Check if user is admin (for now, any logged-in user can update reviews)
    if current_user.role != 'admin':
        # In a full implementation, you would check if the user owns this review
        pass
    
    # Update fields
    for key, value in data.items():
        if key in ['text', 'rating', 'date']:
            setattr(review, key, value)
    
    # Recalculate sentiment if text or rating changed
    if 'text' in data or 'rating' in data:
        review.sentiment = review.analyze_sentiment()
    
    # Save changes
    for i, r in enumerate(reviews_db):
        if r.get('id') == review_id:
            reviews_db[i] = review.to_dict()
            break
    
    Review.save_reviews_db(reviews_db)
    
    return jsonify(review.to_dict()), 200

@reviews_bp.route('/<review_id>', methods=['DELETE'])
@login_required
def delete_review(review_id):
    """Delete a review"""
    reviews_db = Review.get_reviews_db()
    review = Review.get_by_id(review_id, reviews_db)
    
    if not review:
        return jsonify({"error": "Review not found"}), 404
    
    # Check if user is admin (for now, any logged-in user can delete reviews)
    if current_user.role != 'admin':
        # In a full implementation, you would check if the user owns this review
        pass
    
    # Delete the review
    reviews_db = [r for r in reviews_db if r.get('id') != review_id]
    Review.save_reviews_db(reviews_db)
    
    return jsonify({"message": "Review deleted"}), 200

@reviews_bp.route('/<review_id>/sentiment', methods=['GET'])
def get_review_sentiment(review_id):
    """Get sentiment analysis for a specific review"""
    reviews_db = Review.get_reviews_db()
    review = Review.get_by_id(review_id, reviews_db)
    
    if not review:
        return jsonify({"error": "Review not found"}), 404
        
    return jsonify({
        "review_id": review.id,
        "sentiment": review.sentiment,
        "text": review.text,
        "product_id": review.product_id
    }), 200 