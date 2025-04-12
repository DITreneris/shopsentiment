"""
ShopSentiment Main Application

This is the main entry point for the ShopSentiment application.
It initializes the Flask application and sets up the routes.
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory

# Create the Flask application
app = Flask(__name__)

# Configure the app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-development')
app.config['DEBUG'] = os.environ.get('FLASK_ENV', 'development') == 'development'

# Mock data for products
PRODUCTS = [
    {
        "id": "B123456789",
        "name": "Example Product 1",
        "sentiment": "positive",
        "reviews_count": 5,
        "description": "This is a high-quality product with excellent features. Users love its durability and ease of use.",
        "price": "$49.99",
        "rating": 4.7,
        "features": ["Durable", "Easy to use", "Long battery life", "Lightweight"],
        "image_url": "https://via.placeholder.com/300x200?text=Product+1"
    },
    {
        "id": "E123456789",
        "name": "Example Product 2",
        "sentiment": "neutral",
        "reviews_count": 3,
        "description": "A standard product that meets most user expectations. Some find it useful while others think it's just average.",
        "price": "$29.99",
        "rating": 3.5,
        "features": ["Affordable", "Standard quality", "Easy setup"],
        "image_url": "https://via.placeholder.com/300x200?text=Product+2"
    },
    {
        "id": "C123456789",
        "name": "Example Product 3",
        "sentiment": "negative",
        "reviews_count": 7,
        "description": "This product has received mixed reviews, with many users reporting issues with quality and reliability.",
        "price": "$39.99",
        "rating": 2.1,
        "features": ["Low cost", "Fast shipping", "Multiple colors"],
        "image_url": "https://via.placeholder.com/300x200?text=Product+3"
    }
]

# Mock reviews data
REVIEWS = {
    "B123456789": [
        {"text": "Great product, very satisfied!", "sentiment": "positive", "author": "John D.", "date": "2025-03-15", "rating": 5},
        {"text": "Works as expected, good value.", "sentiment": "positive", "author": "Sarah M.", "date": "2025-03-10", "rating": 4},
        {"text": "Better than I expected!", "sentiment": "positive", "author": "Robert K.", "date": "2025-02-28", "rating": 5},
        {"text": "Good quality for the price.", "sentiment": "positive", "author": "Lisa T.", "date": "2025-02-22", "rating": 4},
        {"text": "Would recommend to friends.", "sentiment": "positive", "author": "Michael P.", "date": "2025-02-15", "rating": 5}
    ],
    "E123456789": [
        {"text": "It's okay, nothing special.", "sentiment": "neutral", "author": "David W.", "date": "2025-03-12", "rating": 3},
        {"text": "Average product, does the job.", "sentiment": "neutral", "author": "Emily R.", "date": "2025-02-25", "rating": 3},
        {"text": "Decent quality, expected more features.", "sentiment": "neutral", "author": "James L.", "date": "2025-02-10", "rating": 4}
    ],
    "C123456789": [
        {"text": "Disappointed with the quality.", "sentiment": "negative", "author": "Patricia G.", "date": "2025-03-20", "rating": 2},
        {"text": "Not worth the money.", "sentiment": "negative", "author": "Thomas H.", "date": "2025-03-05", "rating": 1},
        {"text": "Broke after a week of use.", "sentiment": "negative", "author": "Jessica F.", "date": "2025-02-28", "rating": 1},
        {"text": "Poor customer service experience.", "sentiment": "negative", "author": "Richard S.", "date": "2025-02-20", "rating": 2},
        {"text": "Would not recommend.", "sentiment": "negative", "author": "Jennifer B.", "date": "2025-02-15", "rating": 2},
        {"text": "Doesn't work as advertised.", "sentiment": "negative", "author": "Charles M.", "date": "2025-02-10", "rating": 2},
        {"text": "Very frustrating to use.", "sentiment": "negative", "author": "Karen L.", "date": "2025-02-05", "rating": 3}
    ]
}

# Mock sentiment analysis data
SENTIMENT = {
    "B123456789": {"positive": 80, "neutral": 15, "negative": 5, "score": 0.8},
    "E123456789": {"positive": 30, "neutral": 60, "negative": 10, "score": 0.55},
    "C123456789": {"positive": 10, "neutral": 15, "negative": 75, "score": 0.2}
}

# Home page route
@app.route('/')
def home():
    return render_template('index.html')

# Product detail page route
@app.route('/product/<product_id>')
def product_detail(product_id):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return render_template('error.html', message="Product not found"), 404
    return render_template('product_detail.html', product=product)

# API Routes
@app.route('/api/products', methods=['GET'])
def get_products():
    """API endpoint to get all products"""
    return jsonify({"products": PRODUCTS})

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """API endpoint to get a specific product by ID"""
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"product": product})

@app.route('/api/products/<product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    """API endpoint to get reviews for a specific product"""
    if product_id not in REVIEWS:
        return jsonify({"error": "Reviews not found"}), 404
    return jsonify({"reviews": REVIEWS[product_id]})

@app.route('/api/products/<product_id>/sentiment', methods=['GET'])
def get_product_sentiment(product_id):
    """API endpoint to get sentiment analysis for a specific product"""
    if product_id not in SENTIMENT:
        return jsonify({"error": "Sentiment data not found"}), 404
    return jsonify({"sentiment": SENTIMENT[product_id]})

@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    """API endpoint to analyze sentiment of provided text"""
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"error": "Text is required"}), 400
    
    text = data['text']
    # Simple sentiment analysis
    if any(word in text.lower() for word in ['great', 'good', 'excellent', 'happy', 'satisfied']):
        sentiment = "positive"
        score = 0.8
    elif any(word in text.lower() for word in ['bad', 'poor', 'terrible', 'awful', 'disappointed']):
        sentiment = "negative"
        score = 0.2
    else:
        sentiment = "neutral"
        score = 0.5
    
    return jsonify({
        "result": {
            "sentiment": sentiment,
            "score": score,
            "timestamp": datetime.now().isoformat()
        }
    })

# Health check endpoint
@app.route('/api/health')
def health_check():
    """API endpoint for health check"""
    return jsonify({
        "message": "Shop Sentiment Analysis API is running",
        "status": "ok"
    })

# Debug endpoint
@app.route('/debug')
def debug():
    """Debug endpoint with system information"""
    return jsonify({
        "working_directory": os.getcwd(),
        "directory_contents": os.listdir('.'),
        "templates_exist": os.path.exists('templates'),
        "static_exist": os.path.exists('static'),
        "env_vars": {k: v for k, v in os.environ.items() 
                    if not k.startswith('AWS_') and not k.startswith('HEROKU_')}
    })

# Serve static files in development
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Create an error template if it doesn't exist
if not os.path.exists('templates/error.html'):
    os.makedirs('templates', exist_ok=True)
    with open('templates/error.html', 'w') as f:
        f.write("""
        {% extends 'base.html' %}
        
        {% block title %}Error - {{ message }}{% endblock %}
        
        {% block content %}
        <div class="error-container">
            <h2>Error</h2>
            <p>{{ message }}</p>
            <a href="{{ url_for('home') }}" class="back-button">Back to Home</a>
        </div>
        {% endblock %}
        """)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 