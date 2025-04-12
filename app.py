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
        <title>Simple Flask App</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 600px; 
                margin: 0 auto; 
                padding: 20px;
                line-height: 1.6;
            }
            h1 { color: #4285f4; }
            .success { 
                color: #28a745; 
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <h1>Flask App on Heroku</h1>
        <p class="success">✓ Application is working correctly!</p>
        <p>This is a working Flask application deployed to Heroku.</p>
        <p>Current time on server: <strong id="server-time"></strong></p>
        
        <script>
            document.getElementById('server-time').textContent = new Date().toLocaleString();
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True) 