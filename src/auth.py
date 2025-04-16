"""
Authentication module for the ShopSentiment application.
"""

import logging
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)

# Create a blueprint for auth routes
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint."""
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({
                'error': 'Bad request',
                'message': 'Missing email or password'
            }), 400
            
        email = data['email']
        password = data['password']
        
        # In a real implementation, this would check against a database
        # For demonstration, using a mock user
        if email == 'user@example.com' and password == 'password':
            session['user_id'] = '1'
            session['email'] = email
            
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': '1',
                    'email': email
                }
            })
        else:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid credentials'
            }), 401
            
    except Exception as e:
        logger.error(f'Error in login endpoint: {str(e)}')
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred during login'
        }), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register endpoint."""
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({
                'error': 'Bad request',
                'message': 'Missing email or password'
            }), 400
            
        email = data['email']
        password = data['password']
        
        # In a real implementation, this would store the user in a database
        # For demonstration, just return success
        return jsonify({
            'message': 'Registration successful',
            'user': {
                'id': '1',
                'email': email
            }
        }), 201
            
    except Exception as e:
        logger.error(f'Error in register endpoint: {str(e)}')
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred during registration'
        }), 500


@auth_bp.route('/me', methods=['GET'])
def me():
    """Get current user information."""
    try:
        if 'user_id' not in session:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Not logged in'
            }), 401
            
        # In a real implementation, this would fetch the user from a database
        return jsonify({
            'user': {
                'id': session['user_id'],
                'email': session.get('email', 'unknown')
            }
        })
            
    except Exception as e:
        logger.error(f'Error in me endpoint: {str(e)}')
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred while fetching user information'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint."""
    try:
        session.pop('user_id', None)
        session.pop('email', None)
        
        return jsonify({
            'message': 'Logout successful'
        })
            
    except Exception as e:
        logger.error(f'Error in logout endpoint: {str(e)}')
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred during logout'
        }), 500


# Function to register the blueprint with the app
def register_auth_routes(app):
    """Register auth routes with the Flask app."""
    app.register_blueprint(auth_bp)
