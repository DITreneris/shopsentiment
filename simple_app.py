from flask import Flask, render_template, request, jsonify
import os

# Create a simple Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Shop Sentiment Analysis API is running"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# Run the app if executed directly
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 