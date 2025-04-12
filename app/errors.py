"""Error handling module for Shop Sentiment Analysis"""
import logging
import traceback
from functools import wraps
from flask import jsonify, current_app

# Configure logging
logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base class for API errors"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """Convert error to dictionary for JSON response"""
        error_dict = dict(self.payload or {})
        error_dict['error'] = self.message
        error_dict['status'] = 'error'
        return error_dict

# Specific error types
class NotFoundError(APIError):
    """Resource not found error"""
    def __init__(self, message="Resource not found", payload=None):
        super().__init__(message, status_code=404, payload=payload)

class ValidationError(APIError):
    """Validation error for invalid input"""
    def __init__(self, message="Invalid input", payload=None):
        super().__init__(message, status_code=400, payload=payload)

class AuthenticationError(APIError):
    """Authentication error"""
    def __init__(self, message="Authentication failed", payload=None):
        super().__init__(message, status_code=401, payload=payload)

class AuthorizationError(APIError):
    """Authorization error"""
    def __init__(self, message="You don't have permission to perform this action", payload=None):
        super().__init__(message, status_code=403, payload=payload)

def handle_api_errors(app):
    """Register error handlers for API errors"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handler for APIError instances"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handler for 404 Not Found errors"""
        logger.warning(f"Resource not found: {error}")
        return jsonify({'error': 'Resource not found', 'status': 'error'}), 404
    
    @app.errorhandler(500)
    def handle_server_error(error):
        """Handler for 500 Internal Server Error"""
        logger.error(f"Internal Server Error: {error}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error', 'status': 'error'}), 500

def error_handler(f):
    """Decorator to handle errors in route functions"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            # APIError instances will be handled by the registered errorhandler
            raise e
        except Exception as e:
            # Unexpected exceptions are logged and returned as 500 errors
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'error': 'Internal server error', 'status': 'error'}), 500
    
    return decorated 