from pymongo import MongoClient
from datetime import datetime, timedelta
import json

def validate_data():
    """Validate the generated test data"""
    client = MongoClient('mongodb://localhost:27017/')
    db = client['shopsentiment']
    
    validation_results = {
        "products": {"status": "PASS", "issues": []},
        "reviews": {"status": "PASS", "issues": []},
        "indexes": {"status": "PASS", "issues": []},
        "relationships": {"status": "PASS", "issues": []}
    }
    
    # 1. Validate Products Collection
    try:
        products_count = db.products.count_documents({})
        if products_count != 1000:
            validation_results["products"]["issues"].append(
                f"Expected 1000 products, found {products_count}"
            )
            validation_results["products"]["status"] = "FAIL"
        
        # Check product schema
        sample_product = db.products.find_one({})
        required_fields = ["platform_id", "platform", "title", "brand", "price", "stats"]
        for field in required_fields:
            if field not in sample_product:
                validation_results["products"]["issues"].append(
                    f"Missing required field: {field}"
                )
                validation_results["products"]["status"] = "FAIL"
    except Exception as e:
        validation_results["products"]["issues"].append(str(e))
        validation_results["products"]["status"] = "FAIL"
    
    # 2. Validate Reviews Collection
    try:
        reviews_count = db.reviews.count_documents({})
        if reviews_count < 50000:  # Minimum expected reviews
            validation_results["reviews"]["issues"].append(
                f"Expected at least 50000 reviews, found {reviews_count}"
            )
            validation_results["reviews"]["status"] = "FAIL"
        
        # Check review schema
        sample_review = db.reviews.find_one({})
        required_fields = ["product_id", "rating", "sentiment", "date"]
        for field in required_fields:
            if field not in sample_review:
                validation_results["reviews"]["issues"].append(
                    f"Missing required field: {field}"
                )
                validation_results["reviews"]["status"] = "FAIL"
    except Exception as e:
        validation_results["reviews"]["issues"].append(str(e))
        validation_results["reviews"]["status"] = "FAIL"
    
    # 3. Validate Indexes
    try:
        product_indexes = db.products.index_information()
        review_indexes = db.reviews.index_information()
        
        required_product_indexes = ["platform_id_1_platform_1", "brand_1", "category_1"]
        required_review_indexes = ["product_id_1", "date_-1", "sentiment.label_1"]
        
        for idx in required_product_indexes:
            if idx not in product_indexes:
                validation_results["indexes"]["issues"].append(
                    f"Missing product index: {idx}"
                )
                validation_results["indexes"]["status"] = "FAIL"
        
        for idx in required_review_indexes:
            if idx not in review_indexes:
                validation_results["indexes"]["issues"].append(
                    f"Missing review index: {idx}"
                )
                validation_results["indexes"]["status"] = "FAIL"
    except Exception as e:
        validation_results["indexes"]["issues"].append(str(e))
        validation_results["indexes"]["status"] = "FAIL"
    
    # 4. Validate Relationships
    try:
        # Check if all reviews have valid product references
        orphan_reviews = db.reviews.count_documents({
            "product_id": {"$nin": [p["_id"] for p in db.products.find({}, {"_id": 1})]}
        })
        if orphan_reviews > 0:
            validation_results["relationships"]["issues"].append(
                f"Found {orphan_reviews} reviews with invalid product references"
            )
            validation_results["relationships"]["status"] = "FAIL"
        
        # Validate product stats
        sample_product = db.products.find_one({})
        product_reviews = db.reviews.count_documents({"product_id": sample_product["_id"]})
        if product_reviews != sample_product["stats"]["review_count"]:
            validation_results["relationships"]["issues"].append(
                "Product stats don't match actual review count"
            )
            validation_results["relationships"]["status"] = "FAIL"
    except Exception as e:
        validation_results["relationships"]["issues"].append(str(e))
        validation_results["relationships"]["status"] = "FAIL"
    
    return validation_results

def print_validation_results(results):
    """Print validation results in a readable format"""
    print("\n=== Data Validation Results ===\n")
    
    for category, data in results.items():
        status_color = "\033[92m" if data["status"] == "PASS" else "\033[91m"  # Green or Red
        print(f"{category.upper()}: {status_color}{data['status']}\033[0m")
        
        if data["issues"]:
            print("Issues found:")
            for issue in data["issues"]:
                print(f"  - {issue}")
        print()

def main():
    """Run data validation and display results"""
    try:
        results = validate_data()
        print_validation_results(results)
        
        # Check if any validation failed
        if any(data["status"] == "FAIL" for data in results.values()):
            print("\n❌ Validation failed! Please check the issues above.")
            return False
        else:
            print("\n✅ All validations passed successfully!")
            return True
            
    except Exception as e:
        print(f"\n❌ Error during validation: {str(e)}")
        return False

if __name__ == "__main__":
    main() 