"""
Dashboard Data Service
Provides optimized data access for dashboard visualizations using precomputed stats
"""

import logging
import time
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app, g
from bson import ObjectId

from app.utils.mongodb_aggregations import AggregationPipelines
from app.utils.redis_fallback import redis_fallback, with_redis_fallback

logger = logging.getLogger(__name__)

# Constants
CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours in seconds
FRESH_STATS_MAX_AGE = 24  # Max age for precomputed stats in hours
METRIC_WARNING_THRESHOLD = 1000  # Milliseconds - log warning if query exceeds this time

# Global instance of the dashboard service
dashboard_service = None

def init_dashboard_service(app, cache):
    """Initialize the dashboard service with app instance and cache"""
    global dashboard_service
    
    if dashboard_service is None:
        logger.info("Initializing Dashboard Service")
        dashboard_service = DashboardService()
        
        # Set Redis connection if provided by cache
        if cache and hasattr(cache, 'cache') and hasattr(cache.cache, '_client'):
            app.redis = cache.cache._client
            # Configure redis fallback with the Redis client
            redis_fallback.set_redis_client(app.redis)
            logger.info("Redis client configured for Dashboard Service with fallback enabled")
        else:
            logger.warning("Redis client not available, Dashboard Service will use fallback mechanism")
    
    return dashboard_service

def timeit(method):
    """Decorator to measure the execution time of methods"""
    @wraps(method)
    def timed(*args, **kwargs):
        start_time = time.time()
        result = method(*args, **kwargs)
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000  # Convert to milliseconds
        
        if duration > METRIC_WARNING_THRESHOLD:
            logger.warning(f"Slow dashboard query: {method.__name__} took {duration:.2f}ms")
        else:
            logger.debug(f"Dashboard query time: {method.__name__} took {duration:.2f}ms")
            
        # Add metric for monitoring
        if hasattr(current_app, 'metrics'):
            current_app.metrics.add_metric(f"dashboard_query.{method.__name__}", duration)
            
        return result
    return timed

class DashboardService:
    """Service for providing data to dashboard views with optimized performance"""
    
    @staticmethod
    def get_mongodb():
        """Get MongoDB connection from the Flask app context"""
        if hasattr(current_app, 'mongodb'):
            return current_app.mongodb
        logger.error("MongoDB not initialized in Flask app")
        return None
    
    @staticmethod
    def get_redis():
        """Get Redis connection from the Flask app context"""
        if hasattr(current_app, 'redis'):
            return current_app.redis
        logger.error("Redis not initialized in Flask app")
        return None
    
    @staticmethod
    def cache_key(key_type, identifier=None):
        """Generate a standardized cache key for Redis"""
        if identifier:
            return f"dashboard:{key_type}:{identifier}"
        return f"dashboard:{key_type}"
    
    @timeit
    def get_sentiment_trend(self, product_id, days=30, interval='day', force_refresh=False):
        """
        Get sentiment trend data for a product, using precomputed stats if available
        
        Args:
            product_id: MongoDB ObjectId for the product
            days: Number of days to look back
            interval: Time grouping - 'day', 'week', or 'month'
            force_refresh: Force recalculation instead of using cached data
            
        Returns:
            List of sentiment data points over time
        """
        # Convert product_id to string if it's an ObjectId
        if isinstance(product_id, ObjectId):
            product_id_str = str(product_id)
        else:
            product_id_str = product_id
            # Convert to ObjectId for MongoDB queries if it's a string
            product_id = ObjectId(product_id) if isinstance(product_id, str) else product_id
        
        # Key for this specific trend data
        stats_type = f"sentiment_trend:{days}:{interval}"
        
        # Create aggregation pipelines instance
        pipelines = AggregationPipelines()
        
        # Step 1: Check Redis cache first (fastest)
        cache_key = self.cache_key(stats_type, product_id_str)
        
        if not force_refresh:
            cached_data = redis_fallback.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data
        
        # Step 2: Check precomputed MongoDB stats (next fastest)
        if not force_refresh:
            precomputed_stats = pipelines.get_precomputed_stats(
                stats_type, 
                product_id_str,
                max_age_hours=FRESH_STATS_MAX_AGE
            )
            if precomputed_stats:
                # Cache in Redis for faster future access
                redis_fallback.set(cache_key, precomputed_stats, CACHE_TIMEOUT)
                logger.debug(f"MongoDB precomputed stats hit for {stats_type}:{product_id_str}")
                return precomputed_stats
        
        # Step 3: Calculate fresh data (slowest but always up-to-date)
        fresh_data = pipelines.sentiment_over_time(product_id, days, interval)
        
        # Store in precomputed stats for future use
        pipelines.store_precomputed_stats(
            stats_type=stats_type, 
            identifier=product_id_str, 
            data=fresh_data,
            expiration=days  # Set expiration based on days parameter
        )
        
        # Cache in Redis for faster future access
        redis_fallback.set(cache_key, fresh_data, CACHE_TIMEOUT)
        logger.debug(f"Fresh data calculated and cached for {stats_type}:{product_id_str}")
        
        return fresh_data
    
    @timeit
    def get_rating_distribution(self, platform=None, days=90, force_refresh=False):
        """
        Get rating distribution by platform, using precomputed stats if available
        
        Args:
            platform: Optional platform filter (e.g., 'amazon', 'ebay')
            days: Number of days to look back
            force_refresh: Force recalculation instead of using cached data
            
        Returns:
            Rating distribution data grouped by platform
        """
        # Key for this specific distribution data
        stats_type = f"rating_distribution_by_platform:{days}"
        identifier = platform if platform else "all_platforms"
        
        # Create aggregation pipelines instance
        pipelines = AggregationPipelines()
        
        # Step 1: Check Redis cache first (fastest)
        cache_key = self.cache_key(stats_type, identifier)
        
        if not force_refresh:
            cached_data = redis_fallback.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data
        
        # Step 2: Check precomputed MongoDB stats (next fastest)
        if not force_refresh:
            precomputed_stats = pipelines.get_precomputed_stats(
                stats_type, 
                identifier,
                max_age_hours=FRESH_STATS_MAX_AGE
            )
            if precomputed_stats:
                # Cache in Redis for faster future access
                redis_fallback.set(cache_key, precomputed_stats, CACHE_TIMEOUT)
                logger.debug(f"MongoDB precomputed stats hit for {stats_type}:{identifier}")
                return precomputed_stats
        
        # Step 3: Calculate fresh data (slowest but always up-to-date)
        fresh_data = pipelines.rating_distribution_by_platform(days=days)
        
        # Filter by platform if specified
        if platform and platform != "all_platforms":
            # Only include data for the requested platform
            filtered_data = {k: v for k, v in fresh_data.items() if k == platform}
            store_data = filtered_data
        else:
            store_data = fresh_data
        
        # Store in precomputed stats for future use
        pipelines.store_precomputed_stats(
            stats_type=stats_type, 
            identifier=identifier, 
            data=store_data,
            expiration=max(days // 2, 24)  # Expire based on days parameter but min 24 hours
        )
        
        # Cache in Redis for faster future access
        redis_fallback.set(cache_key, store_data, CACHE_TIMEOUT)
        logger.debug(f"Fresh data calculated and cached for {stats_type}:{identifier}")
        
        return store_data
    
    @timeit
    def get_keyword_sentiment(self, min_count=10, force_refresh=False):
        """
        Get keyword sentiment analysis data, using precomputed stats if available
        
        Args:
            min_count: Minimum keyword occurrence to include
            force_refresh: Force recalculation instead of using cached data
            
        Returns:
            Keyword sentiment analysis data
        """
        # Key for this specific keyword data
        stats_type = f"global_keyword_sentiment:{min_count}"
        identifier = "global"
        
        # Create aggregation pipelines instance
        pipelines = AggregationPipelines()
        
        # Step 1: Check Redis cache first (fastest)
        cache_key = self.cache_key(stats_type, identifier)
        
        if not force_refresh:
            cached_data = redis_fallback.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data
        
        # Step 2: Check precomputed MongoDB stats (next fastest)
        if not force_refresh:
            precomputed_stats = pipelines.get_precomputed_stats(
                stats_type, 
                identifier,
                max_age_hours=FRESH_STATS_MAX_AGE
            )
            if precomputed_stats:
                # Cache in Redis for faster future access
                redis_fallback.set(cache_key, precomputed_stats, CACHE_TIMEOUT)
                logger.debug(f"MongoDB precomputed stats hit for {stats_type}:{identifier}")
                return precomputed_stats
        
        # Step 3: Calculate fresh data (slowest but always up-to-date)
        fresh_data = pipelines.global_keyword_sentiment(min_count=min_count)
        
        # Store in precomputed stats for future use
        pipelines.store_precomputed_stats(
            stats_type=stats_type, 
            identifier=identifier, 
            data=fresh_data,
            expiration=48  # 48 hours
        )
        
        # Cache in Redis for faster future access
        redis_fallback.set(cache_key, fresh_data, CACHE_TIMEOUT)
        logger.debug(f"Fresh data calculated and cached for {stats_type}:{identifier}")
        
        return fresh_data
    
    @timeit
    def get_product_comparison(self, product_ids, force_refresh=False):
        """
        Get product comparison data, using precomputed stats if available
        
        Args:
            product_ids: List of MongoDB ObjectIds for the products to compare
            force_refresh: Force recalculation instead of using cached data
            
        Returns:
            Product comparison data
        """
        # Convert product_ids to strings
        product_id_strs = [str(pid) if isinstance(pid, ObjectId) else pid for pid in product_ids]
        
        # Sort IDs to ensure consistent caching regardless of order
        sorted_ids = sorted(product_id_strs)
        
        # Create a stable identifier from the sorted IDs
        identifier = "_".join(sorted_ids)
        
        # Key for this specific comparison data
        stats_type = f"product_comparison:{len(product_ids)}"
        
        # Create aggregation pipelines instance
        pipelines = AggregationPipelines()
        
        # Step 1: Check Redis cache first (fastest)
        cache_key = self.cache_key(stats_type, identifier)
        
        if not force_refresh:
            cached_data = redis_fallback.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data
        
        # Step 2: Check precomputed MongoDB stats (next fastest)
        if not force_refresh:
            precomputed_stats = pipelines.get_precomputed_stats(
                stats_type, 
                identifier,
                max_age_hours=FRESH_STATS_MAX_AGE
            )
            if precomputed_stats:
                # Cache in Redis for faster future access
                redis_fallback.set(cache_key, precomputed_stats, CACHE_TIMEOUT)
                logger.debug(f"MongoDB precomputed stats hit for {stats_type}:{identifier}")
                return precomputed_stats
        
        # Step 3: Calculate fresh data (slowest but always up-to-date)
        # Convert strings back to ObjectIds for MongoDB queries
        object_ids = [ObjectId(pid) if isinstance(pid, str) else pid for pid in product_ids]
        fresh_data = pipelines.product_comparison(object_ids)
        
        # Store in precomputed stats for future use
        pipelines.store_precomputed_stats(
            stats_type=stats_type, 
            identifier=identifier, 
            data=fresh_data,
            expiration=48  # 48 hours
        )
        
        # Cache in Redis for faster future access
        redis_fallback.set(cache_key, fresh_data, CACHE_TIMEOUT)
        logger.debug(f"Fresh data calculated and cached for {stats_type}:{identifier}")
        
        return fresh_data
    
    @timeit
    def get_trending_products(self, limit=10, days=30, force_refresh=False):
        """
        Get trending products based on recent reviews and sentiment
        
        Args:
            limit: Number of products to return
            days: Number of days to look back
            force_refresh: Force recalculation instead of using cached data
            
        Returns:
            List of trending products with score and metadata
        """
        # Key for trending products
        stats_type = f"trending_products:{days}"
        identifier = f"top{limit}"
        
        # Create aggregation pipelines instance
        pipelines = AggregationPipelines()
        
        # Step 1: Check Redis cache first (fastest)
        cache_key = self.cache_key(stats_type, identifier)
        
        if not force_refresh:
            cached_data = redis_fallback.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data
        
        # Step 2: Check precomputed MongoDB stats (next fastest)
        if not force_refresh:
            precomputed_stats = pipelines.get_precomputed_stats(
                stats_type, 
                identifier,
                max_age_hours=FRESH_STATS_MAX_AGE
            )
            if precomputed_stats:
                # Cache in Redis for faster future access
                redis_fallback.set(cache_key, precomputed_stats, CACHE_TIMEOUT)
                logger.debug(f"MongoDB precomputed stats hit for {stats_type}:{identifier}")
                return precomputed_stats
        
        # Step 3: Calculate fresh data (slowest but always up-to-date)
        fresh_data = pipelines.trending_products(days=days, limit=limit)
        
        # Store in precomputed stats for future use
        pipelines.store_precomputed_stats(
            stats_type=stats_type, 
            identifier=identifier, 
            data=fresh_data,
            expiration=24  # 24 hours - trending data changes frequently
        )
        
        # Cache in Redis for faster future access
        redis_fallback.set(cache_key, fresh_data, CACHE_TIMEOUT)
        logger.debug(f"Fresh data calculated and cached for {stats_type}:{identifier}")
        
        return fresh_data
    
    def get_cache_metrics(self):
        """
        Get metrics about caching performance
        
        Returns:
            Dictionary with cache hit rates and other metrics
        """
        # Get redis fallback info
        redis_info = redis_fallback.get_info()
        
        # Get MongoDB precomputed stats info
        mongodb = self.get_mongodb()
        mongo_stats = {}
        
        if mongodb:
            pipelines = AggregationPipelines()
            freshness = pipelines.get_stats_freshness()
            mongo_stats["freshness"] = freshness
            
            # Count by type
            stats_types = pipelines.list_precomputed_stats_types()
            type_counts = {}
            
            for stats_type in stats_types:
                count = mongodb.precomputed_stats.count_documents({"stats_type": stats_type})
                type_counts[stats_type] = count
            
            mongo_stats["type_counts"] = type_counts
            mongo_stats["total_count"] = mongodb.precomputed_stats.count_documents({})
        
        return {
            "redis": redis_info,
            "mongodb": mongo_stats,
            "cache_timeout": CACHE_TIMEOUT,
            "fresh_stats_max_age": FRESH_STATS_MAX_AGE
        }

# Create a singleton instance
dashboard_service = DashboardService() 