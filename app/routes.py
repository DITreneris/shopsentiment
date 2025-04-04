from flask import render_template, request, redirect, url_for, flash, jsonify, session, send_file
from app import app, get_db_connection, get_users_db
import pandas as pd
import json
import os
import subprocess
import sys
import tempfile
import csv
import io
from datetime import datetime
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import Counter
from nltk.tokenize import word_tokenize
import re
from flask_login import login_required, current_user

# Home page
@app.route('/')
def index():
    # Get recent products for display
    conn = get_db_connection()
    
    if current_user.is_authenticated:
        # Show only the user's products if logged in
        recent_products = conn.execute('''
            SELECT p.*, AVG(r.sentiment) as avg_sentiment, datetime(p.created_at) as analyzed_date
            FROM products p
            LEFT JOIN reviews r ON p.id = r.product_id
            WHERE p.user_id = ?
            GROUP BY p.id
            ORDER BY p.created_at DESC
            LIMIT 5
        ''', (current_user.id,)).fetchall()
    else:
        # Show public products if not logged in
        recent_products = conn.execute('''
            SELECT p.*, AVG(r.sentiment) as avg_sentiment, datetime(p.created_at) as analyzed_date
            FROM products p
            LEFT JOIN reviews r ON p.id = r.product_id
            WHERE p.user_id IS NULL
            GROUP BY p.id
            ORDER BY p.created_at DESC
            LIMIT 5
        ''').fetchall()
    
    conn.close()
    
    return render_template('index.html', recent_products=recent_products)

# User analyses page
@app.route('/my-analyses')
@login_required
def user_analyses():
    conn = get_db_connection()
    user_products = conn.execute('''
        SELECT p.*, AVG(r.sentiment) as avg_sentiment, datetime(p.created_at) as analyzed_date,
               COUNT(r.id) as review_count
        FROM products p
        LEFT JOIN reviews r ON p.id = r.product_id
        WHERE p.user_id = ?
        GROUP BY p.id
        ORDER BY p.created_at DESC
    ''', (current_user.id,)).fetchall()
    conn.close()
    
    return render_template('user_analyses.html', products=user_products)

# Analysis trigger endpoint
@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    try:
        # Get form data
        platform = request.form['platform']
        product_id = request.form['product_id']
        url = request.form.get('url', '')  # Make URL optional
        
        # Store product info in database with user association
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO products (platform, product_id, url, user_id) VALUES (?, ?, ?, ?)',
            (platform, product_id, url, current_user.id)
        )
        product_db_id = cursor.lastrowid
        conn.commit()
        
        # Launch scraper (in a real app, this would be a background task)
        # For MVP, this is a simplified version
        if platform == 'amazon':
            # In a production app, would use a task queue like Celery
            # For MVP, just trigger the spider and wait
            spider_path = os.path.join(app.root_path, 'scrapers', 'amazon_spider.py')
            # This is a simplified example - in production would use proper Scrapy project structure
            subprocess.Popen([sys.executable, spider_path, product_id, str(product_db_id)])
            
        elif platform == 'ebay':
            spider_path = os.path.join(app.root_path, 'scrapers', 'ebay_spider.py')
            subprocess.Popen([sys.executable, spider_path, product_id, str(product_db_id)])
            
        elif platform == 'custom':
            # For custom sites, we'd need a bit more configuration
            # This would be expanded in a real implementation
            config_path = os.path.join(app.root_path, 'scrapers', 'configs', f'{product_id}.json')
            with open(config_path, 'w') as f:
                json.dump({
                    'url': url,
                    'selectors': {
                        'review': request.form.get('review_selector', ''),
                        'rating': request.form.get('rating_selector', ''),
                        'date': request.form.get('date_selector', '')
                    }
                }, f)
            
            spider_path = os.path.join(app.root_path, 'scrapers', 'generic_spider.py')
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
    
    # Check if the product belongs to a user and if the current user has permission
    if product['user_id']:
        if not current_user.is_authenticated:
            # If the product has a user_id but no logged-in user, redirect to login
            flash('Please log in to view this analysis', 'error')
            return redirect(url_for('auth.login', next=request.path))
        elif str(product['user_id']) != str(current_user.id):
            # If the product has a user_id, only the owner can view it
            flash('You do not have permission to view this analysis', 'error')
            return redirect(url_for('index'))
    
    # Get reviews
    reviews_data = conn.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
    conn.close()
    
    # If no reviews yet, show a waiting page
    if not reviews_data:
        return render_template('waiting.html', product=product, product_id=product_id)
    
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

# Export to CSV
@app.route('/export/csv/<int:product_id>')
def export_csv(product_id):
    conn = get_db_connection()
    
    # Get product info for filename
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('index'))
        
    # Get reviews
    reviews = conn.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
    conn.close()
    
    if not reviews:
        flash('No reviews to export', 'warning')
        return redirect(url_for('dashboard', product_id=product_id))
    
    # Create a CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['id', 'date', 'rating', 'sentiment', 'text'])
    
    # Write data
    for review in reviews:
        writer.writerow([
            review['id'],
            review['date'],
            review['rating'],
            review['sentiment'],
            review['text']
        ])
    
    # Create response
    output.seek(0)
    filename = f"{product['platform']}_{product['product_id']}_reviews_{datetime.now().strftime('%Y%m%d')}.csv"
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.csv') as temp:
        temp.write(output.getvalue())
        temp_path = temp.name
        
    return send_file(
        temp_path,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

# Export to JSON
@app.route('/export/json/<int:product_id>')
def export_json(product_id):
    conn = get_db_connection()
    
    # Get product info for metadata and filename
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('index'))
        
    # Get reviews
    reviews = conn.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
    conn.close()
    
    if not reviews:
        flash('No reviews to export', 'warning')
        return redirect(url_for('dashboard', product_id=product_id))
    
    # Create JSON data
    data = {
        'product': dict(product),
        'reviews': [dict(review) for review in reviews],
        'export_date': datetime.now().isoformat(),
        'total_reviews': len(reviews)
    }
    
    # Create a temporary file
    filename = f"{product['platform']}_{product['product_id']}_reviews_{datetime.now().strftime('%Y%m%d')}.json"
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json') as temp:
        json.dump(data, temp, indent=2)
        temp_path = temp.name
    
    return send_file(
        temp_path,
        mimetype='application/json',
        as_attachment=True,
        download_name=filename
    )

# API endpoint to get review data in JSON format
@app.route('/api/reviews/<int:product_id>')
def api_reviews(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    
    # Check permissions
    if product and product['user_id']:
        if not current_user.is_authenticated or str(product['user_id']) != str(current_user.id):
            return jsonify({"error": "Access denied"}), 403
    
    reviews = conn.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in reviews])

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