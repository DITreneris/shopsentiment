from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
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

def print_data_summary():
    # Count documents
    product_count = db.products.count_documents({})
    review_count = db.reviews.count_documents({})
    
    print(f"===== DATA SUMMARY =====")
    print(f"Total products: {product_count}")
    print(f"Total reviews: {review_count}")
    
    if product_count > 0:
        # Get sample product
        sample_product = db.products.find_one({})
        print("\n===== SAMPLE PRODUCT =====")
        print(json.dumps(sample_product, cls=MongoJSONEncoder, indent=2))
        
        # Check product stats
        stats = sample_product.get('stats', {})
        print(f"\n===== PRODUCT STATS =====")
        print(f"Review count: {stats.get('review_count', 0)}")
        print(f"Average rating: {stats.get('avg_rating', 0)}")
        print(f"Rating distribution: {stats.get('rating_distribution', {})}")
        print(f"Sentiment distribution: {stats.get('sentiment_distribution', {})}")
        
        # Get number of reviews for this product
        product_id = sample_product['_id']
        product_reviews_count = db.reviews.count_documents({"product_id": product_id})
        print(f"Actual reviews for this product: {product_reviews_count}")
    
    if review_count > 0:
        # Get sample review
        sample_review = db.reviews.find_one({})
        print("\n===== SAMPLE REVIEW =====")
        print(json.dumps(sample_review, cls=MongoJSONEncoder, indent=2))
    
    # Check indexes
    print("\n===== INDEXES =====")
    product_indexes = db.products.index_information()
    review_indexes = db.reviews.index_information()
    print("Product indexes:", json.dumps(product_indexes, cls=MongoJSONEncoder, indent=2))
    print("Review indexes:", json.dumps(review_indexes, cls=MongoJSONEncoder, indent=2))

if __name__ == "__main__":
    try:
        print_data_summary()
    except Exception as e:
        print(f"Error: {str(e)}") 