"""
Simple Flask application runner for ShopSentiment.
"""

from flask import Flask, render_template
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'development_key')
app.config['DEBUG'] = True
app.config['CACHE_TYPE'] = 'memory'
app.config['CACHE_TIMEOUT'] = 300

# Register blueprints
from routes.product import product_bp

app.register_blueprint(product_bp)

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
    from datetime import datetime
    return {
        'now': datetime.now(),
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'config': app.config
    }

if __name__ == '__main__':
    logger.info("Starting ShopSentiment Flask application")
    app.run(host='127.0.0.1', port=5000, debug=True) 