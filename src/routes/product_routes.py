from flask import Blueprint, render_template, request, jsonify, current_app
from datetime import datetime, timedelta
import random

from src.services.sentiment_service import create_sentiment_service

# Create a Blueprint for product routes
product_bp = Blueprint('product', __name__, url_prefix='/products')

@product_bp.route('/')
def product_list():
    """
    Route to display a list of all products
    """
    # In a real application, this would fetch products from the database
    products = get_mock_products()
    return render_template('product_list.html', products=products)

@product_bp.route('/<string:product_id>')
def product_detail(product_id):
    """
    Route to display detailed information about a specific product
    including sentiment analysis results
    """
    # Get the filter parameter (default to 'all')
    filter_type = request.args.get('filter', 'all')
    
    # In a real application, these would be fetched from the database
    product = get_mock_product(product_id)
    sentiment_summary = get_mock_sentiment_summary(product_id)
    reviews = get_mock_reviews(product_id, filter_type)
    trend_data = get_mock_trend_data(product_id)
    insights = get_mock_insights(product_id)
    
    return render_template(
        'product_detail.html',
        product=product,
        sentiment_summary=sentiment_summary,
        reviews=reviews,
        trend_data=trend_data,
        insights=insights
    )

@product_bp.route('/<string:product_id>/api/sentiment')
def product_sentiment_api(product_id):
    """
    API route to get sentiment data for a product
    """
    sentiment_service = create_sentiment_service()
    summary = sentiment_service.get_product_sentiment_summary(product_id)
    
    if not summary:
        return jsonify({
            'error': 'Product not found or no sentiment data available'
        }), 404
    
    return jsonify(summary)

# Mock data helpers (would be replaced with database calls in production)
def get_mock_products():
    """Get a list of mock products for development"""
    return [
        {
            'id': 'p001',
            'name': 'Premium Wireless Headphones',
            'category': 'Electronics',
            'price': '$149.99',
            'image_url': '/static/img/products/headphones.jpg',
            'sentiment_score': 0.82,
            'sentiment_label': 'positive',
            'review_count': 128
        },
        {
            'id': 'p002',
            'name': 'Smart Fitness Tracker',
            'category': 'Wearables',
            'price': '$89.99',
            'image_url': '/static/img/products/fitness-tracker.jpg',
            'sentiment_score': 0.76,
            'sentiment_label': 'positive',
            'review_count': 95
        },
        {
            'id': 'p003',
            'name': 'Ultra-Slim Laptop',
            'category': 'Computers',
            'price': '$899.99',
            'image_url': '/static/img/products/laptop.jpg',
            'sentiment_score': 0.64,
            'sentiment_label': 'neutral',
            'review_count': 52
        },
        {
            'id': 'p004',
            'name': 'Smart Home Speaker',
            'category': 'Smart Home',
            'price': '$129.99',
            'image_url': '/static/img/products/speaker.jpg',
            'sentiment_score': 0.38,
            'sentiment_label': 'negative',
            'review_count': 74
        }
    ]

def get_mock_product(product_id):
    """Get a single mock product by ID"""
    products = get_mock_products()
    for product in products:
        if product['id'] == product_id:
            # Add additional details not in the list view
            product['description'] = 'This is a detailed description of the product. It includes information about features, specifications, and benefits to the customer.'
            product['url'] = '#'
            return product
    
    # Return a default product if ID not found
    return {
        'id': product_id,
        'name': 'Unknown Product',
        'category': 'Miscellaneous',
        'price': '$0.00',
        'description': 'Product details not available',
        'image_url': '/static/img/products/placeholder.jpg',
        'url': '#'
    }

def get_mock_sentiment_summary(product_id):
    """Get mock sentiment summary for a product"""
    products = get_mock_products()
    for product in products:
        if product['id'] == product_id:
            score = product.get('sentiment_score', 0.5)
            label = product.get('sentiment_label', 'neutral')
            
            # Derive class for Bootstrap styling
            sentiment_class = {
                'positive': 'success',
                'neutral': 'warning',
                'negative': 'danger'
            }.get(label, 'secondary')
            
            review_count = product.get('review_count', 0)
            
            # Calculate mock counts based on the score
            positive_count = int(review_count * (score if score > 0.6 else 0.3))
            negative_count = int(review_count * ((1 - score) if score < 0.4 else 0.2))
            neutral_count = review_count - positive_count - negative_count
            
            return {
                'sentiment_score': score,
                'sentiment_label': label,
                'sentiment_class': sentiment_class,
                'review_count': review_count,
                'positive_count': positive_count,
                'neutral_count': neutral_count,
                'negative_count': negative_count,
                'last_updated': datetime.now() - timedelta(hours=random.randint(1, 48))
            }
    
    # Return default if not found
    return {
        'sentiment_score': 0.5,
        'sentiment_label': 'neutral',
        'sentiment_class': 'warning',
        'review_count': 0,
        'positive_count': 0,
        'neutral_count': 0,
        'negative_count': 0,
        'last_updated': None
    }

def get_mock_reviews(product_id, filter_type='all'):
    """Get mock reviews for a product with optional filtering"""
    product = get_mock_product(product_id)
    review_count = product.get('review_count', 10)
    score = product.get('sentiment_score', 0.5)
    
    reviews = []
    
    # Generate some sample review texts based on sentiment
    positive_texts = [
        "Really love this product! It exceeded my expectations in every way.",
        "Great quality and value for money. Would definitely recommend to friends.",
        "Works perfectly and arrived earlier than expected. Very happy with my purchase!",
        "Excellent product, does exactly what it says. Customer service was also top notch.",
        "I've been using this for a month now and it's still performing like new!"
    ]
    
    neutral_texts = [
        "It's okay, nothing special but does the job.",
        "Good product but a bit overpriced for what you get.",
        "Works as described, delivery was a bit slow though.",
        "Average quality. I've seen better but also much worse.",
        "Neither impressed nor disappointed. It's functional."
    ]
    
    negative_texts = [
        "Disappointed with the quality, expected better for the price.",
        "Stopped working after just two weeks of use.",
        "The description is misleading, product is much smaller than shown.",
        "Customer service was unhelpful when I reported issues with the product.",
        "Wouldn't recommend, there are better alternatives available."
    ]
    
    # Generate mock reviews
    for i in range(min(20, review_count)):
        # Random sentiment that follows the overall product sentiment
        r = random.random()
        if r < score * 1.2:  # More likely to be positive if product sentiment is high
            sentiment = 'positive'
            sentiment_score = random.uniform(0.7, 1.0)
            text = random.choice(positive_texts)
        elif r > 1 - ((1 - score) * 1.2):  # More likely to be negative if product sentiment is low
            sentiment = 'negative'
            sentiment_score = random.uniform(0.0, 0.3)
            text = random.choice(negative_texts)
        else:
            sentiment = 'neutral'
            sentiment_score = random.uniform(0.4, 0.6)
            text = random.choice(neutral_texts)
        
        # Skip if filtering is enabled and doesn't match
        if filter_type != 'all' and filter_type != sentiment:
            continue
        
        # Create a mock review
        review = {
            'id': f"r{i+1:03d}",
            'product_id': product_id,
            'customer_name': f"Customer {i+1}",
            'date': datetime.now() - timedelta(days=random.randint(1, 90)),
            'text': text,
            'sentiment_score': sentiment_score,
            'sentiment_label': sentiment
        }
        
        reviews.append(review)
    
    # Sort by date, newest first
    reviews.sort(key=lambda x: x['date'], reverse=True)
    
    return reviews

def get_mock_trend_data(product_id):
    """Generate mock trend data for sentiment over time"""
    product = get_mock_product(product_id)
    score = product.get('sentiment_score', 0.5)
    
    # Generate data for the last 30 days
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
    
    # Generate scores with a slight upward or downward trend based on current score
    trend_direction = 0.001 if score > 0.5 else -0.001
    base_score = max(0.3, min(0.7, score - (trend_direction * 30 * 5)))  # Starting point
    
    scores = []
    counts = []
    
    for i in range(30):
        # Add some random variation to the score
        day_score = min(1.0, max(0.0, base_score + (trend_direction * i * 5) + random.uniform(-0.05, 0.05)))
        scores.append(round(day_score, 2))
        
        # Random review count for each day
        counts.append(random.randint(0, 5))
    
    return {
        'dates': dates,
        'scores': scores,
        'counts': counts
    }

def get_mock_insights(product_id):
    """Generate mock insights for a product"""
    product = get_mock_product(product_id)
    score = product.get('sentiment_score', 0.5)
    
    insights = []
    
    # Generate insights based on the sentiment score
    if score > 0.7:
        insights.append({
            'trend': 'up',
            'text': 'Sentiment has improved by 12% over the last 30 days'
        })
        insights.append({
            'trend': 'up',
            'text': 'Positive reviews mention "quality" and "durability" frequently'
        })
    elif score < 0.4:
        insights.append({
            'trend': 'down',
            'text': 'Sentiment has declined by 8% over the last 30 days'
        })
        insights.append({
            'trend': 'down',
            'text': 'Negative reviews often mention "customer service" issues'
        })
    else:
        insights.append({
            'trend': 'neutral',
            'text': 'Sentiment has remained stable over the last 30 days'
        })
    
    # Add some general insights
    if random.random() > 0.5:
        insights.append({
            'trend': 'up' if random.random() > 0.5 else 'down',
            'text': f'Review volume has {"increased" if random.random() > 0.5 else "decreased"} by {random.randint(5, 20)}% recently'
        })
    
    return insights 