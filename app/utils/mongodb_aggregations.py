"""
MongoDB Aggregation Pipelines for ShopSentiment
Optimized to use pre-computed collections where available
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, cast, Union
from pymongo import MongoClient
from bson import ObjectId
from flask import current_app
from pymongo.server_api import ServerApi

logger = logging.getLogger(__name__)

# MongoDB connection
uri = "mongodb+srv://tomasstaniulis76:JaLhUd1NLZUtwVb5@shop1.11tjwh5.mongodb.net/?retryWrites=true&w=majority&appName=Shop1"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.shopsentiment

def get_db():
    """Get MongoDB database connection from current app"""
    if hasattr(current_app, 'mongodb'):
        return current_app.mongodb
    else:
        logger.error("MongoDB not initialized in Flask app")
        return None

class AggregationPipelines:
    """MongoDB aggregation pipelines for analytics"""

    @staticmethod
    def sentiment_over_time(product_id: Union[str, ObjectId], days: int = 30, interval: str = 'day') -> List[Dict[str, Any]]:
        """
        Calculate sentiment trends over time for a specific product
        
        Args:
            product_id: MongoDB ObjectId for the product
            days: Number of days to look back
            interval: Time grouping - 'day', 'week', or 'month'
        
        Returns:
            List of sentiment statistics grouped by time interval
        """
        db = get_db()
        if not db:
            return []
            
        # Convert product_id to ObjectId if it's a string
        if isinstance(product_id, str) and ObjectId.is_valid(product_id):
            product_id = ObjectId(product_id)
        else:
            logger.error(f"Invalid ObjectId format: {product_id}")
            return []
            
        # Try to get from pre-computed collection first
        time_series = db.time_series_stats.find_one({
            "product_id": product_id,
            "interval": interval
        })
        
        if time_series:
            # Filter the data to match the requested date range
            now = datetime.utcnow()
            start_date = now - timedelta(days=days)
            
            filtered_data = [
                point for point in time_series['data']
                if point['date'] >= start_date
            ]
            
            # Update view count for this product's time series
            db.time_series_stats.update_one(
                {"product_id": product_id, "interval": interval},
                {"$inc": {"view_count": 1}}
            )
            
            return filtered_data
        
        # Fallback to the original aggregation if pre-computed data is not available
        # Define date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Define date grouping format
        if interval == 'day':
            date_format = "%Y-%m-%d"
            date_group = {
                "year": {"$year": "$date"},
                "month": {"$month": "$date"},
                "day": {"$dayOfMonth": "$date"}
            }
        elif interval == 'week':
            date_format = "Week %U, %Y"
            date_group = {
                "year": {"$year": "$date"},
                "week": {"$week": "$date"}
            }
        else:  # month
            date_format = "%Y-%m"
            date_group = {
                "year": {"$year": "$date"},
                "month": {"$month": "$date"}
            }
            
        pipeline = [
            # Match reviews for the specified product and date range
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
            
            # Convert sentiment array to object
            {"$project": {
                "date": "$_id",
                "sentiments": {"$arrayToObject": "$sentiments"},
                "total": 1,
                "_id": 0
            }},
            
            # Add formatted date string
            {"$addFields": {
                "date_str": {
                    "$dateToString": {
                        "format": date_format,
                        "date": {
                            "$dateFromParts": {
                                "year": "$date.year",
                                "month": {"$ifNull": ["$date.month", 1]},
                                "day": {"$ifNull": ["$date.day", 1]}
                            }
                        }
                    }
                }
            }},
            
            # Sort by date
            {"$sort": {"date.year": 1, "date.month": 1, "date.day": 1}}
        ]
        
        try:
            results = list(db.reviews.aggregate(pipeline))
            
            # Transform results for API consistency
            formatted_results = []
            for item in results:
                date_str = item.get('date_str', '')
                total = item.get('total', 0)
                if total == 0:
                    continue
                    
                sentiments = item.get('sentiments', {})
                positive = sentiments.get('positive', {}).get('count', 0)
                neutral = sentiments.get('neutral', {}).get('count', 0)
                negative = sentiments.get('negative', {}).get('count', 0)
                
                formatted_results.append({
                    'date': date_str,
                    'positive_percentage': round((positive / total) * 100, 1) if total > 0 else 0,
                    'neutral_percentage': round((neutral / total) * 100, 1) if total > 0 else 0,
                    'negative_percentage': round((negative / total) * 100, 1) if total > 0 else 0,
                    'total': total
                })
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in sentiment_over_time aggregation: {e}")
            return []

    @staticmethod
    def rating_distribution_by_platform(days: int = 90) -> Dict[str, Dict[str, int]]:
        """
        Calculate rating distribution across different platforms
        
        Args:
            days: Number of days to look back
            
        Returns:
            Rating distribution statistics by platform
        """
        db = get_db()
        if not db:
            return {}
            
        # Try to get from pre-computed collection
        platform_stats = db.platform_stats.find_one({
            "_id": "rating_distribution",
            "period": "all_time" if days is None else f"{days}_days"
        })
        
        if platform_stats:
            return platform_stats['platforms']
        
        # Fallback to original aggregation if pre-computed data is not available
        # Define date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days) if days else None
        
        match_stage = {}
        if start_date:
            # First find products with recent reviews
            products_with_recent_reviews = db.reviews.distinct(
                "product_id", 
                {"date": {"$gte": start_date}}
            )
            match_stage = {"_id": {"$in": products_with_recent_reviews}}
        
        pipeline = [
            # Find products with recent reviews if needed
            {"$match": match_stage} if match_stage else {"$match": {}},
            
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
        
        results = list(db.products.aggregate(pipeline))
        
        # Format results
        platform_data = {}
        for item in results:
            platform = item.get('platform', 'unknown')
            platform_data[platform] = {
                "total_products": item.get("total_products", 0),
                "avg_rating": item.get("avg_rating", 0),
                "rating_distribution": item.get("rating_distribution", {})
            }
        
        return platform_data

    @staticmethod
    def keyword_sentiment_analysis(min_count: int = 10) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for common keywords in reviews
        
        Args:
            min_count: Minimum occurrences to include a keyword
            
        Returns:
            List of keywords with sentiment scores
        """
        db = get_db()
        if not db:
            return []
        
        # Try to get from pre-computed collection
        pipeline = [
            {"$match": {"count": {"$gte": min_count}}},
            {"$sort": {"count": -1}},
            {"$limit": 50}
        ]
        
        keyword_stats = list(db.keyword_stats.aggregate(pipeline))
        
        if keyword_stats:
            # Transform to match the expected format
            result = []
            for keyword in keyword_stats:
                result.append({
                    "_id": keyword["keyword"],
                    "count": keyword["count"],
                    "avg_sentiment": keyword["sentiment"]["score"],
                    "sentiment_label": keyword["sentiment"]["label"],
                    "products": keyword["products"]
                })
            return result
        
        # Fallback to original aggregation if pre-computed data is not available
        pipeline = [
            # Unwind keywords array to work with individual keywords
            {"$unwind": "$keywords"},
            
            # Group by keyword
            {"$group": {
                "_id": "$keywords",
                "count": {"$sum": 1},
                "avg_sentiment": {"$avg": "$sentiment.score"},
                "reviews": {"$push": "$_id"}
            }},
            
            # Filter out uncommon keywords
            {"$match": {
                "count": {"$gte": min_count}
            }},
            
            # Sort by frequency
            {"$sort": {"count": -1}},
            
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
            
            # Limit results
            {"$limit": 50}
        ]
        
        return list(db.reviews.aggregate(pipeline))

    @staticmethod
    def product_comparison(product_ids: List[Union[str, ObjectId]]) -> Dict[str, Any]:
        """
        Compare multiple products based on various metrics
        
        Args:
            product_ids: List of MongoDB ObjectIds for products to compare
            
        Returns:
            Comparison data for the products
        """
        db = get_db()
        if not db:
            return {}
        
        # Convert string IDs to ObjectId
        product_objids = []
        for pid in product_ids:
            if isinstance(pid, str) and ObjectId.is_valid(pid):
                product_objids.append(ObjectId(pid))
            else:
                product_objids.append(pid)
        
        if not product_objids:
            return {}
        
        # Sort product IDs for consistent caching
        sorted_ids = sorted(str(pid) for pid in product_objids)
        cache_key = "_".join(sorted_ids)
        
        # Create a hash for the comparison
        import hashlib
        comparison_hash = hashlib.md5(cache_key.encode()).hexdigest()
        
        # Try to get from cached comparisons
        cached_comparison = db.product_comparisons.find_one({"hash": comparison_hash})
        
        if cached_comparison:
            # Update view count
            db.product_comparisons.update_one(
                {"hash": comparison_hash},
                {
                    "$inc": {"view_count": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            return cached_comparison["comparison_data"]
        
        # Fallback to original aggregation if cached data is not available
        pipeline = [
            # Match the specified products
            {"$match": {
                "_id": {"$in": product_objids}
            }},
            
            # Lookup reviews for each product
            {"$lookup": {
                "from": "reviews",
                "localField": "_id",
                "foreignField": "product_id",
                "as": "review_data"
            }},
            
            # Calculate additional metrics
            {"$project": {
                "title": 1,
                "brand": 1,
                "platform": 1,
                "price": 1,
                "stats": 1,
                "review_count": {"$size": "$review_data"},
                "keywords": 1,
                "avg_sentiment": {"$avg": "$review_data.sentiment.score"},
                "review_samples": {"$slice": ["$review_data", 3]}
            }},
            
            # Sort by average rating
            {"$sort": {"stats.avg_rating": -1}}
        ]
        
        comparison_data = list(db.products.aggregate(pipeline))
        
        # Cache the comparison results for future use
        now = datetime.utcnow()
        expires_at = now + timedelta(days=7)  # Cache for 7 days
        
        db.product_comparisons.insert_one({
            "products": product_objids,
            "hash": comparison_hash,
            "comparison_data": comparison_data,
            "view_count": 1,
            "updated_at": now,
            "expires_at": expires_at
        })
        
        return comparison_data

    @staticmethod
    def create_time_series_collection() -> bool:
        """
        Create a time series collection for storing metrics over time
        This uses MongoDB 5.0+ time series collection feature
        
        Returns:
            Success status
        """
        db = get_db()
        if not db:
            return False
            
        try:
            # Check if collection exists
            if "metrics_timeseries" in db.list_collection_names():
                logger.info("Time series collection already exists")
                return True
                
            # Create time series collection
            db.create_collection(
                "metrics_timeseries",
                timeseries={
                    "timeField": "timestamp",
                    "metaField": "metadata",
                    "granularity": "minutes"
                }
            )
            
            # Create indexes
            db.metrics_timeseries.create_index([
                ("metadata.metric_name", 1),
                ("timestamp", -1)
            ])
            
            logger.info("Successfully created time series collection")
            return True
            
        except Exception as e:
            logger.error(f"Error creating time series collection: {e}")
            return False

    @staticmethod
    def create_precomputed_stats_collection() -> bool:
        """
        Create a collection for storing precomputed statistics
        
        Returns:
            Success status
        """
        db = get_db()
        if not db:
            return False
            
        try:
            # Check if collection exists
            if "precomputed_stats" in db.list_collection_names():
                logger.info("Precomputed stats collection already exists")
                return True
                
            # Create precomputed stats collection
            db.create_collection("precomputed_stats")
            
            # Create indexes
            db.precomputed_stats.create_index([
                ("stats_type", 1),
                ("target_id", 1),
                ("created_at", -1)
            ])
            
            logger.info("Successfully created precomputed stats collection")
            return True
            
        except Exception as e:
            logger.error(f"Error creating precomputed stats collection: {e}")
            return False

    @staticmethod
    def store_precomputed_stats(stats_type: str, identifier: str, data: Any, expiration: int = None) -> bool:
        """
        Store precomputed statistics in MongoDB
        
        Args:
            stats_type: Type of statistic (e.g., 'sentiment_trend:30:day')
            identifier: Object identifier (e.g., product_id)
            data: The precomputed data to store
            expiration: Optional expiration time in hours (default: 7 days)
            
        Returns:
            True if successful, False otherwise
        """
        db = get_db()
        if not db:
            return False
            
        # Default expiration: 7 days
        if expiration is None:
            expiration = 7 * 24  # hours
            
        # Calculate expiration date
        expires_at = datetime.now() + timedelta(hours=expiration)
        
        try:
            # Upsert the data
            db.precomputed_stats.update_one(
                {"stats_type": stats_type, "identifier": identifier},
                {"$set": {
                    "data": data,
                    "created_at": datetime.now(),
                    "expires_at": expires_at
                }},
                upsert=True
            )
            logger.debug(f"Stored precomputed stats: {stats_type} for {identifier}")
            return True
        except Exception as e:
            logger.error(f"Error storing precomputed stats: {e}")
            return False

    @staticmethod
    def get_precomputed_stats(stats_type: str, identifier: str, max_age_hours: int = 24) -> Union[Any, None]:
        """
        Retrieve precomputed statistics from MongoDB
        
        Args:
            stats_type: Type of statistic (e.g., 'sentiment_trend:30:day')
            identifier: Object identifier (e.g., product_id)
            max_age_hours: Maximum age of stats in hours before considered stale
            
        Returns:
            Precomputed statistics or None if not found or too old
        """
        db = get_db()
        if not db:
            return None
            
        # Calculate maximum age timestamp
        max_age = datetime.now() - timedelta(hours=max_age_hours)
        
        try:
            # Find the precomputed stats
            stats = db.precomputed_stats.find_one({
                "stats_type": stats_type,
                "identifier": identifier,
                "created_at": {"$gte": max_age}
            })
            
            if stats and "data" in stats:
                logger.debug(f"Found precomputed stats: {stats_type} for {identifier}")
                return stats["data"]
            else:
                logger.debug(f"No fresh precomputed stats found: {stats_type} for {identifier}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving precomputed stats: {e}")
            return None

    @staticmethod
    def invalidate_precomputed_stats(stats_type: str = None, identifier: str = None) -> bool:
        """
        Invalidate precomputed statistics in MongoDB
        
        Args:
            stats_type: Optional type of statistic to invalidate (all types if None)
            identifier: Optional object identifier to invalidate (all identifiers if None)
            
        Returns:
            True if successful, False otherwise
        """
        db = get_db()
        if not db:
            return False
            
        try:
            # Build query based on provided parameters
            query = {}
            if stats_type:
                query["stats_type"] = stats_type
            if identifier:
                query["identifier"] = identifier
                
            # Delete matching stats
            result = db.precomputed_stats.delete_many(query)
            logger.info(f"Invalidated {result.deleted_count} precomputed stats" +
                        f"{f' for {stats_type}' if stats_type else ''}" +
                        f"{f' with identifier {identifier}' if identifier else ''}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating precomputed stats: {e}")
            return False

    @staticmethod
    def list_precomputed_stats_types() -> List[str]:
        """
        List all available precomputed statistic types
        
        Returns:
            List of unique stats_type values
        """
        db = get_db()
        if not db:
            return []
            
        try:
            # Get unique stats types
            stats_types = db.precomputed_stats.distinct("stats_type")
            return stats_types
        except Exception as e:
            logger.error(f"Error listing precomputed stats types: {e}")
            return []

    @staticmethod
    def get_stats_freshness(stats_type: str = None) -> Dict[str, Any]:
        """
        Get freshness information for precomputed statistics
        
        Args:
            stats_type: Optional type of statistic to check (all types if None)
            
        Returns:
            Dictionary with freshness information
        """
        db = get_db()
        if not db:
            return {}
            
        try:
            # Build pipeline to get freshness info
            pipeline = [
                # Match stats_type if provided
                {"$match": {"stats_type": stats_type}} if stats_type else {"$match": {}},
                
                # Group by stats_type
                {"$group": {
                    "_id": "$stats_type",
                    "count": {"$sum": 1},
                    "oldest": {"$min": "$created_at"},
                    "newest": {"$max": "$created_at"},
                    "avg_age_hours": {
                        "$avg": {
                            "$divide": [
                                {"$subtract": [datetime.now(), "$created_at"]},
                                3600000  # Convert ms to hours
                            ]
                        }
                    }
                }},
                
                # Format the output
                {"$project": {
                    "stats_type": "$_id",
                    "count": 1,
                    "oldest": 1,
                    "newest": 1,
                    "avg_age_hours": {"$round": ["$avg_age_hours", 1]},
                    "_id": 0
                }},
                
                # Sort by stats_type
                {"$sort": {"stats_type": 1}}
            ]
            
            # Execute pipeline
            results = list(db.precomputed_stats.aggregate(pipeline))
            
            # Format into a dictionary keyed by stats_type
            freshness = {}
            for item in results:
                stats_type = item.pop("stats_type")
                freshness[stats_type] = item
                
            return freshness
        except Exception as e:
            logger.error(f"Error getting stats freshness: {e}")
            return {}

# Additional helper functions can be added here
def refresh_precomputed_data_for_product(product_id):
    """
    Manually trigger a refresh of pre-computed data for a specific product.
    Useful after significant changes to a product's reviews.
    
    Args:
        product_id: ObjectId or string of the product to refresh
    """
    # Convert product_id to ObjectId if it's a string
    if isinstance(product_id, str) and ObjectId.is_valid(product_id):
        product_id = ObjectId(product_id)
    
    # Import the refresh functions from background_refresh module
    import sys
    import os
    
    # Add the project root to the Python path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    
    from background_refresh import refresh_product_time_series
    
    # Refresh time series data for all intervals
    now = datetime.utcnow()
    ninety_days_ago = now - timedelta(days=90)
    
    for interval in ["day", "week", "month"]:
        refresh_product_time_series(product_id, interval, ninety_days_ago, now)
    
    return {"status": "success", "message": f"Refreshed pre-computed data for product {product_id}"} 