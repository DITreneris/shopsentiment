from flask import Flask, send_from_directory, jsonify
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info("Starting application")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Directory contents: {os.listdir('.')}")

app = Flask(__name__)

# Debug route to check environment
@app.route('/debug')
def debug():
    return jsonify({
        "working_directory": os.getcwd(),
        "directory_contents": os.listdir('.'),
        "frontend_exists": os.path.exists('frontend'),
        "frontend_contents": os.listdir('frontend') if os.path.exists('frontend') else [],
        "env_vars": {k: v for k, v in os.environ.items() if not k.startswith('AWS_') and not k.startswith('HEROKU_')}
    })

# Serve static files from the frontend directory
@app.route('/')
def serve_root():
    try:
        logger.info("Attempting to serve index.html from frontend directory")
        return send_from_directory('frontend', 'index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return jsonify({"error": str(e), "message": "Could not serve index.html"}), 500

@app.route('/<path:path>')
def serve_static(path):
    try:
        logger.info(f"Attempting to serve static file: {path}")
        return send_from_directory('frontend', path)
    except Exception as e:
        logger.error(f"Error serving {path}: {e}")
        try:
            return send_from_directory('frontend', 'index.html')
        except Exception as e2:
            logger.error(f"Error serving fallback index.html: {e2}")
            return jsonify({"error": str(e), "message": f"Could not serve {path}"}), 500

# Health check endpoint
@app.route('/api/health')
def health_check():
    return jsonify({
        "message": "Shop Sentiment Analysis API is running",
        "status": "ok"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 