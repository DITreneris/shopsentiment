"""
Simple HTTP server for serving the frontend files.
"""
import http.server
import socketserver
import os
import webbrowser
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the port to serve on
PORT = 8000

# Change directory to the frontend directory
os.chdir('frontend')

# Create a simple HTTP request handler
Handler = http.server.SimpleHTTPRequestHandler

# Create a TCP server
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    logger.info(f"Serving frontend on port {PORT}")
    logger.info(f"Open your browser at http://localhost:{PORT}")
    
    # Open the browser automatically
    webbrowser.open(f'http://localhost:{PORT}')
    
    # Serve until interrupted
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}") 