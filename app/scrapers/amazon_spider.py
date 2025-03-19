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

class AmazonReviewSpider(scrapy.Spider):
    name = "amazon_reviews"
    
    def __init__(self, asin=None, product_db_id=None, *args, **kwargs):
        super(AmazonReviewSpider, self).__init__(*args, **kwargs)
        self.asin = asin
        self.product_db_id = int(product_db_id)
        self.start_urls = [f'https://www.amazon.com/product-reviews/{self.asin}']
        
        # Initialize sentiment analyzer
        self.sid = SentimentIntensityAnalyzer()
        
    def parse(self, response):
        # Parse review elements
        reviews = response.css('div[data-hook="review"]')
        
        for review in reviews:
            # Extract data
            review_text = review.css('span[data-hook="review-body"] span::text').get().strip()
            rating_text = review.css('i[data-hook="review-star-rating"] span::text').get()
            date_text = review.css('span[data-hook="review-date"]::text').get()
            
            # Process rating (convert "4.0 out of 5 stars" to 4.0)
            rating = float(re.search(r'([\d.]+)', rating_text).group(1)) if rating_text else None
            
            # Process date
            date = date_text.split('on ')[-1] if date_text else None
            
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
        
        # Follow pagination
        next_page = response.css('li.a-last a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)
    
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
        print("Usage: python amazon_spider.py <ASIN> <product_db_id>")
        sys.exit(1)
        
    asin = sys.argv[1]
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
    process.crawl(AmazonReviewSpider, asin=asin, product_db_id=product_db_id)
    process.start() 