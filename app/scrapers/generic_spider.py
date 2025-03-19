#!/usr/bin/env python
import sys
import json
import sqlite3
import os
import re
from datetime import datetime
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Get path to the database
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
db_path = os.path.join(root_dir, 'reviews.db')

class GenericReviewSpider(scrapy.Spider):
    name = "generic_reviews"
    
    def __init__(self, product_id=None, product_db_id=None, *args, **kwargs):
        super(GenericReviewSpider, self).__init__(*args, **kwargs)
        self.product_id = product_id
        self.product_db_id = int(product_db_id)
        
        # Load the configuration file
        config_path = os.path.join(current_dir, 'configs', f'{product_id}.json')
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Set the start URL from the config
        self.start_urls = [self.config['url']]
        
        # Selector definitions
        self.review_selector = self.config['selectors']['review']
        self.rating_selector = self.config['selectors']['rating']
        self.date_selector = self.config['selectors']['date']
        
        # Optional pagination selector
        self.pagination_selector = self.config['selectors'].get('pagination')
        
        # Initialize sentiment analyzer
        self.sid = SentimentIntensityAnalyzer()
    
    def parse(self, response):
        # Parse review elements - support both CSS and XPath selectors
        if self.review_selector.startswith('//'):
            reviews = response.xpath(self.review_selector)
        else:
            reviews = response.css(self.review_selector)
        
        self.logger.info(f"Found {len(reviews)} reviews")
        
        for review in reviews:
            # Extract review text
            if self.review_selector.startswith('//'):
                review_text = review.xpath('string()').get().strip()
            else:
                review_text = review.css('::text').get().strip()
            
            # Extract rating if available
            rating = None
            if self.rating_selector:
                if self.rating_selector.startswith('//'):
                    rating_text = review.xpath(self.rating_selector).get()
                else:
                    rating_text = review.css(self.rating_selector).get()
                
                if rating_text:
                    # Try to extract a numeric value from the rating
                    rating_match = re.search(r'([\d.]+)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
            
            # Extract date if available
            date = None
            if self.date_selector:
                if self.date_selector.startswith('//'):
                    date = review.xpath(self.date_selector).get()
                else:
                    date = review.css(self.date_selector).get()
            
            # Skip if no review text was found
            if not review_text:
                continue
                
            # Perform sentiment analysis
            sentiment_score = self.sid.polarity_scores(review_text)['compound']
            
            # Save to database
            self.save_review(review_text, rating, date, sentiment_score)
            
            # Yield for debugging/logging
            yield {
                'text': review_text,
                'rating': rating,
                'date': date,
                'sentiment': sentiment_score
            }
        
        # Follow pagination if specified
        if self.pagination_selector:
            if self.pagination_selector.startswith('//'):
                next_page = response.xpath(self.pagination_selector).get()
            else:
                next_page = response.css(self.pagination_selector).get()
                
            if next_page:
                # Make absolute URL if it's relative
                if not next_page.startswith(('http://', 'https://')):
                    next_page = response.urljoin(next_page)
                
                self.logger.info(f"Following pagination: {next_page}")
                yield scrapy.Request(next_page, callback=self.parse)
    
    def save_review(self, text, rating, date, sentiment):
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Insert the review
            cursor.execute('''
                INSERT INTO reviews (product_id, text, rating, date, sentiment)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.product_db_id, text, rating, date, sentiment))
            
            conn.commit()
        except Exception as e:
            print(f"Error saving review: {e}")
        finally:
            conn.close()

# If run directly, start the crawler
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python generic_spider.py <product_id> <product_db_id>")
        sys.exit(1)
        
    product_id = sys.argv[1]
    product_db_id = sys.argv[2]
    
    # Configure crawler settings
    settings = get_project_settings()
    settings.update({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 2,  # 2 seconds delay between requests to avoid being blocked
        'CONCURRENT_REQUESTS': 1,
        'LOG_LEVEL': 'INFO',
    })
    
    # Create and start the crawler
    process = CrawlerProcess(settings)
    process.crawl(GenericReviewSpider, product_id=product_id, product_db_id=product_db_id)
    process.start() 