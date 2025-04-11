"""
Enhance MongoDB Slow Query Logging

This script sets up enhanced slow query logging for MongoDB and provides tools
to analyze and optimize slow queries based on the query patterns.
"""

import logging
import time
from datetime import datetime, timedelta
import json
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import json_util
import pandas as pd
import matplotlib.pyplot as plt

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

class SlowQueryAnalyzer:
    """Analyzes and optimizes slow MongoDB queries."""
    
    def __init__(self, threshold_ms=100):
        """
        Initialize the slow query analyzer.
        
        Args:
            threshold_ms: Threshold in milliseconds for slow query detection
        """
        self.threshold_ms = threshold_ms
        
        # Ensure profiling is enabled
        self._enable_profiling()
        
        # Create directory for reports if it doesn't exist
        os.makedirs('slow_query_reports', exist_ok=True)
    
    def _enable_profiling(self):
        """Enable MongoDB profiling for slow queries."""
        try:
            # Set profiling level
            # 0 = off, 1 = slow queries only, 2 = all operations
            current_level = db.command({'profile': -1})
            logger.info(f"Current profiling level: {current_level}")
            
            if current_level['was'] != 1 or current_level['slowms'] != self.threshold_ms:
                db.set_profiling_level(1, self.threshold_ms)
                logger.info(f"Enabled profiling for queries slower than {self.threshold_ms}ms")
            else:
                logger.info("Profiling already enabled with requested parameters")
        except Exception as e:
            logger.error(f"Error enabling profiling: {e}")
    
    def get_slow_queries(self, hours=24):
        """
        Get slow queries from the system.profile collection.
        
        Args:
            hours: Number of hours to look back for slow queries
            
        Returns:
            List of slow query documents
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        try:
            # Query the system.profile collection for slow queries
            slow_queries = list(db.system.profile.find({
                "ts": {"$gt": start_time},
                "millis": {"$gte": self.threshold_ms}
            }).sort("millis", -1))
            
            logger.info(f"Found {len(slow_queries)} slow queries in the last {hours} hours")
            return slow_queries
        except Exception as e:
            logger.error(f"Error getting slow queries: {e}")
            return []
    
    def analyze_slow_queries(self, hours=24):
        """
        Analyze slow queries and generate a report.
        
        Args:
            hours: Number of hours to look back for slow queries
            
        Returns:
            Analysis results
        """
        slow_queries = self.get_slow_queries(hours)
        
        if not slow_queries:
            logger.info("No slow queries found for analysis")
            return None
        
        # Analyze by collection
        collection_stats = {}
        operation_stats = {}
        
        for query in slow_queries:
            # Extract collection name
            namespace = query.get('ns', '')
            parts = namespace.split('.')
            collection = parts[1] if len(parts) > 1 else 'unknown'
            
            # Extract operation type
            op_type = query.get('op', 'unknown')
            
            # Extract duration
            duration_ms = query.get('millis', 0)
            
            # Collect collection stats
            if collection not in collection_stats:
                collection_stats[collection] = {
                    'count': 0,
                    'total_duration_ms': 0,
                    'max_duration_ms': 0,
                    'avg_duration_ms': 0,
                    'queries': []
                }
            
            collection_stats[collection]['count'] += 1
            collection_stats[collection]['total_duration_ms'] += duration_ms
            collection_stats[collection]['max_duration_ms'] = max(
                collection_stats[collection]['max_duration_ms'], duration_ms
            )
            collection_stats[collection]['queries'].append(query)
            
            # Collect operation stats
            if op_type not in operation_stats:
                operation_stats[op_type] = {
                    'count': 0,
                    'total_duration_ms': 0,
                    'max_duration_ms': 0,
                    'avg_duration_ms': 0
                }
            
            operation_stats[op_type]['count'] += 1
            operation_stats[op_type]['total_duration_ms'] += duration_ms
            operation_stats[op_type]['max_duration_ms'] = max(
                operation_stats[op_type]['max_duration_ms'], duration_ms
            )
        
        # Calculate averages
        for collection in collection_stats:
            stats = collection_stats[collection]
            stats['avg_duration_ms'] = stats['total_duration_ms'] / stats['count']
        
        for op_type in operation_stats:
            stats = operation_stats[op_type]
            stats['avg_duration_ms'] = stats['total_duration_ms'] / stats['count']
        
        # Prepare analysis results
        results = {
            'total_slow_queries': len(slow_queries),
            'time_period_hours': hours,
            'threshold_ms': self.threshold_ms,
            'collection_stats': collection_stats,
            'operation_stats': operation_stats,
            'timestamp': datetime.utcnow()
        }
        
        # Generate report
        self._generate_report(results)
        
        return results
    
    def _generate_report(self, results):
        """
        Generate a human-readable report from analysis results.
        
        Args:
            results: Analysis results from analyze_slow_queries
        """
        if not results:
            return
        
        timestamp = results['timestamp'].strftime('%Y%m%d_%H%M%S')
        report_file = f"slow_query_reports/slow_query_analysis_{timestamp}.txt"
        
        with open(report_file, 'w') as f:
            f.write("MongoDB Slow Query Analysis Report\n")
            f.write("=================================\n\n")
            
            f.write(f"Time Period: Past {results['time_period_hours']} hours\n")
            f.write(f"Threshold: {results['threshold_ms']}ms\n")
            f.write(f"Total Slow Queries: {results['total_slow_queries']}\n")
            f.write(f"Generated At: {results['timestamp']}\n\n")
            
            # Collection statistics
            f.write("Statistics by Collection\n")
            f.write("------------------------\n")
            
            collection_stats = results['collection_stats']
            for collection, stats in sorted(
                collection_stats.items(), 
                key=lambda x: x[1]['total_duration_ms'], 
                reverse=True
            ):
                f.write(f"Collection: {collection}\n")
                f.write(f"  - Count: {stats['count']}\n")
                f.write(f"  - Total Duration: {stats['total_duration_ms']}ms\n")
                f.write(f"  - Average Duration: {stats['avg_duration_ms']:.2f}ms\n")
                f.write(f"  - Maximum Duration: {stats['max_duration_ms']}ms\n")
                
                # Sample of slow queries for this collection
                top_queries = sorted(
                    stats['queries'], 
                    key=lambda x: x.get('millis', 0), 
                    reverse=True
                )[:3]
                
                f.write("  - Top Slow Queries:\n")
                for i, query in enumerate(top_queries, 1):
                    f.write(f"    {i}. Duration: {query.get('millis', 0)}ms\n")
                    
                    # Try to get query details
                    command = query.get('command', query.get('query', {}))
                    f.write(f"       Command: {json.dumps(command, default=str)[:200]}...\n")
                
                f.write("\n")
            
            # Operation statistics
            f.write("Statistics by Operation Type\n")
            f.write("---------------------------\n")
            
            operation_stats = results['operation_stats']
            for op_type, stats in sorted(
                operation_stats.items(), 
                key=lambda x: x[1]['total_duration_ms'], 
                reverse=True
            ):
                f.write(f"Operation: {op_type}\n")
                f.write(f"  - Count: {stats['count']}\n")
                f.write(f"  - Total Duration: {stats['total_duration_ms']}ms\n")
                f.write(f"  - Average Duration: {stats['avg_duration_ms']:.2f}ms\n")
                f.write(f"  - Maximum Duration: {stats['max_duration_ms']}ms\n\n")
            
            # Optimization suggestions
            f.write("Optimization Suggestions\n")
            f.write("-----------------------\n")
            
            for collection, stats in sorted(
                collection_stats.items(), 
                key=lambda x: x[1]['total_duration_ms'], 
                reverse=True
            ):
                if stats['avg_duration_ms'] > 200:
                    f.write(f"- Consider adding indexes to the {collection} collection\n")
                if stats['count'] > 50:
                    f.write(f"- High frequency of slow queries on {collection}, review query patterns\n")
                if stats['max_duration_ms'] > 1000:
                    f.write(f"- Extremely slow queries detected on {collection}, consider pre-computing\n")
            
            if 'find' in operation_stats and operation_stats['find']['avg_duration_ms'] > 200:
                f.write("- Optimize 'find' operations by adding appropriate indexes\n")
            if 'aggregate' in operation_stats and operation_stats['aggregate']['avg_duration_ms'] > 300:
                f.write("- Consider optimizing aggregation pipelines or pre-computing results\n")
            if 'update' in operation_stats and operation_stats['update']['avg_duration_ms'] > 200:
                f.write("- Review update operations for performance, consider bulk operations\n")
            
            f.write("\n")
            f.write("End of Report\n")
        
        logger.info(f"Generated slow query analysis report: {report_file}")
        
        # Generate charts for visualization
        self._generate_charts(results, timestamp)
    
    def _generate_charts(self, results, timestamp):
        """
        Generate charts from analysis results.
        
        Args:
            results: Analysis results from analyze_slow_queries
            timestamp: Timestamp for filenames
        """
        try:
            # Extract data for charts
            collections = []
            avg_durations = []
            counts = []
            
            for collection, stats in sorted(
                results['collection_stats'].items(), 
                key=lambda x: x[1]['total_duration_ms'], 
                reverse=True
            )[:10]:  # Top 10 collections
                collections.append(collection)
                avg_durations.append(stats['avg_duration_ms'])
                counts.append(stats['count'])
            
            # Create dataframe
            data = {
                'Collection': collections,
                'Average Duration (ms)': avg_durations,
                'Query Count': counts
            }
            df = pd.DataFrame(data)
            
            # Generate duration chart
            plt.figure(figsize=(12, 6))
            plt.barh(df['Collection'], df['Average Duration (ms)'], color='skyblue')
            plt.xlabel('Average Duration (ms)')
            plt.title('Average Query Duration by Collection')
            plt.tight_layout()
            plt.savefig(f"slow_query_reports/duration_chart_{timestamp}.png")
            
            # Generate count chart
            plt.figure(figsize=(12, 6))
            plt.barh(df['Collection'], df['Query Count'], color='salmon')
            plt.xlabel('Query Count')
            plt.title('Slow Query Count by Collection')
            plt.tight_layout()
            plt.savefig(f"slow_query_reports/count_chart_{timestamp}.png")
            
            logger.info("Generated slow query analysis charts")
        except Exception as e:
            logger.error(f"Error generating charts: {e}")

def main():
    """Set up MongoDB slow query logging and perform initial analysis."""
    logger.info("Setting up enhanced MongoDB slow query logging")
    
    # Initialize analyzer with 100ms threshold
    analyzer = SlowQueryAnalyzer(threshold_ms=100)
    
    # Run initial analysis for the past 24 hours
    analyzer.analyze_slow_queries(hours=24)
    
    logger.info("Enhanced slow query logging is set up.")
    logger.info("Use the SlowQueryAnalyzer class to analyze slow queries and generate reports.")
    logger.info("Reports are stored in the 'slow_query_reports' directory.")

if __name__ == "__main__":
    main() 