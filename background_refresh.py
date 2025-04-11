"""
Background Refresh for Pre-computed MongoDB Collections
This script can be scheduled with cron or Celery to keep cached data fresh
"""

import logging
import time
from datetime import datetime, timedelta
import schedule
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mongodb_refresh.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# MongoDB connection
uri = "mongodb+srv://tomasstaniulis76:JaLhUd1NLZUtwVb5@shop1.11tjwh5.mongodb.net/?retryWrites=true&w=majority&appName=Shop1"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.shopsentiment

def refresh_keyword_stats():
    """Refresh the keyword_stats collection."""
    logger.info("Refreshing keyword_stats collection...")
    start_time = time.time()
    
    try:
        # Find keywords that need updating (older than 24 hours or new ones)
        one_day_ago = datetime.utcnow() - timedelta(hours=24)
        
        # Define the aggregation pipeline for keyword analysis
        pipeline = [
            # Unwind keywords array
            {"$unwind": "$keywords"},
            
            # Group by keyword
            {"$group": {
                "_id": "$keywords",
                "count": {"$sum": 1},
                "avg_sentiment": {"$avg": "$sentiment.score"},
                "products": {"$addToSet": "$product_id"}
            }},
            
            # Filter out uncommon keywords
            {"$match": {
                "count": {"$gte": 5}  # Minimum threshold
            }},
            
            # Categorize sentiment
            {"$addFields": {
                "sentiment_label": {
                    "$cond": [
                        {"$gte": ["$avg_sentiment", 0.6]},
                        "positive",
                        {"$cond": [
                            {"$lt": ["$avg_sentiment", 0.4]},
                            "negative",
                            "neutral"
                        ]}
                    ]
                }
            }},
            
            # Sort by frequency
            {"$sort": {"count": -1}}
        ]
        
        # Execute the pipeline
        keyword_results = list(db.reviews.aggregate(pipeline))
        logger.info(f"Found {len(keyword_results)} keywords to update")
        
        # Insert into keyword_stats collection
        now = datetime.utcnow()
        bulk_ops = []
        
        for keyword_data in keyword_results:
            keyword_doc = {
                "keyword": keyword_data["_id"],
                "count": keyword_data["count"],
                "sentiment": {
                    "score": keyword_data["avg_sentiment"],
                    "label": keyword_data["sentiment_label"]
                },
                "products": keyword_data["products"],
                "updated_at": now
            }
            
            # Use upsert to avoid duplicates
            bulk_ops.append({
                "replaceOne": {
                    "filter": {"keyword": keyword_data["_id"]},
                    "replacement": keyword_doc,
                    "upsert": True
                }
            })
            
            # Execute in batches of 100
            if len(bulk_ops) >= 100:
                db.keyword_stats.bulk_write(bulk_ops)
                bulk_ops = []
        
        # Insert any remaining operations
        if bulk_ops:
            db.keyword_stats.bulk_write(bulk_ops)
        
        elapsed = time.time() - start_time
        logger.info(f"Refreshed keyword_stats collection in {elapsed:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error refreshing keyword_stats: {e}", exc_info=True)

def refresh_platform_stats():
    """Refresh the platform_stats collection."""
    logger.info("Refreshing platform_stats collection...")
    start_time = time.time()
    
    try:
        # Calculate rating distribution by platform for different periods
        for period, days in [("all_time", None), ("90_days", 90), ("30_days", 30), ("7_days", 7)]:
            # Build match criteria based on period
            match_criteria = {}
            if days:
                start_date = datetime.utcnow() - timedelta(days=days)
                # First find products with recent reviews
                products_with_recent_reviews = db.reviews.distinct(
                    "product_id", 
                    {"date": {"$gte": start_date}}
                )
                match_criteria = {"_id": {"$in": products_with_recent_reviews}}
            
            # Run the aggregation pipeline
            pipeline = [
                # Match products if needed
                {"$match": match_criteria} if match_criteria else {"$match": {}},
                
                # Group by platform
                {"$group": {
                    "_id": "$platform",
                    "total_products": {"$sum": 1},
                    "avg_rating": {"$avg": "$stats.avg_rating"},
                    "rating_distribution": {
                        "$push": "$stats.rating_distribution"
                    }
                }},
                
                # Compute aggregated rating distribution
                {"$project": {
                    "platform": "$_id",
                    "total_products": 1,
                    "avg_rating": 1,
                    "rating_distribution": {
                        "1": {"$sum": "$rating_distribution.1"},
                        "2": {"$sum": "$rating_distribution.2"},
                        "3": {"$sum": "$rating_distribution.3"},
                        "4": {"$sum": "$rating_distribution.4"},
                        "5": {"$sum": "$rating_distribution.5"}
                    },
                    "_id": 0
                }}
            ]
            
            # Execute the pipeline
            platform_results = list(db.products.aggregate(pipeline))
            
            # Process and format the results
            platforms_data = {}
            for item in platform_results:
                platform = item.get('platform', 'unknown')
                platforms_data[platform] = {
                    "total_products": item.get("total_products", 0),
                    "avg_rating": item.get("avg_rating", 0),
                    "rating_distribution": item.get("rating_distribution", {})
                }
            
            # Create the document
            now = datetime.utcnow()
            platform_doc = {
                "_id": "rating_distribution",
                "platforms": platforms_data,
                "period": period,
                "updated_at": now
            }
            
            # Upsert into platform_stats collection
            db.platform_stats.replace_one(
                {"_id": "rating_distribution", "period": period},
                platform_doc,
                upsert=True
            )
            
            logger.info(f"Refreshed platform stats for period: {period}")
        
        elapsed = time.time() - start_time
        logger.info(f"Refreshed platform_stats collection in {elapsed:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error refreshing platform_stats: {e}", exc_info=True)

def refresh_time_series_stats():
    """Refresh time series stats for recently active products."""
    logger.info("Refreshing time_series_stats collection...")
    start_time = time.time()
    
    try:
        # Find recently active products (products with reviews in the last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_product_ids = db.reviews.distinct(
            "product_id", 
            {"date": {"$gte": thirty_days_ago}}
        )
        
        logger.info(f"Found {len(recent_product_ids)} recently active products")
        
        # Limit to 50 products per refresh to avoid overloading the system
        product_batch = recent_product_ids[:50]
        
        now = datetime.utcnow()
        ninety_days_ago = now - timedelta(days=90)
        
        # Update stats for each product in the batch
        for product_id in product_batch:
            for interval in ["day", "week", "month"]:
                refresh_product_time_series(product_id, interval, ninety_days_ago, now)
        
        elapsed = time.time() - start_time
        logger.info(f"Refreshed time_series_stats for {len(product_batch)} products in {elapsed:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error refreshing time_series_stats: {e}", exc_info=True)

def refresh_product_time_series(product_id, interval, start_date, end_date):
    """Refresh time series data for a specific product."""
    # Define date grouping format based on interval
    if interval == 'day':
        date_group = {
            "year": {"$year": "$date"},
            "month": {"$month": "$date"},
            "day": {"$dayOfMonth": "$date"}
        }
        date_format = "%Y-%m-%d"
    elif interval == 'week':
        date_group = {
            "year": {"$year": "$date"},
            "week": {"$week": "$date"}
        }
        date_format = "Week %U, %Y"
    else:  # month
        date_group = {
            "year": {"$year": "$date"},
            "month": {"$month": "$date"}
        }
        date_format = "%Y-%m"
    
    # Aggregation pipeline for sentiment over time
    pipeline = [
        # Match reviews for this product in date range
        {"$match": {
            "product_id": product_id,
            "date": {"$gte": start_date, "$lte": end_date}
        }},
        
        # Group by date interval and sentiment
        {"$group": {
            "_id": {
                "date": date_group,
                "sentiment": "$sentiment.label"
            },
            "count": {"$sum": 1},
            "avg_score": {"$avg": "$sentiment.score"}
        }},
        
        # Reshape data to have sentiment categories as fields
        {"$group": {
            "_id": "$_id.date",
            "sentiments": {
                "$push": {
                    "k": "$_id.sentiment",
                    "v": {
                        "count": "$count",
                        "avg_score": "$avg_score"
                    }
                }
            },
            "total": {"$sum": "$count"}
        }},
        
        # Add formatted date string
        {"$addFields": {
            "date_str": {
                "$dateToString": {
                    "format": date_format,
                    "date": {
                        "$dateFromParts": {
                            "year": "$_id.year",
                            "month": {"$ifNull": ["$_id.month", 1]},
                            "day": {"$ifNull": ["$_id.day", 1]}
                        }
                    }
                }
            }
        }},
        
        # Sort by date
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}}
    ]
    
    # Execute the pipeline
    results = list(db.reviews.aggregate(pipeline))
    
    # Transform data for storage
    time_series_data = []
    for item in results:
        date_parts = item["_id"]
        date_obj = datetime(
            year=date_parts["year"],
            month=date_parts.get("month", 1),
            day=date_parts.get("day", 1)
        )
        
        # Convert sentiments array to object
        sentiments_dict = {}
        for sentiment_entry in item["sentiments"]:
            sentiments_dict[sentiment_entry["k"]] = sentiment_entry["v"]
        
        # Add percentages
        total = item["total"]
        if total > 0:
            for label in ["positive", "negative", "neutral"]:
                if label in sentiments_dict:
                    sentiments_dict[label]["percentage"] = round(
                        (sentiments_dict[label]["count"] / total) * 100, 1
                    )
        
        time_series_data.append({
            "date": date_obj,
            "date_str": item["date_str"],
            "sentiments": sentiments_dict,
            "total": total
        })
    
    # Store in time_series_stats collection
    now = datetime.utcnow()
    db.time_series_stats.update_one(
        {"product_id": product_id, "interval": interval},
        {
            "$set": {
                "product_id": product_id,
                "interval": interval,
                "start_date": start_date,
                "end_date": end_date,
                "data": time_series_data,
                "updated_at": now
            }
        },
        upsert=True
    )

def clean_expired_comparisons():
    """Clean up expired product comparison caches."""
    logger.info("Cleaning expired product comparison caches...")
    
    try:
        # Delete old comparison caches (older than 7 days and low view count)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        result = db.product_comparisons.delete_many({
            "updated_at": {"$lt": seven_days_ago},
            "view_count": {"$lt": 5}
        })
        
        logger.info(f"Cleaned {result.deleted_count} expired product comparisons")
        
    except Exception as e:
        logger.error(f"Error cleaning expired comparisons: {e}", exc_info=True)

def run_all_refreshes():
    """Run all refresh tasks."""
    logger.info("Starting scheduled refresh of all pre-computed collections")
    
    # Run all refresh tasks
    refresh_keyword_stats()
    refresh_platform_stats()
    refresh_time_series_stats()
    clean_expired_comparisons()
    
    logger.info("Completed all refresh tasks")

def run_scheduled_tasks():
    """Configure and run scheduled tasks."""
    # Schedule tasks at different frequencies
    schedule.every().day.at("02:00").do(refresh_keyword_stats)  # Daily at 2 AM
    schedule.every(3).hours.do(refresh_platform_stats)  # Every 3 hours
    schedule.every(6).hours.do(refresh_time_series_stats)  # Every 6 hours
    schedule.every().day.at("03:00").do(clean_expired_comparisons)  # Daily at 3 AM
    
    logger.info("Scheduled refresh tasks initialized")
    
    # Run tasks on startup
    run_all_refreshes()
    
    # Keep running scheduled tasks
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    try:
        # Run scheduled tasks
        run_scheduled_tasks()
    except KeyboardInterrupt:
        logger.info("Scheduled tasks stopped by user")
    except Exception as e:
        logger.error(f"Error in scheduled tasks: {e}", exc_info=True) 