"""
API package initialization for the ShopSentiment application.
"""

# Import the register_api function at usage time, not module load time
# to avoid circular imports

__all__ = ['register_api']

def register_api(app):
    """
    Register API v1 blueprints with the application.
    
    This is a proxy function that ensures proper importing
    of the API v1 module at runtime.
    
    Args:
        app: Flask application instance
    """
    from src.api.v1 import register_api as v1_register_api
    return v1_register_api(app) 