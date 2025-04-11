"""
MongoDB Monitoring Test Mode
Simulates MongoDB metrics for testing without a connection
"""

import logging
import time
import json
import os
from datetime import datetime, timedelta
import random
from prometheus_client import start_http_server, Gauge, Counter, Histogram, Summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define Prometheus metrics
CONNECTION_POOL_SIZE = Gauge('mongodb_connection_pool_size', 
                             'Current size of the MongoDB connection pool')
CONNECTION_POOL_CHECKEDOUT = Gauge('mongodb_connection_pool_checked_out', 
                                  'Number of connections currently checked out')
CONNECTION_POOL_WAITQUEUESIZE = Gauge('mongodb_connection_pool_waitqueue_size', 
                                    'Current size of the wait queue')

OPERATIONS_TOTAL = Counter('mongodb_operations_total', 
                         'Total number of MongoDB operations',
                         ['operation_type', 'collection'])

OPERATION_DURATION = Histogram('mongodb_operation_duration_ms', 
                              'Duration of MongoDB operations in milliseconds',
                              ['operation_type', 'collection'],
                              buckets=[10, 50, 100, 200, 500, 1000, 2000, 5000])

SLOW_QUERY_COUNT = Counter('mongodb_slow_query_count', 
                         'Count of slow queries (>100ms)',
                         ['collection', 'operation_type'])

class TestMongoDBMonitor:
    """Test implementation of MongoDB monitoring that simulates metrics."""
    
    def __init__(self):
        self.collections = ['products', 'reviews', 'precomputed_stats', 'time_series_stats', 'platform_stats']
        self.operation_types = ['find', 'insert', 'update', 'remove', 'aggregate', 'distinct', 'count']
        self.max_connections = 100
        self.connection_growth = 0
        
    def simulate_connection_pool(self):
        """Simulate connection pool metrics."""
        # Simulate connection pool with realistic behavior
        
        # Gradually increase connections over time to show growth
        self.connection_growth = min(self.connection_growth + random.uniform(-3, 5), self.max_connections)
        current_connections = max(10, int(self.connection_growth))
        
        # Random variations in checked out connections
        checked_out = min(int(current_connections * random.uniform(0.2, 0.7)), current_connections)
        
        # Occasional wait queue entries
        wait_queue = 0
        if random.random() < 0.2:  # 20% chance of wait queue entries
            wait_queue = random.randint(1, 5)
        
        # Set metrics
        CONNECTION_POOL_SIZE.set(current_connections)
        CONNECTION_POOL_CHECKEDOUT.set(checked_out)
        CONNECTION_POOL_WAITQUEUESIZE.set(wait_queue)
        
        # Log
        logger.info(f"Connection pool - Size: {current_connections}, Checked out: {checked_out}, Wait queue: {wait_queue}")
        
        return {
            'current': current_connections,
            'available': current_connections - checked_out,
            'wait_queue': wait_queue
        }
    
    def simulate_operations(self):
        """Simulate MongoDB operations."""
        # Simulate various MongoDB operations with realistic behavior
        
        # For each collection, generate some operations
        for collection in self.collections:
            # Number of operations varies by collection
            if collection == 'reviews':
                num_ops = random.randint(10, 30)  # More activity on reviews
            elif collection == 'products':
                num_ops = random.randint(5, 15)
            else:
                num_ops = random.randint(0, 5)
            
            # Generate operation metrics
            for _ in range(num_ops):
                op_type = random.choice(self.operation_types)
                
                # Increment operation counter
                OPERATIONS_TOTAL.labels(operation_type=op_type, collection=collection).inc()
                
                # Simulate operation duration with weighted random values
                if op_type == 'aggregate' and collection in ['reviews', 'precomputed_stats']:
                    # Aggregations tend to be slower
                    duration_ms = random.uniform(50, 1500)
                elif op_type == 'find' and 'text' in collection:
                    # Text searches tend to be slower
                    duration_ms = random.uniform(30, 800)
                else:
                    # Regular operations
                    duration_ms = random.uniform(5, 200)
                
                # Record operation duration
                OPERATION_DURATION.labels(
                    operation_type=op_type, 
                    collection=collection
                ).observe(duration_ms)
                
                # Record slow queries
                if duration_ms > 100:
                    SLOW_QUERY_COUNT.labels(
                        collection=collection,
                        operation_type=op_type
                    ).inc()
        
        # Log summary
        logger.info(f"Simulated operations across {len(self.collections)} collections")
        
        # Occasionally simulate a very slow query
        if random.random() < 0.1:  # 10% chance
            slow_collection = random.choice(['reviews', 'products'])
            slow_op = random.choice(['aggregate', 'find'])
            very_slow_ms = random.uniform(1000, 3000)
            OPERATION_DURATION.labels(
                operation_type=slow_op,
                collection=slow_collection
            ).observe(very_slow_ms)
            SLOW_QUERY_COUNT.labels(
                collection=slow_collection,
                operation_type=slow_op
            ).inc()
            logger.warning(f"Simulated very slow {slow_op} on {slow_collection}: {very_slow_ms:.1f}ms")
    
    def run_test_monitoring(self):
        """Run simulated monitoring."""
        logger.info("Starting MongoDB monitoring simulation")
        
        # Simulate metrics
        self.simulate_connection_pool()
        self.simulate_operations()
        
        logger.info("Completed MongoDB monitoring simulation pass")


def run_test():
    """Run test monitoring."""
    try:
        # Start Prometheus metrics HTTP server
        start_http_server(8000)
        logger.info("Started Prometheus metrics server on port 8000")
        
        # Create test monitor
        monitor = TestMongoDBMonitor()
        
        # Run monitoring simulation loop
        logger.info("MongoDB monitoring test mode is running")
        logger.info("Press Ctrl+C to stop the test")
        
        while True:
            # Run monitoring simulation
            monitor.run_test_monitoring()
            
            # Wait between simulation runs
            time.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("MongoDB monitoring test mode stopped by user")
    except Exception as e:
        logger.error(f"Error in MongoDB monitoring test: {e}", exc_info=True)

if __name__ == "__main__":
    run_test() 