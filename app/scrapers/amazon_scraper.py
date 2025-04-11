import os
import json
import logging
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from app.utils.resilient_scraper import ResilientScraper

# Configure logging
logger = logging.getLogger(__name__)

class AmazonScraper:
    """
    A scraper for Amazon product reviews that uses the resilient scraper utility
    for handling retries, proxies, and CAPTCHA detection.
    """
    
    def __init__(self, min_delay=2.0, max_delay=5.0, use_proxies=False):
        """
        Initialize the Amazon scraper with the resilient scraper utility.
        
        Args:
            min_delay (float): Minimum delay between requests in seconds
            max_delay (float): Maximum delay between requests in seconds
            use_proxies (bool): Whether to use proxy rotation
        """
        self.scraper = ResilientScraper(
            use_proxies=use_proxies,
            min_delay=min_delay,
            max_delay=max_delay
        )
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
    
    def get_product_url(self, asin):
        """
        Get the URL for a product page.
        
        Args:
            asin (str): Amazon Standard Identification Number
            
        Returns:
            str: URL for the product page
        """
        return f"https://www.amazon.com/dp/{asin}"
    
    def get_reviews_url(self, asin, page=1):
        """
        Get the URL for a reviews page.
        
        Args:
            asin (str): Amazon Standard Identification Number
            page (int): Page number
            
        Returns:
            str: URL for the reviews page
        """
        return f"https://www.amazon.com/product-reviews/{asin}?pageNumber={page}"
    
    def scrape_product_info(self, asin):
        """
        Scrape basic product information.
        
        Args:
            asin (str): Amazon Standard Identification Number
            
        Returns:
            dict: Product information
        """
        url = self.get_product_url(asin)
        logger.info(f"Scraping product info from {url}")
        
        try:
            response = self.scraper.get(url)
            soup = self.scraper.parse_html(response.text)
            
            # Extract product title
            title_element = soup.select_one('#productTitle')
            title = title_element.text.strip() if title_element else "Unknown Title"
            
            # Extract product price
            price_element = soup.select_one('.a-price .a-offscreen')
            price = price_element.text.strip() if price_element else "Unknown Price"
            
            # Extract product rating
            rating_element = soup.select_one('#acrPopover')
            rating = rating_element.get('title', 'Unknown Rating').split(' ')[0] if rating_element else "Unknown Rating"
            
            # Extract product image
            image_element = soup.select_one('#landingImage')
            image_url = image_element.get('src') if image_element else None
            
            return {
                'asin': asin,
                'title': title,
                'price': price,
                'rating': rating,
                'image_url': image_url,
                'url': url
            }
            
        except Exception as e:
            logger.error(f"Error scraping product info: {e}")
            return {
                'asin': asin,
                'title': "Error retrieving product information",
                'url': url
            }
    
    def scrape_reviews(self, asin, max_pages=5):
        """
        Scrape reviews for a product.
        
        Args:
            asin (str): Amazon Standard Identification Number
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            list: List of review dictionaries
        """
        all_reviews = []
        
        for page in range(1, max_pages + 1):
            url = self.get_reviews_url(asin, page)
            logger.info(f"Scraping reviews from {url} (page {page}/{max_pages})")
            
            try:
                response = self.scraper.get(url)
                soup = self.scraper.parse_html(response.text)
                
                # Extract reviews
                review_elements = soup.select('div[data-hook="review"]')
                
                if not review_elements:
                    logger.info(f"No reviews found on page {page}, stopping")
                    break
                
                for review_element in review_elements:
                    try:
                        # Extract review title
                        title_element = review_element.select_one('a[data-hook="review-title"]')
                        if not title_element:
                            title_element = review_element.select_one('span[data-hook="review-title"]')
                        title = title_element.text.strip() if title_element else "No Title"
                        
                        # Extract review rating
                        rating_element = review_element.select_one('i[data-hook="review-star-rating"] span')
                        if not rating_element:
                            rating_element = review_element.select_one('i[data-hook="cmps-review-star-rating"] span')
                        rating_text = rating_element.text.strip() if rating_element else "0 out of 5 stars"
                        rating = float(rating_text.split(' ')[0])
                        
                        # Extract review date
                        date_element = review_element.select_one('span[data-hook="review-date"]')
                        date_text = date_element.text.strip() if date_element else "Unknown Date"
                        try:
                            # Try to parse Amazon's date format (e.g., "Reviewed in the United States on February 25, 2023")
                            date_parts = date_text.split(' on ')[1].strip()
                            review_date = datetime.strptime(date_parts, '%B %d, %Y').strftime('%Y-%m-%d')
                        except (IndexError, ValueError):
                            # Fallback to current date if parsing fails
                            review_date = datetime.now().strftime('%Y-%m-%d')
                        
                        # Extract review text
                        body_element = review_element.select_one('span[data-hook="review-body"] span')
                        review_text = body_element.text.strip() if body_element else "No review text"
                        
                        # Analyze sentiment
                        sentiment = self.sentiment_analyzer.polarity_scores(review_text)['compound']
                        
                        # Create review dictionary
                        review = {
                            'title': title,
                            'rating': rating,
                            'date': review_date,
                            'text': review_text,
                            'sentiment': sentiment
                        }
                        
                        all_reviews.append(review)
                        
                    except Exception as e:
                        logger.warning(f"Error extracting review: {e}")
                
                # If we have enough reviews or there are no more pages, stop
                if len(review_elements) < 10:
                    logger.info(f"Found fewer than 10 reviews on page {page}, likely the last page")
                    break
                    
            except Exception as e:
                logger.error(f"Error scraping reviews page {page}: {e}")
                break
        
        logger.info(f"Scraped {len(all_reviews)} reviews for product {asin}")
        return all_reviews
    
    def store_reviews_in_db(self, db_id, reviews, db_path=None):
        """
        Store scraped reviews in the database.
        
        Args:
            db_id (int): Database ID for the product
            reviews (list): List of review dictionaries
            db_path (str, optional): Path to the database file
            
        Returns:
            int: Number of reviews stored
        """
        if not db_path:
            # Get the default database path
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'reviews.db')
        
        logger.info(f"Storing {len(reviews)} reviews for product DB ID {db_id}")
        
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        for review in reviews:
            cur.execute(
                "INSERT INTO reviews (product_id, text, rating, date, sentiment) VALUES (?, ?, ?, ?, ?)",
                (db_id, review["text"], review["rating"], review["date"], review["sentiment"])
            )
        
        conn.commit()
        conn.close()
        
        return len(reviews)
    
    def scrape_and_store(self, asin, db_id, max_pages=5):
        """
        Scrape reviews for a product and store them in the database.
        
        Args:
            asin (str): Amazon Standard Identification Number
            db_id (int): Database ID for the product
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            dict: Result statistics
        """
        logger.info(f"Starting scrape and store for Amazon product {asin}, DB ID {db_id}")
        
        # Get product info (optional, could be stored in a separate table)
        product_info = self.scrape_product_info(asin)
        
        # Scrape reviews
        reviews = self.scrape_reviews(asin, max_pages)
        
        # Store reviews in database
        stored_count = self.store_reviews_in_db(db_id, reviews)
        
        logger.info(f"Completed scrape and store for Amazon product {asin}, stored {stored_count} reviews")
        
        return {
            'product': product_info,
            'reviews_count': len(reviews),
            'stored_count': stored_count
        }

# Demo functionality if script is run directly
if __name__ == "__main__":
    import sys
    
    # Configure logging to console
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 3:
        print("Usage: python amazon_scraper.py <asin> <db_id> [max_pages]")
        sys.exit(1)
    
    asin = sys.argv[1]
    db_id = int(sys.argv[2])
    max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    
    scraper = AmazonScraper(min_delay=2.0, max_delay=5.0)
    result = scraper.scrape_and_store(asin, db_id, max_pages)
    
    print(json.dumps(result, indent=2)) 