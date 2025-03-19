#!/usr/bin/env python
import sys
print("Python executable:", sys.executable)
print("Python version:", sys.version)

try:
    from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
    print("Flask imported successfully")
except ImportError as e:
    print("Error importing Flask:", e)
    sys.exit(1)

try:
    import nltk
    print("NLTK imported successfully")
except ImportError as e:
    print("Error importing NLTK:", e)

try:
    import pandas as pd
    print("Pandas imported successfully")
except ImportError as e:
    print("Error importing Pandas:", e)

import os
import sqlite3
import json
import subprocess
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import Counter
from nltk.tokenize import word_tokenize
import re

print("Current working directory:", os.getcwd())
print("Templates directory exists:", os.path.exists('app/templates'))
print("Static directory exists:", os.path.exists('app/static'))

# Initialize Flask app
app = Flask(__name__, 
            template_folder='app/templates',
            static_folder='app/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-development')
app.config['DATABASE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reviews.db')

# Ensure the NLTK data is downloaded
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Initialize database
def init_db():
    conn = get_db_connection()
    
    # Create tables
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            product_id TEXT NOT NULL,
            url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            rating FLOAT,
            date TEXT,
            sentiment FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# Common English stopwords (simplified - would use NLTK's full stopword list in production)
common_stopwords = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
    'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
    'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
    'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
    'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
    'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
    'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down',
    'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here',
    'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
    'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
}

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Analysis trigger endpoint
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Get form data
        platform = request.form['platform']
        product_id = request.form['product_id']
        url = request.form['url']
        
        # Store product info in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO products (platform, product_id, url) VALUES (?, ?, ?)',
            (platform, product_id, url)
        )
        product_db_id = cursor.lastrowid
        conn.commit()
        
        # Launch scraper (in a real app, this would be a background task)
        # For MVP, this is a simplified version
        if platform == 'amazon':
            # In a production app, would use a task queue like Celery
            # For MVP, just trigger the spider and wait
            spider_path = os.path.join('app', 'scrapers', 'amazon_spider.py')
            # This is a simplified example - in production would use proper Scrapy project structure
            subprocess.Popen([sys.executable, spider_path, product_id, str(product_db_id)])
            
        elif platform == 'ebay':
            spider_path = os.path.join('app', 'scrapers', 'ebay_spider.py')
            subprocess.Popen([sys.executable, spider_path, product_id, str(product_db_id)])
            
        elif platform == 'custom':
            # For custom sites, we'd need a bit more configuration
            # This would be expanded in a real implementation
            config_path = os.path.join('app', 'scrapers', 'configs', f'{product_id}.json')
            with open(config_path, 'w') as f:
                json.dump({
                    'url': url,
                    'selectors': {
                        'review': request.form.get('review_selector', ''),
                        'rating': request.form.get('rating_selector', ''),
                        'date': request.form.get('date_selector', '')
                    }
                }, f)
            
            spider_path = os.path.join('app', 'scrapers', 'generic_spider.py')
            subprocess.Popen([sys.executable, spider_path, product_id, str(product_db_id)])
        
        # In real app, would redirect to a status page that polls for completion
        # For MVP, just redirect to dashboard (which may not have data yet)
        return redirect(url_for('dashboard', product_id=product_db_id))
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))

# Dashboard display
@app.route('/dashboard/<int:product_id>')
def dashboard(product_id):
    conn = get_db_connection()
    
    # Get product info
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('index'))
    
    # Get reviews
    reviews_data = conn.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
    conn.close()
    
    # If no reviews yet, show a waiting page
    if not reviews_data:
        return render_template('waiting.html', product=product)
    
    # Convert to DataFrame for analysis
    reviews_df = pd.DataFrame([dict(row) for row in reviews_data])
    
    # Compute sentiment distribution
    sentiment_counts = {
        'Positive': len(reviews_df[reviews_df['sentiment'] > 0.05]),
        'Neutral': len(reviews_df[(reviews_df['sentiment'] >= -0.05) & (reviews_df['sentiment'] <= 0.05)]),
        'Negative': len(reviews_df[reviews_df['sentiment'] < -0.05])
    }
    
    # Extract keywords (simplified - would use more sophisticated NLP in production)
    all_text = ' '.join(reviews_df['text'].tolist())
    # Remove common stopwords and non-alphabetic tokens
    words = [word.lower() for word in word_tokenize(all_text) 
             if word.isalpha() and len(word) > 3 and word.lower() not in common_stopwords]
    keywords = dict(Counter(words).most_common(10))
    
    # Time series of sentiment (simplified)
    # In production would parse dates properly and aggregate by time periods
    sentiment_by_date = reviews_df.sort_values('date').to_dict('records')
    
    return render_template(
        'dashboard.html',
        product=product,
        sentiment_counts=sentiment_counts,
        keywords=keywords,
        reviews=reviews_df.to_dict('records'),
        sentiment_by_date=sentiment_by_date
    )

# API endpoint to get review data in JSON format
@app.route('/api/reviews/<int:product_id>')
def api_reviews(product_id):
    conn = get_db_connection()
    reviews = conn.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in reviews])

# Initialize the database
try:
    print("Initializing database...")
    init_db()
    print("Database initialized successfully")
except Exception as e:
    print("Error initializing database:", e)

print("Starting Flask application...")
if __name__ == '__main__':
    app.run(debug=True) 