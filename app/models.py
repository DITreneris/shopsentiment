from datetime import datetime
import os
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
# Import db conditionally to handle test environment
try:
    from app import db
except ImportError:
    db = None
from bson.objectid import ObjectId
import logging

logger = logging.getLogger(__name__)

# Check if we're using MongoDB or SQLite
USING_MONGODB = os.environ.get('MONGODB_URI') is not None

class User(UserMixin):
    """User model that supports both SQLite and MongoDB."""
    
    def __init__(self, id=None, username=None, email=None, password_hash=None, 
                 is_admin=False, created_at=None, last_login=None, db_dict=None):
        """
        Initialize a User instance.
        
        Args:
            id: User ID (str for MongoDB ObjectId, int for SQLite)
            username: Username
            email: Email address
            password_hash: Hashed password
            is_admin: Admin flag
            created_at: Creation timestamp
            last_login: Last login timestamp
            db_dict: Dictionary from database (for MongoDB documents)
        """
        if db_dict:
            # Initialize from MongoDB document
            self.id = str(db_dict.get('_id'))
            self.username = db_dict.get('username')
            self.email = db_dict.get('email')
            self.password_hash = db_dict.get('password_hash')
            self.is_admin = db_dict.get('is_admin', False)
            self.created_at = db_dict.get('created_at')
            self.last_login = db_dict.get('last_login')
        else:
            # Initialize from parameters
            self.id = str(id) if id else None
            self.username = username
            self.email = email
            self.password_hash = password_hash
            self.is_admin = is_admin
            self.created_at = created_at or datetime.now()
            self.last_login = last_login
    
    def set_password(self, password):
        """Hash and set the password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    @classmethod
    def get_by_id(cls, user_id):
        """
        Get user by ID.
        
        Args:
            user_id: User ID (str for MongoDB ObjectId, int for SQLite)
            
        Returns:
            User instance or None
        """
        if USING_MONGODB:
            from app.utils.mongodb import get_collection
            try:
                # Convert string ID to ObjectId
                if isinstance(user_id, str):
                    object_id = ObjectId(user_id)
                else:
                    object_id = user_id
                    
                users_collection = get_collection('users')
                user_doc = users_collection.find_one({'_id': object_id})
                
                if user_doc:
                    return cls(db_dict=user_doc)
                return None
            except Exception as e:
                logger.error(f"Error getting user by ID from MongoDB: {e}")
                return None
        else:
            try:
                # SQLite query
                user = db.execute(
                    'SELECT * FROM users WHERE id = ?', (user_id,)
                ).fetchone()
                
                if user:
                    return cls(
                        id=user['id'],
                        username=user['username'],
                        email=user['email'],
                        password_hash=user['password_hash'],
                        is_admin=bool(user.get('admin', 0)),
                        created_at=user.get('created_at'),
                        last_login=user.get('last_login')
                    )
                return None
            except Exception as e:
                logger.error(f"Error getting user by ID from SQLite: {e}")
                return None
    
    @classmethod
    def get_by_email(cls, email):
        """
        Get user by email.
        
        Args:
            email: Email address
            
        Returns:
            User instance or None
        """
        if USING_MONGODB:
            from app.utils.mongodb import get_collection
            try:
                users_collection = get_collection('users')
                user_doc = users_collection.find_one({'email': email})
                
                if user_doc:
                    return cls(db_dict=user_doc)
                return None
            except Exception as e:
                logger.error(f"Error getting user by email from MongoDB: {e}")
                return None
        else:
            try:
                # SQLite query
                user = db.execute(
                    'SELECT * FROM users WHERE email = ?', (email,)
                ).fetchone()
                
                if user:
                    return cls(
                        id=user['id'],
                        username=user['username'],
                        email=user['email'],
                        password_hash=user['password_hash'],
                        is_admin=bool(user.get('admin', 0)),
                        created_at=user.get('created_at'),
                        last_login=user.get('last_login')
                    )
                return None
            except Exception as e:
                logger.error(f"Error getting user by email from SQLite: {e}")
                return None
    
    def save(self):
        """
        Save user to database.
        
        Returns:
            User ID or None on error
        """
        if USING_MONGODB:
            from app.utils.mongodb import get_collection
            try:
                users_collection = get_collection('users')
                
                # Prepare document
                user_doc = {
                    'username': self.username,
                    'email': self.email,
                    'password_hash': self.password_hash,
                    'is_admin': self.is_admin,
                    'created_at': self.created_at,
                    'last_login': self.last_login
                }
                
                if self.id and ObjectId.is_valid(self.id):
                    # Update existing user
                    result = users_collection.update_one(
                        {'_id': ObjectId(self.id)},
                        {'$set': user_doc}
                    )
                    return self.id if result.modified_count > 0 else None
                else:
                    # Insert new user
                    result = users_collection.insert_one(user_doc)
                    self.id = str(result.inserted_id)
                    return self.id
            except Exception as e:
                logger.error(f"Error saving user to MongoDB: {e}")
                return None
        else:
            try:
                # SQLite operations
                if self.id:
                    # Update existing user
                    db.execute(
                        'UPDATE users SET username = ?, email = ?, password_hash = ?, '
                        'admin = ?, last_login = ? WHERE id = ?',
                        (self.username, self.email, self.password_hash, 
                         1 if self.is_admin else 0, self.last_login, self.id)
                    )
                else:
                    # Insert new user
                    cursor = db.execute(
                        'INSERT INTO users (username, email, password_hash, admin, created_at, last_login) '
                        'VALUES (?, ?, ?, ?, ?, ?)',
                        (self.username, self.email, self.password_hash, 
                         1 if self.is_admin else 0, self.created_at, self.last_login)
                    )
                    self.id = cursor.lastrowid
                
                db.commit()
                return self.id
            except Exception as e:
                logger.error(f"Error saving user to SQLite: {e}")
                db.rollback()
                return None

class Product:
    """Product model that supports both SQLite and MongoDB."""
    
    def __init__(self, id=None, platform_id=None, platform=None, title=None, 
                 brand=None, price=None, image_url=None, url=None, 
                 created_by=None, created_at=None, last_updated=None, 
                 stats=None, keywords=None, db_dict=None):
        """
        Initialize a Product instance.
        
        Args:
            id: Product ID (str for MongoDB ObjectId, int for SQLite)
            platform_id: Platform-specific product ID
            platform: Platform name (amazon, ebay, etc.)
            title: Product title
            brand: Product brand
            price: Product price
            image_url: Product image URL
            url: Product URL
            created_by: User ID who created this product
            created_at: Creation timestamp
            last_updated: Last update timestamp
            stats: Product statistics (for MongoDB)
            keywords: List of keywords (for MongoDB)
            db_dict: Dictionary from database (for MongoDB documents)
        """
        if db_dict:
            # Initialize from MongoDB document
            self.id = str(db_dict.get('_id'))
            self.platform_id = db_dict.get('platform_id')
            self.platform = db_dict.get('platform')
            self.title = db_dict.get('title')
            self.brand = db_dict.get('brand')
            self.price = db_dict.get('price')
            self.image_url = db_dict.get('image_url')
            self.url = db_dict.get('url')
            self.created_by = str(db_dict.get('created_by')) if db_dict.get('created_by') else None
            self.created_at = db_dict.get('created_at')
            self.last_updated = db_dict.get('last_updated')
            self.stats = db_dict.get('stats', {})
            self.keywords = db_dict.get('keywords', [])
        else:
            # Initialize from parameters
            self.id = str(id) if id else None
            self.platform_id = platform_id
            self.platform = platform
            self.title = title
            self.brand = brand
            self.price = price
            self.image_url = image_url
            self.url = url
            self.created_by = created_by
            self.created_at = created_at or datetime.now()
            self.last_updated = last_updated or datetime.now()
            self.stats = stats or {
                'review_count': 0,
                'avg_rating': 0,
                'rating_distribution': {},
                'sentiment_distribution': {}
            }
            self.keywords = keywords or []
    
    @classmethod
    def get_by_id(cls, product_id):
        """
        Get product by ID.
        
        Args:
            product_id: Product ID (str for MongoDB ObjectId, int for SQLite)
            
        Returns:
            Product instance or None
        """
        if USING_MONGODB:
            from app.utils.mongodb import get_collection
            try:
                # Convert string ID to ObjectId
                if isinstance(product_id, str):
                    object_id = ObjectId(product_id)
                else:
                    object_id = product_id
                    
                products_collection = get_collection('products')
                product_doc = products_collection.find_one({'_id': object_id})
                
                if product_doc:
                    return cls(db_dict=product_doc)
                return None
            except Exception as e:
                logger.error(f"Error getting product by ID from MongoDB: {e}")
                return None
        else:
            try:
                # SQLite query
                product = db.execute(
                    'SELECT * FROM products WHERE id = ?', (product_id,)
                ).fetchone()
                
                if product:
                    return cls(
                        id=product['id'],
                        platform_id=product['product_id'],
                        platform=product['platform'],
                        title=product['title'],
                        brand=product['brand'],
                        price=product['price'],
                        image_url=product['image_url'],
                        url=product['url'],
                        created_by=product['user_id'],
                        created_at=product.get('created_at'),
                        last_updated=product.get('updated_at')
                    )
                return None
            except Exception as e:
                logger.error(f"Error getting product by ID from SQLite: {e}")
                return None
    
    @classmethod
    def get_by_platform_id(cls, platform, platform_id):
        """
        Get product by platform ID.
        
        Args:
            platform: Platform name
            platform_id: Platform-specific product ID
            
        Returns:
            Product instance or None
        """
        if USING_MONGODB:
            from app.utils.mongodb import get_collection
            try:
                products_collection = get_collection('products')
                product_doc = products_collection.find_one({
                    'platform': platform.lower(),
                    'platform_id': platform_id
                })
                
                if product_doc:
                    return cls(db_dict=product_doc)
                return None
            except Exception as e:
                logger.error(f"Error getting product by platform ID from MongoDB: {e}")
                return None
        else:
            try:
                # SQLite query
                product = db.execute(
                    'SELECT * FROM products WHERE platform = ? AND product_id = ?',
                    (platform, platform_id)
                ).fetchone()
                
                if product:
                    return cls(
                        id=product['id'],
                        platform_id=product['product_id'],
                        platform=product['platform'],
                        title=product['title'],
                        brand=product['brand'],
                        price=product['price'],
                        image_url=product['image_url'],
                        url=product['url'],
                        created_by=product['user_id'],
                        created_at=product.get('created_at'),
                        last_updated=product.get('updated_at')
                    )
                return None
            except Exception as e:
                logger.error(f"Error getting product by platform ID from SQLite: {e}")
                return None
    
    @classmethod
    def get_all(cls, limit=100, offset=0):
        """
        Get all products with pagination.
        
        Args:
            limit: Maximum number of products to return
            offset: Number of products to skip
            
        Returns:
            List of Product instances
        """
        if USING_MONGODB:
            from app.utils.mongodb import get_collection
            try:
                products_collection = get_collection('products')
                product_docs = products_collection.find().sort(
                    'created_at', -1
                ).skip(offset).limit(limit)
                
                return [cls(db_dict=doc) for doc in product_docs]
            except Exception as e:
                logger.error(f"Error getting all products from MongoDB: {e}")
                return []
        else:
            try:
                # SQLite query
                products = db.execute(
                    'SELECT * FROM products ORDER BY created_at DESC LIMIT ? OFFSET ?',
                    (limit, offset)
                ).fetchall()
                
                return [cls(
                    id=p['id'],
                    platform_id=p['product_id'],
                    platform=p['platform'],
                    title=p['title'],
                    brand=p['brand'],
                    price=p['price'],
                    image_url=p['image_url'],
                    url=p['url'],
                    created_by=p['user_id'],
                    created_at=p.get('created_at'),
                    last_updated=p.get('updated_at')
                ) for p in products]
            except Exception as e:
                logger.error(f"Error getting all products from SQLite: {e}")
                return []
    
    def save(self):
        """
        Save product to database.
        
        Returns:
            Product ID or None on error
        """
        if USING_MONGODB:
            from app.utils.mongodb import get_collection
            try:
                products_collection = get_collection('products')
                
                # Prepare document
                product_doc = {
                    'platform_id': self.platform_id,
                    'platform': self.platform.lower() if self.platform else 'unknown',
                    'title': self.title,
                    'brand': self.brand,
                    'price': self.price,
                    'image_url': self.image_url,
                    'url': self.url,
                    'created_at': self.created_at,
                    'last_updated': datetime.now(),
                    'stats': self.stats,
                    'keywords': self.keywords
                }
                
                # Add created_by if available
                if self.created_by:
                    if isinstance(self.created_by, str) and ObjectId.is_valid(self.created_by):
                        product_doc['created_by'] = ObjectId(self.created_by)
                    elif isinstance(self.created_by, int):
                        product_doc['created_by'] = self.created_by
                
                if self.id and ObjectId.is_valid(self.id):
                    # Update existing product
                    result = products_collection.update_one(
                        {'_id': ObjectId(self.id)},
                        {'$set': product_doc}
                    )
                    return self.id if result.modified_count > 0 else None
                else:
                    # Insert new product
                    result = products_collection.insert_one(product_doc)
                    self.id = str(result.inserted_id)
                    return self.id
            except Exception as e:
                logger.error(f"Error saving product to MongoDB: {e}")
                return None
        else:
            try:
                # SQLite operations
                if self.id:
                    # Update existing product
                    db.execute(
                        'UPDATE products SET product_id = ?, platform = ?, '
                        'title = ?, brand = ?, price = ?, image_url = ?, '
                        'url = ?, user_id = ?, updated_at = ? WHERE id = ?',
                        (self.platform_id, self.platform, self.title, self.brand,
                         self.price, self.image_url, self.url, self.created_by,
                         datetime.now().isoformat(), self.id)
                    )
                else:
                    # Insert new product
                    cursor = db.execute(
                        'INSERT INTO products (product_id, platform, title, brand, '
                        'price, image_url, url, user_id, created_at, updated_at) '
                        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (self.platform_id, self.platform, self.title, self.brand,
                         self.price, self.image_url, self.url, self.created_by,
                         self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
                         datetime.now().isoformat())
                    )
                    self.id = cursor.lastrowid
                
                db.commit()
                return self.id
            except Exception as e:
                logger.error(f"Error saving product to SQLite: {e}")
                db.rollback()
                return None

class Review:
    """Review model that supports both SQLite and MongoDB."""
    
    def __init__(self, id=None, product_id=None, platform_review_id=None, 
                 title=None, content=None, rating=None, author=None, 
                 date=None, verified_purchase=False, sentiment=None, 
                 keywords=None, created_at=None, db_dict=None):
        """
        Initialize a Review instance.
        
        Args:
            id: Review ID (str for MongoDB ObjectId, int for SQLite)
            product_id: Product ID
            platform_review_id: Platform-specific review ID
            title: Review title
            content: Review content
            rating: Review rating
            author: Review author
            date: Review date
            verified_purchase: Verified purchase flag
            sentiment: Sentiment score or dict (for MongoDB)
            keywords: List of keywords (for MongoDB)
            created_at: Creation timestamp
            db_dict: Dictionary from database (for MongoDB documents)
        """
        if db_dict:
            # Initialize from MongoDB document
            self.id = str(db_dict.get('_id'))
            self.product_id = str(db_dict.get('product_id')) if db_dict.get('product_id') else None
            self.platform_review_id = db_dict.get('platform_review_id')
            self.title = db_dict.get('title', '')
            self.content = db_dict.get('content', '')
            self.rating = db_dict.get('rating')
            self.author = db_dict.get('author', 'Anonymous')
            self.date = db_dict.get('date')
            self.verified_purchase = db_dict.get('verified_purchase', False)
            
            # Handle sentiment as either a scalar or dictionary
            if isinstance(db_dict.get('sentiment'), dict):
                self.sentiment = db_dict.get('sentiment')
                self.sentiment_score = db_dict.get('sentiment', {}).get('score', 0)
            else:
                self.sentiment_score = db_dict.get('sentiment', 0)
                self.sentiment = {
                    'score': self.sentiment_score,
                    'label': 'positive' if self.sentiment_score >= 0.05 else 
                            ('negative' if self.sentiment_score <= -0.05 else 'neutral')
                }
                
            self.keywords = db_dict.get('keywords', [])
            self.created_at = db_dict.get('created_at')
        else:
            # Initialize from parameters
            self.id = str(id) if id else None
            self.product_id = product_id
            self.platform_review_id = platform_review_id
            self.title = title or ''
            self.content = content or ''
            self.rating = rating
            self.author = author or 'Anonymous'
            self.date = date or datetime.now()
            self.verified_purchase = verified_purchase
            
            # Handle sentiment as either a scalar or dictionary
            if isinstance(sentiment, dict):
                self.sentiment = sentiment
                self.sentiment_score = sentiment.get('score', 0)
            else:
                self.sentiment_score = sentiment or 0
                self.sentiment = {
                    'score': self.sentiment_score,
                    'label': 'positive' if self.sentiment_score >= 0.05 else 
                            ('negative' if self.sentiment_score <= -0.05 else 'neutral')
                }
                
            self.keywords = keywords or []
            self.created_at = created_at or datetime.now()
    
    @classmethod
    def get_by_id(cls, review_id):
        """
        Get review by ID.
        
        Args:
            review_id: Review ID (str for MongoDB ObjectId, int for SQLite)
            
        Returns:
            Review instance or None
        """
        if USING_MONGODB:
            from app.utils.mongodb import get_collection
            try:
                # Convert string ID to ObjectId
                if isinstance(review_id, str):
                    object_id = ObjectId(review_id)
                else:
                    object_id = review_id
                    
                reviews_collection = get_collection('reviews')
                review_doc = reviews_collection.find_one({'_id': object_id})
                
                if review_doc:
                    return cls(db_dict=review_doc)
                return None
            except Exception as e:
                logger.error(f"Error getting review by ID from MongoDB: {e}")
                return None
        else:
            try:
                # SQLite query
                review = db.execute(
                    'SELECT * FROM reviews WHERE id = ?', (review_id,)
                ).fetchone()
                
                if review:
                    return cls(
                        id=review['id'],
                        product_id=review['product_id'],
                        platform_review_id=review.get('platform_review_id'),
                        content=review['text'],
                        rating=review['rating'],
                        author=review['author'],
                        date=review['date'],
                        verified_purchase=bool(review.get('verified_purchase', 0)),
                        sentiment=review['sentiment'],
                        created_at=review.get('created_at')
                    )
                return None
            except Exception as e:
                logger.error(f"Error getting review by ID from SQLite: {e}")
                return None
    
    @classmethod
    def get_by_product_id(cls, product_id, limit=100, offset=0):
        """
        Get reviews by product ID.
        
        Args:
            product_id: Product ID
            limit: Maximum number of reviews to return
            offset: Number of reviews to skip
            
        Returns:
            List of Review instances
        """
        if USING_MONGODB:
            from app.utils.mongodb import get_collection
            try:
                # Convert string ID to ObjectId if using MongoDB
                if isinstance(product_id, str) and ObjectId.is_valid(product_id):
                    mongo_product_id = ObjectId(product_id)
                else:
                    mongo_product_id = product_id
                    
                reviews_collection = get_collection('reviews')
                review_docs = reviews_collection.find(
                    {'product_id': mongo_product_id}
                ).sort('date', -1).skip(offset).limit(limit)
                
                return [cls(db_dict=doc) for doc in review_docs]
            except Exception as e:
                logger.error(f"Error getting reviews by product ID from MongoDB: {e}")
                return []
        else:
            try:
                # SQLite query
                reviews = db.execute(
                    'SELECT * FROM reviews WHERE product_id = ? ORDER BY date DESC LIMIT ? OFFSET ?',
                    (product_id, limit, offset)
                ).fetchall()
                
                return [cls(
                    id=r['id'],
                    product_id=r['product_id'],
                    platform_review_id=r.get('platform_review_id'),
                    content=r['text'],
                    rating=r['rating'],
                    author=r['author'],
                    date=r['date'],
                    verified_purchase=bool(r.get('verified_purchase', 0)),
                    sentiment=r['sentiment'],
                    created_at=r.get('created_at')
                ) for r in reviews]
            except Exception as e:
                logger.error(f"Error getting reviews by product ID from SQLite: {e}")
                return []
    
    def save(self):
        """
        Save review to database.
        
        Returns:
            Review ID or None on error
        """
        if USING_MONGODB:
            from app.utils.mongodb import get_collection
            try:
                reviews_collection = get_collection('reviews')
                
                # Prepare document
                review_doc = {
                    'product_id': ObjectId(self.product_id) if isinstance(self.product_id, str) and ObjectId.is_valid(self.product_id) else self.product_id,
                    'platform_review_id': self.platform_review_id,
                    'title': self.title,
                    'content': self.content,
                    'rating': self.rating,
                    'author': self.author,
                    'date': self.date,
                    'verified_purchase': self.verified_purchase,
                    'sentiment': self.sentiment,
                    'keywords': self.keywords,
                    'created_at': self.created_at
                }
                
                if self.id and ObjectId.is_valid(self.id):
                    # Update existing review
                    result = reviews_collection.update_one(
                        {'_id': ObjectId(self.id)},
                        {'$set': review_doc}
                    )
                    
                    # Update product stats after updating review
                    if result.modified_count > 0:
                        from app.utils.mongodb import update_product_stats
                        update_product_stats(self.product_id)
                        
                    return self.id if result.modified_count > 0 else None
                else:
                    # Insert new review
                    result = reviews_collection.insert_one(review_doc)
                    self.id = str(result.inserted_id)
                    
                    # Update product stats after adding new review
                    from app.utils.mongodb import update_product_stats
                    update_product_stats(self.product_id)
                    
                    return self.id
            except Exception as e:
                logger.error(f"Error saving review to MongoDB: {e}")
                return None
        else:
            try:
                # SQLite operations
                if self.id:
                    # Update existing review
                    db.execute(
                        'UPDATE reviews SET product_id = ?, rating = ?, text = ?, '
                        'author = ?, date = ?, verified_purchase = ?, sentiment = ? '
                        'WHERE id = ?',
                        (self.product_id, self.rating, self.content, self.author,
                         self.date, 1 if self.verified_purchase else 0, 
                         self.sentiment_score, self.id)
                    )
                else:
                    # Insert new review
                    cursor = db.execute(
                        'INSERT INTO reviews (product_id, rating, text, author, '
                        'date, verified_purchase, sentiment, created_at) '
                        'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                        (self.product_id, self.rating, self.content, self.author,
                         self.date.isoformat() if isinstance(self.date, datetime) else self.date,
                         1 if self.verified_purchase else 0, self.sentiment_score,
                         self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at)
                    )
                    self.id = cursor.lastrowid
                
                db.commit()
                return self.id
            except Exception as e:
                logger.error(f"Error saving review to SQLite: {e}")
                db.rollback()
                return None

class Feedback:
    """Model for user feedback on the platform, products, or any other entity."""
    
    def __init__(self, id=None, user_id=None, entity_type=None, entity_id=None, 
                 rating=None, title=None, content=None, tags=None, 
                 sentiment=None, created_at=None, updated_at=None, db_dict=None):
        """
        Initialize a Feedback instance.
        
        Args:
            id: Feedback ID (str for MongoDB ObjectId)
            user_id: ID of the user who submitted the feedback
            entity_type: Type of entity being rated ('product', 'platform', 'app', etc.)
            entity_id: ID of the entity being rated
            rating: Numerical rating (1-5)
            title: Feedback title/summary
            content: Detailed feedback text
            tags: List of tags associated with the feedback
            sentiment: Calculated sentiment score
            created_at: Creation timestamp
            updated_at: Last update timestamp
            db_dict: Dictionary from database (for MongoDB documents)
        """
        if db_dict:
            # Initialize from MongoDB document
            self.id = str(db_dict.get('_id'))
            self.user_id = db_dict.get('user_id')
            self.entity_type = db_dict.get('entity_type')
            self.entity_id = db_dict.get('entity_id')
            self.rating = db_dict.get('rating')
            self.title = db_dict.get('title')
            self.content = db_dict.get('content')
            self.tags = db_dict.get('tags', [])
            self.sentiment = db_dict.get('sentiment')
            self.created_at = db_dict.get('created_at')
            self.updated_at = db_dict.get('updated_at')
        else:
            # Initialize from parameters
            self.id = str(id) if id else None
            self.user_id = user_id
            self.entity_type = entity_type
            self.entity_id = entity_id
            self.rating = rating
            self.title = title
            self.content = content
            self.tags = tags or []
            self.sentiment = sentiment
            self.created_at = created_at or datetime.now()
            self.updated_at = updated_at or datetime.now()
    
    @classmethod
    def get_by_id(cls, feedback_id):
        """
        Get feedback by ID.
        
        Args:
            feedback_id: Feedback ID (str for MongoDB ObjectId)
            
        Returns:
            Feedback instance or None
        """
        if USING_MONGODB:
            from app.utils.mongodb import get_collection
            try:
                # Convert string ID to ObjectId
                if isinstance(feedback_id, str):
                    object_id = ObjectId(feedback_id)
                else:
                    object_id = feedback_id
                    
                feedback_collection = get_collection('feedback')
                feedback_doc = feedback_collection.find_one({'_id': object_id})
                
                if feedback_doc:
                    return cls(db_dict=feedback_doc)
                return None
            except Exception as e:
                logger.error(f"Error getting feedback by ID from MongoDB: {e}")
                return None
        else:
            # SQLite implementation if needed in the future
            logger.error("SQLite implementation for Feedback not available")
            return None
            
    @classmethod
    def get_by_entity(cls, entity_type, entity_id, limit=100, offset=0):
        """
        Get feedback for a specific entity.
        
        Args:
            entity_type: Type of entity ('product', 'platform', 'app', etc.)
            entity_id: ID of the entity
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of Feedback instances
        """
        if USING_MONGODB:
            from app.utils.mongodb import get_collection
            try:
                feedback_collection = get_collection('feedback')
                cursor = feedback_collection.find({
                    'entity_type': entity_type,
                    'entity_id': entity_id
                }).sort('created_at', -1).skip(offset).limit(limit)
                
                return [cls(db_dict=doc) for doc in cursor]
            except Exception as e:
                logger.error(f"Error getting feedback by entity from MongoDB: {e}")
                return []
        else:
            # SQLite implementation if needed in the future
            logger.error("SQLite implementation for Feedback not available")
            return []
    
    def save(self):
        """
        Save feedback to database.
        
        Returns:
            Feedback ID or None on error
        """
        if USING_MONGODB:
            from app.utils.mongodb import get_collection
            try:
                feedback_collection = get_collection('feedback')
                
                # Update timestamps
                self.updated_at = datetime.now()
                if not self.created_at:
                    self.created_at = self.updated_at
                
                # Prepare document
                feedback_doc = {
                    'user_id': self.user_id,
                    'entity_type': self.entity_type,
                    'entity_id': self.entity_id,
                    'rating': self.rating,
                    'title': self.title,
                    'content': self.content,
                    'tags': self.tags,
                    'sentiment': self.sentiment,
                    'created_at': self.created_at,
                    'updated_at': self.updated_at
                }
                
                if self.id and ObjectId.is_valid(self.id):
                    # Update existing feedback
                    result = feedback_collection.update_one(
                        {'_id': ObjectId(self.id)},
                        {'$set': feedback_doc}
                    )
                    return self.id if result.modified_count > 0 else None
                else:
                    # Insert new feedback
                    result = feedback_collection.insert_one(feedback_doc)
                    self.id = str(result.inserted_id)
                    return self.id
            except Exception as e:
                logger.error(f"Error saving feedback to MongoDB: {e}")
                return None
        else:
            # SQLite implementation if needed in the future
            logger.error("SQLite implementation for Feedback not available")
            return None
    
    @classmethod
    def delete(cls, feedback_id):
        """
        Delete feedback from database.
        
        Args:
            feedback_id: Feedback ID
            
        Returns:
            True if successful, False otherwise
        """
        if USING_MONGODB:
            from app.utils.mongodb import get_collection
            try:
                feedback_collection = get_collection('feedback')
                
                # Convert string ID to ObjectId
                if isinstance(feedback_id, str):
                    object_id = ObjectId(feedback_id)
                else:
                    object_id = feedback_id
                
                result = feedback_collection.delete_one({'_id': object_id})
                return result.deleted_count > 0
            except Exception as e:
                logger.error(f"Error deleting feedback from MongoDB: {e}")
                return False
        else:
            # SQLite implementation if needed in the future
            logger.error("SQLite implementation for Feedback not available")
            return False 