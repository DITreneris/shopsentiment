"""
Web routes for the ShopSentiment application.
These routes handle the front-end web views.
"""

import logging
import os
from datetime import datetime
import sqlite3
from flask import Blueprint, render_template, current_app, g

logger = logging.getLogger(__name__)

# Create a Blueprint for the web routes
web_bp = Blueprint('web', __name__)

def get_db_connection():
    """Get a connection to the SQLite database."""
    if 'db' not in g:
        db_path = os.environ.get('DATABASE_PATH', 'data/shopsentiment.db')
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

def get_products_with_sentiment():
    """Get products with sentiment data from SQLite."""
    db = get_db_connection()
    
    try:
        # Get all products
        products = db.execute('''
            SELECT p.id, p.name, p.description, p.category, p.price
            FROM products p
            ORDER BY p.created_at DESC
        ''').fetchall()
        
        # For each product, get the sentiment data
        result = []
        for product in products:
            # Get review count
            review_count = db.execute('''
                SELECT COUNT(*) as count 
                FROM reviews 
                WHERE product_id = ?
            ''', (product['id'],)).fetchone()['count']
            
            # Get average sentiment
            sentiment_avg = db.execute('''
                SELECT AVG(sentiment_score) as avg_score 
                FROM reviews 
                WHERE product_id = ?
            ''', (product['id'],)).fetchone()['avg_score']
            
            # If there are no reviews, set default values
            if sentiment_avg is None:
                sentiment_avg = 0.5
            
            # Create a dictionary with product and sentiment data
            result.append({
                'id': product['id'],
                'name': product['name'],
                'description': product['description'],
                'category': product['category'],
                'price': product['price'],
                'sentiment_score': round(sentiment_avg, 2),
                'reviews_count': review_count
            })
            
        return result
    except Exception as e:
        logger.error(f"Error getting products with sentiment: {str(e)}")
        return []

def register_web_routes(app):
    """Register the web routes with the application."""
    app.register_blueprint(web_bp)
    
    # Define routes
    @app.route('/')
    def index():
        """Render the index page."""
        return render_template('index.html', 
                              server_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    @app.route('/dashboard')
    def dashboard():
        """Render the dashboard page."""
        try:
            # Get real data from database
            products = get_products_with_sentiment()
            logger.info(f"Retrieved {len(products)} products for dashboard")
            
            # Render the dashboard template with the data
            return render_template('dashboard.html', 
                                products=products,
                                server_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        except Exception as e:
            logger.error(f"Error in dashboard route: {str(e)}")
            # Fallback to sample data if there's an error
            sample_data = [
                {'name': 'Product A', 'sentiment_score': 0.85, 'reviews_count': 128},
                {'name': 'Product B', 'sentiment_score': 0.42, 'reviews_count': 64},
                {'name': 'Product C', 'sentiment_score': 0.91, 'reviews_count': 256}
            ]
            return render_template('dashboard.html', 
                                products=sample_data,
                                server_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    @app.route('/about')
    def about():
        """Render the about page."""
        return render_template('about.html',
                              server_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
