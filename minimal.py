from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Minimal App</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 40px;
                line-height: 1.6;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            h1 {
                color: #4285f4;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Minimal Heroku App</h1>
            <p>This is a minimal Flask application successfully deployed to Heroku.</p>
            <p>The application is working correctly.</p>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 