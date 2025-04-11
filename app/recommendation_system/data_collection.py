import logging
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
from pymongo import MongoClient
from config import MONGO_URI, RATE_LIMIT_DELAY
from performance_optimization import PerformanceOptimizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self):
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client['shop_sentiment']
        self.products_collection = self.db['products']
        self.competitor_collection = self.db['competitor_products']
        self.optimizer = PerformanceOptimizer(MONGO_URI)
        
    @PerformanceOptimizer.profile_function
    @PerformanceOptimizer.cache_result(ttl=3600)  # Cache for 1 hour
    def collect_product_data(self) -> List[Dict]:
        """
        Collect product data from our database
        """
        try:
            # Use optimized query with proper indexes
            self.optimizer.optimize_query(
                self.products_collection,
                {},
                {
                    'product_id': 1,
                    'name': 1,
                    'category': 1,
                    'price': 1,
                    'sales_data': 1,
                    'customer_reviews': 1,
                    '_id': 0
                }
            )
            
            # Use materialized view if available
            if 'popular_products_by_category' in self.db.list_collection_names():
                logger.info("Using materialized view for product data")
                products = []
                for category_doc in self.db['popular_products_by_category'].find():
                    products.extend(category_doc.get('products', []))
                if products:
                    logger.info(f"Collected {len(products)} products from materialized view")
                    return products
            
            # Fallback to regular query
            products = list(self.products_collection.find(
                {},
                {
                    'product_id': 1,
                    'name': 1,
                    'category': 1,
                    'price': 1,
                    'sales_data': 1,
                    'customer_reviews': 1,
                    '_id': 0
                }
            ))
            logger.info(f"Collected {len(products)} products")
            return products
        except Exception as e:
            logger.error(f"Error collecting product data: {str(e)}")
            return []

    @PerformanceOptimizer.profile_function
    def collect_competitor_data(self, competitor_urls: List[str]) -> List[Dict]:
        """
        Scrape competitor product data from given URLs
        """
        def process_url_batch(url_batch):
            batch_results = []
            for url in url_batch:
                try:
                    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract product information (this will need to be customized per competitor)
                    products = soup.find_all('div', class_='product')  # Adjust selector based on competitor site
                    
                    for product in products:
                        product_data = {
                            'competitor_url': url,
                            'name': product.find('h2').text.strip(),
                            'price': float(product.find('span', class_='price').text.strip().replace('$', '')),
                            'timestamp': datetime.now(),
                            'category': product.find('div', class_='category').text.strip()
                        }
                        batch_results.append(product_data)
                    
                    # Respect rate limiting
                    time.sleep(RATE_LIMIT_DELAY)
                    
                except Exception as e:
                    logger.error(f"Error scraping competitor data from {url}: {str(e)}")
                    continue
            return batch_results
        
        # Use parallel processing for multiple URLs
        competitor_products = self.optimizer.batch_process(
            competitor_urls, 
            process_url_batch, 
            batch_size=5,  # Process 5 URLs per batch
            use_multiprocessing=False  # Use threads for I/O-bound scraping
        )
        
        return competitor_products

    @PerformanceOptimizer.profile_function
    def store_competitor_data(self, competitor_products: List[Dict]):
        """
        Store competitor product data in MongoDB
        """
        if not competitor_products:
            return
            
        try:
            # Process in batches for better performance
            def store_batch(batch):
                self.competitor_collection.insert_many(batch)
                return len(batch)
            
            # Use batch processing
            total_stored = sum(self.optimizer.batch_process(
                competitor_products,
                store_batch,
                batch_size=100,  # Insert 100 documents at a time
                use_multiprocessing=False
            ))
            
            logger.info(f"Stored {total_stored} competitor products")
        except Exception as e:
            logger.error(f"Error storing competitor data: {str(e)}")

    @PerformanceOptimizer.profile_function
    def preprocess_data(self, products: List[Dict]) -> pd.DataFrame:
        """
        Preprocess the collected data for ML model
        """
        try:
            df = pd.DataFrame(products)
            
            # Basic preprocessing steps
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df['category'] = df['category'].astype('category')
            
            # Handle missing values
            df = df.fillna({
                'price': df['price'].median(),
                'category': 'unknown'
            })
            
            # Optimize DataFrame memory usage
            df = self.optimizer.optimize_dataframe(df)
            
            return df
        except Exception as e:
            logger.error(f"Error preprocessing data: {str(e)}")
            return pd.DataFrame()

    def optimize_collections(self):
        """
        Apply performance optimizations to MongoDB collections
        """
        self.optimizer.optimize_mongodb_collections()
        self.optimizer.create_materialized_views()

if __name__ == "__main__":
    collector = DataCollector()
    
    # Apply optimizations
    collector.optimize_collections()
    
    # Collect our product data
    products = collector.collect_product_data()
    
    # Example competitor URLs (replace with actual URLs)
    competitor_urls = [
        "https://example-competitor1.com/products",
        "https://example-competitor2.com/products"
    ]
    
    # Collect competitor data
    competitor_products = collector.collect_competitor_data(competitor_urls)
    
    # Store competitor data
    collector.store_competitor_data(competitor_products)
    
    # Preprocess data
    processed_data = collector.preprocess_data(products)
    
    logger.info("Data collection and preprocessing completed successfully") 