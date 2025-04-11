"""
Implement Incremental Updates for Large Collections

This script enhances the background refresh process by implementing
incremental updates instead of full refreshes for large collections.
This reduces CPU and memory load during refresh operations.
"""

import logging
import time
from datetime import datetime, timedelta
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mongodb_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# MongoDB connection
uri = "mongodb+srv://tomasstaniulis76:JaLhUd1NLZUtwVb5@shop1.11tjwh5.mongodb.net/?retryWrites=true&w=majority&appName=Shop1"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.shopsentiment

class IncrementalUpdater:
    """Handles incremental updates for pre-computed collections."""
    
    @staticmethod
    def incremental_keyword_stats_update():
        """
        Incremental update for keyword_stats collection.
        Only updates keywords from reviews that were updated since last refresh.
        """
        logger.info("Starting incremental keyword stats update...")
        start_time = time.time()
        
        try:
            # Get the last update timestamp from metadata
            metadata = db.collection_metadata.find_one({"collection": "keyword_stats"})
            
            if metadata and "last_incremental_update" in metadata:
                last_update = metadata["last_incremental_update"]
                logger.info(f"Last incremental update was at: {last_update}")
            else:
                # Default to 24 hours ago if no previous update
                last_update = datetime.utcnow() - timedelta(hours=24)
                logger.info(f"No previous update found, using default: {last_update}")
            
            # Find reviews updated since last refresh
            updated_reviews_query = {
                "updated_at": {"$gte": last_update}
            }
            
            updated_reviews_count = db.reviews.count_documents(updated_reviews_query)
            logger.info(f"Found {updated_reviews_count} reviews updated since last refresh")
            
            if updated_reviews_count == 0:
                logger.info("No updated reviews found, skipping keyword stats update")
                return 0
            
            # Extract unique keywords from updated reviews
            pipeline = [
                {"$match": updated_reviews_query},
                {"$unwind": "$keywords"},
                {"$group": {"_id": "$keywords"}}
            ]
            
            updated_keywords = [doc["_id"] for doc in db.reviews.aggregate(pipeline)]
            logger.info(f"Found {len(updated_keywords)} keywords to update")
            
            # Process each keyword incrementally
            keywords_updated = 0
            
            for keyword in updated_keywords:
                # Calculate updated stats for this keyword
                keyword_pipeline = [
                    {"$match": {"keywords": keyword}},
                    {"$group": {
                        "_id": None,
                        "count": {"$sum": 1},
                        "avg_sentiment": {"$avg": "$sentiment.score"},
                        "products": {"$addToSet": "$product_id"}
                    }},
                    {"$project": {
                        "_id": 0,
                        "count": 1,
                        "avg_sentiment": 1,
                        "products": 1
                    }}
                ]
                
                result = list(db.reviews.aggregate(keyword_pipeline))
                
                if result:
                    keyword_data = result[0]
                    
                    # Determine sentiment label
                    sentiment_score = keyword_data["avg_sentiment"]
                    if sentiment_score >= 0.6:
                        sentiment_label = "positive"
                    elif sentiment_score < 0.4:
                        sentiment_label = "negative"
                    else:
                        sentiment_label = "neutral"
                    
                    # Update or insert keyword stats
                    db.keyword_stats.update_one(
                        {"keyword": keyword},
                        {"$set": {
                            "count": keyword_data["count"],
                            "sentiment": {
                                "score": sentiment_score,
                                "label": sentiment_label
                            },
                            "products": keyword_data["products"],
                            "updated_at": datetime.utcnow()
                        }},
                        upsert=True
                    )
                    
                    keywords_updated += 1
                    
                    # Log progress every 100 keywords
                    if keywords_updated % 100 == 0:
                        logger.info(f"Updated {keywords_updated}/{len(updated_keywords)} keywords")
            
            # Update the metadata with current timestamp
            db.collection_metadata.update_one(
                {"collection": "keyword_stats"},
                {"$set": {
                    "last_incremental_update": datetime.utcnow(),
                    "last_full_update": metadata["last_full_update"] if metadata and "last_full_update" in metadata else None
                }},
                upsert=True
            )
            
            elapsed = time.time() - start_time
            logger.info(f"Completed incremental keyword stats update in {elapsed:.2f} seconds, updated {keywords_updated} keywords")
            
            return keywords_updated
            
        except Exception as e:
            logger.error(f"Error in incremental keyword stats update: {e}", exc_info=True)
            return 0
    
    @staticmethod
    def incremental_time_series_stats_update():
        """
        Incremental update for time_series_stats collection.
        Only processes recent time periods that might have changed.
        """
        logger.info("Starting incremental time series stats update...")
        start_time = time.time()
        
        try:
            # Get products that have had reviews updated recently
            recent_period = datetime.utcnow() - timedelta(days=30)
            
            pipeline = [
                {"$match": {"date": {"$gte": recent_period}}},
                {"$group": {"_id": "$product_id"}}
            ]
            
            recent_product_ids = [doc["_id"] for doc in db.reviews.aggregate(pipeline)]
            logger.info(f"Found {len(recent_product_ids)} products with recent review updates")
            
            periods_updated = 0
            
            for product_id in recent_product_ids:
                # Calculate time series data for recent periods only
                for interval_days in [30, 90, 180]:
                    interval_start = datetime.utcnow() - timedelta(days=interval_days)
                    
                    # Get sentiment data for this period
                    sentiment_pipeline = [
                        {"$match": {
                            "product_id": product_id,
                            "date": {"$gte": interval_start}
                        }},
                        {"$group": {
                            "_id": {
                                "year": {"$year": "$date"},
                                "month": {"$month": "$date"},
                                "day": {"$dayOfMonth": "$date"}
                            },
                            "avg_sentiment": {"$avg": "$sentiment.score"},
                            "count": {"$sum": 1}
                        }},
                        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}}
                    ]
                    
                    time_series_data = list(db.reviews.aggregate(sentiment_pipeline))
                    
                    # Format the time series data
                    formatted_data = []
                    for entry in time_series_data:
                        date_str = f"{entry['_id']['year']}-{entry['_id']['month']:02d}-{entry['_id']['day']:02d}"
                        formatted_data.append({
                            "date": date_str,
                            "sentiment": entry["avg_sentiment"],
                            "count": entry["count"]
                        })
                    
                    # Update time series stats
                    db.time_series_stats.update_one(
                        {
                            "product_id": product_id,
                            "interval": f"{interval_days}_day"
                        },
                        {
                            "$set": {
                                "data": formatted_data,
                                "updated_at": datetime.utcnow()
                            }
                        },
                        upsert=True
                    )
                    
                    periods_updated += 1
            
            elapsed = time.time() - start_time
            logger.info(f"Completed incremental time series stats update in {elapsed:.2f} seconds, updated {periods_updated} periods")
            
            return periods_updated
            
        except Exception as e:
            logger.error(f"Error in incremental time series stats update: {e}", exc_info=True)
            return 0

def main():
    """Run incremental updates for pre-computed collections."""
    logger.info("Starting incremental updates for pre-computed collections")
    
    updater = IncrementalUpdater()
    
    # Run incremental updates
    keywords_updated = updater.incremental_keyword_stats_update()
    time_series_updated = updater.incremental_time_series_stats_update()
    
    logger.info("Incremental updates summary:")
    logger.info(f"  - Keywords updated: {keywords_updated}")
    logger.info(f"  - Time series periods updated: {time_series_updated}")
    
    logger.info("Incremental updates completed")

if __name__ == "__main__":
    main() 