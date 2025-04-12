from flask import Flask, send_from_directory
import os

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Shop Sentiment Analysis</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            h1 {
                color: #4285f4;
                text-align: center;
            }
            .success-message {
                background-color: #d4edda;
                color: #155724;
                padding: 10px;
                border-radius: 4px;
                text-align: center;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Shop Sentiment Analysis</h1>
            <div class="success-message">
                <p>🎉 Application successfully deployed to Heroku! 🎉</p>
                <p>The application is working correctly.</p>
            </div>
            <p>This is a simplified version of the Shop Sentiment Analysis application.</p>
            <p>Features:</p>
            <ul>
                <li>Analyze sentiment of product reviews</li>
                <li>View sentiment breakdown for products</li>
                <li>Track sentiment trends over time</li>
            </ul>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 