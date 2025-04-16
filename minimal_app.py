"""
Minimal Flask app for testing the cache monitoring feature.
"""

from flask import Flask, render_template, Blueprint

app = Flask(__name__)
app.config['SECRET_KEY'] = 'testing123'
app.config['DEBUG'] = True

# Create a product blueprint
product_bp = Blueprint('product', __name__)

@app.route('/')
def index():
    return "<h1>Home Page</h1><p><a href='/product/cache-stats'>Cache Stats</a></p>"

@product_bp.route('/cache-stats')
def cache_stats():
    return "<h1>Cache Stats Page</h1><p>This is the cache statistics page.</p>"

# Register the blueprint with a URL prefix
app.register_blueprint(product_bp, url_prefix='/product')

if __name__ == '__main__':
    print("Starting minimal Flask app on http://127.0.0.1:5000")
    app.run(debug=True) 