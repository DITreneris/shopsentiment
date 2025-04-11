from flask import render_template, request, redirect, url_for, flash, jsonify, session, send_file
from app import app, get_db_connection, get_users_db, cache, limiter
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
from app.tasks import scrape_amazon, scrape_ebay, scrape_custom, analyze_sentiment
from app.forms import AnalysisForm, FilterForm, ExportForm

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
@cache.cached(timeout=60)  # Cache homepage for 1 minute
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
    
    # Create analysis form for the homepage
    form = AnalysisForm()
    
    return render_template('index.html', recent_products=recent_products, form=form)

# User analyses page
@app.route('/my-analyses')
@login_required
def user_analyses():
    # Create a cache key based on user ID and last update time
    cache_key = f'user_analyses_{current_user.id}_{int(datetime.now().timestamp() // 60)}'  # Cache per minute
    
    @cache.cached(timeout=120, key_prefix=cache_key)
    def get_user_analyses():
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
        return [dict(p) for p in user_products]
    
    products = get_user_analyses()
    return render_template('user_analyses.html', products=products)

# Analysis trigger endpoint
@app.route('/analyze', methods=['GET', 'POST'])
@login_required
@limiter.limit("20 per hour")  # Rate limiting for analysis requests
def analyze():
    form = AnalysisForm()
    
    if form.validate_on_submit():
        try:
            # Get form data
            platform = form.platform.data
            product_id = form.product_id.data
            url = form.url.data or ''  # Handle None value
            
            # Store product info in database with user association
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO products (platform, product_id, url, user_id) VALUES (?, ?, ?, ?)',
                (platform, product_id, url, current_user.id)
            )
            product_db_id = cursor.lastrowid
            conn.commit()
            
            # Launch scraper as a Celery task
            task = None
            if platform == 'amazon':
                task = scrape_amazon.delay(product_id, product_db_id)
                
            elif platform == 'ebay':
                task = scrape_ebay.delay(product_id, product_db_id)
                
            elif platform == 'custom':
                # For custom sites, we'd need a bit more configuration
                config = {
                    'url': url,
                    'selectors': {
                        'review': form.review_selector.data or '',
                        'rating': form.rating_selector.data or '',
                        'date': form.date_selector.data or ''
                    }
                }
                task = scrape_custom.delay(product_id, product_db_id, config)
            
            # Store task ID in session for status checks
            if task:
                # Store in database or use a more persistent session store in production
                if 'tasks' not in session:
                    session['tasks'] = {}
                session['tasks'][str(product_db_id)] = task.id
                session.modified = True
            
            # Queue sentiment analysis task to run after scraping
            analyze_sentiment.apply_async(args=[product_db_id], countdown=60)  # Run after 60 seconds
            
            # Redirect to dashboard with waiting screen
            return redirect(url_for('dashboard', product_id=product_db_id))
            
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    # If GET or form invalid, show form (this handles GET requests to /analyze)
    return render_template('analyze.html', form=form)

# Task status endpoint
@app.route('/task-status/<int:product_id>')
def task_status(product_id):
    from celery.result import AsyncResult
    
    if 'tasks' not in session or str(product_id) not in session['tasks']:
        return jsonify({'status': 'unknown', 'message': 'Task not found'})
    
    task_id = session['tasks'][str(product_id)]
    task_result = AsyncResult(task_id)
    
    status = {
        'status': task_result.status,
        'ready': task_result.ready(),
        'info': task_result.info if task_result.ready() else None
    }
    
    return jsonify(status)

# Dashboard display
@app.route('/dashboard/<int:product_id>')
def dashboard(product_id):
    # Get product info
    conn = get_db_connection()
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
    
    # Get reviews from cache or database
    cache_key = f'product_dashboard_{product_id}'
    
    @cache.cached(timeout=300, key_prefix=cache_key)
    def get_dashboard_data():
        # Get reviews
        reviews_data = conn.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
        
        # If no reviews yet, return None
        if not reviews_data:
            return None
        
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
        
        return {
            'reviews': reviews_df.to_dict('records'),
            'sentiment_counts': sentiment_counts,
            'keywords': keywords,
            'sentiment_by_date': sentiment_by_date
        }
    
    dashboard_data = get_dashboard_data()
    conn.close()
    
    if not dashboard_data:
        # If there's a task in progress, pass task_id to the template
        task_id = None
        if 'tasks' in session and str(product_id) in session['tasks']:
            task_id = session['tasks'][str(product_id)]
        return render_template('waiting.html', product=product, product_id=product_id, task_id=task_id)
    
    # Initialize filter form
    filter_form = FilterForm()
    export_form = ExportForm()
    
    return render_template(
        'dashboard.html',
        product=product,
        sentiment_counts=dashboard_data['sentiment_counts'],
        keywords=dashboard_data['keywords'],
        reviews=dashboard_data['reviews'],
        sentiment_by_date=dashboard_data['sentiment_by_date'],
        filter_form=filter_form,
        export_form=export_form
    )

# Filter reviews
@app.route('/filter/<int:product_id>', methods=['POST'])
def filter_reviews(product_id):
    filter_form = FilterForm()
    
    if filter_form.validate_on_submit():
        conn = get_db_connection()
        
        # Get product info
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if not product:
            flash('Product not found', 'error')
            return redirect(url_for('index'))
        
        # Check permissions
        if product['user_id']:
            if not current_user.is_authenticated or str(product['user_id']) != str(current_user.id):
                flash('You do not have permission to view this analysis', 'error')
                return redirect(url_for('index'))
        
        # Build the query with filter conditions
        query = 'SELECT * FROM reviews WHERE product_id = ?'
        params = [product_id]
        
        # Add filter conditions
        if filter_form.min_rating.data:
            query += ' AND rating >= ?'
            params.append(float(filter_form.min_rating.data))
        
        if filter_form.max_rating.data:
            query += ' AND rating <= ?'
            params.append(float(filter_form.max_rating.data))
        
        if filter_form.sentiment.data:
            if filter_form.sentiment.data == 'positive':
                query += ' AND sentiment > 0.05'
            elif filter_form.sentiment.data == 'neutral':
                query += ' AND sentiment BETWEEN -0.05 AND 0.05'
            elif filter_form.sentiment.data == 'negative':
                query += ' AND sentiment < -0.05'
        
        if filter_form.keyword.data:
            query += ' AND text LIKE ?'
            params.append(f'%{filter_form.keyword.data}%')
        
        if filter_form.date_from.data:
            query += ' AND date >= ?'
            params.append(filter_form.date_from.data)
        
        if filter_form.date_to.data:
            query += ' AND date <= ?'
            params.append(filter_form.date_to.data)
        
        # Get filtered reviews
        reviews = conn.execute(query, params).fetchall()
        conn.close()
        
        # Convert to dictionary for template
        reviews_dict = [dict(row) for row in reviews]
        
        # Create sentiment counts for filtered reviews
        sentiment_counts = {
            'Positive': len([r for r in reviews_dict if r['sentiment'] > 0.05]),
            'Neutral': len([r for r in reviews_dict if -0.05 <= r['sentiment'] <= 0.05]),
            'Negative': len([r for r in reviews_dict if r['sentiment'] < -0.05])
        }
        
        # Get the filter criteria as text for UI
        filter_criteria = []
        if filter_form.min_rating.data:
            filter_criteria.append(f"Min Rating: {filter_form.min_rating.data} stars")
        if filter_form.max_rating.data:
            filter_criteria.append(f"Max Rating: {filter_form.max_rating.data} stars")
        if filter_form.sentiment.data:
            filter_criteria.append(f"Sentiment: {filter_form.sentiment.data}")
        if filter_form.keyword.data:
            filter_criteria.append(f'Keyword: "{filter_form.keyword.data}"')
        if filter_form.date_from.data:
            filter_criteria.append(f"From: {filter_form.date_from.data}")
        if filter_form.date_to.data:
            filter_criteria.append(f"To: {filter_form.date_to.data}")
        
        # Pass all data back to the template
        return render_template(
            'filtered_reviews.html',
            product=product,
            reviews=reviews_dict,
            sentiment_counts=sentiment_counts,
            filter_criteria=filter_criteria,
            filter_form=filter_form,
            export_form=ExportForm()
        )
    
    # If form invalid, redirect back to dashboard
    return redirect(url_for('dashboard', product_id=product_id))

# Export to CSV
@app.route('/export/csv/<int:product_id>')
def export_csv(product_id):
    export_form = ExportForm(request.args)
    conn = get_db_connection()
    
    # Get product info for filename
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('index'))
        
    # Check permissions
    if product['user_id']:
        if not current_user.is_authenticated or str(product['user_id']) != str(current_user.id):
            flash('You do not have permission to export this data', 'error')
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
    
    # Set the header row based on export options
    headers = ['id', 'date', 'rating', 'text']
    if export_form.include_sentiment.data:
        headers.extend(['sentiment', 'sentiment_category'])
    
    writer.writerow(headers)
    
    # Write data rows
    for review in reviews:
        row = [
            review['id'],
            review['date'],
            review['rating'],
            review['text']
        ]
        
        # Add sentiment data if requested
        if export_form.include_sentiment.data:
            row.append(review['sentiment'])
            if review['sentiment'] > 0.05:
                row.append('positive')
            elif review['sentiment'] < -0.05:
                row.append('negative')
            else:
                row.append('neutral')
        
        writer.writerow(row)
    
    # Create a unique filename
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
    export_form = ExportForm(request.args)
    conn = get_db_connection()
    
    # Get product info for filename and metadata
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('index'))
        
    # Check permissions
    if product['user_id']:
        if not current_user.is_authenticated or str(product['user_id']) != str(current_user.id):
            flash('You do not have permission to export this data', 'error')
            return redirect(url_for('index'))
    
    # Get reviews
    reviews = conn.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
    conn.close()
    
    if not reviews:
        flash('No reviews to export', 'warning')
        return redirect(url_for('dashboard', product_id=product_id))
    
    # Convert SQLite rows to dictionaries
    product_dict = dict(product)
    reviews_list = [dict(review) for review in reviews]
    
    # Prepare JSON data based on form options
    export_data = {}
    
    # Include product information if requested
    if export_form.include_product_info.data:
        export_data['product'] = {
            'id': product_dict['product_id'],
            'platform': product_dict['platform'],
            'url': product_dict['url'],
            'created_at': product_dict['created_at']
        }
    
    # Process reviews based on export options
    processed_reviews = []
    for review in reviews_list:
        review_data = {
            'id': review['id'],
            'date': review['date'],
            'rating': review['rating'],
            'text': review['text']
        }
        
        # Include sentiment data if requested
        if export_form.include_sentiment.data:
            review_data['sentiment'] = review['sentiment']
            # Add sentiment category
            if review['sentiment'] > 0.05:
                review_data['sentiment_category'] = 'positive'
            elif review['sentiment'] < -0.05:
                review_data['sentiment_category'] = 'negative'
            else:
                review_data['sentiment_category'] = 'neutral'
        
        processed_reviews.append(review_data)
    
    export_data['reviews'] = processed_reviews
    export_data['metadata'] = {
        'exported_at': datetime.now().isoformat(),
        'review_count': len(processed_reviews),
        'export_type': 'full'
    }
    
    # Create a temporary JSON file
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json') as temp:
        json.dump(export_data, temp, indent=2)
        temp_path = temp.name
    
    # Create a unique filename
    filename = f"{product['platform']}_{product['product_id']}_reviews_{datetime.now().strftime('%Y%m%d')}.json"
    
    return send_file(
        temp_path,
        mimetype='application/json',
        as_attachment=True,
        download_name=filename
    )

# API endpoint for reviews
@app.route('/api/reviews/<int:product_id>')
def api_reviews(product_id):
    # Verify authentication for API access
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
        
    conn = get_db_connection()
    
    # Get product info
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Check permissions (only owner can access)
    if str(product['user_id']) != str(current_user.id):
        return jsonify({'error': 'Access denied'}), 403
        
    # Get reviews
    reviews = conn.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
    conn.close()
    
    # Convert to dictionaries for JSON serialization
    reviews_list = [dict(review) for review in reviews]
    
    return jsonify({
        'product': dict(product),
        'reviews': reviews_list,
        'count': len(reviews_list)
    }) 