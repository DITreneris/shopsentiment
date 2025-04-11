from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import json

def check_schema():
    """Check MongoDB collection schema"""
    uri = "mongodb+srv://tomasstaniulis76:JaLhUd1NLZUtwVb5@shop1.11tjwh5.mongodb.net/?retryWrites=true&w=majority&appName=Shop1"
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client.shopsentiment
    
    try:
        # Get collection options
        products_options = db.products.options()
        reviews_options = db.reviews.options()
        
        print("Products Collection Schema:")
        if 'validator' in products_options:
            print(json.dumps(products_options['validator'], indent=2))
        else:
            print("No schema validator found")
        
        print("\nReviews Collection Schema:")
        if 'validator' in reviews_options:
            print(json.dumps(reviews_options['validator'], indent=2))
        else:
            print("No schema validator found")
            
        # Get sample documents
        print("\nSample Product Document:")
        sample_product = db.products.find_one()
        if sample_product:
            print(json.dumps(sample_product, indent=2, default=str))
        else:
            print("No products found")
            
        print("\nSample Review Document:")
        sample_review = db.reviews.find_one()
        if sample_review:
            print(json.dumps(sample_review, indent=2, default=str))
        else:
            print("No reviews found")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    check_schema() 