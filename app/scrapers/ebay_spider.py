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

class EbayReviewSpider(scrapy.Spider):
    name = "ebay_reviews"
    
    def __init__(self, item_id=None, product_db_id=None, *args, **kwargs):
        super(EbayReviewSpider, self).__init__(*args, **kwargs)
        self.item_id = item_id
        self.product_db_id = int(product_db_id)
        
        # This is a simplified approach - in a real app, we'd likely 
        # first need to get the seller ID from the item page
        # For now, we'll use the item ID and construct the feedback URL directly
        self.start_urls = [f'https://www.ebay.com/itm/{self.item_id}']
        
        # Initialize sentiment analyzer
        self.sid = SentimentIntensityAnalyzer()
    
    def parse(self, response):
        # Get the seller ID from the item page
        seller_id = response.css('span.usr-name::text').get()
        
        if seller_id:
            # Now go to the feedback page
            feedback_url = f'https://www.ebay.com/fdbk/feedback_profile/{seller_id}'
            yield scrapy.Request(feedback_url, callback=self.parse_feedback)
        else:
            self.logger.error("Could not find seller ID")
    
    def parse_feedback(self, response):
        # Parse feedback comments
        feedback_items = response.css('div.ebay-feedback-card')
        
        for item in feedback_items:
            # Extract data
            text = item.css('div.card-item-feedback span::text').get()
            if not text:
                continue
                
            # Get rating information
            rating_class = item.css('div.rating span::attr(class)').get()
            if 'positive' in rating_class:
                rating = 5.0
            elif 'neutral' in rating_class:
                rating = 3.0
            elif 'negative' in rating_class:
                rating = 1.0
            else:
                rating = None
            
            # Get date
            date = item.css('div.card-item-date span::text').get()
            
            # Perform sentiment analysis
            sentiment_score = self.sid.polarity_scores(text)['compound']
            
            # Save to database
            self.save_review(text, rating, date, sentiment_score)
            
            # Yield for debugging/logging
            yield {
                'text': text,
                'rating': rating,
                'date': date,
                'sentiment': sentiment_score
            }
        
        # Follow pagination
        next_page = response.css('a.ebay-pagination-next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse_feedback)
    
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
        print("Usage: python ebay_spider.py <item_id> <product_db_id>")
        sys.exit(1)
        
    item_id = sys.argv[1]
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
    process.crawl(EbayReviewSpider, item_id=item_id, product_db_id=product_db_id)
    process.start() 