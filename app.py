"""
ShopSentiment Main Application

This is the main entry point for the ShopSentiment application.
It initializes the Flask application and sets up the routes.
"""

from flask import Flask, send_from_directory, jsonify, request
import os
import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Mock data for API
PRODUCTS = [
    {
        "id": "B123456789",
        "name": "Example Product 1",
        "sentiment": "positive",
        "reviews_count": 5
    },
    {
        "id": "E123456789",
        "name": "Example Product 2",
        "sentiment": "neutral",
        "reviews_count": 3
    },
    {
        "id": "C123456789",
        "name": "Example Product 3",
        "sentiment": "negative",
        "reviews_count": 7
    }
]

# Mock reviews
REVIEWS = {
    "B123456789": [
        {"text": "Great product, very satisfied!", "sentiment": "positive"},
        {"text": "Works as expected, good value.", "sentiment": "positive"},
        {"text": "Better than I expected!", "sentiment": "positive"},
        {"text": "Good quality for the price.", "sentiment": "positive"},
        {"text": "Would recommend to friends.", "sentiment": "positive"}
    ],
    "E123456789": [
        {"text": "It's okay, nothing special.", "sentiment": "neutral"},
        {"text": "Average product, does the job.", "sentiment": "neutral"},
        {"text": "Decent quality, expected more features.", "sentiment": "neutral"}
    ],
    "C123456789": [
        {"text": "Disappointed with the quality.", "sentiment": "negative"},
        {"text": "Not worth the money.", "sentiment": "negative"},
        {"text": "Broke after a week of use.", "sentiment": "negative"},
        {"text": "Poor customer service experience.", "sentiment": "negative"},
        {"text": "Would not recommend.", "sentiment": "negative"},
        {"text": "Doesn't work as advertised.", "sentiment": "negative"},
        {"text": "Very frustrating to use.", "sentiment": "negative"}
    ]
}

# Mock sentiment analysis
SENTIMENT = {
    "B123456789": {"positive": 80, "neutral": 15, "negative": 5, "score": 0.8},
    "E123456789": {"positive": 30, "neutral": 60, "negative": 10, "score": 0.55},
    "C123456789": {"positive": 10, "neutral": 15, "negative": 75, "score": 0.2}
}

# API routes
@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify({"products": PRODUCTS})

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"product": product})

@app.route('/api/products/<product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    if product_id not in REVIEWS:
        return jsonify({"error": "Reviews not found"}), 404
    return jsonify({"reviews": REVIEWS[product_id]})

@app.route('/api/products/<product_id>/sentiment', methods=['GET'])
def get_product_sentiment(product_id):
    if product_id not in SENTIMENT:
        return jsonify({"error": "Sentiment data not found"}), 404
    return jsonify({"sentiment": SENTIMENT[product_id]})

@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"error": "Text is required"}), 400
    
    text = data['text']
    # Simple mock sentiment analysis
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

@app.route('/api/health')
def health_check():
    return jsonify({
        "message": "Shop Sentiment Analysis API is running",
        "status": "ok"
    })

# Debug route
@app.route('/debug')
def debug():
    return jsonify({
        "working_directory": os.getcwd(),
        "directory_contents": os.listdir('.'),
        "frontend_exists": os.path.exists('frontend'),
        "frontend_contents": os.listdir('frontend') if os.path.exists('frontend') else [],
        "env_vars": {k: v for k, v in os.environ.items() if not k.startswith('AWS_') and not k.startswith('HEROKU_')}
    })

# Serve frontend
@app.route('/')
def serve_root():
    try:
        logger.info("Attempting to serve index.html from frontend directory")
        return send_from_directory('frontend', 'index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return jsonify({"error": str(e), "message": "Could not serve index.html"}), 500

@app.route('/<path:path>')
def serve_static(path):
    try:
        logger.info(f"Attempting to serve static file: {path}")
        return send_from_directory('frontend', path)
    except Exception as e:
        logger.error(f"Error serving {path}: {e}")
        try:
            return send_from_directory('frontend', 'index.html')
        except Exception as e2:
            logger.error(f"Error serving fallback index.html: {e2}")
            return jsonify({"error": str(e), "message": f"Could not serve {path}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 