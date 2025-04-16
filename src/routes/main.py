"""
Main web routes for the ShopSentiment application.
This module contains the Blueprint for the main web routes.
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, jsonify

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the index page."""
    return render_template('index.html', 
                          server_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@main_bp.route('/health')
def health():
    """Return the health status of the application."""
    return jsonify({
        'status': 'healthy',
        'service': 'ShopSentiment Analysis',
        'timestamp': datetime.now().isoformat()
    })

@main_bp.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html', 
                          server_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')) 