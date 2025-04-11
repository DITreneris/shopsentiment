"""
Performance Comparison Test Script
Compares execution time between original and optimized MongoDB queries
"""

import time
import statistics
from datetime import datetime, timedelta
import logging
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
uri = "mongodb+srv://tomasstaniulis76:JaLhUd1NLZUtwVb5@shop1.11tjwh5.mongodb.net/?retryWrites=true&w=majority&appName=Shop1"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.shopsentiment

# Number of test iterations
ITERATIONS = 5

class PerformanceTester:
    """Tests and compares performance between original and optimized queries."""
    
    def __init__(self):
        self.results = {
            "queries": [],
            "summary": {}
        }
    
    def measure_execution_time(self, name, func, *args, **kwargs):
        """Measure the execution time of a function."""
        times = []
        
        for i in range(ITERATIONS):
            # Clear MongoDB cache between runs
            db.command({"serverStatus": 1})
            
            # Run the query and measure time
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            elapsed = (end_time - start_time) * 1000  # Convert to ms
            times.append(elapsed)
            
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
            "runs": times
        }
        
        self.results["queries"].append(stats)
        return stats
    
    def compare_queries(self, name, original_func, optimized_func, *args, **kwargs):
        """Compare performance between original and optimized versions of a query."""
        logger.info(f"Testing performance for: {name}")
        
        # Measure original implementation
        original_stats = self.measure_execution_time(
            f"{name} (Original)", original_func, *args, **kwargs
        )
        
        # Measure optimized implementation
        optimized_stats = self.measure_execution_time(
            f"{name} (Optimized)", optimized_func, *args, **kwargs
        )
        
        # Calculate improvement
        improvement = 0
        if original_stats["average_ms"] > 0:
            improvement = round(
                (original_stats["average_ms"] - optimized_stats["average_ms"]) / 
                original_stats["average_ms"] * 100, 
                2
            )
        
        comparison = {
            "query": name,
            "original_ms": original_stats["average_ms"],
            "optimized_ms": optimized_stats["average_ms"],
            "improvement_percent": improvement,
            "speedup_factor": round(original_stats["average_ms"] / max(optimized_stats["average_ms"], 0.1), 2)
        }
        
        if "comparisons" not in self.results:
            self.results["comparisons"] = []
        
        self.results["comparisons"].append(comparison)
        
        logger.info(f"Comparison - {name}:")
        logger.info(f"  Original: {original_stats['average_ms']}ms")
        logger.info(f"  Optimized: {optimized_stats['average_ms']}ms")
        logger.info(f"  Improvement: {improvement}%")
        
        return comparison
    
    def generate_summary(self):
        """Generate a summary of all performance comparisons."""
        if not self.results.get("comparisons"):
            return
        
        total_original = sum(c["original_ms"] for c in self.results["comparisons"])
        total_optimized = sum(c["optimized_ms"] for c in self.results["comparisons"])
        
        # Calculate overall improvement
        overall_improvement = 0
        if total_original > 0:
            overall_improvement = (total_original - total_optimized) / total_original * 100
        
        self.results["summary"] = {
            "total_original_ms": round(total_original, 2),
            "total_optimized_ms": round(total_optimized, 2),
            "overall_improvement_percent": round(overall_improvement, 2),
            "average_improvement_percent": round(
                statistics.mean(c["improvement_percent"] for c in self.results["comparisons"]), 
                2
            ),
            "fastest_query": min(self.results["comparisons"], key=lambda x: x["optimized_ms"])["query"],
            "slowest_query": max(self.results["comparisons"], key=lambda x: x["optimized_ms"])["query"],
            "most_improved_query": max(self.results["comparisons"], key=lambda x: x["improvement_percent"])["query"]
        }
        
        logger.info("Performance Summary:")
        logger.info(f"  Total Original Time: {self.results['summary']['total_original_ms']}ms")
        logger.info(f"  Total Optimized Time: {self.results['summary']['total_optimized_ms']}ms")
        logger.info(f"  Overall Improvement: {self.results['summary']['overall_improvement_percent']}%")
    
    def visualize_results(self, output_file="performance_comparison.png"):
        """Create a visualization of the performance comparison results."""
        if not self.results.get("comparisons"):
            return
        
        # Prepare data for plotting
        queries = [c["query"] for c in self.results["comparisons"]]
        original = [c["original_ms"] for c in self.results["comparisons"]]
        optimized = [c["optimized_ms"] for c in self.results["comparisons"]]
        improvements = [c["improvement_percent"] for c in self.results["comparisons"]]
        
        # Create a figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Bar chart for query times
        x = np.arange(len(queries))
        width = 0.35
        
        ax1.bar(x - width/2, original, width, label='Original')
        ax1.bar(x + width/2, optimized, width, label='Optimized')
        
        ax1.set_ylabel('Execution Time (ms)')
        ax1.set_title('Query Execution Time Comparison')
        ax1.set_xticks(x)
        ax1.set_xticklabels(queries, rotation=45, ha='right')
        ax1.legend()
        
        # Add value labels on bars
        for i, v in enumerate(original):
            ax1.text(i - width/2, v + 5, str(round(v)), ha='center')
        
        for i, v in enumerate(optimized):
            ax1.text(i + width/2, v + 5, str(round(v)), ha='center')
        
        # Bar chart for improvement percentages
        ax2.bar(x, improvements, width*1.5, color='green')
        ax2.set_ylabel('Improvement (%)')
        ax2.set_title('Performance Improvement Percentage')
        ax2.set_xticks(x)
        ax2.set_xticklabels(queries, rotation=45, ha='right')
        
        # Add value labels on bars
        for i, v in enumerate(improvements):
            ax2.text(i, v + 1, str(round(v, 1)) + '%', ha='center')
        
        # Add summary information as text
        summary_text = (
            f"Overall Improvement: {self.results['summary']['overall_improvement_percent']}%\n"
            f"Average Improvement: {self.results['summary']['average_improvement_percent']}%\n"
            f"Most Improved Query: {self.results['summary']['most_improved_query']}"
        )
        
        fig.text(0.1, 0.01, summary_text, fontsize=12)
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)
        plt.savefig(output_file)
        logger.info(f"Performance visualization saved to {output_file}")

# Original (unoptimized) implementations of MongoDB queries
def original_sentiment_over_time(product_id, days=30, interval='day'):
    """Original implementation of sentiment over time."""
    # Define date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Convert product_id to ObjectId if it's a string
    if isinstance(product_id, str) and ObjectId.is_valid(product_id):
        product_id = ObjectId(product_id)
    
    # Define date grouping format
    if interval == 'day':
        date_group = {
            "year": {"$year": "$date"},
            "month": {"$month": "$date"},
            "day": {"$dayOfMonth": "$date"}
        }
    elif interval == 'week':
        date_group = {
            "year": {"$year": "$date"},
            "week": {"$week": "$date"}
        }
    else:  # month
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
        
        # Sort by date
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}}
    ]
    
    return list(db.reviews.aggregate(pipeline))

def original_rating_distribution_by_platform(days=90):
    """Original implementation of rating distribution by platform."""
    # Define date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    pipeline = [
        # Find products with recent reviews
        {"$lookup": {
            "from": "reviews",
            "localField": "_id",
            "foreignField": "product_id",
            "pipeline": [
                {"$match": {"date": {"$gte": start_date}}},
                {"$limit": 1}
            ],
            "as": "recent_reviews"
        }},
        
        # Only include products with recent reviews
        {"$match": {"recent_reviews": {"$ne": []}}},
        
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

def original_keyword_sentiment_analysis(min_count=10):
    """Original implementation of keyword sentiment analysis."""
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

def original_product_comparison(product_ids):
    """Original implementation of product comparison."""
    # Convert string IDs to ObjectId
    product_objids = []
    for pid in product_ids:
        if isinstance(pid, str) and ObjectId.is_valid(pid):
            product_objids.append(ObjectId(pid))
        else:
            product_objids.append(pid)
    
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
    
    return list(db.products.aggregate(pipeline))

# Optimized implementations that use pre-computed collections
def optimized_sentiment_over_time(product_id, days=30, interval='day'):
    """Optimized implementation of sentiment over time using pre-computed data."""
    # Convert product_id to ObjectId if it's a string
    if isinstance(product_id, str) and ObjectId.is_valid(product_id):
        product_id = ObjectId(product_id)
    
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
        
        return filtered_data
    
    # Fallback to the original aggregation if pre-computed data is not available
    return original_sentiment_over_time(product_id, days, interval)

def optimized_rating_distribution_by_platform(days=90):
    """Optimized implementation of rating distribution by platform using pre-computed data."""
    # Determine which period to use
    if days is None:
        period = "all_time"
    elif days <= 7:
        period = "7_days"
    elif days <= 30:
        period = "30_days"
    elif days <= 90:
        period = "90_days"
    else:
        period = "all_time"
    
    # Try to get from pre-computed collection
    platform_stats = db.platform_stats.find_one({
        "_id": "rating_distribution",
        "period": period
    })
    
    if platform_stats:
        return platform_stats['platforms']
    
    # Fallback to original aggregation if pre-computed data is not available
    return original_rating_distribution_by_platform(days)

def optimized_keyword_sentiment_analysis(min_count=10):
    """Optimized implementation of keyword sentiment analysis using pre-computed data."""
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
    return original_keyword_sentiment_analysis(min_count)

def optimized_product_comparison(product_ids):
    """Optimized implementation of product comparison using cached comparisons."""
    # Convert string IDs to ObjectId
    product_objids = []
    for pid in product_ids:
        if isinstance(pid, str) and ObjectId.is_valid(pid):
            product_objids.append(ObjectId(pid))
        else:
            product_objids.append(pid)
    
    # Sort product IDs for consistent caching
    sorted_ids = sorted(str(pid) for pid in product_objids)
    cache_key = "_".join(sorted_ids)
    
    # Create a hash for the comparison
    import hashlib
    comparison_hash = hashlib.md5(cache_key.encode()).hexdigest()
    
    # Try to get from cached comparisons
    cached_comparison = db.product_comparisons.find_one({"hash": comparison_hash})
    
    if cached_comparison:
        return cached_comparison["comparison_data"]
    
    # Fallback to original aggregation if cached data is not available
    return original_product_comparison(product_ids)

def run_performance_tests():
    """Run performance tests comparing original and optimized implementations."""
    logger.info("Starting MongoDB performance comparison tests")
    
    tester = PerformanceTester()
    
    # Get a sample product ID and product IDs for testing
    sample_product = db.products.find_one({})
    if not sample_product:
        logger.error("No products found in the database.")
        return
    
    product_id = sample_product["_id"]
    product_ids = [p["_id"] for p in db.products.find().limit(3)]
    
    # Compare performance of sentiment over time query
    tester.compare_queries(
        "Sentiment Over Time (30 days)",
        original_sentiment_over_time,
        optimized_sentiment_over_time,
        product_id, 30, 'day'
    )
    
    # Compare performance of rating distribution by platform query
    tester.compare_queries(
        "Rating Distribution by Platform",
        original_rating_distribution_by_platform,
        optimized_rating_distribution_by_platform,
        90
    )
    
    # Compare performance of keyword sentiment analysis query
    tester.compare_queries(
        "Keyword Sentiment Analysis",
        original_keyword_sentiment_analysis,
        optimized_keyword_sentiment_analysis,
        10
    )
    
    # Compare performance of product comparison query
    tester.compare_queries(
        "Product Comparison",
        original_product_comparison,
        optimized_product_comparison,
        product_ids
    )
    
    # Generate summary and visualize results
    tester.generate_summary()
    tester.visualize_results()
    
    # Save results to CSV
    df = pd.DataFrame(tester.results["comparisons"])
    df.to_csv("performance_comparison_results.csv", index=False)
    
    logger.info("Performance comparison tests completed")
    logger.info(f"Overall improvement: {tester.results['summary']['overall_improvement_percent']}%")

if __name__ == "__main__":
    run_performance_tests() 