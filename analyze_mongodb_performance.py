"""
MongoDB Aggregation Performance Analysis
Identifies slow aggregation pipelines and suggests optimizations
"""

import time
import statistics
from datetime import datetime, timedelta
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
import json

# MongoDB connection
uri = "mongodb+srv://tomasstaniulis76:JaLhUd1NLZUtwVb5@shop1.11tjwh5.mongodb.net/?retryWrites=true&w=majority&appName=Shop1"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.shopsentiment

# Performance tracking
ITERATIONS = 3  # Number of times to run each query for consistent results

class QueryTester:
    """Tests MongoDB query performance."""
    
    def __init__(self):
        self.results = {
            "aggregations": [],
            "suggestions": []
        }
    
    def run_query(self, name, func, *args, **kwargs):
        """Run a query multiple times and measure performance."""
        times = []
        explain_info = None
        
        for i in range(ITERATIONS):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            elapsed = (end_time - start_time) * 1000  # Convert to ms
            times.append(elapsed)
            
            # On first run, capture the result summary
            if i == 0:
                # For list results
                if isinstance(result, list):
                    result_summary = {
                        "count": len(result),
                        "sample": result[0] if result else None
                    }
                # For dictionary results
                elif isinstance(result, dict):
                    result_summary = {
                        "keys": list(result.keys()),
                        "sample": list(result.items())[0] if result else None
                    }
                else:
                    result_summary = str(result)
                    
                # Try to get explain info if applicable
                try:
                    if hasattr(func, '_pipeline') and hasattr(func, '_collection'):
                        explain_info = db[func._collection].aggregate(
                            func._pipeline, 
                            explain=True
                        )
                except:
                    explain_info = None
        
        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        
        # Record result
        query_result = {
            "name": name,
            "average_ms": round(avg_time, 2),
            "median_ms": round(median_time, 2),
            "min_ms": round(min_time, 2),
            "max_ms": round(max_time, 2),
            "result_summary": result_summary,
            "explain": explain_info
        }
        
        self.results["aggregations"].append(query_result)
        print(f"Query: {name}, Avg: {avg_time:.2f}ms, Median: {median_time:.2f}ms")
        
        return query_result
    
    def analyze_results(self):
        """Analyze performance results and generate suggestions."""
        slow_threshold = 100  # ms
        
        for query in self.results["aggregations"]:
            if query["average_ms"] > slow_threshold:
                suggestion = {
                    "query": query["name"],
                    "performance": f"{query['average_ms']}ms avg",
                    "issues": [],
                    "suggestions": []
                }
                
                # Look for common issues in aggregation pipelines
                if "sentiment_over_time" in query["name"]:
                    suggestion["issues"].append("Complex date manipulation in pipeline")
                    suggestion["suggestions"].append("Create a precomputed time-series collection")
                    suggestion["suggestions"].append("Add compound index on product_id and date fields")
                
                elif "rating_distribution" in query["name"]:
                    suggestion["issues"].append("$lookup operation between products and reviews")
                    suggestion["suggestions"].append("Create a materialized view with regular updates")
                    suggestion["suggestions"].append("Add index on date field in reviews collection")
                
                elif "keyword" in query["name"]:
                    suggestion["issues"].append("Text processing and grouping operations")
                    suggestion["suggestions"].append("Create a keywords collection with pre-computed sentiment stats")
                    suggestion["suggestions"].append("Use MongoDB text indexes for improved performance")
                
                elif "comparison" in query["name"]:
                    suggestion["issues"].append("Multiple lookups between collections")
                    suggestion["suggestions"].append("Denormalize key metrics into product documents")
                    suggestion["suggestions"].append("Use cached results for frequently compared products")
                
                self.results["suggestions"].append(suggestion)
        
        # Output summary
        if self.results["suggestions"]:
            print("\n=== PERFORMANCE SUGGESTIONS ===")
            for sugg in self.results["suggestions"]:
                print(f"\nQuery: {sugg['query']} - {sugg['performance']}")
                print("Issues:")
                for issue in sugg["issues"]:
                    print(f"  - {issue}")
                print("Suggestions:")
                for suggestion in sugg["suggestions"]:
                    print(f"  - {suggestion}")
        else:
            print("\nAll queries perform within acceptable parameters.")

def sentiment_over_time(product_id, days=30, interval='day'):
    """Test for sentiment over time pipeline."""
    # Define date range
    end_date = datetime.now()
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
    
    # Add pipeline metadata for explain analysis
    sentiment_over_time._pipeline = pipeline
    sentiment_over_time._collection = 'reviews'
    
    return list(db.reviews.aggregate(pipeline))

def rating_distribution_by_platform(days=90):
    """Test for rating distribution by platform pipeline."""
    # Define date range
    end_date = datetime.now()
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
    
    # Add pipeline metadata for explain analysis
    rating_distribution_by_platform._pipeline = pipeline
    rating_distribution_by_platform._collection = 'products'
    
    results = list(db.products.aggregate(pipeline))
    
    # Format results
    platform_data = {}
    for item in results:
        platform = item.get('platform', 'unknown')
        platform_data[platform] = item.get('rating_distribution', {})
    
    return platform_data

def keyword_sentiment_analysis(min_count=10):
    """Test for keyword sentiment analysis pipeline."""
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
    
    # Add pipeline metadata for explain analysis
    keyword_sentiment_analysis._pipeline = pipeline
    keyword_sentiment_analysis._collection = 'reviews'
    
    return list(db.reviews.aggregate(pipeline))

def product_comparison(product_ids):
    """Test for product comparison pipeline."""
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
    
    # Add pipeline metadata for explain analysis
    product_comparison._pipeline = pipeline
    product_comparison._collection = 'products'
    
    return list(db.products.aggregate(pipeline))

def main():
    """Run performance tests and analyze results."""
    print("MongoDB Aggregation Performance Analysis")
    print("=======================================")
    
    # Create tester
    tester = QueryTester()
    
    # Get a sample product ID for testing
    sample_product = db.products.find_one({})
    if not sample_product:
        print("No products found in the database.")
        return
    
    product_id = sample_product["_id"]
    print(f"Using sample product ID: {product_id}")
    
    # Get multiple product IDs for comparison test
    product_ids = [p["_id"] for p in db.products.find().limit(5)]
    
    # Run tests
    print("\nRunning performance tests...")
    tester.run_query("Sentiment Over Time (30 days, daily)", sentiment_over_time, product_id, 30, 'day')
    tester.run_query("Sentiment Over Time (90 days, weekly)", sentiment_over_time, product_id, 90, 'week')
    tester.run_query("Rating Distribution by Platform", rating_distribution_by_platform)
    tester.run_query("Keyword Sentiment Analysis", keyword_sentiment_analysis)
    tester.run_query("Product Comparison", product_comparison, product_ids)
    
    # Analyze results
    tester.analyze_results()
    
    # Output results to JSON file
    with open('mongodb_performance_analysis.json', 'w') as f:
        json.dump(tester.results, f, indent=2, default=str)
    
    print("\nAnalysis complete. Results saved to mongodb_performance_analysis.json")

if __name__ == "__main__":
    main() 