from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import time
import json
from bson import ObjectId
from datetime import datetime

# MongoDB connection
uri = "mongodb+srv://tomasstaniulis76:JaLhUd1NLZUtwVb5@shop1.11tjwh5.mongodb.net/?retryWrites=true&w=majority&appName=Shop1"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.shopsentiment

# Custom JSON encoder to handle MongoDB ObjectId and datetime types
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return json.JSONEncoder.default(self, obj)

def measure_query_time(query_func, *args, **kwargs):
    """Measure the execution time of a query function"""
    start_time = time.time()
    result = query_func(*args, **kwargs)
    end_time = time.time()
    elapsed = end_time - start_time
    return result, elapsed

def test_product_queries():
    """Test various product queries for performance"""
    print("\n===== PRODUCT QUERY PERFORMANCE =====")
    
    # 1. Find a product by ID
    random_product = db.products.find_one({})
    product_id = random_product["_id"]
    
    result, elapsed = measure_query_time(db.products.find_one, {"_id": product_id})
    print(f"Find product by ID: {elapsed:.6f} seconds")
    
    # 2. Find products by brand
    brand = random_product["brand"]
    result, elapsed = measure_query_time(
        lambda: list(db.products.find({"brand": brand}).limit(10))
    )
    print(f"Find products by brand (limit 10): {elapsed:.6f} seconds")
    
    # 3. Find products by category
    category = random_product["category"]
    result, elapsed = measure_query_time(
        lambda: list(db.products.find({"category": category}).limit(10))
    )
    print(f"Find products by category (limit 10): {elapsed:.6f} seconds")

def test_review_queries():
    """Test various review queries for performance"""
    print("\n===== REVIEW QUERY PERFORMANCE =====")
    
    # 1. Find reviews for a product
    random_product = db.products.find_one({})
    product_id = random_product["_id"]
    
    result, elapsed = measure_query_time(
        lambda: list(db.reviews.find({"product_id": product_id}).limit(10))
    )
    print(f"Find reviews for product (limit 10): {elapsed:.6f} seconds")
    
    # 2. Find reviews with positive sentiment
    result, elapsed = measure_query_time(
        lambda: list(db.reviews.find(
            {"product_id": product_id, "sentiment.label": "positive"}
        ).limit(10))
    )
    print(f"Find positive reviews for product (limit 10): {elapsed:.6f} seconds")
    
    # 3. Find reviews sorted by date
    result, elapsed = measure_query_time(
        lambda: list(db.reviews.find({"product_id": product_id}).sort("date", -1).limit(10))
    )
    print(f"Find recent reviews for product (limit 10): {elapsed:.6f} seconds")

def test_aggregation_queries():
    """Test aggregation queries for performance"""
    print("\n===== AGGREGATION QUERY PERFORMANCE =====")
    
    # 1. Get average rating per brand
    pipeline = [
        {"$group": {"_id": "$brand", "avgRating": {"$avg": "$stats.avg_rating"}}},
        {"$sort": {"avgRating": -1}}
    ]
    
    result, elapsed = measure_query_time(
        lambda: list(db.products.aggregate(pipeline))
    )
    print(f"Average rating per brand: {elapsed:.6f} seconds")
    print("Results:")
    for item in result:
        print(f"  {item['_id']}: {item['avgRating']:.2f}")
    
    # 2. Get sentiment distribution across all reviews
    pipeline = [
        {"$group": {
            "_id": "$sentiment.label", 
            "count": {"$sum": 1},
            "avg_score": {"$avg": "$sentiment.score"}
        }},
        {"$sort": {"count": -1}}
    ]
    
    result, elapsed = measure_query_time(
        lambda: list(db.reviews.aggregate(pipeline))
    )
    print(f"\nSentiment distribution across all reviews: {elapsed:.6f} seconds")
    print("Results:")
    for item in result:
        print(f"  {item['_id']}: {item['count']} reviews, avg score: {item['avg_score']:.2f}")

if __name__ == "__main__":
    try:
        # Run the performance tests
        test_product_queries()
        test_review_queries()
        test_aggregation_queries()
        
    except Exception as e:
        print(f"Error: {str(e)}") 