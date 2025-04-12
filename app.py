"""
ShopSentiment Main Application

This is the main entry point for the ShopSentiment application.
It initializes the Flask application and sets up the routes.
"""

import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello from Flask! This is a working Heroku app."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 