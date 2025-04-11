#!/usr/bin/env python
"""
MongoDB Synthetic Data Generator for Load Testing
Generates 10x production volume data for performance testing
"""

import os
import sys
import random
import json
import datetime
import argparse
from tqdm import tqdm
from dotenv import load_dotenv
from bson import ObjectId
from pymongo import MongoClient, InsertMany

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "shopsentiment")

# Data generation settings
DEFAULT_USERS = 100
DEFAULT_PRODUCTS_PER_USER = 5
DEFAULT_REVIEWS_PER_PRODUCT = 200  # 10x normal volume
BATCH_SIZE = 1000  # Insert in batches for better performance

# Sample data for generation
PLATFORMS = ["amazon", "ebay", "walmart", "target", "bestbuy"]
PRODUCT_CATEGORIES = ["electronics", "home", "kitchen", "clothing", "beauty", "toys", "sports", "books"]
BRANDS = ["TechPro", "HomeEssentials", "KitchenMaster", "FashionElite", "BeautyGlow", "ToyWonder", "SportMax", "BookHaven"]
DOMAINS = ["example.com", "test.com", "demo.org", "sample.net"]
SENTIMENT_LABELS = ["positive", "neutral", "negative"]

def generate_random_date(start_date, end_date):
    """Generate a random date between start_date and end_date"""
    delta = end_date - start_date
    random_days = random.randrange(delta.days)
    return start_date + datetime.timedelta(days=random_days)

def generate_user():
    """Generate a random user document"""
    user_id = ObjectId()
    username = f"user_{random.randint(1000, 9999)}"
    
    return {
        "_id": user_id,
        "username": username,
        "email": f"{username}@{random.choice(DOMAINS)}",
        "password_hash": "hashed_password_placeholder",
        "created_at": generate_random_date(
            datetime.datetime(2024, 1, 1), 
            datetime.datetime.now()
        ),
        "last_login": generate_random_date(
            datetime.datetime(2024, 3, 1), 
            datetime.datetime.now()
        ),
        "is_admin": random.random() < 0.05,  # 5% chance of being admin
        "settings": {
            "theme": random.choice(["dark", "light"]),
            "email_notifications": random.choice([True, False])
        }
    }, user_id

def generate_product(user_id):
    """Generate a random product document"""
    product_id = ObjectId()
    platform = random.choice(PLATFORMS)
    platform_id = f"{random.choice(['B', 'A', 'P'])}{random.randint(10000000, 99999999)}"
    category = random.choice(PRODUCT_CATEGORIES)
    brand = random.choice(BRANDS)
    
    # Generate review stats
    review_count = random.randint(50, 300)
    
    # Generate rating distribution
    rating_distribution = {
        "1": random.randint(1, 20),
        "2": random.randint(5, 30),
        "3": random.randint(10, 50),
        "4": random.randint(20, 100),
        "5": random.randint(30, 150)
    }
    
    total_reviews = sum(rating_distribution.values())
    avg_rating = sum([int(k) * v for k, v in rating_distribution.items()]) / total_reviews
    
    # Generate sentiment distribution
    sentiment_distribution = {
        "positive": random.randint(30, 200),
        "neutral": random.randint(20, 100),
        "negative": random.randint(5, 50)
    }
    
    # Generate keywords
    keywords = []
    keyword_options = [
        "quality", "price", "value", "durability", "design", "features",
        "customer service", "shipping", "packaging", "performance", "battery life",
        "ease of use", "size", "weight", "color", "material", "functionality"
    ]
    
    for _ in range(random.randint(5, 10)):
        term = random.choice(keyword_options)
        if not any(k["term"] == term for k in keywords):  # Avoid duplicates
            keywords.append({
                "term": term,
                "count": random.randint(5, 50),
                "sentiment_score": round(random.uniform(-1.0, 1.0), 2)
            })
    
    return {
        "_id": product_id,
        "platform_id": platform_id,
        "platform": platform,
        "category": category,
        "title": f"{brand} {category.title()} {random.choice(['Pro', 'Plus', 'Max', 'Ultra', 'Basic'])}",
        "brand": brand,
        "price": f"{random.randint(10, 1000)}.{random.randint(0, 99):02d}",
        "image_url": f"https://{platform}.{random.choice(DOMAINS)}/images/{platform_id}.jpg",
        "url": f"https://{platform}.{random.choice(DOMAINS)}/product/{platform_id}",
        "created_at": generate_random_date(
            datetime.datetime(2024, 1, 1), 
            datetime.datetime.now()
        ),
        "last_updated": datetime.datetime.now(),
        "created_by": user_id,
        "stats": {
            "review_count": review_count,
            "avg_rating": round(avg_rating, 1),
            "rating_distribution": rating_distribution,
            "sentiment_distribution": sentiment_distribution
        },
        "keywords": keywords
    }, product_id

def generate_review(product_id):
    """Generate a random review document"""
    # Determine sentiment
    sentiment_label = random.choice(SENTIMENT_LABELS)
    
    # Set base sentiment score based on label
    if sentiment_label == "positive":
        base_score = random.uniform(0.6, 1.0)
    elif sentiment_label == "neutral":
        base_score = random.uniform(-0.3, 0.3)
    else:  # negative
        base_score = random.uniform(-1.0, -0.6)
    
    # Generate review components matching the sentiment
    rating = 0
    if sentiment_label == "positive":
        rating = random.randint(4, 5)
        title_options = [
            "Great product", "Excellent choice", "Highly recommend",
            "Love this item", "Fantastic purchase", "Very satisfied"
        ]
    elif sentiment_label == "neutral":
        rating = random.randint(3, 4)
        title_options = [
            "Decent product", "It's okay", "Not bad, not great",
            "Does the job", "As expected", "Average quality"
        ]
    else:  # negative
        rating = random.randint(1, 2)
        title_options = [
            "Disappointed", "Not worth it", "Don't recommend",
            "Save your money", "Poor quality", "Wouldn't buy again"
        ]
    
    # Generate review content
    title = random.choice(title_options)
    
    # Pick potential keywords for this review
    potential_keywords = ["quality", "price", "durability", "design", "shipping", 
                        "customer service", "value", "performance", "features", 
                        "size", "color", "material", "ease of use"]
    
    # Select a few keywords for this review
    review_keywords = random.sample(potential_keywords, random.randint(1, 5))
    
    return {
        "_id": ObjectId(),
        "product_id": product_id,
        "platform_review_id": f"R{random.randint(10000000, 99999999)}",
        "title": title,
        "content": f"This is a synthetic review for load testing. {title}. " + 
                   f"Mentioning {', '.join(review_keywords)}.",
        "rating": rating,
        "author": f"Tester{random.randint(1000, 9999)}",
        "date": generate_random_date(
            datetime.datetime(2023, 1, 1), 
            datetime.datetime.now()
        ),
        "verified_purchase": random.choice([True, False]),
        "sentiment": {
            "label": sentiment_label,
            "score": round(base_score, 2),
            "compound": round(base_score, 2),
            "pos": round(max(0, random.uniform(0, 1) * base_score), 2) if base_score > 0 else round(random.uniform(0, 0.2), 2),
            "neg": round(max(0, random.uniform(0, 1) * -base_score), 2) if base_score < 0 else round(random.uniform(0, 0.2), 2),
            "neu": round(random.uniform(0.1, 0.9), 2)
        },
        "keywords": review_keywords,
        "created_at": datetime.datetime.now()
    }

def generate_data(users_count, products_per_user, reviews_per_product):
    """Generate all test data"""
    print(f"Generating data: {users_count} users, {products_per_user} products per user, {reviews_per_product} reviews per product")
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    
    # Clear existing collections if requested
    if args.clear:
        print("Clearing existing collections...")
        db.users.delete_many({})
        db.products.delete_many({})
        db.reviews.delete_many({})
    
    # Generate and insert users
    print("Generating users...")
    users_batch = []
    user_ids = []
    
    for i in tqdm(range(users_count)):
        user, user_id = generate_user()
        users_batch.append(user)
        user_ids.append(user_id)
        
        if len(users_batch) >= BATCH_SIZE or i == users_count - 1:
            db.users.insert_many(users_batch)
            users_batch = []
    
    # Generate and insert products
    print("Generating products...")
    all_product_ids = []
    products_batch = []
    
    for i, user_id in tqdm(enumerate(user_ids)):
        for j in range(products_per_user):
            product, product_id = generate_product(user_id)
            products_batch.append(product)
            all_product_ids.append(product_id)
            
            if len(products_batch) >= BATCH_SIZE:
                db.products.insert_many(products_batch)
                products_batch = []
    
    # Insert remaining products
    if products_batch:
        db.products.insert_many(products_batch)
    
    # Generate and insert reviews
    print("Generating reviews...")
    reviews_batch = []
    total_reviews = len(all_product_ids) * reviews_per_product
    
    with tqdm(total=total_reviews) as pbar:
        for product_id in all_product_ids:
            for _ in range(reviews_per_product):
                review = generate_review(product_id)
                reviews_batch.append(review)
                
                if len(reviews_batch) >= BATCH_SIZE:
                    db.reviews.insert_many(reviews_batch)
                    pbar.update(len(reviews_batch))
                    reviews_batch = []
    
    # Insert remaining reviews
    if reviews_batch:
        db.reviews.insert_many(reviews_batch)
        pbar.update(len(reviews_batch))
    
    # Print collection stats
    print("\nCollection Statistics:")
    print(f"Users: {db.users.count_documents({})}")
    print(f"Products: {db.products.count_documents({})}")
    print(f"Reviews: {db.reviews.count_documents({})}")
    
    client.close()
    print("Data generation complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic MongoDB data for load testing")
    parser.add_argument("--users", type=int, default=DEFAULT_USERS, help=f"Number of users to generate (default: {DEFAULT_USERS})")
    parser.add_argument("--products", type=int, default=DEFAULT_PRODUCTS_PER_USER, help=f"Products per user (default: {DEFAULT_PRODUCTS_PER_USER})")
    parser.add_argument("--reviews", type=int, default=DEFAULT_REVIEWS_PER_PRODUCT, help=f"Reviews per product (default: {DEFAULT_REVIEWS_PER_PRODUCT})")
    parser.add_argument("--clear", action="store_true", help="Clear existing collections before generating new data")
    
    args = parser.parse_args()
    
    try:
        generate_data(args.users, args.products, args.reviews)
    except Exception as e:
        print(f"Error generating data: {e}")
        sys.exit(1) 