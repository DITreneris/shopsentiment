#!/usr/bin/env python
"""
Dashboard Initialization Script
Initializes required collections and precomputes initial dashboard statistics
"""

import os
import sys
import logging
import time
from datetime import datetime, timedelta
from bson import ObjectId

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import app modules after modifying path
from app import app
from app.utils.mongodb_aggregations import AggregationPipelines

def setup_mongodb_collections():
    """Set up required MongoDB collections for dashboard functionality"""
    logger.info("Setting up MongoDB collections for dashboard")
    
    # Create time series collection for metrics
    if AggregationPipelines.create_time_series_collection():
        logger.info("✓ Time series collection setup complete")
    else:
        logger.error("✗ Failed to setup time series collection")
        
    # Create collection for precomputed stats
    if AggregationPipelines.create_precomputed_stats_collection():
        logger.info("✓ Precomputed stats collection setup complete")
    else:
        logger.error("✗ Failed to setup precomputed stats collection")

def precompute_initial_stats():
    """Precompute initial statistics for dashboard performance"""
    logger.info("Precomputing initial dashboard statistics")
    
    # Get MongoDB connection
    with app.app_context():
        if not hasattr(app, 'mongodb'):
            logger.error("MongoDB not initialized in Flask app")
            return False
            
        db = app.mongodb
        
        # Get list of products to precompute stats for
        products = list(db.products.find({}, {"_id": 1}).sort("stats.review_count", -1).limit(20))
        product_count = len(products)
        logger.info(f"Found {product_count} products for precomputation")
        
        if product_count == 0:
            logger.warning("No products found to precompute stats for")
            return False
            
        # Precompute sentiment trends for each product
        for i, product in enumerate(products):
            product_id = product["_id"]
            logger.info(f"Precomputing stats for product {i+1}/{product_count}: {product_id}")
            
            try:
                # Compute sentiment trend with different timeframes
                for days in [7, 30, 90]:
                    for interval in ['day', 'week']:
                        logger.debug(f"Computing sentiment trend: {days} days, {interval} interval")
                        stats_type = f"sentiment_trend:{days}:{interval}"
                        
                        # Compute fresh data
                        fresh_data = AggregationPipelines.sentiment_over_time(
                            product_id, 
                            days=days, 
                            interval=interval
                        )
                        
                        # Store for future use
                        AggregationPipelines.store_precomputed_stats(
                            stats_type,
                            str(product_id),
                            fresh_data
                        )
                        
                        # Add small delay to avoid overwhelming database
                        time.sleep(0.1)
                
                logger.debug(f"Completed sentiment trend stats for product {product_id}")
                
            except Exception as e:
                logger.error(f"Error precomputing stats for product {product_id}: {e}")
                continue
                
        # Precompute platform-wide stats
        try:
            # Rating distribution by platform
            logger.info("Precomputing platform-wide rating distribution")
            for days in [30, 90, 180]:
                stats_type = f"rating_distribution:{days}"
                
                # Compute fresh data
                fresh_data = AggregationPipelines.rating_distribution_by_platform(days=days)
                
                # Store for future use
                AggregationPipelines.store_precomputed_stats(
                    stats_type,
                    "all",
                    fresh_data
                )
                
                # Also store individual platform stats
                for platform, data in fresh_data.items():
                    AggregationPipelines.store_precomputed_stats(
                        stats_type,
                        platform,
                        data
                    )
                    
            # Keyword sentiment analysis
            logger.info("Precomputing keyword sentiment analysis")
            for min_count in [5, 10, 20]:
                stats_type = f"keyword_sentiment:{min_count}"
                
                # Compute fresh data
                fresh_data = AggregationPipelines.keyword_sentiment_analysis(min_count=min_count)
                
                # Store for future use
                AggregationPipelines.store_precomputed_stats(
                    stats_type,
                    "all",
                    fresh_data
                )
                
            logger.info("✓ Platform-wide stats precomputation complete")
                
        except Exception as e:
            logger.error(f"Error precomputing platform-wide stats: {e}")
            return False
            
        # Precompute common product comparisons
        try:
            logger.info("Precomputing common product comparisons")
            
            # Find pairs of products that might be commonly compared
            # Here we're just using top products in each category as a proxy
            platforms = db.products.distinct("platform")
            
            for platform in platforms:
                # Get top 3 products for this platform
                top_products = list(
                    db.products.find(
                        {"platform": platform}, 
                        {"_id": 1}
                    ).sort("stats.review_count", -1).limit(3)
                )
                
                if len(top_products) >= 2:
                    # Create product ID list
                    product_ids = [p["_id"] for p in top_products]
                    
                    # Compute comparison
                    logger.debug(f"Computing comparison for {len(product_ids)} products on {platform}")
                    comparison_data = AggregationPipelines.product_comparison(product_ids)
                    
                    # Store for future use
                    stats_type = "product_comparison"
                    target_id = f"{platform}:top{len(product_ids)}"
                    
                    AggregationPipelines.store_precomputed_stats(
                        stats_type,
                        target_id,
                        comparison_data
                    )
            
            logger.info("✓ Product comparison precomputation complete")
                
        except Exception as e:
            logger.error(f"Error precomputing product comparisons: {e}")
            return False
            
        logger.info("✓ All initial dashboard statistics precomputed successfully")
        return True

def main():
    """Main execution function"""
    start_time = time.time()
    logger.info("Starting dashboard initialization")
    
    # Setup collections first
    setup_mongodb_collections()
    
    # Then precompute initial stats
    if precompute_initial_stats():
        logger.info("Dashboard initialization completed successfully")
    else:
        logger.error("Dashboard initialization completed with errors")
        
    elapsed_time = time.time() - start_time
    logger.info(f"Initialization process took {elapsed_time:.2f} seconds")
    
if __name__ == "__main__":
    main() 