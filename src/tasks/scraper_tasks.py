import os
import time
import logging
from bson import ObjectId
from datetime import datetime

# Import the Celery app instance defined in celery_app.py
from src.celery_app import celery
from src import create_app  # Import the app factory
from src.scraper.amazon_scraper import AmazonScraper
from src.models.product import Product, Review # Assuming models are here
# Adjust DAL import path if necessary
from src.database.product_dal import ProductDAL 

# Configure logging
logger = logging.getLogger(__name__)

# --- Amazon scraper task ---
# The task decorator now uses the imported 'celery' instance
@celery.task(bind=True, name='src.tasks.scrape_amazon') 
def scrape_amazon(self, product_asin, product_url=None):
    """
    Scrape Amazon product reviews and store in database using ProductDAL.
    
    Args:
        product_asin (str): Amazon product ID (ASIN)
        product_url (str, optional): Full product URL (used if ASIN doesn't exist yet)

    Returns:
        dict: Task result information
    """
    logger.info(f"Starting Amazon scrape task for ASIN: {product_asin}")
    
    # Create app context to access db, config, etc.
    # This is crucial for tasks needing Flask context (config, extensions)
    app = create_app() 
    with app.app_context():
        try:
            # Check if using SQLite (should ideally not happen for scraping)
            use_sqlite = app.config.get('USE_SQLITE', False)
            if use_sqlite:
                 logger.error("Scraping task initiated but configured to use SQLite. Aborting.")
                 # Use 'ignore_result=False' on task decorator or configure backend properly
                 # if you want state/result updates.
                 self.update_state(state='FAILURE', meta={'status': 'Configured for SQLite, cannot use MongoDB DAL.'})
                 return {'status': 'failure', 'message': 'App configured for SQLite.'}

            # Get Product DAL instance (within app context)
            product_dal = ProductDAL()
            
            # Update task state to PROGRESS
            self.update_state(state='PROGRESS', meta={'status': 'Starting Amazon scraper'})
            
            # Create Amazon scraper
            # TODO: Configure delays/proxies from app.config if needed
            scraper = AmazonScraper(min_delay=app.config.get('SCRAPER_MIN_DELAY', 2.0), 
                                    max_delay=app.config.get('SCRAPER_MAX_DELAY', 5.0))
            
            # Update task state
            self.update_state(state='PROGRESS', meta={'status': 'Scraping product page and reviews'})
            
            # --- Database Interaction using DAL --- 
            logger.info(f"Using MongoDB DAL for ASIN: {product_asin}")
            
            # Find or Create Product using DAL
            # TODO: Ensure get_product_by_asin exists in ProductDAL
            product = await product_dal.get_product_by_asin(product_asin) 
            
            db_id = None
            product_name = "N/A"
            if product:
                logger.info(f"Found existing product in DB with ID: {product.get('_id')} for ASIN: {product_asin}")
                db_id = product.get('_id')
                product_name = product.get('name', 'N/A')
            else:
                logger.info(f"Product with ASIN {product_asin} not found. Scraping info and creating.")
                # Scrape product info first if not found
                product_info = scraper.scrape_product_info(product_asin) # This is synchronous
                if product_info and "Error" not in product_info.get("title", ""):
                     product_name = product_info.get('title', 'N/A')
                     # Create a Product model instance (adapt fields as needed)
                     # Ensure ProductDAL's parse_price handles potential errors
                     price_value, price_currency = await product_dal.parse_price(product_info.get('price'))

                     new_product_data = Product(
                         id=str(ObjectId()), # Generate new ID
                         asin=product_asin, # Store ASIN
                         name=product_name,
                         description=product_info.get('description', ''), 
                         price=price_value, 
                         currency=price_currency,
                         category=product_info.get('category', 'Unknown'), 
                         url=product_info.get('url'),
                         image_url=product_info.get('image_url')
                         # reviews and sentiment will be populated/updated later
                     )
                     created_id = await product_dal.create_product(new_product_data)
                     if created_id:
                         logger.info(f"Created new product with ID: {created_id} for ASIN: {product_asin}")
                         db_id = created_id
                     else:
                         # Log error instead of raising to prevent task failure if creation fails
                         logger.error(f"Failed to create product entry for ASIN: {product_asin}")
                         self.update_state(state='FAILURE', meta={'status': f'Failed to create product entry for ASIN: {product_asin}'})
                         return {'status': 'failure', 'message': 'Product creation failed'}
                else:
                     logger.error(f"Failed to scrape initial product info for ASIN: {product_asin}")
                     self.update_state(state='FAILURE', meta={'status': f'Failed to scrape initial product info for ASIN: {product_asin}'})
                     return {'status': 'failure', 'message': 'Product info scraping failed'}
            
            if not db_id:
                 logger.error("Could not obtain database ID for product.")
                 self.update_state(state='FAILURE', meta={'status': 'Could not obtain database ID'})
                 return {'status': 'failure', 'message': 'DB ID acquisition failed'}

            # Scrape reviews
            reviews_count_this_run = 0
            max_pages = app.config.get('SCRAPER_MAX_PAGES', 5) 
            
            # Scrape reviews page by page using the scraper method
            # Note: scrape_reviews in amazon_scraper.py gets ALL reviews up to max_pages
            # We might want to adapt it to scrape page-by-page if needed, or just call it once.
            # Let's assume scrape_reviews gets reviews efficiently.
            
            self.update_state(state='PROGRESS', meta={'status': f'Scraping up to {max_pages} review pages'})
            scraped_reviews = scraper.scrape_reviews(product_asin, max_pages=max_pages) # Synchronous call
            
            if not scraped_reviews:
                logger.info(f"No reviews found or scraped for ASIN {product_asin}")
            else:
                logger.info(f"Scraped {len(scraped_reviews)} potential reviews for ASIN {product_asin}. Storing...")
                # Store reviews using ProductDAL
                for review_data in scraped_reviews:
                    try:
                        # Format review data for Review model
                        # Sentiment analysis should happen elsewhere (e.g., in DAL or another task)
                        new_review = Review(
                            id=str(ObjectId()), # Generate new ID
                            product_id=str(db_id), # Link to our product ID
                            text=review_data.get('text', ''),
                            rating=float(review_data.get('rating', 0)),
                            # Add mapping for other fields if available from scraper
                            # user_name=review_data.get('user', 'Anonymous'), 
                            created_at_source=review_data.get('date') # Store original date string? Parse?
                        )
                        
                        # TODO: Ensure add_review exists in ProductDAL and handles potential duplicates
                        added = await product_dal.add_review(str(db_id), new_review) 
                        if added:
                            reviews_count_this_run += 1
                        else:
                            # Log if add_review returns False (e.g., duplicate)
                             logger.debug(f"Review skipped (possibly duplicate) for product {db_id}")

                    except Exception as review_error:
                        logger.warning(f"Error processing one review for {db_id}: {review_error}", exc_info=False) # Log warning, continue with others


            # --- End Database Interaction ---

            # Final success state update
            logger.info(f"Completed scraping for ASIN {product_asin}. Processed {reviews_count_this_run} new reviews in this run.")
            self.update_state(
                state='SUCCESS',
                meta={
                    'status': 'Completed',
                    'reviews_processed_this_run': reviews_count_this_run, 
                    'product_name': product_name 
                }
            )
            
            return {
                'status': 'success',
                'reviews_processed': reviews_count_this_run,
                'product_name': product_name
            }

        except Exception as e:
            logger.exception(f"Error in Amazon scrape task for ASIN {product_asin}: {str(e)}") 
            self.update_state(state='FAILURE', meta={'status': f'Error: {str(e)}'})
            # Reraise the exception so Celery knows the task failed
            raise 

# --- Placeholder tasks (if needed) ---

# Placeholder for eBay scraper task
@celery.task(bind=True, name='src.tasks.scrape_ebay')
def scrape_ebay(self, product_id, db_id):
    logger.info(f"Starting eBay scrape task for product ID: {product_id}, DB ID: {db_id}")
    self.update_state(state='PENDING', meta={'status': 'eBay scraper not implemented'})
    # You might want to raise NotImplementedError or return a specific status
    # raise NotImplementedError("eBay scraper task is not implemented.")
    return {'status': 'not_implemented', 'message': 'eBay scraper not available.'}

# Placeholder for Custom scraper task
@celery.task(bind=True, name='src.tasks.scrape_custom')
def scrape_custom(self, product_id, db_id, config):
    logger.info(f"Starting Custom scrape task for product ID: {product_id}, DB ID: {db_id}")
    self.update_state(state='PENDING', meta={'status': 'Custom scraper not implemented'})
    # raise NotImplementedError("Custom scraper task is not implemented.")
    return {'status': 'not_implemented', 'message': 'Custom scraper not available.'}

# --- Example: Separate Sentiment Analysis Task (Optional) ---
# This task could be triggered after reviews are added, or run periodically.
@celery.task(bind=True, name='src.tasks.analyze_product_sentiment')
def analyze_product_sentiment(self, product_db_id):
    logger.info(f"Starting sentiment analysis task for DB ID: {product_db_id}")
    app = create_app()
    with app.app_context():
        try: 
            product_dal = ProductDAL()
            # TODO: Implement analyze_sentiment_for_product in ProductDAL
            # This method would fetch reviews without sentiment, analyze, and update them.
            analysis_result = await product_dal.analyze_sentiment_for_product(product_db_id)
            
            if analysis_result:
                 logger.info(f"Sentiment analysis completed for {product_db_id}. Updated: {analysis_result.get('updated_count', 0)}")
                 self.update_state(state='SUCCESS', meta={'status': 'Analysis complete', **analysis_result})
                 return {'status': 'success', **analysis_result}
            else:
                 logger.warning(f"Sentiment analysis did not run or failed for {product_db_id}")
                 self.update_state(state='FAILURE', meta={'status': 'Analysis failed or not applicable'})
                 return {'status': 'failure', 'message': 'Analysis failed'}

        except Exception as e:
            logger.exception(f"Error in sentiment analysis task for DB ID {product_db_id}: {str(e)}")
            self.update_state(state='FAILURE', meta={'status': f'Error: {str(e)}'})
            raise

# Note: Ensure necessary methods (get_product_by_asin, parse_price, add_review, analyze_sentiment_for_product) 
# exist and are correctly implemented (sync/async) in the ProductDAL.
# Also ensure the Product/Review models in src/models/product.py match the fields used here. 