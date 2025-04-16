"""
Super simple Dashboard App - No imports needed beyond Flask
"""
import os
import sys
import sqlite3
from datetime import datetime

try:
    from flask import Flask, render_template, g
except ImportError:
    print("Installing Flask...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
    from flask import Flask, render_template, g

# Create the sample database and data
DB_PATH = 'simple_shop.db'

def create_sample_data():
    """Create the database and populate with sample data"""
    print("Creating sample database...")
    
    # Define sample data
    products = [
        ("Smart Watch Pro", "Electronics", 199.99),
        ("Ultra HD 4K TV", "Electronics", 649.99),
        ("Premium Coffee Maker", "Home & Kitchen", 129.99)
    ]
    
    reviews = [
        (1, "JohnD", 5, "Love this product!", 0.95),
        (1, "SarahK", 4, "Good but expensive", 0.65),
        (1, "MikeR", 2, "Stopped working quickly", 0.25),
        (2, "EmmaL", 5, "Amazing picture quality", 0.85),
        (2, "DavidW", 3, "Average TV", 0.50),
        (3, "LisaM", 5, "Great coffee maker", 0.90)
    ]
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        price REAL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY,
        product_id INTEGER,
        user_name TEXT,
        rating INTEGER,
        text TEXT,
        sentiment_score REAL,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    # Insert sample data
    cursor.execute("DELETE FROM reviews")
    cursor.execute("DELETE FROM products")
    
    for product in products:
        cursor.execute("INSERT INTO products (name, category, price) VALUES (?, ?, ?)", product)
    
    for review in reviews:
        cursor.execute("INSERT INTO reviews (product_id, user_name, rating, text, sentiment_score) VALUES (?, ?, ?, ?, ?)", review)
    
    conn.commit()
    conn.close()
    print("Sample data created successfully!")

# Create Flask application
app = Flask(__name__, template_folder='templates', static_folder='static')

# Add context processor to inject 'now' into all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Database helper functions
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_product_data():
    db = get_db()
    # Query for products and their sentiment scores
    products = db.execute('''
        SELECT p.id, p.name, p.category, p.price,
               AVG(r.sentiment_score) as sentiment_score,
               COUNT(r.id) as reviews_count
        FROM products p
        LEFT JOIN reviews r ON p.id = r.product_id
        GROUP BY p.id
    ''').fetchall()
    
    # Convert to list of dictionaries
    result = []
    for p in products:
        result.append({
            'id': p['id'],
            'name': p['name'],
            'category': p['category'],
            'price': p['price'],
            'sentiment_score': round(p['sentiment_score'] or 0.5, 2),
            'reviews_count': p['reviews_count']
        })
    return result

# Define routes
@app.route('/')
def index():
    server_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f'''
    <html>
        <head>
            <title>ShopSentiment</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                h1 {{ color: #4285f4; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to ShopSentiment</h1>
                <p>Analyze and understand customer sentiment to improve your business</p>
                <p><a href="/dashboard">View Dashboard</a></p>
                <p>Server time: {server_time}</p>
            </div>
        </body>
    </html>
    '''

@app.route('/dashboard')
def dashboard():
    # Get product data
    products = get_product_data()
    server_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Calculate metrics
    total_products = len(products)
    if total_products > 0:
        avg_sentiment = sum(p['sentiment_score'] for p in products) / total_products
        total_reviews = sum(p['reviews_count'] for p in products)
    else:
        avg_sentiment = 0
        total_reviews = 0
    
    return render_template('dashboard.html', 
                          products=products,
                          server_time=server_time,
                          now=datetime.now())

@app.route('/about')
def about():
    """About page route."""
    server_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f'''
    <html>
        <head>
            <title>About - ShopSentiment</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                h1 {{ color: #4285f4; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>About ShopSentiment</h1>
                <p>ShopSentiment is a powerful tool for analyzing customer sentiment from product reviews.</p>
                <p>It uses natural language processing to determine the sentiment of reviews and provides 
                   actionable insights to help improve product offerings.</p>
                <p><a href="/">Home</a> | <a href="/dashboard">Dashboard</a></p>
                <p>Server time: {server_time}</p>
            </div>
        </body>
    </html>
    '''

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        create_sample_data()
    
    print("\nStarting simple dashboard application...")
    print("URL: http://localhost:5000")
    print("Dashboard: http://localhost:5000/dashboard")
    print("Press Ctrl+C to stop\n")
    
    # Run the Flask app
    app.run(host='127.0.0.1', port=5000, debug=True) 