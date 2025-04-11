import random
from datetime import datetime, timedelta
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from faker import Faker
import numpy as np
from bson import ObjectId
import json

# Initialize Faker
fake = Faker()

# MongoDB connection
uri = "mongodb+srv://tomasstaniulis76:JaLhUd1NLZUtwVb5@shop1.11tjwh5.mongodb.net/?retryWrites=true&w=majority&appName=Shop1"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.shopsentiment

def generate_product():
    """Generate a single product with realistic metadata"""
    brands = ['Apple', 'Samsung', 'Sony', 'LG', 'Dell', 'HP', 'Lenovo', 'Asus', 'Acer', 'Microsoft']
    categories = ['Electronics', 'Computers', 'Smartphones', 'Accessories', 'Audio', 'Gaming']
    
    # Generate price as string with currency symbol
    price = f"${round(random.uniform(49.99, 1999.99), 2)}"
    
    return {
        "_id": ObjectId(),
        "platform_id": f"B{fake.bothify('??##???#??')}",
        "platform": random.choice(['amazon', 'ebay']),
        "title": fake.catch_phrase(),
        "brand": random.choice(brands),
        "category": random.choice(categories),
        "price": price,  # Price as string with currency
        "image_url": f"https://example.com/images/{fake.uuid4()}.jpg",
        "url": f"https://example.com/products/{fake.uuid4()}",
        "created_at": fake.date_time_between(start_date='-1y'),
        "last_updated": datetime.now(),
        "stats": {
            "review_count": 0,
            "avg_rating": 0,
            "rating_distribution": {str(i): 0 for i in range(1, 6)},
            "sentiment_distribution": {
                "positive": 0,
                "neutral": 0,
                "negative": 0
            }
        },
        "keywords": []
    }

def generate_review(product_id):
    """Generate a single review with realistic sentiment"""
    rating = int(np.random.choice([1, 2, 3, 4, 5], p=[0.1, 0.1, 0.2, 0.3, 0.3]))
    
    # Generate sentiment based on rating
    if rating >= 4:
        sentiment = {"label": "positive", "score": random.uniform(0.6, 1.0)}
    elif rating <= 2:
        sentiment = {"label": "negative", "score": random.uniform(0.0, 0.4)}
    else:
        sentiment = {"label": "neutral", "score": random.uniform(0.4, 0.6)}
    
    # Generate realistic keywords based on sentiment
    positive_keywords = ['great', 'excellent', 'awesome', 'perfect', 'love']
    negative_keywords = ['poor', 'bad', 'terrible', 'disappointing', 'hate']
    neutral_keywords = ['okay', 'average', 'decent', 'fair', 'normal']
    
    if sentiment["label"] == "positive":
        keywords = random.sample(positive_keywords, k=random.randint(1, 3))
    elif sentiment["label"] == "negative":
        keywords = random.sample(negative_keywords, k=random.randint(1, 3))
    else:
        keywords = random.sample(neutral_keywords, k=random.randint(1, 3))

    return {
        "_id": ObjectId(),
        "product_id": product_id,
        "platform_review_id": f"R{fake.bothify('??##???#??')}",
        "title": fake.sentence(),
        "content": fake.paragraph(nb_sentences=random.randint(3, 8)),
        "rating": rating,
        "author": fake.name(),
        "date": fake.date_time_between(start_date='-6m'),
        "verified_purchase": random.choice([True, False]),
        "sentiment": sentiment,
        "keywords": keywords,
        "created_at": datetime.now()
    }

def update_product_stats(product_id, reviews):
    """Update product statistics based on its reviews"""
    product_reviews = [r for r in reviews if r["product_id"] == product_id]
    
    if not product_reviews:
        return
    
    # Calculate statistics
    review_count = len(product_reviews)
    avg_rating = sum(r["rating"] for r in product_reviews) / review_count
    
    # Calculate rating distribution
    rating_dist = {str(i): 0 for i in range(1, 6)}
    for review in product_reviews:
        rating_dist[str(review["rating"])] += 1
    
    # Calculate sentiment distribution
    sentiment_dist = {"positive": 0, "neutral": 0, "negative": 0}
    for review in product_reviews:
        sentiment_dist[review["sentiment"]["label"]] += 1
    
    # Extract common keywords
    all_keywords = [k for r in product_reviews for k in r["keywords"]]
    keyword_freq = {}
    for k in all_keywords:
        if k not in keyword_freq:
            keyword_freq[k] = 1
        else:
            keyword_freq[k] += 1
    
    # Get top 10 keywords with their frequencies
    top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    keywords_with_stats = [{"term": k, "count": c, "sentiment_score": random.uniform(0.0, 1.0)} 
                          for k, c in top_keywords]
    
    # Update product stats
    db.products.update_one(
        {"_id": product_id},
        {
            "$set": {
                "stats": {
                    "review_count": review_count,
                    "avg_rating": round(avg_rating, 2),
                    "rating_distribution": rating_dist,
                    "sentiment_distribution": sentiment_dist
                },
                "keywords": keywords_with_stats
            }
        }
    )

def main():
    """Generate test data and insert into MongoDB"""
    try:
        # Clear existing collections
        print("Clearing existing collections...")
        db.products.delete_many({})
        db.reviews.delete_many({})
        
        # Generate and insert products in smaller batches
        print("Generating products...")
        batch_size = 100
        total_products = 1000
        all_products = []
        
        for i in range(0, total_products, batch_size):
            batch = [generate_product() for _ in range(batch_size)]
            try:
                result = db.products.insert_many(batch)
                all_products.extend(batch)
                print(f"Inserted {len(result.inserted_ids)} products...")
            except Exception as e:
                print(f"Error inserting products batch: {str(e)}")
                # Try inserting one by one to identify problematic documents
                for product in batch:
                    try:
                        db.products.insert_one(product)
                        all_products.append(product)
                    except Exception as e:
                        print(f"Error inserting product: {str(e)}")
                        print(f"Problematic document: {json.dumps(product, default=str)}")
        
        print(f"Generated {len(all_products)} products")
        
        # Generate and insert reviews
        print("Generating reviews...")
        all_reviews = []
        for product in all_products:
            num_reviews = random.randint(50, 150)
            product_reviews = [generate_review(product["_id"]) for _ in range(num_reviews)]
            
            # Insert reviews in smaller batches
            review_batch_size = 100
            for i in range(0, len(product_reviews), review_batch_size):
                batch = product_reviews[i:i + review_batch_size]
                try:
                    result = db.reviews.insert_many(batch)
                    all_reviews.extend(batch)
                    print(f"Inserted {len(result.inserted_ids)} reviews for product {product['_id']}...")
                except Exception as e:
                    print(f"Error inserting reviews batch: {str(e)}")
                    # Try inserting one by one
                    for review in batch:
                        try:
                            db.reviews.insert_one(review)
                            all_reviews.append(review)
                        except Exception as e:
                            print(f"Error inserting review: {str(e)}")
                            print(f"Problematic document: {json.dumps(review, default=str)}")
        
        print("Updating product statistics...")
        for product in all_products:
            try:
                update_product_stats(product["_id"], all_reviews)
            except Exception as e:
                print(f"Error updating stats for product {product['_id']}: {str(e)}")
        
        print("\nData generation complete!")
        print(f"Total products: {db.products.count_documents({})}")
        print(f"Total reviews: {db.reviews.count_documents({})}")
        
        # Create indexes
        print("\nCreating indexes...")
        try:
            db.products.create_index([("platform_id", 1), ("platform", 1)], unique=True)
            db.products.create_index([("brand", 1)])
            db.products.create_index([("category", 1)])
            db.reviews.create_index([("product_id", 1)])
            db.reviews.create_index([("date", -1)])
            db.reviews.create_index([("sentiment.label", 1)])
            print("Indexes created successfully!")
        except Exception as e:
            print(f"Error creating indexes: {str(e)}")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 