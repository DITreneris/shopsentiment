"""
Standalone ShopSentiment application for easy testing.
This version doesn't rely on complex imports from src.
"""

from flask import Flask, render_template, flash, redirect, url_for, request, jsonify
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our models and services
from models.product import Product
from models.review import Review
from services.sentiment_service import create_sentiment_service

# Import the utility modules
import sys
sys.path.append('src')  # Add src directory to path for importing
from utils.cache_adapter import create_cache_adapter
from utils.cache_monitor import CacheMonitor

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'development_key')
app.config['DEBUG'] = True
# Use FLASK_DEBUG instead of FLASK_ENV to avoid deprecation warning
os.environ['FLASK_DEBUG'] = '1'
if 'FLASK_ENV' in os.environ:
    del os.environ['FLASK_ENV']
app.config['CACHE_TYPE'] = 'memory'
app.config['CACHE_TIMEOUT'] = 300

@app.route('/products')
def product_list():
    # Get sorting parameters
    sort_by = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    filter_category = request.args.get('category', None)
    
    # Get products from database
    products = Product.get_all_products()
    
    # Filter products by category if requested
    if filter_category:
        products = [p for p in products if p.category == filter_category]
    
    # Get sentiment service
    sentiment_service = create_sentiment_service()
    
    # Get cache adapter for sentiment data
    cache = create_cache_adapter(
        adapter_type=app.config.get('CACHE_TYPE', 'memory'),
        namespace='sentiment',
        config=app.config.get('CACHE_CONFIG', {})
    )
    
    # Get sentiment data for each product
    product_ids = [p.id for p in products]
    cache_keys = [f'product_sentiment_{pid}' for pid in product_ids]
    
    # Try to get multiple summaries from cache at once
    cached_summaries = cache.get_many(cache_keys)
    
    for product in products:
        cache_key = f'product_sentiment_{product.id}'
        
        # Check if in cache
        if cache_key in cached_summaries:
            summary = cached_summaries[cache_key]
        else:
            # If not in cache, get from service and cache it
            summary = sentiment_service.get_product_sentiment_summary(product.id)
            if summary:
                cache.set(
                    cache_key, 
                    summary, 
                    ttl=app.config.get('CACHE_TIMEOUT', 300)
                )
        
        # Update product with sentiment data if available
        if summary:
            product.sentiment_score = summary.get('average_score', 0)
            product.sentiment_label = summary.get('sentiment_label', 'neutral')
            product.review_count = summary.get('review_count', 0)
    
    # Sort products
    reverse = order == 'desc'
    if sort_by == 'sentiment':
        products.sort(key=lambda x: x.sentiment_score or 0, reverse=reverse)
    elif sort_by == 'reviews':
        products.sort(key=lambda x: x.review_count or 0, reverse=reverse)
    else:  # Default sort by name
        products.sort(key=lambda x: getattr(x, sort_by, ''), reverse=reverse)
    
    # Get all categories for filter dropdown
    categories = sorted(set(p.category for p in Product.get_all_products() if p.category))
    
    return render_template('product_list.html', 
                          products=products, 
                          categories=categories,
                          current_sort=sort_by,
                          current_order=order,
                          current_category=filter_category)

@app.route('/products/<int:product_id>')
def product_detail(product_id):
    """
    Display detailed information about a specific product, including reviews and sentiment analysis.
    """
    product = Product.get_by_id(product_id)
    if not product:
        flash('Product not found', 'error')
        return redirect('/products')
    
    # Get the sentiment service
    sentiment_service = create_sentiment_service()
    
    # Get cache adapter for sentiment data
    cache = create_cache_adapter(
        adapter_type=app.config.get('CACHE_TYPE', 'memory'),
        namespace='sentiment',
        config=app.config.get('CACHE_CONFIG', {})
    )
    
    # Try to get sentiment summary from cache
    cache_key = f'product_sentiment_{product_id}'
    sentiment_summary = cache.get(cache_key)
    
    # If not in cache, get from sentiment service and cache it
    if sentiment_summary is None:
        sentiment_summary = sentiment_service.get_product_sentiment_summary(product_id)
        if sentiment_summary:
            cache.set(
                cache_key, 
                sentiment_summary, 
                ttl=app.config.get('CACHE_TIMEOUT', 300)
            )
    
    # Get reviews for the product
    reviews = Review.get_by_product_id(product_id)
    
    # Render the product detail template with all the data
    return render_template('product_detail.html', 
                           product=product,
                           reviews=reviews,
                           sentiment_summary=sentiment_summary)

@app.route('/cache-stats')
def cache_stats():
    """
    Display cache statistics for product sentiment data.
    For admin and development use.
    """
    # Only allow in development mode
    if not app.debug:
        flash('Cache statistics are only available in development mode', 'warning')
        return redirect('/products')
    
    # Get cache monitor instance
    monitor = CacheMonitor.get_instance()
    stats = monitor.get_metrics()
    
    # Get top keys by hits and misses
    top_hits = monitor.get_top_keys(n=10, sort_by="hits")
    top_misses = monitor.get_top_keys(n=10, sort_by="misses")
    
    return render_template('cache_stats.html',
                          stats=stats,
                          top_hits=top_hits,
                          top_misses=top_misses,
                          title="Product Sentiment Cache Statistics")

@app.route('/cache-stats/reset', methods=['POST'])
def reset_cache_stats():
    """
    Reset the cache statistics for product sentiment data.
    Requires POST method for security.
    """
    # Only allow in development mode
    if not app.debug:
        flash('Cache statistics can only be reset in development mode', 'warning')
        return redirect('/products')
    
    # Get cache monitor instance and reset stats
    monitor = CacheMonitor.get_instance()
    monitor.reset()
    
    flash('Cache statistics have been reset successfully', 'success')
    return redirect('/cache-stats')

@app.route('/')
def index():
    """Home page route."""
    return render_template('dashboard.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard route."""
    return render_template('dashboard.html')

@app.route('/about')
def about():
    """About page."""
    return render_template('about.html', 
                          title="About ShopSentiment",
                          content="ShopSentiment is a tool for analyzing product reviews.")

# Context processor for templates
@app.context_processor
def inject_globals():
    return {
        'now': datetime.now(),
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'config': app.config
    }

if __name__ == '__main__':
    logger.info("Starting ShopSentiment Flask application")
    app.run(host='127.0.0.1', port=5000, debug=True) 