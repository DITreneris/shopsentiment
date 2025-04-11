"""
Comprehensive MongoDB Performance Tests

This script runs comprehensive performance tests comparing the original and
optimized MongoDB implementations, measuring improvements across different
query types and generating detailed reports.
"""

import logging
import time
import json
import os
from datetime import datetime, timedelta
import statistics
import pandas as pd
import matplotlib.pyplot as plt
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId

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

# Test parameters
ITERATIONS = 5  # Number of iterations for each test
PRODUCT_SAMPLE_SIZE = 10  # Number of random products to test

class ComprehensivePerformanceTester:
    """Performs comprehensive performance testing of MongoDB queries."""
    
    def __init__(self):
        """Initialize the performance tester."""
        self.results = {
            "queries": [],
            "comparisons": [],
            "summary": {}
        }
        
        # Create output directory
        os.makedirs('performance_reports', exist_ok=True)
    
    def measure_execution_time(self, name, func, *args, **kwargs):
        """
        Measure the execution time of a function.
        
        Args:
            name: Name of the function being tested
            func: Function to test
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Dictionary with performance statistics
        """
        times = []
        results = None
        
        for i in range(ITERATIONS):
            # Clear MongoDB cache between runs
            try:
                db.command({"serverStatus": 1})
            except Exception:
                pass
            
            # Run the query and measure time
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            elapsed = (end_time - start_time) * 1000  # Convert to ms
            times.append(elapsed)
            
            # Store the results from the first run
            if i == 0:
                results = result
            
            logger.info(f"Run {i+1}: {name} - {elapsed:.2f}ms")
        
        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        
        stats = {
            "name": name,
            "average_ms": round(avg_time, 2),
            "median_ms": round(median_time, 2),
            "min_ms": round(min_time, 2),
            "max_ms": round(max_time, 2),
            "runs": times,
            "result": results
        }
        
        self.results["queries"].append(stats)
        return stats
    
    def compare_queries(self, test_name, original_func, optimized_func, *args, **kwargs):
        """
        Compare the performance of original and optimized query implementations.
        
        Args:
            test_name: Name of the test being performed
            original_func: Original function implementation
            optimized_func: Optimized function implementation
            *args, **kwargs: Arguments to pass to both functions
            
        Returns:
            Dictionary with comparison results
        """
        logger.info(f"Comparing performance: {test_name}")
        
        # Test original function
        original_stats = self.measure_execution_time(f"Original {test_name}", original_func, *args, **kwargs)
        
        # Test optimized function
        optimized_stats = self.measure_execution_time(f"Optimized {test_name}", optimized_func, *args, **kwargs)
        
        # Calculate improvement
        original_avg = original_stats["average_ms"]
        optimized_avg = optimized_stats["average_ms"]
        
        if original_avg > 0:
            improvement_ms = original_avg - optimized_avg
            improvement_percent = (improvement_ms / original_avg) * 100
        else:
            improvement_ms = 0
            improvement_percent = 0
        
        comparison = {
            "test_name": test_name,
            "original_avg_ms": original_avg,
            "optimized_avg_ms": optimized_avg,
            "improvement_ms": round(improvement_ms, 2),
            "improvement_percent": round(improvement_percent, 2)
        }
        
        self.results["comparisons"].append(comparison)
        
        logger.info(f"Comparison results for {test_name}:")
        logger.info(f"  Original: {original_avg:.2f}ms")
        logger.info(f"  Optimized: {optimized_avg:.2f}ms")
        logger.info(f"  Improvement: {improvement_ms:.2f}ms ({improvement_percent:.2f}%)")
        
        return comparison
    
    def generate_summary(self):
        """Generate a summary of all performance comparisons."""
        comparisons = self.results["comparisons"]
        
        if not comparisons:
            logger.warning("No comparison data available for summary generation")
            return
        
        # Calculate overall improvement
        total_original = sum(comp["original_avg_ms"] for comp in comparisons)
        total_optimized = sum(comp["optimized_avg_ms"] for comp in comparisons)
        
        if total_original > 0:
            overall_improvement_ms = total_original - total_optimized
            overall_improvement_percent = (overall_improvement_ms / total_original) * 100
        else:
            overall_improvement_ms = 0
            overall_improvement_percent = 0
        
        summary = {
            "total_original_ms": round(total_original, 2),
            "total_optimized_ms": round(total_optimized, 2),
            "overall_improvement_ms": round(overall_improvement_ms, 2),
            "overall_improvement_percent": round(overall_improvement_percent, 2),
            "tests_improved": sum(1 for comp in comparisons if comp["improvement_percent"] > 0),
            "tests_worsened": sum(1 for comp in comparisons if comp["improvement_percent"] < 0),
            "total_tests": len(comparisons)
        }
        
        self.results["summary"] = summary
        
        logger.info("Performance Test Summary:")
        logger.info(f"  Total Tests: {summary['total_tests']}")
        logger.info(f"  Tests Improved: {summary['tests_improved']}")
        logger.info(f"  Tests Worsened: {summary['tests_worsened']}")
        logger.info(f"  Overall Improvement: {summary['overall_improvement_percent']}%")
        
        return summary
    
    def visualize_results(self):
        """Generate visualization charts for the performance results."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        comparisons = self.results["comparisons"]
        
        if not comparisons:
            logger.warning("No comparison data available for visualization")
            return
        
        # Create dataframe
        df = pd.DataFrame(comparisons)
        
        try:
            # Bar chart comparing original vs optimized
            plt.figure(figsize=(12, 8))
            
            # Sort by original execution time
            df_sorted = df.sort_values('original_avg_ms', ascending=False)
            
            # Create the grouped bar chart
            bar_width = 0.35
            index = range(len(df_sorted))
            
            plt.bar(index, df_sorted['original_avg_ms'], bar_width, label='Original', color='lightcoral')
            plt.bar([i + bar_width for i in index], df_sorted['optimized_avg_ms'], bar_width, label='Optimized', color='skyblue')
            
            plt.xlabel('Query Type')
            plt.ylabel('Average Execution Time (ms)')
            plt.title('Performance Comparison: Original vs. Optimized')
            plt.xticks([i + bar_width/2 for i in index], df_sorted['test_name'], rotation=45, ha='right')
            plt.legend()
            plt.tight_layout()
            
            # Save the chart
            chart_file = f"performance_reports/performance_comparison_{timestamp}.png"
            plt.savefig(chart_file)
            logger.info(f"Generated performance comparison chart: {chart_file}")
            
            # Improvement percentage chart
            plt.figure(figsize=(12, 8))
            
            # Sort by improvement percentage
            df_sorted = df.sort_values('improvement_percent', ascending=False)
            
            # Colors based on improvement (green for positive, red for negative)
            colors = ['green' if x > 0 else 'red' for x in df_sorted['improvement_percent']]
            
            plt.bar(df_sorted['test_name'], df_sorted['improvement_percent'], color=colors)
            plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            plt.xlabel('Query Type')
            plt.ylabel('Improvement Percentage (%)')
            plt.title('Performance Improvement Percentage by Query Type')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Save the chart
            chart_file = f"performance_reports/improvement_percentage_{timestamp}.png"
            plt.savefig(chart_file)
            logger.info(f"Generated improvement percentage chart: {chart_file}")
            
        except Exception as e:
            logger.error(f"Error generating visualization: {e}")
    
    def generate_report(self):
        """Generate a comprehensive performance test report."""
        if not self.results["comparisons"]:
            logger.warning("No data available for report generation")
            return
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        report_file = f"performance_reports/performance_report_{timestamp}.txt"
        
        with open(report_file, 'w') as f:
            f.write("MongoDB Performance Optimization Report\n")
            f.write("=====================================\n\n")
            
            f.write(f"Generated: {datetime.utcnow()}\n")
            f.write(f"Test Iterations: {ITERATIONS}\n\n")
            
            # Write summary
            summary = self.results["summary"]
            f.write("Performance Summary\n")
            f.write("-----------------\n")
            f.write(f"Total Tests: {summary['total_tests']}\n")
            f.write(f"Tests Improved: {summary['tests_improved']}\n")
            f.write(f"Tests Worsened: {summary['tests_worsened']}\n")
            f.write(f"Overall Improvement: {summary['overall_improvement_percent']}%\n\n")
            
            # Write detailed comparisons
            f.write("Detailed Test Results\n")
            f.write("-------------------\n")
            
            for comp in sorted(self.results["comparisons"], key=lambda x: x["improvement_percent"], reverse=True):
                f.write(f"Test: {comp['test_name']}\n")
                f.write(f"  Original: {comp['original_avg_ms']}ms\n")
                f.write(f"  Optimized: {comp['optimized_avg_ms']}ms\n")
                f.write(f"  Improvement: {comp['improvement_ms']}ms ({comp['improvement_percent']}%)\n\n")
            
            # Write recommendations
            f.write("Recommendations\n")
            f.write("--------------\n")
            
            if summary['overall_improvement_percent'] > 50:
                f.write("✅ Overall performance has significantly improved. The optimization is highly effective.\n")
            elif summary['overall_improvement_percent'] > 0:
                f.write("✅ Overall performance has improved. The optimization is effective but can be further enhanced.\n")
            else:
                f.write("❌ Overall performance has degraded. The optimization needs revision.\n")
            
            # Add specific recommendations based on test results
            worsened_tests = [comp for comp in self.results["comparisons"] if comp["improvement_percent"] < 0]
            if worsened_tests:
                f.write("\nAreas needing improvement:\n")
                for test in worsened_tests:
                    f.write(f"- {test['test_name']}: Performance degraded by {abs(test['improvement_percent']):.2f}%\n")
            
            f.write("\nNext Steps:\n")
            if summary['overall_improvement_percent'] > 0:
                f.write("1. Deploy the optimized implementation to production\n")
                f.write("2. Implement monitoring to track performance in real-world usage\n")
                f.write("3. Continue optimizing queries that showed below-average improvement\n")
            else:
                f.write("1. Revise the optimization strategy based on test results\n")
                f.write("2. Focus on fixing queries that showed significant performance degradation\n")
                f.write("3. Re-run tests after implementation changes\n")
        
        logger.info(f"Generated performance report: {report_file}")
        
        # Generate CSV export of detailed results
        csv_file = f"performance_reports/performance_data_{timestamp}.csv"
        df = pd.DataFrame(self.results["comparisons"])
        df.to_csv(csv_file, index=False)
        logger.info(f"Exported performance data to CSV: {csv_file}")
        
        return report_file

# Query functions to test

def original_sentiment_over_time(product_id, days=30, interval='day'):
    """Original implementation of sentiment over time query."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    pipeline = [
        {"$match": {
            "product_id": product_id,
            "date": {"$gte": start_date, "$lte": end_date}
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
    
    result = list(db.reviews.aggregate(pipeline))
    
    # Format the result
    formatted_result = []
    for entry in result:
        date_str = f"{entry['_id']['year']}-{entry['_id']['month']:02d}-{entry['_id']['day']:02d}"
        formatted_result.append({
            "date": date_str,
            "sentiment": entry["avg_sentiment"],
            "count": entry["count"]
        })
    
    return formatted_result

def optimized_sentiment_over_time(product_id, days=30, interval='day'):
    """Optimized implementation of sentiment over time query using pre-computed stats."""
    # First try to get from pre-computed stats
    try:
        stats = db.time_series_stats.find_one({
            "product_id": product_id,
            "interval": f"{days}_{interval}"
        })
        
        if stats and "data" in stats:
            return stats["data"]
    except Exception as e:
        logger.error(f"Error retrieving pre-computed sentiment stats: {e}")
    
    # Fall back to original implementation if pre-computed data is not available
    return original_sentiment_over_time(product_id, days, interval)

def original_rating_distribution_by_platform(days=90):
    """Original implementation of rating distribution by platform query."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    pipeline = [
        {"$match": {
            "date": {"$gte": start_date, "$lte": end_date}
        }},
        {"$lookup": {
            "from": "products",
            "localField": "product_id",
            "foreignField": "_id",
            "as": "product"
        }},
        {"$unwind": "$product"},
        {"$group": {
            "_id": {
                "platform": "$product.platform",
                "rating": "$rating"
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.platform": 1, "_id.rating": 1}}
    ]
    
    result = list(db.reviews.aggregate(pipeline))
    
    # Format the result
    formatted_result = {}
    for entry in result:
        platform = entry["_id"]["platform"]
        rating = entry["_id"]["rating"]
        count = entry["count"]
        
        if platform not in formatted_result:
            formatted_result[platform] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        formatted_result[platform][rating] = count
    
    return formatted_result

def optimized_rating_distribution_by_platform(days=90):
    """Optimized implementation of rating distribution by platform query using pre-computed stats."""
    # Try to get from pre-computed stats
    try:
        stats = db.platform_stats.find_one({
            "period": f"{days}_day"
        })
        
        if stats and "rating_distribution" in stats:
            return stats["rating_distribution"]
    except Exception as e:
        logger.error(f"Error retrieving pre-computed platform stats: {e}")
    
    # Fall back to original implementation
    return original_rating_distribution_by_platform(days)

def original_keyword_sentiment_analysis(min_count=10):
    """Original implementation of keyword sentiment analysis query."""
    pipeline = [
        {"$unwind": "$keywords"},
        {"$group": {
            "_id": "$keywords",
            "count": {"$sum": 1},
            "avg_sentiment": {"$avg": "$sentiment.score"},
            "products": {"$addToSet": "$product_id"}
        }},
        {"$match": {
            "count": {"$gte": min_count}
        }},
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
        {"$sort": {"count": -1}},
        {"$limit": 100}
    ]
    
    result = list(db.reviews.aggregate(pipeline))
    
    # Format the result
    formatted_result = []
    for entry in result:
        formatted_result.append({
            "keyword": entry["_id"],
            "count": entry["count"],
            "sentiment": {
                "score": entry["avg_sentiment"],
                "label": entry["sentiment_label"]
            },
            "products_count": len(entry["products"])
        })
    
    return formatted_result

def optimized_keyword_sentiment_analysis(min_count=10):
    """Optimized implementation of keyword sentiment analysis query using pre-computed stats."""
    # Try to get from pre-computed stats
    try:
        stats = list(db.keyword_stats.find({
            "count": {"$gte": min_count}
        }).sort("count", -1).limit(100))
        
        if stats:
            # Format the result
            formatted_result = []
            for entry in stats:
                formatted_result.append({
                    "keyword": entry["keyword"],
                    "count": entry["count"],
                    "sentiment": {
                        "score": entry["sentiment"]["score"],
                        "label": entry["sentiment"]["label"]
                    },
                    "products_count": len(entry.get("products", []))
                })
            
            return formatted_result
    except Exception as e:
        logger.error(f"Error retrieving pre-computed keyword stats: {e}")
    
    # Fall back to original implementation
    return original_keyword_sentiment_analysis(min_count)

def original_product_comparison(product_ids):
    """Original implementation of product comparison query."""
    # Convert string IDs to ObjectId if needed
    object_ids = []
    for pid in product_ids:
        if isinstance(pid, str) and ObjectId.is_valid(pid):
            object_ids.append(ObjectId(pid))
        else:
            object_ids.append(pid)
    
    pipeline = [
        {"$match": {
            "product_id": {"$in": object_ids}
        }},
        {"$group": {
            "_id": "$product_id",
            "avg_rating": {"$avg": "$rating"},
            "avg_sentiment": {"$avg": "$sentiment.score"},
            "review_count": {"$sum": 1},
            "ratings": {
                "$push": "$rating"
            },
            "sentiment_scores": {
                "$push": "$sentiment.score"
            }
        }},
        {"$lookup": {
            "from": "products",
            "localField": "_id",
            "foreignField": "_id",
            "as": "product"
        }},
        {"$unwind": "$product"},
        {"$project": {
            "product_name": "$product.name",
            "avg_rating": 1,
            "avg_sentiment": 1,
            "review_count": 1,
            "rating_distribution": {
                "1": {"$size": {"$filter": {"input": "$ratings", "cond": {"$eq": ["$$this", 1]}}}},
                "2": {"$size": {"$filter": {"input": "$ratings", "cond": {"$eq": ["$$this", 2]}}}},
                "3": {"$size": {"$filter": {"input": "$ratings", "cond": {"$eq": ["$$this", 3]}}}},
                "4": {"$size": {"$filter": {"input": "$ratings", "cond": {"$eq": ["$$this", 4]}}}},
                "5": {"$size": {"$filter": {"input": "$ratings", "cond": {"$eq": ["$$this", 5]}}}}
            }
        }}
    ]
    
    result = list(db.reviews.aggregate(pipeline))
    return result

def optimized_product_comparison(product_ids):
    """Optimized implementation of product comparison query using pre-computed stats."""
    # Convert string IDs to ObjectId if needed
    object_ids = []
    for pid in product_ids:
        if isinstance(pid, str) and ObjectId.is_valid(pid):
            object_ids.append(ObjectId(pid))
        else:
            object_ids.append(pid)
    
    # Sort product IDs for consistent caching
    sorted_ids = sorted(str(pid) for pid in object_ids)
    id_string = "_".join(sorted_ids)
    
    # Create a hash for the comparison
    import hashlib
    comparison_hash = hashlib.md5(id_string.encode()).hexdigest()
    
    # Try to get from pre-computed comparisons
    try:
        cached = db.product_comparisons.find_one({"hash": comparison_hash})
        if cached and "comparison_data" in cached:
            # Update view count
            db.product_comparisons.update_one(
                {"hash": comparison_hash},
                {"$inc": {"view_count": 1}}
            )
            return cached["comparison_data"]
    except Exception as e:
        logger.error(f"Error retrieving pre-computed comparison: {e}")
    
    # Fall back to original implementation
    return original_product_comparison(product_ids)

def run_performance_tests():
    """Run comprehensive performance tests on MongoDB queries."""
    logger.info("Starting comprehensive MongoDB performance tests")
    
    tester = ComprehensivePerformanceTester()
    
    # Get sample product IDs for testing
    try:
        sample_products = list(db.products.find().limit(PRODUCT_SAMPLE_SIZE))
        if not sample_products:
            logger.error("No products found in the database for testing")
            return
        
        product_ids = [p["_id"] for p in sample_products]
        logger.info(f"Selected {len(product_ids)} products for testing")
        
        # Test sentiment over time query
        for interval_days in [30, 90]:
            product_id = product_ids[0]  # Use first product
            tester.compare_queries(
                f"Sentiment Over Time ({interval_days} days)",
                original_sentiment_over_time,
                optimized_sentiment_over_time,
                product_id, interval_days, 'day'
            )
        
        # Test rating distribution by platform query
        for period_days in [30, 90, 180]:
            tester.compare_queries(
                f"Rating Distribution by Platform ({period_days} days)",
                original_rating_distribution_by_platform,
                optimized_rating_distribution_by_platform,
                period_days
            )
        
        # Test keyword sentiment analysis query
        for min_count in [5, 10, 25]:
            tester.compare_queries(
                f"Keyword Sentiment Analysis (min count: {min_count})",
                original_keyword_sentiment_analysis,
                optimized_keyword_sentiment_analysis,
                min_count
            )
        
        # Test product comparison query
        # Test with different numbers of products
        for num_products in [2, 3, 5]:
            if num_products <= len(product_ids):
                test_product_ids = product_ids[:num_products]
                tester.compare_queries(
                    f"Product Comparison ({num_products} products)",
                    original_product_comparison,
                    optimized_product_comparison,
                    test_product_ids
                )
        
        # Generate summary, visualizations, and report
        tester.generate_summary()
        tester.visualize_results()
        report_file = tester.generate_report()
        
        logger.info("Comprehensive performance tests completed")
        logger.info(f"Report generated: {report_file}")
        
        return tester.results
        
    except Exception as e:
        logger.error(f"Error running performance tests: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    run_performance_tests() 