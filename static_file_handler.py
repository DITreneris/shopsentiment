"""
Static file handler for ShopSentiment application.

This module provides WSGI middleware for serving static files in production.
It's a simplified version of whitenoise for Flask applications.
"""

import os
import mimetypes
import time
from flask import Flask, send_from_directory

class StaticFileHandler:
    """WSGI middleware for serving static files."""
    
    def __init__(self, app, static_folder='static', max_age=31536000):
        """Initialize the static file handler.
        
        Args:
            app: Flask application
            static_folder: Folder containing static files
            max_age: Cache control max age in seconds
        """
        self.app = app
        self.static_folder = static_folder
        self.max_age = max_age
        self.files = {}
        self._initialize()
        
    def _initialize(self):
        """Find all static files and prepare for serving."""
        if not os.path.isdir(self.static_folder):
            return
            
        for root, _, files in os.walk(self.static_folder):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.static_folder)
                url_path = '/' + rel_path.replace('\\', '/')
                
                mime_type, _ = mimetypes.guess_type(file_path)
                
                self.files[url_path] = {
                    'path': file_path,
                    'mime_type': mime_type or 'application/octet-stream',
                    'mtime': os.path.getmtime(file_path)
                }
    
    def add_static_handler(self):
        """Add static file route to Flask application."""
        @self.app.route('/<path:path>')
        def serve_static(path):
            """Serve static files."""
            url_path = '/' + path
            if url_path in self.files:
                response = send_from_directory(
                    os.path.dirname(self.files[url_path]['path']),
                    os.path.basename(self.files[url_path]['path']),
                    mimetype=self.files[url_path]['mime_type']
                )
                response.cache_control.max_age = self.max_age
                response.cache_control.public = True
                response.add_etag()
                return response
            
            # Not a static file, pass to the next handler
            return self.app.handle_request()

def configure_static_files(app):
    """Configure static file handling for the application.
    
    Args:
        app: Flask application
    """
    if os.environ.get('FLASK_ENV') == 'production' or 'DYNO' in os.environ:
        # In production, use static file handler
        handler = StaticFileHandler(app)
        handler.add_static_handler()
    
    # In development, Flask's built-in static file handling is used 