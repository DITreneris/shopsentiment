"""
Celery tasks for dashboard data management
Handles background refresh of precomputed statistics
"""

import logging
from celery import shared_task, states
from bson import ObjectId
from datetime import datetime, timedelta
import time
import random
from pymongo import UpdateOne, InsertOne
from flask import current_app

from app.services.dashboard_service import dashboard_service
from app.utils.mongodb_aggregations import AggregationPipelines

logger = logging.getLogger(__name__)

# Constants
MAX_PRODUCTS_PER_BATCH = 20  # Maximum number of products to process in a single task
STAGGER_SECONDS = 2  # Seconds to stagger between product refreshes to avoid Redis/MongoDB contention

# Task execution history (in-memory cache for demo purposes)
# In a production system, this would be stored in Redis or a database
TASK_HISTORY = {}

@shared_task(name="refresh_popular_product_stats")
def refresh_popular_product_stats():
    """
    Refresh precomputed statistics for popular products
    Run periodically in the background to ensure dashboard data is current
    """
    task_name = 'refresh_popular_product_stats'
    record_task_start(task_name)
    
    try:
        logger.info("Starting refresh of popular product statistics")
        
        # Get MongoDB connection
        db = dashboard_service.get_mongodb()
        if not db:
            logger.error("MongoDB not available, cannot refresh stats")
            record_task_completion(task_name, states.FAILURE, "MongoDB not initialized")
            return False
        
        # Find recently viewed products (most popular)
        # This query would be customized based on how you track popularity
        # Here we're using review count as a proxy for popularity
        popular_products = list(db.products.find(
            {}, 
            {"_id": 1}
        ).sort("stats.review_count", -1).limit(MAX_PRODUCTS_PER_BATCH))
        
        logger.info(f"Found {len(popular_products)} popular products to refresh")
        
        # Process each product
        for product in popular_products:
            product_id = product["_id"]
            product_id_str = str(product_id)
            
            try:
                # Refresh all time periods and intervals for sentiment trends
                for days in [7, 30, 90, 365]:
                    for interval in ['day', 'week', 'month']:
                        logger.debug(f"Refreshing sentiment trend ({days} days, {interval}) for product {product_id}")
                        stats_type = f"sentiment_trend:{days}:{interval}"
                        
                        # Get fresh data directly from aggregation pipeline
                        sentiment_data = AggregationPipelines.sentiment_over_time(
                            product_id=product_id,
                            days=days,
                            interval=interval
                        )
                        
                        # Store in precomputed stats collection
                        if sentiment_data:
                            AggregationPipelines.store_precomputed_stats(
                                stats_type=stats_type,
                                identifier=product_id_str,
                                data=sentiment_data,
                                expiration=days * 2  # Longer time periods get longer cache
                            )
                            logger.debug(f"Stored {len(sentiment_data)} data points for {stats_type}, product {product_id}")
                        else:
                            logger.warning(f"No data generated for {stats_type}, product {product_id}")
                
                # Slightly stagger processing to avoid spikes
                time.sleep(STAGGER_SECONDS)
                    
            except Exception as e:
                logger.error(f"Error refreshing sentiment data for product {product_id}: {e}")
                # Continue with next product
                continue
        
        logger.info("Completed refresh of popular product statistics")
        record_task_completion(task_name, states.SUCCESS, f"Refreshed stats for {len(popular_products)} products")
        return True
        
    except Exception as e:
        logger.error(f"Error in refresh_popular_product_stats task: {e}", exc_info=True)
        record_task_completion(task_name, states.FAILURE, str(e))
        return False

@shared_task(name="refresh_product_stats")
def refresh_product_stats(product_id):
    """
    Refresh all statistics for a specific product
    
    Args:
        product_id: MongoDB ObjectId for the product (string)
    """
    try:
        logger.info(f"Starting refresh of statistics for product {product_id}")
        
        # Convert string to ObjectId if necessary
        if isinstance(product_id, str):
            product_obj_id = ObjectId(product_id)
        else:
            product_obj_id = product_id
            product_id = str(product_obj_id)
        
        pipelines = AggregationPipelines()
        
        # 1. Refresh sentiment trends for different time periods
        for days in [7, 30, 90, 365]:
            for interval in ['day', 'week', 'month']:
                stats_type = f"sentiment_trend:{days}:{interval}"
                try:
                    data = pipelines.sentiment_over_time(product_obj_id, days, interval)
                    if data:
                        pipelines.store_precomputed_stats(stats_type, product_id, data)
                        logger.debug(f"Refreshed {stats_type} for product {product_id}")
                except Exception as e:
                    logger.error(f"Error refreshing {stats_type} for product {product_id}: {e}")
        
        # 2. Refresh keyword sentiment
        try:
            stats_type = "keyword_sentiment"
            data = pipelines.keyword_sentiment_analysis(product_obj_id)
            if data:
                pipelines.store_precomputed_stats(stats_type, product_id, data)
                logger.debug(f"Refreshed {stats_type} for product {product_id}")
        except Exception as e:
            logger.error(f"Error refreshing keyword sentiment for product {product_id}: {e}")
        
        # 3. Refresh rating distribution
        try:
            stats_type = "rating_distribution"
            data = pipelines.rating_distribution_for_product(product_obj_id)
            if data:
                pipelines.store_precomputed_stats(stats_type, product_id, data)
                logger.debug(f"Refreshed {stats_type} for product {product_id}")
        except Exception as e:
            logger.error(f"Error refreshing rating distribution for product {product_id}: {e}")
        
        logger.info(f"Completed refresh of statistics for product {product_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error in refresh_product_stats task: {e}")
        return False

@shared_task(name="schedule_stats_refresh")
def schedule_stats_refresh():
    """
    Intelligently schedule refreshes for products based on access patterns
    """
    try:
        logger.info("Starting statistics refresh scheduling")
        
        db = dashboard_service.get_mongodb()
        if not db:
            logger.error("MongoDB not available, cannot schedule refreshes")
            return False
            
        # Get list of products that need refreshing
        # Prioritize based on:
        # 1. Recently accessed products (if you track this)
        # 2. Products with stale precomputed stats
        # 3. Products with high review counts
        
        # This is a placeholder implementation - in a real system, you would
        # track product access and prioritize accordingly
        
        # Get products with stale stats (older than 24 hours)
        stale_cutoff = datetime.now() - timedelta(hours=24)
        
        pipeline = [
            # Join with precomputed_stats to find products with stale stats
            {"$lookup": {
                "from": "precomputed_stats",
                "let": {"product_id": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$eq": ["$identifier", "$$product_id"]},
                        "created_at": {"$lt": stale_cutoff}
                    }}
                ],
                "as": "stale_stats"
            }},
            
            # Match products with stale stats or no stats at all
            {"$match": {"$or": [
                {"stale_stats": {"$ne": []}},
                {"stale_stats": {"$size": 0}}
            ]}},
            
            # Project only needed fields
            {"$project": {
                "_id": 1,
                "review_count": "$stats.review_count",
                "stale_stats_count": {"$size": "$stale_stats"}
            }},
            
            # Sort by number of stale stats (desc) and review count (desc)
            {"$sort": {
                "stale_stats_count": -1,
                "review_count": -1
            }},
            
            # Limit to a reasonable batch size
            {"$limit": 50}
        ]
        
        products_to_refresh = list(db.products.aggregate(pipeline))
        
        logger.info(f"Scheduling refreshes for {len(products_to_refresh)} products")
        
        # Schedule individual refresh tasks with staggered delays
        for i, product in enumerate(products_to_refresh):
            # Add some randomness to the delay to avoid thundering herd
            delay_seconds = i * 60 + random.randint(0, 30)
            
            # Schedule the task with the calculated delay
            refresh_product_stats.apply_async(
                args=[str(product["_id"])],
                countdown=delay_seconds
            )
            
            logger.debug(f"Scheduled refresh for product {product['_id']} with {delay_seconds}s delay")
        
        logger.info("Completed scheduling of product statistics refreshes")
        return True
        
    except Exception as e:
        logger.error(f"Error in schedule_stats_refresh task: {e}")
        return False

@shared_task(name="refresh_platform_stats")
def refresh_platform_stats():
    """
    Refresh platform-wide statistics such as rating distributions and keyword sentiment
    """
    task_name = 'refresh_platform_stats'
    record_task_start(task_name)
    
    try:
        logger.info("Starting refresh of platform-wide statistics")
        
        pipelines = AggregationPipelines()
        
        # Refresh rating distribution by platform
        try:
            for days in [30, 90, 365]:
                stats_type = f"rating_distribution_by_platform:{days}"
                logger.debug(f"Refreshing {stats_type}")
                
                distribution_data = pipelines.rating_distribution_by_platform(days=days)
                
                if distribution_data:
                    # Store in precomputed stats
                    pipelines.store_precomputed_stats(
                        stats_type=stats_type,
                        identifier="all_platforms",
                        data=distribution_data,
                        expiration=days  # Scale expiration with time range
                    )
                    logger.debug(f"Stored rating distribution data for {len(distribution_data)} platforms")
                else:
                    logger.warning(f"No rating distribution data generated for {stats_type}")
                
        except Exception as e:
            logger.error(f"Error refreshing rating distribution: {e}")
        
        # Refresh global keyword sentiment
        try:
            for min_count in [5, 10, 25]:
                stats_type = f"global_keyword_sentiment:{min_count}"
                logger.debug(f"Refreshing {stats_type}")
                
                keyword_data = pipelines.global_keyword_sentiment(min_count=min_count)
                
                if keyword_data:
                    # Store in precomputed stats
                    pipelines.store_precomputed_stats(
                        stats_type=stats_type,
                        identifier="global",
                        data=keyword_data,
                        expiration=48  # 48 hours
                    )
                    logger.debug(f"Stored global keyword sentiment data for {len(keyword_data)} keywords")
                else:
                    logger.warning(f"No global keyword sentiment data generated for {stats_type}")
                
        except Exception as e:
            logger.error(f"Error refreshing global keyword sentiment: {e}")
        
        # Refresh platform stats by time period
        try:
            for days in [30, 90, 365]:
                stats_type = f"platform_stats:{days}"
                logger.debug(f"Refreshing {stats_type}")
                
                platform_stats = pipelines.platform_stats_by_time_period(days=days)
                
                if platform_stats:
                    # Store in precomputed stats
                    pipelines.store_precomputed_stats(
                        stats_type=stats_type,
                        identifier="all_platforms",
                        data=platform_stats,
                        expiration=days  # Scale expiration with time range
                    )
                    logger.debug(f"Stored platform stats for {len(platform_stats)} platforms")
                else:
                    logger.warning(f"No platform stats generated for {stats_type}")
                
        except Exception as e:
            logger.error(f"Error refreshing platform stats: {e}")
        
        logger.info("Completed refresh of platform-wide statistics")
        record_task_completion(task_name, states.SUCCESS, "Refreshed platform statistics")
        return True
        
    except Exception as e:
        logger.error(f"Error in refresh_platform_stats task: {e}", exc_info=True)
        record_task_completion(task_name, states.FAILURE, str(e))
        return False

@shared_task(name="refresh_comparison_stats")
def refresh_comparison_stats():
    """
    Refresh product comparison statistics for commonly compared products
    """
    task_name = 'refresh_comparison_stats'
    record_task_start(task_name)
    
    try:
        logger.info("Starting refresh of product comparison statistics")
        
        # Get MongoDB connection
        db = dashboard_service.get_mongodb()
        if not db:
            logger.error("MongoDB not available, cannot refresh comparison stats")
            record_task_completion(task_name, states.FAILURE, "MongoDB not initialized")
            return False
        
        pipelines = AggregationPipelines()
        
        # Find most popular product sets for comparison
        # In a real system, you might track commonly compared products
        # For now, we'll just use the top products by review count
        top_products = list(db.products.find(
            {}, 
            {"_id": 1}
        ).sort("stats.review_count", -1).limit(10))
        
        if len(top_products) < 2:
            logger.warning("Not enough products for comparison refresh")
            record_task_completion(task_name, states.WARNING, "Not enough products for comparison refresh")
            return False
        
        # Get IDs
        product_ids = [str(p["_id"]) for p in top_products]
        
        # Consider all pairs and some triplets of top products
        comparisons_to_refresh = []
        
        # All pairs
        for i in range(len(product_ids)):
            for j in range(i+1, len(product_ids)):
                comparisons_to_refresh.append([product_ids[i], product_ids[j]])
        
        # Some triplets (limit to avoid too many combinations)
        for i in range(min(5, len(product_ids))):
            for j in range(i+1, min(6, len(product_ids))):
                for k in range(j+1, min(7, len(product_ids))):
                    comparisons_to_refresh.append([product_ids[i], product_ids[j], product_ids[k]])
        
        logger.info(f"Found {len(comparisons_to_refresh)} product combinations to refresh")
        
        # Process each comparison set
        for product_set in comparisons_to_refresh:
            try:
                # Create a stable identifier from sorted product IDs
                set_id = "_".join(sorted(product_set))
                stats_type = f"product_comparison:{len(product_set)}"
                
                logger.debug(f"Refreshing comparison for products: {set_id}")
                
                # Convert string IDs to ObjectIDs for the pipeline
                object_ids = [ObjectId(pid) for pid in product_set]
                
                # Get comparison data
                comparison_data = pipelines.product_comparison(object_ids)
                
                if comparison_data:
                    # Store in precomputed stats
                    pipelines.store_precomputed_stats(
                        stats_type=stats_type,
                        identifier=set_id,
                        data=comparison_data,
                        expiration=48  # 48 hours
                    )
                    logger.debug(f"Stored comparison data for {len(comparison_data)} products")
                else:
                    logger.warning(f"No comparison data generated for {set_id}")
                
                # Stagger processing
                time.sleep(STAGGER_SECONDS)
                
            except Exception as e:
                logger.error(f"Error refreshing comparison for set {set_id}: {e}")
                continue
        
        logger.info("Completed refresh of product comparison statistics")
        record_task_completion(task_name, states.SUCCESS, f"Refreshed {len(comparisons_to_refresh)} product comparisons")
        return True
        
    except Exception as e:
        logger.error(f"Error in refresh_comparison_stats task: {e}", exc_info=True)
        record_task_completion(task_name, states.FAILURE, str(e))
        return False

@shared_task(name="refresh_all_dashboard_stats")
def refresh_all_dashboard_stats():
    """
    Refresh all dashboard statistics in sequence
    """
    task_name = 'refresh_all_dashboard_stats'
    record_task_start(task_name)
    
    try:
        logger.info("Starting complete dashboard statistics refresh")
        
        # Refresh platform stats first (these are fewer and provide global context)
        platform_result = refresh_platform_stats()
        
        # Schedule product stats refreshes (this will run them in the background)
        schedule_result = schedule_stats_refresh()
        
        # Refresh comparison stats
        comparison_result = refresh_comparison_stats()
        
        # Check success
        success = platform_result and schedule_result and comparison_result
        
        logger.info(f"Completed dashboard statistics refresh initialization. Success: {success}")
        record_task_completion(task_name, states.SUCCESS, f"Refreshed all dashboard statistics. Success: {success}")
        return success
        
    except Exception as e:
        logger.error(f"Error in refresh_all_dashboard_stats task: {e}", exc_info=True)
        record_task_completion(task_name, states.FAILURE, str(e))
        return False

@shared_task(name="prune_stale_stats")
def prune_stale_stats():
    """
    Remove very old precomputed statistics that are no longer needed
    This helps keep the precomputed_stats collection from growing too large
    """
    task_name = 'prune_stale_stats'
    record_task_start(task_name)
    
    try:
        logger.info("Starting cleanup of stale statistics")
        
        # Get MongoDB connection
        db = dashboard_service.get_mongodb()
        if not db:
            logger.error("MongoDB not available, cannot prune stats")
            record_task_completion(task_name, states.FAILURE, "MongoDB not initialized")
            return False
        
        # Define extremely stale cutoff (older than 30 days)
        extreme_stale_cutoff = datetime.now() - timedelta(days=30)
        
        # Delete extremely old stats
        result = db.precomputed_stats.delete_many({
            "created_at": {"$lt": extreme_stale_cutoff}
        })
        
        logger.info(f"Removed {result.deleted_count} extremely stale statistics (older than 30 days)")
        
        # For stats that haven't been invalidated via the TTL index,
        # but are past their expiration, delete them manually
        result = db.precomputed_stats.delete_many({
            "expires_at": {"$lt": datetime.now()}
        })
        
        logger.info(f"Removed {result.deleted_count} expired statistics")
        
        # Log stats collection size
        stats_count = db.precomputed_stats.count_documents({})
        logger.info(f"Current precomputed_stats collection size: {stats_count} documents")
        
        record_task_completion(task_name, states.SUCCESS, f"Pruned {result.deleted_count} stale statistics")
        return True
        
    except Exception as e:
        logger.error(f"Error in prune_stale_stats task: {e}", exc_info=True)
        record_task_completion(task_name, states.FAILURE, str(e))
        return False

def get_task_stats():
    """
    Get statistics about dashboard task executions
    
    Returns:
        List of dictionaries with task statistics
    """
    stats = []
    
    # In a real implementation, we would query Celery's result backend
    # or a database where task execution metrics are stored
    
    # For demo purposes, use the in-memory cache
    for task_name, history in TASK_HISTORY.items():
        if not history:
            continue
            
        # Get the most recent execution
        latest = history[-1]
        
        # Format task info
        display_name = task_name.split('.')[-1]
        
        stats.append({
            'type': display_name,
            'last_run': latest.get('finished_at', 'Unknown'),
            'duration': f"{latest.get('duration', 0):.2f} seconds",
            'status': latest.get('status', 'Unknown'),
            'result': latest.get('result', None)
        })
    
    # Add common tasks if they don't exist in history yet
    task_names = [s['type'] for s in stats]
    
    common_tasks = [
        'refresh_popular_product_stats',
        'refresh_platform_stats',
        'refresh_comparison_stats',
        'refresh_all_dashboard_stats',
        'prune_stale_stats'
    ]
    
    for task in common_tasks:
        if task not in task_names:
            stats.append({
                'type': task,
                'last_run': 'Never',
                'duration': '-',
                'status': 'Not Run',
                'result': None
            })
    
    return stats

def record_task_start(task_name):
    """Record the start of a task execution"""
    if task_name not in TASK_HISTORY:
        TASK_HISTORY[task_name] = []
        
    # Create a new execution record
    execution = {
        'started_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': states.STARTED
    }
    
    TASK_HISTORY[task_name].append(execution)
    return execution

def record_task_completion(task_name, status, result=None):
    """Record the completion of a task execution"""
    if task_name not in TASK_HISTORY or not TASK_HISTORY[task_name]:
        # Should not happen, but handle it gracefully
        record_task_start(task_name)
    
    # Update the latest execution record
    execution = TASK_HISTORY[task_name][-1]
    now = datetime.now()
    
    # Parse the start time
    try:
        started_at = datetime.strptime(execution['started_at'], '%Y-%m-%d %H:%M:%S')
        duration = (now - started_at).total_seconds()
    except (ValueError, KeyError):
        duration = 0
    
    # Update the execution record
    execution.update({
        'finished_at': now.strftime('%Y-%m-%d %H:%M:%S'),
        'status': status,
        'duration': duration,
        'result': result
    })
    
    # Limit history to last 10 executions
    if len(TASK_HISTORY[task_name]) > 10:
        TASK_HISTORY[task_name] = TASK_HISTORY[task_name][-10:]
    
    return execution 