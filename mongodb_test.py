#!/usr/bin/env python3
"""
MongoDB Test Application

A simple Flask application that demonstrates MongoDB connection and functionality.
"""

import os
import logging
from flask import Flask, jsonify, render_template_string
from pymongo import MongoClient
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mongodb_test")

# Load environment variables
load_dotenv()

# Create Flask application
app = Flask(__name__)

# Get MongoDB connection details
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'shopsentiment')

# MongoDB client
client = None
db = None

def get_db():
    """Connect to MongoDB and return the database."""
    global client, db
    if client is None:
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB_NAME]
    return db

@app.route('/')
def index():
    """Display a simple homepage with MongoDB stats."""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ShopSentiment - MongoDB Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; }
            .container { max-width: 800px; margin: 0 auto; }
            .stats { background-color: #f5f5f5; padding: 20px; border-radius: 5px; }
            .collection { margin-bottom: 20px; }
            .collection h3 { margin-top: 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ShopSentiment - MongoDB Integration</h1>
            <p>This page demonstrates the successful connection to MongoDB.</p>
            
            <div class="stats">
                <h2>MongoDB Statistics</h2>
                {% for collection in collections %}
                <div class="collection">
                    <h3>{{ collection.name }}</h3>
                    <p>Document count: {{ collection.count }}</p>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        # Get MongoDB database
        db = get_db()
        
        # Get collection information
        collections = []
        for collection_name in db.list_collection_names():
            collections.append({
                'name': collection_name,
                'count': db[collection_name].count_documents({})
            })
        
        return render_template_string(template, collections=collections)
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/products')
def products():
    """Return all products from MongoDB."""
    try:
        db = get_db()
        products = list(db.products.find({}, {'_id': 1, 'title': 1, 'platform': 1, 'platform_id': 1}))
        
        # Convert ObjectId to string
        for product in products:
            product['_id'] = str(product['_id'])
        
        return jsonify(products)
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews/<product_id>')
def reviews(product_id):
    """Return reviews for a specific product."""
    try:
        from bson import ObjectId
        
        db = get_db()
        reviews = list(db.reviews.find({'product_id': ObjectId(product_id)}))
        
        # Convert ObjectId to string
        for review in reviews:
            review['_id'] = str(review['_id'])
            review['product_id'] = str(review['product_id'])
        
        return jsonify(reviews)
    except Exception as e:
        logger.error(f"Error fetching reviews: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/users')
def users():
    """Return all users from MongoDB."""
    try:
        db = get_db()
        users = list(db.users.find({}, {'_id': 1, 'username': 1, 'email': 1, 'is_admin': 1}))
        
        # Convert ObjectId to string
        for user in users:
            user['_id'] = str(user['_id'])
        
        return jsonify(users)
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "Route not found"}), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info("Starting MongoDB test application")
    app.run(debug=True, host='0.0.0.0', port=5000) 