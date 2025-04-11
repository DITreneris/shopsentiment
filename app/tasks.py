import os
import sys
import subprocess
import time
import logging
from celery import Celery
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from app import app, get_db_connection
from app.scrapers.amazon_scraper import AmazonScraper
from app.models import Product, Review, USING_MONGODB
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Celery
celery = Celery(
    app.name,
    broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)
celery.conf.update(app.config)

# Amazon scraper task
@celery.task(bind=True, name='app.tasks.scrape_amazon')
def scrape_amazon(self, product_id, db_id):
    """
    Scrape Amazon product reviews and store in database.
    
    Args:
        product_id (str): Amazon product ID (ASIN)
        db_id (int|str): Database ID of the product
        
    Returns:
        dict: Task result information
    """
    logger.info(f"Starting Amazon scrape task for product ID: {product_id}, DB ID: {db_id}")
    
    try:
        # Update task state to PROGRESS
        self.update_state(state='PROGRESS', meta={'status': 'Starting Amazon scraper'})
        
        # Create Amazon scraper with resilient capabilities
        scraper = AmazonScraper(min_delay=2.0, max_delay=5.0)
        
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Scraping product page and reviews'})
        
        if USING_MONGODB:
            # MongoDB approach
            logger.info("Using MongoDB for storing reviews")
            
            # Get product from database
            product = Product.get_by_id(db_id)
            if not product:
                raise ValueError(f"Product with ID {db_id} not found in MongoDB")
            
            # Scrape product info
            product_info = scraper.scrape_product_info(product_id)
            
            # Update product with scraped info
            if product_info:
                product.title = product_info.get('title', product.title)
                product.brand = product_info.get('brand', product.brand)
                product.price = product_info.get('price', product.price)
                product.image_url = product_info.get('image_url', product.image_url)
                product.url = product_info.get('url', product.url)
                product.save()
            
            # Scrape reviews
            reviews_count = 0
            for page in range(1, 6):  # Limit to 5 pages
                self.update_state(state='PROGRESS', meta={'status': f'Scraping reviews page {page}'})
                
                reviews = scraper.scrape_reviews(product_id, page)
                if not reviews:
                    logger.info(f"No more reviews to scrape after page {page-1}")
                    break
                
                # Store reviews in MongoDB
                for review_data in reviews:
                    # Check if review already exists
                    from app.utils.mongodb import get_collection
                    reviews_collection = get_collection('reviews')
                    existing_review = reviews_collection.find_one({
                        'product_id': product.id if isinstance(product.id, int) else 
                                     (ObjectId(product.id) if product.id else None),
                        'platform_review_id': review_data.get('id', '')
                    })
                    
                    if existing_review:
                        logger.debug(f"Review with ID {review_data.get('id')} already exists")
                        continue
                    
                    # Create sentiment analysis
                    analyzer = SentimentIntensityAnalyzer()
                    sentiment_scores = analyzer.polarity_scores(review_data.get('text', ''))
                    
                    # Create review object
                    review = Review(
                        product_id=product.id,
                        platform_review_id=review_data.get('id', ''),
                        content=review_data.get('text', ''),
                        rating=float(review_data.get('rating', 0)),
                        author=review_data.get('author', 'Anonymous'),
                        date=review_data.get('date', datetime.now()),
                        verified_purchase=review_data.get('verified_purchase', False),
                        sentiment={
                            'compound': sentiment_scores['compound'],
                            'pos': sentiment_scores['pos'],
                            'neg': sentiment_scores['neg'],
                            'neu': sentiment_scores['neu'],
                            'score': sentiment_scores['compound'],
                            'label': 'positive' if sentiment_scores['compound'] >= 0.05 else 
                                    ('negative' if sentiment_scores['compound'] <= -0.05 else 'neutral')
                        },
                        created_at=datetime.now()
                    )
                    
                    # Save review
                    review.save()
                    reviews_count += 1
                
                # Add a delay between pages
                time.sleep(scraper.get_random_delay())
            
            # Update task state to SUCCESS
            self.update_state(
                state='SUCCESS',
                meta={
                    'status': 'Completed',
                    'reviews_count': reviews_count,
                    'product_info': {
                        'title': product.title,
                        'brand': product.brand,
                        'price': product.price
                    }
                }
            )
            
            logger.info(f"Completed Amazon scrape task for {product_id}: {reviews_count} reviews")
            
            return {
                'status': 'success',
                'reviews_count': reviews_count,
                'product_info': {
                    'title': product.title,
                    'brand': product.brand,
                    'price': product.price
                }
            }
        else:
            # SQLite approach (existing implementation)
            logger.info("Using SQLite for storing reviews")
            
            # Scrape and store reviews
            result = scraper.scrape_and_store(product_id, db_id, max_pages=5)
            
            # Update task state to SUCCESS
            self.update_state(
                state='SUCCESS',
                meta={
                    'status': 'Completed',
                    'reviews_count': result['reviews_count'],
                    'product_info': result['product']
                }
            )
            
            logger.info(f"Completed Amazon scrape task for {product_id}: {result['reviews_count']} reviews")
            
            return {
                'status': 'success',
                'reviews_count': result['reviews_count'],
                'product_info': result['product']
            }
        
    except Exception as e:
        logger.error(f"Error in Amazon scrape task: {str(e)}")
        # Update task state to FAILURE
        self.update_state(state='FAILURE', meta={'status': f'Error: {str(e)}'})
        raise e

# eBay scraper task
@celery.task(bind=True, name='app.tasks.scrape_ebay')
def scrape_ebay(self, product_id, db_id):
    """
    Scrape eBay product reviews and store in database.
    
    Args:
        product_id (str): eBay item ID
        db_id (int|str): Database ID of the product
        
    Returns:
        dict: Task result information
    """
    logger.info(f"Starting eBay scrape task for product ID: {product_id}, DB ID: {db_id}")
    
    try:
        # Update task state to PROGRESS
        self.update_state(state='PROGRESS', meta={'status': 'Starting eBay scraper'})
        
        # Placeholder for actual eBay scraper implementation
        # In a real implementation, we would use a similar approach to the Amazon scraper
        
        # Simulate work
        self.update_state(state='PROGRESS', meta={'status': 'Scraping product page'})
        time.sleep(2)
        
        self.update_state(state='PROGRESS', meta={'status': 'Scraping reviews'})
        time.sleep(3)
        
        # Create some sample reviews for demonstration
        reviews = [
            {"text": "Great item from eBay!", "rating": 5.0, "date": "2023-10-15", "sentiment": 0.8},
            {"text": "Okay product, shipped quickly.", "rating": 4.0, "date": "2023-09-20", "sentiment": 0.4},
            {"text": "Not what I expected from the listing.", "rating": 2.0, "date": "2023-08-10", "sentiment": -0.5},
        ]
        
        if USING_MONGODB:
            # MongoDB approach
            logger.info("Using MongoDB for storing eBay reviews")
            
            # Get product from database
            product = Product.get_by_id(db_id)
            if not product:
                raise ValueError(f"Product with ID {db_id} not found in MongoDB")
            
            # Store reviews in MongoDB
            reviews_count = 0
            for review_data in reviews:
                # Create sentiment analysis with predefined sentiment
                sentiment_score = review_data.get("sentiment", 0)
                
                # Create review object
                review = Review(
                    product_id=product.id,
                    platform_review_id=f"ebay_{product_id}_{reviews_count}", # Generate a fake review ID
                    content=review_data.get('text', ''),
                    rating=float(review_data.get('rating', 0)),
                    author="eBay User",
                    date=datetime.strptime(review_data.get('date', '2023-01-01'), '%Y-%m-%d'),
                    verified_purchase=False,
                    sentiment={
                        'score': sentiment_score,
                        'compound': sentiment_score,
                        'pos': max(0, sentiment_score) if sentiment_score > 0 else 0,
                        'neg': abs(min(0, sentiment_score)) if sentiment_score < 0 else 0,
                        'neu': 1 - abs(sentiment_score) if abs(sentiment_score) < 1 else 0,
                        'label': 'positive' if sentiment_score >= 0.05 else 
                                ('negative' if sentiment_score <= -0.05 else 'neutral')
                    },
                    created_at=datetime.now()
                )
                
                # Save review
                review.save()
                reviews_count += 1
        else:
            # SQLite approach
            logger.info("Using SQLite for storing eBay reviews")
            
            # Simulate storing reviews in database
            conn = get_db_connection()
            
            # Store reviews in database
            for review in reviews:
                conn.execute(
                    'INSERT INTO reviews (product_id, text, rating, date, sentiment) VALUES (?, ?, ?, ?, ?)',
                    (db_id, review["text"], review["rating"], review["date"], review["sentiment"])
                )
            
            conn.commit()
            conn.close()
            
            reviews_count = len(reviews)
        
        # Update task state to SUCCESS
        self.update_state(
            state='SUCCESS',
            meta={
                'status': 'Completed',
                'reviews_count': reviews_count
            }
        )
        
        logger.info(f"Completed eBay scrape task for {product_id}: {reviews_count} reviews")
        
        return {
            'status': 'success',
            'reviews_count': reviews_count
        }
        
    except Exception as e:
        logger.error(f"Error in eBay scrape task: {str(e)}")
        # Update task state to FAILURE
        self.update_state(state='FAILURE', meta={'status': f'Error: {str(e)}'})
        raise e

# Custom site scraper task
@celery.task(bind=True, name='app.tasks.scrape_custom')
def scrape_custom(self, product_id, db_id, config):
    """
    Scrape custom site product reviews and store in database.
    
    Args:
        product_id (str): Custom product ID
        db_id (int|str): Database ID of the product
        config (dict): Configuration for the custom scraper
        
    Returns:
        dict: Task result information
    """
    logger.info(f"Starting custom scrape task for product ID: {product_id}, DB ID: {db_id}")
    
    try:
        # Update task state to PROGRESS
        self.update_state(state='PROGRESS', meta={'status': 'Starting custom scraper'})
        
        # Extract configuration
        url = config.get('url', '')
        selectors = config.get('selectors', {})
        
        logger.info(f"Custom scraper config: URL={url}, Selectors={selectors}")
        
        # Placeholder for actual custom scraper implementation
        # In a real implementation, we would use our resilient scraper here too
        
        # Simulate work
        self.update_state(state='PROGRESS', meta={'status': 'Scraping custom site'})
        time.sleep(3)
        
        # Create some sample reviews for demonstration
        reviews = [
            {"text": "This is a custom site review.", "rating": 3.5, "date": "2023-10-01", "sentiment": 0.2},
            {"text": "Custom site product review.", "rating": 4.0, "date": "2023-09-15", "sentiment": 0.5},
        ]
        
        if USING_MONGODB:
            # MongoDB approach
            logger.info("Using MongoDB for storing custom site reviews")
            
            # Get product from database
            product = Product.get_by_id(db_id)
            if not product:
                raise ValueError(f"Product with ID {db_id} not found in MongoDB")
            
            # Store reviews in MongoDB
            reviews_count = 0
            for review_data in reviews:
                # Create sentiment analysis with predefined sentiment
                sentiment_score = review_data.get("sentiment", 0)
                
                # Create review object
                review = Review(
                    product_id=product.id,
                    platform_review_id=f"custom_{product_id}_{reviews_count}", # Generate a fake review ID
                    content=review_data.get('text', ''),
                    rating=float(review_data.get('rating', 0)),
                    author="Custom Reviewer",
                    date=datetime.strptime(review_data.get('date', '2023-01-01'), '%Y-%m-%d'),
                    verified_purchase=False,
                    sentiment={
                        'score': sentiment_score,
                        'compound': sentiment_score,
                        'pos': max(0, sentiment_score) if sentiment_score > 0 else 0,
                        'neg': abs(min(0, sentiment_score)) if sentiment_score < 0 else 0,
                        'neu': 1 - abs(sentiment_score) if abs(sentiment_score) < 1 else 0,
                        'label': 'positive' if sentiment_score >= 0.05 else 
                                ('negative' if sentiment_score <= -0.05 else 'neutral')
                    },
                    created_at=datetime.now()
                )
                
                # Save review
                review.save()
                reviews_count += 1
        else:
            # SQLite approach
            logger.info("Using SQLite for storing custom site reviews")
            
            # Simulate storing reviews in database
            conn = get_db_connection()
            
            # Store reviews in database
            for review in reviews:
                conn.execute(
                    'INSERT INTO reviews (product_id, text, rating, date, sentiment) VALUES (?, ?, ?, ?, ?)',
                    (db_id, review["text"], review["rating"], review["date"], review["sentiment"])
                )
            
            conn.commit()
            conn.close()
            
            reviews_count = len(reviews)
        
        # Update task state to SUCCESS
        self.update_state(
            state='SUCCESS',
            meta={
                'status': 'Completed',
                'reviews_count': reviews_count
            }
        )
        
        logger.info(f"Completed custom scrape task for {product_id}: {reviews_count} reviews")
        
        return {
            'status': 'success',
            'reviews_count': reviews_count
        }
        
    except Exception as e:
        logger.error(f"Error in custom scrape task: {str(e)}")
        # Update task state to FAILURE
        self.update_state(state='FAILURE', meta={'status': f'Error: {str(e)}'})
        raise e

# Sentiment analysis task
@celery.task(bind=True, name='app.tasks.analyze_sentiment')
def analyze_sentiment(self, product_db_id):
    """
    Analyze sentiment for product reviews.
    
    Args:
        product_db_id (int|str): Database ID of the product
        
    Returns:
        dict: Task result information
    """
    logger.info(f"Starting sentiment analysis task for product DB ID: {product_db_id}")
    
    try:
        # Update task state to PROGRESS
        self.update_state(state='PROGRESS', meta={'status': 'Starting sentiment analysis'})
        
        # Initialize VADER sentiment analyzer
        analyzer = SentimentIntensityAnalyzer()
        analyzed_count = 0
        
        if USING_MONGODB:
            # MongoDB approach
            logger.info("Using MongoDB for sentiment analysis")
            
            # Get product from database
            product = Product.get_by_id(product_db_id)
            if not product:
                raise ValueError(f"Product with ID {product_db_id} not found in MongoDB")
            
            # Get reviews without sentiment or with zero sentiment
            from app.utils.mongodb import get_collection
            reviews_collection = get_collection('reviews')
            
            # Find reviews with null sentiment or sentiment.score = 0
            reviews_to_analyze = reviews_collection.find({
                'product_id': product.id if isinstance(product.id, int) else 
                           (ObjectId(product.id) if product.id else None),
                '$or': [
                    {'sentiment': None},
                    {'sentiment.score': 0}
                ]
            })
            
            for review_doc in reviews_to_analyze:
                # Create Review object from document
                review = Review(db_dict=review_doc)
                
                # Analyze sentiment
                text = review.content
                sentiment_scores = analyzer.polarity_scores(text)
                
                # Update sentiment
                review.sentiment = {
                    'compound': sentiment_scores['compound'],
                    'pos': sentiment_scores['pos'],
                    'neg': sentiment_scores['neg'],
                    'neu': sentiment_scores['neu'],
                    'score': sentiment_scores['compound'],
                    'label': 'positive' if sentiment_scores['compound'] >= 0.05 else 
                            ('negative' if sentiment_scores['compound'] <= -0.05 else 'neutral')
                }
                
                # Save review
                review.save()
                analyzed_count += 1
                
                # Log progress every 10 reviews
                if analyzed_count % 10 == 0:
                    logger.info(f"Analyzed {analyzed_count} reviews so far")
                    self.update_state(
                        state='PROGRESS', 
                        meta={'status': f'Analyzed {analyzed_count} reviews'}
                    )
        else:
            # SQLite approach
            logger.info("Using SQLite for sentiment analysis")
            
            # Get database connection
            conn = get_db_connection()
            
            # Get reviews without sentiment
            reviews = conn.execute(
                'SELECT id, text FROM reviews WHERE product_id = ? AND (sentiment IS NULL OR sentiment = 0)',
                (product_db_id,)
            ).fetchall()
            
            logger.info(f"Found {len(reviews)} reviews to analyze for product {product_db_id}")
            
            if not reviews:
                logger.info("No reviews to analyze")
                return {'status': 'success', 'analyzed_count': 0}
            
            # Analyze sentiment for each review
            for review in reviews:
                # Get sentiment scores
                text = review['text']
                sentiment_scores = analyzer.polarity_scores(text)
                
                # Update review with sentiment
                conn.execute(
                    'UPDATE reviews SET sentiment = ? WHERE id = ?',
                    (sentiment_scores['compound'], review['id'])
                )
                
                analyzed_count += 1
                
                # Log progress every 10 reviews
                if analyzed_count % 10 == 0:
                    logger.info(f"Analyzed {analyzed_count} reviews so far")
                    self.update_state(
                        state='PROGRESS', 
                        meta={'status': f'Analyzed {analyzed_count} reviews'}
                    )
            
            # Commit changes
            conn.commit()
            conn.close()
        
        # Update task state to SUCCESS
        self.update_state(
            state='SUCCESS',
            meta={'status': 'Completed', 'analyzed_count': analyzed_count}
        )
        
        logger.info(f"Completed sentiment analysis task for product {product_db_id}: {analyzed_count} reviews analyzed")
        
        return {'status': 'success', 'analyzed_count': analyzed_count}
        
    except Exception as e:
        logger.error(f"Error in sentiment analysis task: {str(e)}")
        # Update task state to FAILURE
        self.update_state(state='FAILURE', meta={'status': f'Error: {str(e)}'})
        raise e 