"""
ShopSentiment Main Application

This is the main entry point for the ShopSentiment application.
It initializes the Flask application and sets up the routes.
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run() 