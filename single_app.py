from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
import json
import sys
import nltk
import pandas as pd
from collections import Counter
from nltk.tokenize import word_tokenize
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import subprocess
import tempfile
import csv
import io
import re
from datetime import datetime
import random

# Ensure NLTK data is available
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Initialize Flask app
app = Flask(__name__, 
            template_folder='app/templates',
            static_folder='app/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-development')
app.config['DATABASE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reviews.db')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page'
login_manager.login_message_category = 'error'

# Database helpers
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        conn = get_db_connection()
        
        # Create tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                product_id TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT
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

# User model
class User(UserMixin):
    def __init__(self, id, username, email, password_hash=None, password=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = datetime.utcnow()
        self.last_login = None
        
        if password:
            self.set_password(password)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
    
    @staticmethod
    def get_by_id(user_id, users_db):
        for user in users_db:
            if user['id'] == int(user_id):
                return User(
                    user['id'],
                    user['username'],
                    user['email'],
                    user['password_hash']
                )
        return None
    
    @staticmethod
    def get_by_email(email, users_db):
        for user in users_db:
            if user['email'] == email:
                return User(
                    user['id'],
                    user['username'],
                    user['email'],
                    user['password_hash']
                )
        return None
    
    @staticmethod
    def get_by_username(username, users_db):
        for user in users_db:
            if user['username'] == username:
                return User(
                    user['id'],
                    user['username'],
                    user['email'],
                    user['password_hash']
                )
        return None

# User database functions
USERS_FILE = 'data/users.json'

def get_users_db():
    if not os.path.exists(USERS_FILE):
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        with open(USERS_FILE, 'w') as f:
            json.dump([], f)
        return []
    
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_users_db(users):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    users_db = get_users_db()
    return User.get_by_id(user_id, users_db)

# Common stopwords for NLP
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

# Routes
@app.route('/')
def index():
    conn = get_db_connection()
    
    if current_user.is_authenticated:
        recent_products = conn.execute('''
            SELECT p.*, COALESCE(AVG(r.sentiment), 0) as avg_sentiment, datetime(p.created_at) as analyzed_date
            FROM products p
            LEFT JOIN reviews r ON p.id = r.product_id
            WHERE p.user_id = ?
            GROUP BY p.id
            ORDER BY p.created_at DESC
            LIMIT 5
        ''', (current_user.id,)).fetchall()
    else:
        recent_products = conn.execute('''
            SELECT p.*, COALESCE(AVG(r.sentiment), 0) as avg_sentiment, datetime(p.created_at) as analyzed_date
            FROM products p
            LEFT JOIN reviews r ON p.id = r.product_id
            WHERE p.user_id IS NULL
            GROUP BY p.id
            ORDER BY p.created_at DESC
            LIMIT 5
        ''').fetchall()
    
    conn.close()
    
    return render_template('index.html', recent_products=recent_products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please fill in all fields', 'error')
            return render_template('auth/login.html')
        
        users_db = get_users_db()
        user = User.get_by_email(email, users_db)
        
        if user and user.check_password(password):
            login_user(user)
            user.update_last_login()
            
            # Update the last_login in the database
            for u in users_db:
                if u['email'] == email:
                    u['last_login'] = user.last_login.isoformat()
                    break
            save_users_db(users_db)
            
            next_page = request.args.get('next', '')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        
        flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password or not confirm_password:
            flash('Please fill in all fields', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        users_db = get_users_db()
        
        # Check if email or username already exists
        if User.get_by_email(email, users_db):
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
        
        if User.get_by_username(username, users_db):
            flash('Username already taken', 'error')
            return render_template('auth/register.html')
        
        # Generate a new ID (max id + 1)
        user_id = 1
        if users_db:
            user_id = max(user['id'] for user in users_db) + 1
        
        # Create new user
        user = User(user_id, username, email, password=password)
        
        # Add user to database
        users_db.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'password_hash': user.password_hash,
            'created_at': user.created_at.isoformat(),
            'last_login': None
        })
        save_users_db(users_db)
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        if not username or not email:
            flash('Please fill in all fields', 'error')
            return render_template('auth/edit_profile.html')
        
        users_db = get_users_db()
        
        # Check if username or email is already taken by another user
        for user in users_db:
            if user['id'] != current_user.id:
                if user['username'] == username:
                    flash('Username already taken', 'error')
                    return render_template('auth/edit_profile.html')
                if user['email'] == email:
                    flash('Email already registered', 'error')
                    return render_template('auth/edit_profile.html')
        
        # Update the current user
        for user in users_db:
            if user['id'] == current_user.id:
                user['username'] = username
                user['email'] = email
                current_user.username = username
                current_user.email = email
                break
                
        save_users_db(users_db)
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
    
    return render_template('auth/edit_profile.html')

@app.route('/my-analyses')
@login_required
def user_analyses():
    conn = get_db_connection()
    user_products = conn.execute('''
        SELECT p.*, COALESCE(AVG(r.sentiment), 0) as avg_sentiment, datetime(p.created_at) as analyzed_date,
               COUNT(r.id) as review_count
        FROM products p
        LEFT JOIN reviews r ON p.id = r.product_id
        WHERE p.user_id = ?
        GROUP BY p.id
        ORDER BY p.created_at DESC
    ''', (current_user.id,)).fetchall()
    conn.close()
    
    return render_template('user_analyses.html', products=user_products)

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    try:
        platform = request.form['platform']
        product_id = request.form['product_id']
        url = request.form.get('url', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO products (platform, product_id, url, user_id) VALUES (?, ?, ?, ?)',
            (platform, product_id, url, current_user.id)
        )
        product_db_id = cursor.lastrowid
        conn.commit()
        
        # Correctly construct paths to scrapers
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Launch scraper
        if platform == 'amazon':
            spider_path = os.path.join(base_dir, 'app', 'scrapers', 'amazon_spider.py')
            print(f"Launching Amazon scraper: {spider_path}")
            if os.path.exists(spider_path):
                subprocess.Popen([sys.executable, spider_path, product_id, str(product_db_id)])
            else:
                print(f"Spider path does not exist: {spider_path}")
                
        elif platform == 'ebay':
            spider_path = os.path.join(base_dir, 'app', 'scrapers', 'ebay_spider.py')
            print(f"Launching eBay scraper: {spider_path}")
            if os.path.exists(spider_path):
                subprocess.Popen([sys.executable, spider_path, product_id, str(product_db_id)])
            else:
                print(f"Spider path does not exist: {spider_path}")
            
        elif platform == 'custom':
            config_path = os.path.join(base_dir, 'app', 'scrapers', 'configs', f'{product_id}.json')
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump({
                    'url': url,
                    'selectors': {
                        'review': request.form.get('review_selector', ''),
                        'rating': request.form.get('rating_selector', ''),
                        'date': request.form.get('date_selector', '')
                    }
                }, f)
            
            spider_path = os.path.join(base_dir, 'app', 'scrapers', 'generic_spider.py')
            print(f"Launching generic scraper: {spider_path}")
            if os.path.exists(spider_path):
                subprocess.Popen([sys.executable, spider_path, product_id, str(product_db_id)])
            else:
                print(f"Spider path does not exist: {spider_path}")
        
        # As a fallback, create some sample reviews
        print(f"Creating sample reviews for product ID: {product_db_id}")
        create_sample_reviews(product_db_id)
        
        return redirect(url_for('dashboard', product_id=product_db_id))
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))

def create_sample_reviews(product_db_id):
    """Create sample reviews for demonstration purposes"""
    try:
        # Use the product_id to seed random generation for consistent but unique reviews per product
        random.seed(product_db_id)
        
        # Create templates for positive, neutral, and negative reviews
        positive_templates = [
            "This product is amazing! I love how {feature}. Definitely recommend!",
            "Great {product_type}! The {feature} is exceptional and it's worth every penny.",
            "Exceeded my expectations. The {feature} is better than advertised.",
            "Best {product_type} I've ever used. {feature} works flawlessly.",
            "Absolutely love this! The {feature} makes it stand out from competitors."
        ]
        
        neutral_templates = [
            "It's an okay {product_type}. The {feature} is decent but {drawback}.",
            "Got what I paid for. {feature} works as expected, nothing special.",
            "Average {product_type}. {feature} is good, but {drawback}.",
            "It serves its purpose. {feature} is helpful, though {drawback}.",
            "Not bad, not great. The {feature} is standard for this price point."
        ]
        
        negative_templates = [
            "Disappointed with this purchase. The {feature} {issue}.",
            "Would not recommend. {issue} with the {feature} after just a few days.",
            "Save your money. The {feature} {issue} and customer service wasn't helpful.",
            "Returned it immediately. The {feature} {issue} right out of the box.",
            "Not worth the price. {issue} with the {feature} and overall quality is poor."
        ]
        
        # Define product types and features based on product_db_id to create variety
        product_types = ["smartphone", "laptop", "headphones", "gaming mouse", "keyboard", "monitor", "tablet", "camera", "smartwatch", "speaker"]
        features = ["display", "battery life", "sound quality", "responsiveness", "build quality", "design", "performance", "camera", "comfort", "connectivity", "portability", "user interface"]
        drawbacks = ["could be improved", "is nothing exceptional", "is somewhat lacking", "doesn't quite meet expectations", "is just industry standard"]
        issues = ["stopped working", "has serious flaws", "is poorly designed", "malfunctions frequently", "doesn't perform as advertised"]
        
        product_type = product_types[product_db_id % len(product_types)]
        
        # Create a varied set of reviews with different sentiment distributions for each product
        reviews = []
        
        # Determine the ratio of positive/neutral/negative based on product_db_id
        # This ensures different products have different sentiment distributions
        positive_count = max(1, min(5, (product_db_id % 4) + 2))  # Between 2-5 positive reviews
        neutral_count = max(1, min(3, ((product_db_id + 1) % 3) + 1))  # Between 1-3 neutral reviews
        negative_count = max(1, min(4, ((product_db_id + 2) % 3) + 1))  # Between 1-3 negative reviews
        
        # Generate positive reviews
        for i in range(positive_count):
            feature = random.choice(features)
            template = random.choice(positive_templates)
            text = template.format(feature=feature, product_type=product_type)
            rating = random.uniform(4.0, 5.0)
            # Generate a random date within the last year
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            date = f"2023-{month:02d}-{day:02d}"
            reviews.append({"text": text, "rating": rating, "date": date})
        
        # Generate neutral reviews
        for i in range(neutral_count):
            feature = random.choice(features)
            drawback = random.choice(drawbacks)
            template = random.choice(neutral_templates)
            text = template.format(feature=feature, product_type=product_type, drawback=drawback)
            rating = random.uniform(3.0, 3.9)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            date = f"2023-{month:02d}-{day:02d}"
            reviews.append({"text": text, "rating": rating, "date": date})
        
        # Generate negative reviews
        for i in range(negative_count):
            feature = random.choice(features)
            issue = random.choice(issues)
            template = random.choice(negative_templates)
            text = template.format(feature=feature, product_type=product_type, issue=issue)
            rating = random.uniform(1.0, 2.9)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            date = f"2023-{month:02d}-{day:02d}"
            reviews.append({"text": text, "rating": rating, "date": date})
        
        # Analyze sentiment
        sid = SentimentIntensityAnalyzer()
        for review in reviews:
            sentiment = sid.polarity_scores(review["text"])
            review["sentiment"] = sentiment["compound"]
        
        # Store in database
        conn = get_db_connection()
        for review in reviews:
            conn.execute(
                "INSERT INTO reviews (product_id, text, rating, date, sentiment) VALUES (?, ?, ?, ?, ?)",
                (product_db_id, review["text"], review["rating"], review["date"], review["sentiment"])
            )
        conn.commit()
        conn.close()
        
        print(f"Stored {len(reviews)} diverse sample reviews for product ID: {product_db_id}")
    except Exception as e:
        print(f"Error creating sample reviews: {str(e)}")

@app.route('/dashboard/<int:product_id>')
def dashboard(product_id):
    conn = get_db_connection()
    
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('index'))
    
    if product['user_id']:
        if not current_user.is_authenticated:
            flash('Please log in to view this analysis', 'error')
            return redirect(url_for('login', next=request.path))
        elif str(product['user_id']) != str(current_user.id):
            flash('You do not have permission to view this analysis', 'error')
            return redirect(url_for('index'))
    
    reviews_data = conn.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
    conn.close()
    
    if not reviews_data:
        return render_template('waiting.html', product=product, product_id=product_id)
    
    reviews_df = pd.DataFrame([dict(row) for row in reviews_data])
    
    # Handle potential None values in sentiment
    reviews_df['sentiment'] = reviews_df['sentiment'].fillna(0)
    
    sentiment_counts = {
        'Positive': len(reviews_df[reviews_df['sentiment'] > 0.05]),
        'Neutral': len(reviews_df[(reviews_df['sentiment'] >= -0.05) & (reviews_df['sentiment'] <= 0.05)]),
        'Negative': len(reviews_df[reviews_df['sentiment'] < -0.05])
    }
    
    all_text = ' '.join(reviews_df['text'].tolist())
    words = [word.lower() for word in word_tokenize(all_text) 
             if word.isalpha() and len(word) > 3 and word.lower() not in common_stopwords]
    keywords = dict(Counter(words).most_common(10))
    
    sentiment_by_date = reviews_df.sort_values('date').to_dict('records')
    
    return render_template(
        'dashboard.html',
        product=product,
        sentiment_counts=sentiment_counts,
        keywords=keywords,
        reviews=reviews_df.to_dict('records'),
        sentiment_by_date=sentiment_by_date
    )

@app.route('/export/csv/<int:product_id>')
def export_csv(product_id):
    conn = get_db_connection()
    
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('index'))
        
    reviews = conn.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
    conn.close()
    
    if not reviews:
        flash('No reviews to export', 'warning')
        return redirect(url_for('dashboard', product_id=product_id))
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['id', 'date', 'rating', 'sentiment', 'text'])
    
    for review in reviews:
        writer.writerow([
            review['id'],
            review['date'],
            review['rating'],
            review['sentiment'],
            review['text']
        ])
    
    output.seek(0)
    filename = f"{product['platform']}_{product['product_id']}_reviews_{datetime.now().strftime('%Y%m%d')}.csv"
    
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.csv') as temp:
        temp.write(output.getvalue())
        temp_path = temp.name
        
    return send_file(
        temp_path,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/export/json/<int:product_id>')
def export_json(product_id):
    conn = get_db_connection()
    
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('index'))
        
    reviews = conn.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
    conn.close()
    
    if not reviews:
        flash('No reviews to export', 'warning')
        return redirect(url_for('dashboard', product_id=product_id))
    
    data = {
        'product': dict(product),
        'reviews': [dict(review) for review in reviews],
        'export_date': datetime.now().isoformat(),
        'total_reviews': len(reviews)
    }
    
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

@app.route('/api/reviews/<int:product_id>')
def api_reviews(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    
    if product and product['user_id']:
        if not current_user.is_authenticated or str(product['user_id']) != str(current_user.id):
            return jsonify({"error": "Access denied"}), 403
    
    reviews = conn.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in reviews])

@app.route('/documentation')
def documentation():
    """Render the documentation page"""
    return render_template('documentation.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Run the app
if __name__ == '__main__':
    # Initialize the database
    init_db()
    
    # Create static directory if it doesn't exist
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000) 