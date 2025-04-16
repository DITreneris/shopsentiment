"""
Security utilities for the ShopSentiment application.
Implements CSRF protection, rate limiting, and other security features.
"""

import logging
import secrets
from functools import wraps
from flask import request, abort, current_app, session, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)

# Create a rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)


def generate_csrf_token():
    """Generate a new CSRF token and store it in the session."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def csrf_required(f):
    """
    Decorator to require a valid CSRF token for POST, PUT, DELETE requests.
    The token must be provided in either the request header 'X-CSRF-Token'
    or as a form field '_csrf_token'.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Only check CSRF for state-changing methods
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            token = request.headers.get('X-CSRF-Token')
            if not token:
                # Check for token in form data
                token = request.form.get('_csrf_token')
                
            # Check for token in JSON data
            if not token and request.is_json:
                token = request.get_json().get('_csrf_token')
                
            if not token or token != session.get('csrf_token'):
                logger.warning('CSRF token validation failed')
                return jsonify({'error': 'Invalid CSRF token'}), 403
                
        return f(*args, **kwargs)
    return decorated_function


def setup_security(app):
    """Set up security features for the application."""
    # Set secure headers
    @app.after_request
    def set_secure_headers(response):
        # Content Security Policy
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        
        # Prevent XSS
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Prevent content type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Set HSTS header in production
        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
        return response
    
    # Register limiter
    limiter.init_app(app)
    
    # Add CSRF token to all templates
    app.jinja_env.globals['csrf_token'] = generate_csrf_token
    
    # Create a template for rate limit responses
    @limiter.request_filter
    def exempt_internal_ips():
        """Exempt internal IPs from rate limiting."""
        internal_ips = app.config.get('INTERNAL_IPS', [])
        return request.remote_addr in internal_ips


def setup_input_validation(app):
    """Set up input validation for the application."""
    @app.before_request
    def validate_input():
        """Validate input parameters for all requests."""
        if request.is_json:
            try:
                # Ensure that the JSON is valid
                request.get_json()
            except Exception as e:
                logger.warning(f'Invalid JSON in request: {str(e)}')
                return jsonify({'error': 'Invalid JSON in request'}), 400 