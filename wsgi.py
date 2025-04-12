from flask import Flask, send_from_directory, jsonify
import os

app = Flask(__name__)

# Serve static files from the frontend directory
@app.route('/')
def serve_root():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('frontend', path)
    except:
        return send_from_directory('frontend', 'index.html')

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