from flask import Blueprint, render_template, current_app, jsonify
from flask_login import login_required, current_user
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Main landing page"""
    logger.info("Rendering index page")
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard page"""
    logger.info(f"User {current_user.id} accessed dashboard")
    return render_template('dashboard.html')

@bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@bp.route('/features')
def features():
    """Features page"""
    return render_template('features.html') 