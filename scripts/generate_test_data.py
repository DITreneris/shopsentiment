#!/usr/bin/env python3
"""
Generate Synthetic Test Data for Load Testing

This script generates synthetic test data to simulate a production environment
with 10x the normal data volume. It creates products, reviews, and users
to test the ShopSentiment application under load.
"""

import os
import sys
import random
import logging
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from faker import Faker
from pymongo import MongoClient, UpdateOne
from bson.objectid import ObjectId
from tqdm import tqdm
import numpy as np
import hashlib

# Add parent directory to path so we can import app modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("generate_test_data")

# Initialize Faker
fake = Faker()

# Configuration
DEFAULT_CONFIG = {
    "products_count": 1000,  # 10x typical production volume
    "reviews_per_product_min": 50,
    "reviews_per_product_max": 500,
    "users_count": 200,
    "platforms": ["amazon", "ebay", "walmart", "target", "bestbuy"],
    "categories": ["electronics", "home", "clothing", "beauty", "sports", "toys", "books", "grocery"],
    "sentiment_distribution": {"positive": 0.6, "neutral": 0.2, "negative": 0.2},
    "verified_purchase_ratio": 0.8,
    "rating_weights": [0.05, 0.10, 0.15, 0.30, 0.40],  # Weights for ratings 1-5
    "keywords_per_review_min": 2,
    "keywords_per_review_max": 8,
    "common_keywords": {
        "electronics": ["battery", "screen", "price", "quality", "features", "size", "weight", "durability"],
        "home": ["quality", "price", "size", "color", "design", "material", "durability", "comfort"],
        "clothing": ["fit", "size", "quality", "color", "material", "style", "comfort", "price"],
        "beauty": ["smell", "texture", "results", "price", "packaging", "quality", "skin", "color"],
        "sports": ["quality", "durability", "performance", "comfort", "price", "weight", "size", "design"],
        "toys": ["quality", "durability", "fun", "educational", "price", "safety", "age", "size"],
        "books": ["story", "characters", "writing", "length", "price", "author", "quality", "ending"],
        "grocery": ["taste", "quality", "price", "freshness", "packaging", "value", "flavor", "ingredients"]
    }
}

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Generate synthetic test data for load testing")
    parser.add_argument("--products", type=int, default=DEFAULT_CONFIG["products_count"],
                        help=f"Number of products to generate (default: {DEFAULT_CONFIG['products_count']})")
    parser.add_argument("--users", type=int, default=DEFAULT_CONFIG["users_count"],
                        help=f"Number of users to generate (default: {DEFAULT_CONFIG['users_count']})")
    parser.add_argument("--min-reviews", type=int, default=DEFAULT_CONFIG["reviews_per_product_min"],
                        help=f"Minimum reviews per product (default: {DEFAULT_CONFIG['reviews_per_product_min']})")
    parser.add_argument("--max-reviews", type=int, default=DEFAULT_CONFIG["reviews_per_product_max"],
                        help=f"Maximum reviews per product (default: {DEFAULT_CONFIG['reviews_per_product_max']})")
    parser.add_argument("--mongo-uri", type=str, default=os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"),
                        help="MongoDB connection URI")
    parser.add_argument("--db-name", type=str, default=os.environ.get("MONGODB_DB_NAME", "shopsentiment_test"),
                        help="MongoDB database name (default: shopsentiment_test)")
    parser.add_argument("--drop", action="store_true", help="Drop existing collections before importing")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for MongoDB operations")
    return parser.parse_args()

def connect_to_mongodb(uri, db_name):
    """Connect to MongoDB"""
    logger.info(f"Connecting to MongoDB database: {db_name}")
    client = MongoClient(uri)
    db = client[db_name]
    return client, db

def generate_users(count, db):
    """Generate synthetic users"""
    logger.info(f"Generating {count} users")
    users = []
    
    for _ in tqdm(range(count), desc="Generating users"):
        created_at = fake.date_time_between(start_date="-2y", end_date="now")
        last_login = fake.date_time_between(start_date=created_at, end_date="now")
        
        user = {
            "_id": ObjectId(),
            "username": fake.user_name(),
            "email": fake.email(),
            "password_hash": hashlib.sha256(fake.password().encode()).hexdigest(),  # Not for auth, just for realism
            "created_at": created_at,
            "last_login": last_login,
            "is_admin": random.random() < 0.05,  # 5% are admins
            "settings": {
                "theme": random.choice(["light", "dark", "auto"]),
                "email_notifications": random.choice([True, False])
            }
        }
        users.append(user)
    
    if users:
        if db.users.count_documents({}) > 0:
            logger.warning(f"Users collection already contains data")
            if args.drop:
                logger.info("Dropping existing users collection")
                db.users.drop()
        
        logger.info(f"Inserting {len(users)} users into database")
        db.users.insert_many(users)
    
    return users

def generate_products(count, users, db, platforms, categories):
    """Generate synthetic products"""
    logger.info(f"Generating {count} products")
    products = []
    
    for _ in tqdm(range(count), desc="Generating products"):
        # Choose a random creator from the users
        creator = random.choice(users)
        
        # Generate product data
        platform = random.choice(platforms)
        category = random.choice(categories)
        created_at = fake.date_time_between(start_date="-2y", end_date="now")
        
        # Generate a platform-specific ID
        if platform == "amazon":
            platform_id = f"B{fake.bothify('?#?#?#?#?#')}"
        elif platform == "ebay":
            platform_id = fake.bothify("########")
        else:
            platform_id = fake.bothify("????-#########")
        
        # Generate a product title appropriate for the category
        if category == "electronics":
            brand = random.choice(["Apple", "Samsung", "Sony", "LG", "Dell", "HP", "Lenovo", "Asus"])
            product_type = random.choice(["Smartphone", "Laptop", "Tablet", "Headphones", "TV", "Camera"])
            title = f"{brand} {product_type} {fake.word().capitalize()} {fake.random_number(3)} Series"
        elif category == "home":
            brand = random.choice(["Ikea", "Ashley", "Wayfair", "Crate & Barrel", "West Elm", "HomeGoods"])
            product_type = random.choice(["Sofa", "Chair", "Table", "Lamp", "Rug", "Curtains", "Bed"])
            title = f"{brand} {product_type} {fake.word().capitalize()} Collection"
        elif category == "clothing":
            brand = random.choice(["Nike", "Adidas", "H&M", "Zara", "Gap", "Levi's", "Calvin Klein"])
            product_type = random.choice(["Shirt", "Pants", "Dress", "Jacket", "Shoes", "Socks", "Hat"])
            title = f"{brand} {fake.color_name().capitalize()} {product_type} for {random.choice(['Men', 'Women', 'Kids'])}"
        else:
            title = fake.catch_phrase()
        
        # Generate product price based on category
        if category == "electronics":
            price = str(round(random.uniform(100, 2000), 2))
        elif category == "clothing":
            price = str(round(random.uniform(10, 200), 2))
        else:
            price = str(round(random.uniform(5, 500), 2))
        
        product = {
            "_id": ObjectId(),
            "platform_id": platform_id,
            "platform": platform,
            "category": category,
            "title": title,
            "brand": title.split()[0],  # Use the first word as brand
            "price": price,
            "image_url": f"https://example.com/images/{platform}/{platform_id}.jpg",
            "url": f"https://{platform}.com/dp/{platform_id}",
            "created_at": created_at,
            "last_updated": fake.date_time_between(start_date=created_at, end_date="now"),
            "created_by": creator["_id"],
            "stats": {
                "review_count": 0,  # Will be updated after generating reviews
                "avg_rating": 0,    # Will be updated after generating reviews
                "rating_distribution": {
                    "1": 0,
                    "2": 0,
                    "3": 0,
                    "4": 0,
                    "5": 0
                },
                "sentiment_distribution": {
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                }
            },
            "keywords": []  # Will be updated after generating reviews
        }
        products.append(product)
    
    if products:
        if db.products.count_documents({}) > 0:
            logger.warning(f"Products collection already contains data")
            if args.drop:
                logger.info("Dropping existing products collection")
                db.products.drop()
        
        logger.info(f"Inserting {len(products)} products into database")
        db.products.insert_many(products)
    
    return products

def generate_reviews(products, min_reviews, max_reviews, db, config):
    """Generate synthetic reviews for products"""
    logger.info(f"Generating reviews for {len(products)} products")
    
    # Drop reviews collection if it exists and --drop is specified
    if db.reviews.count_documents({}) > 0:
        logger.warning(f"Reviews collection already contains data")
        if args.drop:
            logger.info("Dropping existing reviews collection")
            db.reviews.drop()
    
    # Create batches for bulk operations
    product_update_operations = []
    total_reviews = 0
    
    # Process each product
    for product in tqdm(products, desc="Generating product reviews"):
        # Determine number of reviews for this product
        num_reviews = random.randint(min_reviews, max_reviews)
        
        # Stats accumulators
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        keyword_counts = {}
        total_rating = 0
        reviews_batch = []
        
        # Generate reviews for this product
        for _ in range(num_reviews):
            # Generate a review date
            created_at = fake.date_time_between(start_date="-1y", end_date="now")
            review_date = fake.date_time_between(start_date="-1y", end_date=created_at)
            
            # Generate rating based on weights (more positive than negative)
            rating = random.choices([1, 2, 3, 4, 5], weights=config["rating_weights"])[0]
            rating_counts[rating] += 1
            total_rating += rating
            
            # Generate sentiment based on rating
            if rating >= 4:
                sentiment_label = "positive"
                sentiment_score = random.uniform(0.7, 1.0)
                pos_score = sentiment_score
                neg_score = random.uniform(0, 0.1)
            elif rating == 3:
                sentiment_label = "neutral"
                sentiment_score = random.uniform(0.4, 0.6)
                pos_score = random.uniform(0.4, 0.6)
                neg_score = random.uniform(0.1, 0.3)
            else:
                sentiment_label = "negative"
                sentiment_score = random.uniform(0, 0.3)
                pos_score = random.uniform(0, 0.2)
                neg_score = random.uniform(0.7, 0.9)
            
            neu_score = 1.0 - (pos_score + neg_score)
            neu_score = max(0, min(neu_score, 1.0))  # Ensure it's between 0 and 1
            
            sentiment_counts[sentiment_label] += 1
            
            # Generate keywords related to the product category
            category = product.get("category", random.choice(config["categories"]))
            num_keywords = random.randint(
                config["keywords_per_review_min"], 
                config["keywords_per_review_max"]
            )
            
            available_keywords = config["common_keywords"].get(category, ["product", "quality", "price"])
            keywords = []
            
            # Choose some common keywords
            common_keywords_count = min(len(available_keywords), num_keywords - 1)
            if common_keywords_count > 0:
                keywords.extend(random.sample(available_keywords, common_keywords_count))
            
            # Add some random words
            while len(keywords) < num_keywords:
                keywords.append(fake.word())
            
            # Update keyword counts
            for keyword in keywords:
                if keyword in keyword_counts:
                    keyword_counts[keyword] += 1
                else:
                    keyword_counts[keyword] = 1
            
            # Generate review content based on sentiment and keywords
            review_title = generate_review_title(sentiment_label, rating, keywords)
            review_content = generate_review_content(sentiment_label, rating, keywords, category)
            
            # Create the review document
            review = {
                "_id": ObjectId(),
                "product_id": product["_id"],
                "platform_review_id": fake.bothify("R############"),
                "title": review_title,
                "content": review_content,
                "rating": rating,
                "author": fake.name(),
                "date": review_date,
                "verified_purchase": random.random() < config["verified_purchase_ratio"],
                "sentiment": {
                    "label": sentiment_label,
                    "score": sentiment_score,
                    "compound": sentiment_score,  # Simplification
                    "pos": pos_score,
                    "neg": neg_score,
                    "neu": neu_score
                },
                "keywords": keywords,
                "created_at": created_at
            }
            
            reviews_batch.append(review)
        
        # Insert the reviews
        if reviews_batch:
            db.reviews.insert_many(reviews_batch)
            total_reviews += len(reviews_batch)
        
        # Calculate product stats
        avg_rating = total_rating / num_reviews if num_reviews > 0 else 0
        
        # Generate product keywords with sentiment scores
        product_keywords = []
        for keyword, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
            # Calculate a sentiment score for this keyword based on the reviews it appears in
            keyword_sentiment = random.uniform(-0.5, 1.0)  # Simplification
            product_keywords.append({
                "term": keyword,
                "count": count,
                "sentiment_score": keyword_sentiment
            })
        
        # Create update operation for product stats
        product_update = {
            "stats.review_count": num_reviews,
            "stats.avg_rating": round(avg_rating, 2),
            "stats.rating_distribution.1": rating_counts[1],
            "stats.rating_distribution.2": rating_counts[2],
            "stats.rating_distribution.3": rating_counts[3],
            "stats.rating_distribution.4": rating_counts[4],
            "stats.rating_distribution.5": rating_counts[5],
            "stats.sentiment_distribution.positive": sentiment_counts["positive"],
            "stats.sentiment_distribution.neutral": sentiment_counts["neutral"],
            "stats.sentiment_distribution.negative": sentiment_counts["negative"],
            "keywords": product_keywords
        }
        
        product_update_operations.append(
            UpdateOne({"_id": product["_id"]}, {"$set": product_update})
        )
        
        # Execute product update operations in batches
        if len(product_update_operations) >= args.batch_size:
            db.products.bulk_write(product_update_operations)
            product_update_operations = []
    
    # Process any remaining product update operations
    if product_update_operations:
        db.products.bulk_write(product_update_operations)
    
    logger.info(f"Generated {total_reviews} reviews for {len(products)} products")
    return total_reviews

def generate_review_title(sentiment, rating, keywords):
    """Generate a realistic review title based on sentiment and keywords"""
    if sentiment == "positive":
        templates = [
            f"Great {random.choice(keywords)}!",
            f"Excellent {random.choice(keywords)}",
            f"Love the {random.choice(keywords)}",
            f"Best {random.choice(keywords)} ever",
            f"Highly recommend for {random.choice(keywords)}"
        ]
    elif sentiment == "neutral":
        templates = [
            f"Decent {random.choice(keywords)}",
            f"OK {random.choice(keywords)}",
            f"{random.choice(keywords)} is acceptable",
            f"Average {random.choice(keywords)}",
            f"Not bad {random.choice(keywords)}"
        ]
    else:  # negative
        templates = [
            f"Disappointed with {random.choice(keywords)}",
            f"Poor {random.choice(keywords)}",
            f"Issues with {random.choice(keywords)}",
            f"Would not recommend - {random.choice(keywords)} problems",
            f"Terrible {random.choice(keywords)}"
        ]
    
    return random.choice(templates)

def generate_review_content(sentiment, rating, keywords, category):
    """Generate realistic review content based on sentiment, rating, and keywords"""
    # Number of sentences based on rating (higher ratings tend to have longer reviews)
    num_sentences = random.randint(2, 8)
    
    sentences = []
    
    # First sentence based on overall sentiment
    if sentiment == "positive":
        first_sentences = [
            f"I really love this {category} product.",
            f"This is an excellent purchase.",
            f"I'm very satisfied with this product.",
            f"This exceeded my expectations.",
            f"Absolutely fantastic product."
        ]
    elif sentiment == "neutral":
        first_sentences = [
            f"This {category} product is okay.",
            f"It's a decent product for the price.",
            f"Not great, not terrible.",
            f"It does the job, but nothing special.",
            f"It's an average product in this category."
        ]
    else:  # negative
        first_sentences = [
            f"I'm disappointed with this {category} product.",
            f"I expected much better quality.",
            f"This product has several issues.",
            f"I would not recommend this product.",
            f"Not worth the money at all."
        ]
    
    sentences.append(random.choice(first_sentences))
    
    # Add sentences about specific keywords
    used_keywords = set()
    for _ in range(num_sentences - 1):
        # Try to use a keyword that hasn't been used yet
        available_keywords = [k for k in keywords if k not in used_keywords]
        if not available_keywords and keywords:
            available_keywords = keywords
        
        if available_keywords:
            keyword = random.choice(available_keywords)
            used_keywords.add(keyword)
            
            if sentiment == "positive":
                keyword_sentences = [
                    f"The {keyword} is really impressive.",
                    f"I particularly like the {keyword}.",
                    f"The {keyword} feature works perfectly.",
                    f"Great {keyword} compared to other products.",
                    f"The {keyword} is well designed."
                ]
            elif sentiment == "neutral":
                keyword_sentences = [
                    f"The {keyword} is adequate.",
                    f"The {keyword} is nothing special.",
                    f"The {keyword} could be improved.",
                    f"Average {keyword} for this price range.",
                    f"The {keyword} is functional but basic."
                ]
            else:  # negative
                keyword_sentences = [
                    f"The {keyword} is disappointing.",
                    f"There are issues with the {keyword}.",
                    f"The {keyword} is poorly designed.",
                    f"The {keyword} stopped working quickly.",
                    f"The {keyword} doesn't meet expectations."
                ]
            
            sentences.append(random.choice(keyword_sentences))
        else:
            # Generic sentences if we run out of keywords
            generic_sentences = [
                "It arrived on time.",
                "The packaging was good.",
                "Shipping was quick.",
                "The instructions were clear.",
                "It's exactly as described.",
                "I've had it for a few weeks now.",
                "I would buy it again.",
                "It's a good value for the price.",
                "I've tried similar products before."
            ]
            sentences.append(random.choice(generic_sentences))
    
    # Add a concluding sentence
    if sentiment == "positive":
        conclusions = [
            "Overall, I'm very happy with this purchase.",
            "I would definitely recommend this product.",
            "Five stars without hesitation!",
            "I'll definitely buy from this brand again.",
            "Great product for the price!"
        ]
    elif sentiment == "neutral":
        conclusions = [
            "It's an okay product for the price.",
            "I might recommend it with some reservations.",
            "Not sure if I would buy it again.",
            "It serves its purpose, but there are better options.",
            "Consider it if you're on a budget."
        ]
    else:  # negative
        conclusions = [
            "I would not recommend this product.",
            "Save your money and look elsewhere.",
            "I regret this purchase.",
            "I'll be returning this product.",
            "Very disappointed overall."
        ]
    
    sentences.append(random.choice(conclusions))
    
    return " ".join(sentences)

def create_indexes(db):
    """Create necessary indexes for the database"""
    logger.info("Creating MongoDB indexes")
    
    # Indexes for users collection
    db.users.create_index("email", unique=True)
    db.users.create_index("username", unique=True)
    
    # Indexes for products collection
    db.products.create_index([("platform", 1), ("platform_id", 1)], unique=True)
    db.products.create_index("created_by")
    db.products.create_index([("created_at", -1)])
    db.products.create_index("platform")
    db.products.create_index("category")
    
    # Indexes for reviews collection
    db.reviews.create_index("product_id")
    db.reviews.create_index([("product_id", 1), ("sentiment.label", 1)])
    db.reviews.create_index([("product_id", 1), ("rating", 1)])
    db.reviews.create_index([("product_id", 1), ("date", -1)])
    db.reviews.create_index("keywords")
    
    logger.info("MongoDB indexes created successfully")

def main():
    """Main function to generate test data"""
    # Connect to MongoDB
    client, db = connect_to_mongodb(args.mongo_uri, args.db_name)
    
    try:
        # Generate users
        users = generate_users(args.users, db)
        
        # Generate products
        products = generate_products(
            args.products, 
            users, 
            db, 
            DEFAULT_CONFIG["platforms"], 
            DEFAULT_CONFIG["categories"]
        )
        
        # Generate reviews
        total_reviews = generate_reviews(
            products,
            args.min_reviews,
            args.max_reviews,
            db,
            DEFAULT_CONFIG
        )
        
        # Create indexes
        create_indexes(db)
        
        # Print summary
        logger.info(f"Successfully generated test data:")
        logger.info(f"- Users: {len(users)}")
        logger.info(f"- Products: {len(products)}")
        logger.info(f"- Reviews: {total_reviews}")
        logger.info(f"- Database: {args.db_name}")
        
    finally:
        # Close MongoDB connection
        client.close()

if __name__ == "__main__":
    args = parse_arguments()
    main() 