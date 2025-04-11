"""
Implement Cache Hit/Miss Ratio Tracking

This script implements monitoring for cache hit/miss ratios in MongoDB precomputed
collections and Redis cache, with metrics exposed via Prometheus for dashboards.
"""

import logging
import time
from datetime import datetime, timedelta
import redis
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from prometheus_client import start_http_server, Counter, Gauge, Summary

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

# Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Define Prometheus metrics
MONGO_CACHE_HITS = Counter('mongodb_cache_hits_total', 
                          'Total number of MongoDB precomputed cache hits',
                          ['collection', 'query_type'])

MONGO_CACHE_MISSES = Counter('mongodb_cache_misses_total', 
                            'Total number of MongoDB precomputed cache misses',
                            ['collection', 'query_type'])

REDIS_CACHE_HITS = Counter('redis_cache_hits_total', 
                          'Total number of Redis cache hits',
                          ['cache_key_prefix'])

REDIS_CACHE_MISSES = Counter('redis_cache_misses_total', 
                            'Total number of Redis cache misses',
                            ['cache_key_prefix'])

CACHE_HIT_RATIO = Gauge('cache_hit_ratio_percent', 
                       'Cache hit ratio percentage',
                       ['cache_type', 'collection'])

CACHE_QUERY_DURATION = Summary('cache_query_duration_seconds',
                              'Time spent querying cache vs direct data',
                              ['cache_type', 'query_type', 'hit_or_miss'])

class CacheMonitor:
    """Monitors and tracks cache hit/miss ratios."""
    
    def __init__(self):
        """Initialize the cache monitor."""
        self.mongo_hits = 0
        self.mongo_misses = 0
        self.redis_hits = 0
        self.redis_misses = 0
        
        # Initialize hit tracking in database if not exists
        self._initialize_hit_tracking()
    
    def _initialize_hit_tracking(self):
        """Initialize hit tracking collection if it doesn't exist."""
        if 'cache_stats' not in db.list_collection_names():
            db.create_collection('cache_stats')
            
            # Insert initial documents for each cache type
            db.cache_stats.insert_many([
                {
                    "cache_type": "mongodb_precomputed",
                    "hits": 0,
                    "misses": 0,
                    "last_reset": datetime.utcnow()
                },
                {
                    "cache_type": "redis",
                    "hits": 0,
                    "misses": 0,
                    "last_reset": datetime.utcnow()
                }
            ])
            
            logger.info("Initialized cache_stats collection")
    
    def track_mongo_cache_access(self, collection, query_type, is_hit, duration_seconds):
        """
        Track MongoDB precomputed cache access.
        
        Args:
            collection: The MongoDB collection name
            query_type: Type of query (e.g., sentiment_trend, keyword_analysis)
            is_hit: Whether the access was a cache hit
            duration_seconds: Query duration in seconds
        """
        if is_hit:
            MONGO_CACHE_HITS.labels(collection=collection, query_type=query_type).inc()
            self.mongo_hits += 1
            db.cache_stats.update_one(
                {"cache_type": "mongodb_precomputed"},
                {"$inc": {"hits": 1}}
            )
        else:
            MONGO_CACHE_MISSES.labels(collection=collection, query_type=query_type).inc()
            self.mongo_misses += 1
            db.cache_stats.update_one(
                {"cache_type": "mongodb_precomputed"},
                {"$inc": {"misses": 1}}
            )
        
        hit_or_miss = "hit" if is_hit else "miss"
        CACHE_QUERY_DURATION.labels(
            cache_type="mongodb",
            query_type=query_type,
            hit_or_miss=hit_or_miss
        ).observe(duration_seconds)
        
        # Update hit ratio
        self._update_hit_ratio("mongodb_precomputed", collection)
    
    def track_redis_cache_access(self, key_prefix, is_hit, duration_seconds):
        """
        Track Redis cache access.
        
        Args:
            key_prefix: The Redis key prefix for grouping
            is_hit: Whether the access was a cache hit
            duration_seconds: Query duration in seconds
        """
        if is_hit:
            REDIS_CACHE_HITS.labels(cache_key_prefix=key_prefix).inc()
            self.redis_hits += 1
            db.cache_stats.update_one(
                {"cache_type": "redis"},
                {"$inc": {"hits": 1}}
            )
        else:
            REDIS_CACHE_MISSES.labels(cache_key_prefix=key_prefix).inc()
            self.redis_misses += 1
            db.cache_stats.update_one(
                {"cache_type": "redis"},
                {"$inc": {"misses": 1}}
            )
        
        hit_or_miss = "hit" if is_hit else "miss"
        CACHE_QUERY_DURATION.labels(
            cache_type="redis",
            query_type=key_prefix,
            hit_or_miss=hit_or_miss
        ).observe(duration_seconds)
        
        # Update hit ratio
        self._update_hit_ratio("redis", key_prefix)
    
    def _update_hit_ratio(self, cache_type, collection):
        """
        Update the cache hit ratio metric.
        
        Args:
            cache_type: Type of cache (mongodb_precomputed or redis)
            collection: Collection or key prefix
        """
        # Get current stats
        stats = db.cache_stats.find_one({"cache_type": cache_type})
        
        if stats:
            total = stats["hits"] + stats["misses"]
            ratio = (stats["hits"] / total * 100) if total > 0 else 0
            
            # Update Prometheus metric
            CACHE_HIT_RATIO.labels(cache_type=cache_type, collection=collection).set(ratio)
    
    def get_cache_stats(self):
        """Get cache statistics."""
        mongo_stats = db.cache_stats.find_one({"cache_type": "mongodb_precomputed"})
        redis_stats = db.cache_stats.find_one({"cache_type": "redis"})
        
        mongo_total = mongo_stats["hits"] + mongo_stats["misses"] if mongo_stats else 0
        redis_total = redis_stats["hits"] + redis_stats["misses"] if redis_stats else 0
        
        mongo_ratio = (mongo_stats["hits"] / mongo_total * 100) if mongo_total > 0 else 0
        redis_ratio = (redis_stats["hits"] / redis_total * 100) if redis_total > 0 else 0
        
        return {
            "mongodb": {
                "hits": mongo_stats["hits"] if mongo_stats else 0,
                "misses": mongo_stats["misses"] if mongo_stats else 0,
                "total": mongo_total,
                "hit_ratio": mongo_ratio
            },
            "redis": {
                "hits": redis_stats["hits"] if redis_stats else 0,
                "misses": redis_stats["misses"] if redis_stats else 0,
                "total": redis_total,
                "hit_ratio": redis_ratio
            },
            "timestamp": datetime.utcnow()
        }
    
    def reset_cache_stats(self):
        """Reset cache statistics."""
        now = datetime.utcnow()
        
        db.cache_stats.update_one(
            {"cache_type": "mongodb_precomputed"},
            {"$set": {"hits": 0, "misses": 0, "last_reset": now}}
        )
        
        db.cache_stats.update_one(
            {"cache_type": "redis"},
            {"$set": {"hits": 0, "misses": 0, "last_reset": now}}
        )
        
        # Reset local counters
        self.mongo_hits = 0
        self.mongo_misses = 0
        self.redis_hits = 0
        self.redis_misses = 0
        
        logger.info("Reset cache statistics")
    
    def print_cache_stats_summary(self):
        """Print a summary of cache statistics."""
        stats = self.get_cache_stats()
        
        logger.info("Cache Statistics Summary:")
        logger.info("-------------------------")
        
        # MongoDB stats
        mongo_stats = stats["mongodb"]
        logger.info(f"MongoDB Precomputed Cache:")
        logger.info(f"  - Hits: {mongo_stats['hits']}")
        logger.info(f"  - Misses: {mongo_stats['misses']}")
        logger.info(f"  - Total: {mongo_stats['total']}")
        logger.info(f"  - Hit Ratio: {mongo_stats['hit_ratio']:.2f}%")
        
        # Redis stats
        redis_stats = stats["redis"]
        logger.info(f"Redis Cache:")
        logger.info(f"  - Hits: {redis_stats['hits']}")
        logger.info(f"  - Misses: {redis_stats['misses']}")
        logger.info(f"  - Total: {redis_stats['total']}")
        logger.info(f"  - Hit Ratio: {redis_stats['hit_ratio']:.2f}%")

def start_prometheus_server(port=9090):
    """Start the Prometheus metrics server."""
    try:
        start_http_server(port)
        logger.info(f"Started Prometheus metrics server on port {port}")
    except Exception as e:
        logger.error(f"Failed to start Prometheus metrics server: {e}")

def main():
    """Main function to run cache monitoring."""
    logger.info("Starting cache hit/miss monitoring")
    
    # Start Prometheus server
    start_prometheus_server()
    
    # Initialize cache monitor
    monitor = CacheMonitor()
    
    # Print current stats
    monitor.print_cache_stats_summary()
    
    logger.info("Cache hit/miss monitoring initialized")
    logger.info("Use the CacheMonitor class in your code to track cache accesses")
    logger.info("Prometheus metrics are available on http://localhost:9090/metrics")

if __name__ == "__main__":
    main() 