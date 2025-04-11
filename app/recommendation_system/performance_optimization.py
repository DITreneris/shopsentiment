import logging
import time
import functools
from typing import Dict, List, Any, Callable, Optional
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
import redis
from config import MONGO_URI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Redis client for caching
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    redis_available = True
except Exception as e:
    logger.warning(f"Redis not available, caching will be disabled: {str(e)}")
    redis_available = False

class PerformanceOptimizer:
    def __init__(self, mongo_uri: str = MONGO_URI):
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client['shop_sentiment']
        
    def optimize_mongodb_collections(self):
        """
        Create indexes on MongoDB collections to improve query performance
        """
        try:
            # Optimize products collection
            self.db['products'].create_index([('product_id', ASCENDING)], unique=True)
            self.db['products'].create_index([('category', ASCENDING), ('price', ASCENDING)])
            self.db['products'].create_index([('name', 'text')])
            
            # Optimize competitor_products collection
            self.db['competitor_products'].create_index([('name', 'text')])
            self.db['competitor_products'].create_index([('timestamp', DESCENDING)])
            self.db['competitor_products'].create_index([('category', ASCENDING), ('price', ASCENDING)])
            
            logger.info("MongoDB collections optimized with indexes")
        except Exception as e:
            logger.error(f"Error optimizing MongoDB collections: {str(e)}")
    
    @staticmethod
    def optimize_query(collection: Collection, query: Dict, projection: Dict = None):
        """
        Optimize MongoDB query by adding explain plan analysis
        """
        try:
            # Analyze query performance
            explain_result = collection.find(query, projection).explain()
            
            # Check if query uses an index
            if explain_result.get('queryPlanner', {}).get('winningPlan', {}).get('inputStage', {}).get('stage') != 'IXSCAN':
                logger.warning(f"Query not using an index: {query}")
                
            return explain_result
        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}")
            return None

    @staticmethod
    def create_cache_key(func_name: str, *args, **kwargs) -> str:
        """
        Create a cache key from function name and arguments
        """
        arg_str = str(args) + str(sorted(kwargs.items()))
        return f"{func_name}:{hash(arg_str)}"

    @staticmethod
    def cache_result(ttl: int = 3600):
        """
        Decorator to cache function results in Redis
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not redis_available:
                    return func(*args, **kwargs)
                
                # Create cache key
                cache_key = PerformanceOptimizer.create_cache_key(func.__name__, *args, **kwargs)
                
                # Try to get from cache
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    try:
                        # Return cached result
                        import pickle
                        return pickle.loads(cached_result)
                    except Exception as e:
                        logger.error(f"Error deserializing cached result: {str(e)}")
                
                # Execute function
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Cache result
                try:
                    import pickle
                    redis_client.setex(cache_key, ttl, pickle.dumps(result))
                    logger.info(f"Cached result for {func.__name__} (execution time: {execution_time:.4f}s)")
                except Exception as e:
                    logger.error(f"Error caching result: {str(e)}")
                
                return result
            return wrapper
        return decorator

    @staticmethod
    def batch_process(data: List, process_func: Callable, batch_size: int = 100, use_multiprocessing: bool = False):
        """
        Process data in batches using parallel processing
        """
        results = []
        
        # Split data into batches
        batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]
        
        # Choose executor based on workload type
        executor_class = ProcessPoolExecutor if use_multiprocessing else ThreadPoolExecutor
        
        # Process batches in parallel
        with executor_class(max_workers=min(8, len(batches))) as executor:
            batch_results = list(executor.map(process_func, batches))
            
            # Combine results
            for batch_result in batch_results:
                results.extend(batch_result)
        
        return results

    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize pandas DataFrame memory usage
        """
        # Convert integer columns to smallest possible type
        for col in df.select_dtypes(include=['int']).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')
            
        # Convert float columns to smallest possible type
        for col in df.select_dtypes(include=['float']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')
            
        # Convert object columns to categories if cardinality is low
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) < 0.5:  # If less than 50% of values are unique
                df[col] = df[col].astype('category')
                
        return df

    @staticmethod
    def profile_function(func: Callable):
        """
        Decorator to profile function execution time
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Function {func.__name__} executed in {execution_time:.4f} seconds")
            return result
        return wrapper

    def create_materialized_views(self):
        """
        Create materialized views (precomputed collections) for common queries
        """
        try:
            # Example: Create a materialized view for popular products by category
            pipeline = [
                {"$group": {"_id": "$category", "products": {"$push": "$$ROOT"}}},
                {"$project": {"category": "$_id", "products": {"$slice": ["$products", 50]}, "_id": 0}},
                {"$out": "popular_products_by_category"}
            ]
            self.db['products'].aggregate(pipeline)
            
            # Create index on the materialized view
            self.db['popular_products_by_category'].create_index([('category', ASCENDING)])
            
            logger.info("Materialized views created successfully")
        except Exception as e:
            logger.error(f"Error creating materialized views: {str(e)}")


# Example usage
if __name__ == "__main__":
    optimizer = PerformanceOptimizer()
    
    # Optimize collections
    optimizer.optimize_mongodb_collections()
    
    # Create materialized views
    optimizer.create_materialized_views()
    
    logger.info("Performance optimization completed successfully") 