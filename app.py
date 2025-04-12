"""
ShopSentiment Main Application

This is the main entry point for the ShopSentiment application.
It initializes the Flask application and sets up the routes.
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Shop Sentiment</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 0 auto; padding: 20px; }
            .success { color: green; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Shop Sentiment Analysis</h1>
        <p class="success">Working minimal application!</p>
        <p>This is a basic working version that proves the Flask app can run on Heroku.</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run() 