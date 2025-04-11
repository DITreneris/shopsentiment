"""
Implementation of MongoDB Optimization Plan
- Creates pre-computed collections with proper schema validation
- Adds compound indexes to existing collections
- Implements initial data population for pre-computed statistics
"""

import logging
import time
from datetime import datetime, timedelta
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import OperationFailure, DuplicateKeyError
from bson import ObjectId
import hashlib
import json

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
uri = "mongodb+srv://tomasstaniulis76:JaLhUd1NLZUtwVb5@shop1.11tjwh5.mongodb.net/?retryWrites=true&w=majority&appName=Shop1"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.shopsentiment

class MongoOptimizer:
    """Implements MongoDB optimization strategies."""
    
    def __init__(self, database):
        self.db = database
        
    def create_precomputed_collections(self):
        """Create pre-computed collections with proper schema validation."""
        logger.info("Creating pre-computed collections...")
        
        # Precomputed stats collection - general purpose cache
        try:
            self.db.create_collection("precomputed_stats", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["type", "identifier", "data", "created_at", "updated_at"],
                    "properties": {
                        "type": {
                            "bsonType": "string",
                            "description": "Type of stats (e.g., 'keywords', 'sentiment', 'platform')"
                        },
                        "identifier": {
                            "bsonType": "string",
                            "description": "Unique identifier for this stats record"
                        },
                        "data": {
                            "bsonType": "object",
                            "description": "The pre-computed data"
                        },
                        "created_at": {
                            "bsonType": "date",
                            "description": "When this record was first created"
                        },
                        "updated_at": {
                            "bsonType": "date",
                            "description": "When this record was last updated"
                        },
                        "expires_at": {
                            "bsonType": "date",
                            "description": "When this cache record should expire (optional)"
                        }
                    }
                }
            })
            logger.info("Created precomputed_stats collection")
        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info("precomputed_stats collection already exists")
            else:
                logger.error(f"Error creating precomputed_stats collection: {e}")
        
        # Keywords collection
        try:
            self.db.create_collection("keyword_stats", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["keyword", "count", "sentiment", "updated_at"],
                    "properties": {
                        "keyword": {
                            "bsonType": "string",
                            "description": "The keyword text"
                        },
                        "count": {
                            "bsonType": "int",
                            "description": "Number of occurrences"
                        },
                        "sentiment": {
                            "bsonType": "object",
                            "required": ["score", "label"],
                            "properties": {
                                "score": {
                                    "bsonType": "double",
                                    "description": "Average sentiment score (0-1)"
                                },
                                "label": {
                                    "bsonType": "string",
                                    "enum": ["positive", "neutral", "negative"],
                                    "description": "Sentiment category"
                                }
                            }
                        },
                        "products": {
                            "bsonType": "array",
                            "description": "Array of product IDs where this keyword appears",
                            "items": {
                                "bsonType": "objectId"
                            }
                        },
                        "updated_at": {
                            "bsonType": "date",
                            "description": "When this record was last updated"
                        }
                    }
                }
            })
            logger.info("Created keyword_stats collection")
        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info("keyword_stats collection already exists")
            else:
                logger.error(f"Error creating keyword_stats collection: {e}")
        
        # Time series stats collection
        try:
            self.db.create_collection("time_series_stats", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["product_id", "interval", "data", "updated_at"],
                    "properties": {
                        "product_id": {
                            "bsonType": "objectId",
                            "description": "Product ID this time series belongs to"
                        },
                        "interval": {
                            "bsonType": "string",
                            "enum": ["day", "week", "month"],
                            "description": "Time grouping interval"
                        },
                        "start_date": {
                            "bsonType": "date",
                            "description": "Start date of this time series"
                        },
                        "end_date": {
                            "bsonType": "date",
                            "description": "End date of this time series"
                        },
                        "data": {
                            "bsonType": "array",
                            "description": "Array of time series data points"
                        },
                        "updated_at": {
                            "bsonType": "date",
                            "description": "When this record was last updated"
                        }
                    }
                }
            })
            logger.info("Created time_series_stats collection")
        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info("time_series_stats collection already exists")
            else:
                logger.error(f"Error creating time_series_stats collection: {e}")
        
        # Platform stats collection
        try:
            self.db.create_collection("platform_stats", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["_id", "platforms", "updated_at"],
                    "properties": {
                        "_id": {
                            "bsonType": "string",
                            "description": "Identifier for this stats record"
                        },
                        "platforms": {
                            "bsonType": "object",
                            "description": "Platform-specific statistics"
                        },
                        "period": {
                            "bsonType": "string",
                            "enum": ["all_time", "90_days", "30_days", "7_days"],
                            "description": "Time period for these stats"
                        },
                        "updated_at": {
                            "bsonType": "date",
                            "description": "When this record was last updated"
                        }
                    }
                }
            })
            logger.info("Created platform_stats collection")
        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info("platform_stats collection already exists")
            else:
                logger.error(f"Error creating platform_stats collection: {e}")
        
        # Product comparisons cache collection
        try:
            self.db.create_collection("product_comparisons", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["products", "comparison_data", "updated_at"],
                    "properties": {
                        "products": {
                            "bsonType": "array",
                            "description": "Array of product IDs in this comparison",
                            "items": {
                                "bsonType": "objectId"
                            }
                        },
                        "hash": {
                            "bsonType": "string",
                            "description": "Hash of sorted product IDs for quick lookup"
                        },
                        "comparison_data": {
                            "bsonType": "object",
                            "description": "Pre-computed comparison data"
                        },
                        "view_count": {
                            "bsonType": "int",
                            "description": "Number of times this comparison has been viewed"
                        },
                        "updated_at": {
                            "bsonType": "date",
                            "description": "When this record was last updated"
                        },
                        "expires_at": {
                            "bsonType": "date",
                            "description": "When this cache record should expire"
                        }
                    }
                }
            })
            logger.info("Created product_comparisons collection")
        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info("product_comparisons collection already exists")
            else:
                logger.error(f"Error creating product_comparisons collection: {e}")
    
    def create_indexes(self):
        """Create optimized indexes on collections."""
        logger.info("Creating indexes...")
        
        # Indexes for precomputed_stats
        self.db.precomputed_stats.create_index([("type", 1), ("identifier", 1)], unique=True)
        self.db.precomputed_stats.create_index([("updated_at", 1)])
        self.db.precomputed_stats.create_index([("expires_at", 1)], expireAfterSeconds=0)
        logger.info("Created indexes for precomputed_stats")
        
        # Indexes for keyword_stats
        self.db.keyword_stats.create_index([("keyword", 1)], unique=True)
        self.db.keyword_stats.create_index([("count", -1)])
        self.db.keyword_stats.create_index([("sentiment.label", 1), ("count", -1)])
        self.db.keyword_stats.create_index([("updated_at", 1)])
        logger.info("Created indexes for keyword_stats")
        
        # Indexes for time_series_stats
        self.db.time_series_stats.create_index([("product_id", 1), ("interval", 1)], unique=True)
        self.db.time_series_stats.create_index([("updated_at", 1)])
        logger.info("Created indexes for time_series_stats")
        
        # Indexes for platform_stats
        self.db.platform_stats.create_index([("updated_at", 1)])
        self.db.platform_stats.create_index([("_id", 1), ("period", 1)], unique=True)
        logger.info("Created indexes for platform_stats")
        
        # Indexes for product_comparisons
        self.db.product_comparisons.create_index([("hash", 1)], unique=True)
        self.db.product_comparisons.create_index([("products", 1)])
        self.db.product_comparisons.create_index([("view_count", -1)])
        self.db.product_comparisons.create_index([("updated_at", 1)])
        self.db.product_comparisons.create_index([("expires_at", 1)], expireAfterSeconds=0)
        logger.info("Created indexes for product_comparisons")
        
        # Compound indexes for existing collections
        # Reviews collection
        self.db.reviews.create_index([("product_id", 1), ("date", -1)])
        self.db.reviews.create_index([("product_id", 1), ("sentiment.label", 1)])
        # We don't create a text index here as it requires special handling
        logger.info("Created compound indexes for reviews collection")
        
        # Products collection
        self.db.products.create_index([("platform", 1), ("stats.avg_rating", -1)])
        self.db.products.create_index([("category", 1), ("stats.avg_rating", -1)])
        logger.info("Created compound indexes for products collection")
    
    def populate_keyword_stats(self):
        """Populate keyword_stats collection with pre-computed data."""
        logger.info("Populating keyword_stats collection...")
        start_time = time.time()
        
        # Define the aggregation pipeline for keyword analysis
        pipeline = [
            # Unwind keywords array
            {"$unwind": "$keywords"},
            
            # Group by keyword
            {"$group": {
                "_id": "$keywords",
                "count": {"$sum": 1},
                "avg_sentiment": {"$avg": "$sentiment.score"},
                "products": {"$addToSet": "$product_id"}
            }},
            
            # Filter out uncommon keywords
            {"$match": {
                "count": {"$gte": 5}  # Minimum threshold
            }},
            
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
            
            # Sort by frequency
            {"$sort": {"count": -1}}
        ]
        
        # Execute the pipeline
        keyword_results = list(self.db.reviews.aggregate(pipeline))
        logger.info(f"Found {len(keyword_results)} keywords to store")
        
        # Insert into keyword_stats collection
        now = datetime.utcnow()
        bulk_ops = []
        
        for keyword_data in keyword_results:
            keyword_doc = {
                "keyword": keyword_data["_id"],
                "count": keyword_data["count"],
                "sentiment": {
                    "score": keyword_data["avg_sentiment"],
                    "label": keyword_data["sentiment_label"]
                },
                "products": keyword_data["products"],
                "updated_at": now
            }
            
            # Use upsert to avoid duplicates
            bulk_ops.append({
                "replaceOne": {
                    "filter": {"keyword": keyword_data["_id"]},
                    "replacement": keyword_doc,
                    "upsert": True
                }
            })
            
            # Execute in batches of 100
            if len(bulk_ops) >= 100:
                self.db.keyword_stats.bulk_write(bulk_ops)
                bulk_ops = []
        
        # Insert any remaining operations
        if bulk_ops:
            self.db.keyword_stats.bulk_write(bulk_ops)
        
        elapsed = time.time() - start_time
        logger.info(f"Populated keyword_stats collection in {elapsed:.2f} seconds")
    
    def populate_platform_stats(self):
        """Populate platform_stats collection with pre-computed data."""
        logger.info("Populating platform_stats collection...")
        start_time = time.time()
        
        # Calculate rating distribution by platform
        pipeline = [
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
        
        # Execute the pipeline
        platform_results = list(self.db.products.aggregate(pipeline))
        
        # Process and format the results
        platforms_data = {}
        for item in platform_results:
            platform = item.get('platform', 'unknown')
            platforms_data[platform] = {
                "total_products": item.get("total_products", 0),
                "avg_rating": item.get("avg_rating", 0),
                "rating_distribution": item.get("rating_distribution", {})
            }
        
        # Create the document
        now = datetime.utcnow()
        platform_doc = {
            "_id": "rating_distribution",
            "platforms": platforms_data,
            "period": "all_time",
            "updated_at": now
        }
        
        # Upsert into platform_stats collection
        self.db.platform_stats.replace_one(
            {"_id": "rating_distribution", "period": "all_time"},
            platform_doc,
            upsert=True
        )
        
        elapsed = time.time() - start_time
        logger.info(f"Populated platform_stats collection in {elapsed:.2f} seconds")
    
    def populate_time_series_stats(self, days=90):
        """Populate time_series_stats collection for a sample of products."""
        logger.info("Populating time_series_stats collection for sample products...")
        start_time = time.time()
        
        # Get a sample of products (limited to 20 for initial setup)
        product_sample = list(self.db.products.find().limit(20))
        
        now = datetime.utcnow()
        start_date = now - timedelta(days=days)
        
        # For each product, calculate sentiment over time
        for product in product_sample:
            product_id = product["_id"]
            
            # Calculate daily sentiment
            self._calculate_time_series(product_id, "day", start_date, now)
            
            # Calculate weekly sentiment
            self._calculate_time_series(product_id, "week", start_date, now)
            
            # For monthly, we might want more history, but we'll use the same range for consistency
            self._calculate_time_series(product_id, "month", start_date, now)
        
        elapsed = time.time() - start_time
        logger.info(f"Populated time_series_stats for {len(product_sample)} products in {elapsed:.2f} seconds")
    
    def _calculate_time_series(self, product_id, interval, start_date, end_date):
        """Calculate and store time series data for a product with specified interval."""
        # Define date grouping format based on interval
        if interval == 'day':
            date_group = {
                "year": {"$year": "$date"},
                "month": {"$month": "$date"},
                "day": {"$dayOfMonth": "$date"}
            }
            date_format = "%Y-%m-%d"
        elif interval == 'week':
            date_group = {
                "year": {"$year": "$date"},
                "week": {"$week": "$date"}
            }
            date_format = "Week %U, %Y"
        else:  # month
            date_group = {
                "year": {"$year": "$date"},
                "month": {"$month": "$date"}
            }
            date_format = "%Y-%m"
        
        # Aggregation pipeline for sentiment over time
        pipeline = [
            # Match reviews for this product in date range
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
            
            # Add formatted date string
            {"$addFields": {
                "date_str": {
                    "$dateToString": {
                        "format": date_format,
                        "date": {
                            "$dateFromParts": {
                                "year": "$_id.year",
                                "month": {"$ifNull": ["$_id.month", 1]},
                                "day": {"$ifNull": ["$_id.day", 1]}
                            }
                        }
                    }
                }
            }},
            
            # Sort by date
            {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}}
        ]
        
        # Execute the pipeline
        results = list(self.db.reviews.aggregate(pipeline))
        
        # Transform data for storage
        time_series_data = []
        for item in results:
            date_parts = item["_id"]
            date_obj = datetime(
                year=date_parts["year"],
                month=date_parts.get("month", 1),
                day=date_parts.get("day", 1)
            )
            
            # Convert sentiments array to object
            sentiments_dict = {}
            for sentiment_entry in item["sentiments"]:
                sentiments_dict[sentiment_entry["k"]] = sentiment_entry["v"]
            
            # Add percentages
            total = item["total"]
            if total > 0:
                for label in ["positive", "negative", "neutral"]:
                    if label in sentiments_dict:
                        sentiments_dict[label]["percentage"] = round(
                            (sentiments_dict[label]["count"] / total) * 100, 1
                        )
            
            time_series_data.append({
                "date": date_obj,
                "date_str": item["date_str"],
                "sentiments": sentiments_dict,
                "total": total
            })
        
        # Store in time_series_stats collection
        now = datetime.utcnow()
        self.db.time_series_stats.update_one(
            {"product_id": product_id, "interval": interval},
            {
                "$set": {
                    "product_id": product_id,
                    "interval": interval,
                    "start_date": start_date,
                    "end_date": end_date,
                    "data": time_series_data,
                    "updated_at": now
                }
            },
            upsert=True
        )
    
    def run_all_optimizations(self):
        """Run all optimization steps."""
        logger.info("Starting MongoDB optimization implementation")
        
        # Create collections
        self.create_precomputed_collections()
        
        # Create indexes
        self.create_indexes()
        
        # Populate pre-computed collections
        self.populate_keyword_stats()
        self.populate_platform_stats()
        self.populate_time_series_stats()
        
        logger.info("MongoDB optimization implementation completed")

def main():
    """Main function to run MongoDB optimizations."""
    try:
        optimizer = MongoOptimizer(db)
        optimizer.run_all_optimizations()
    except Exception as e:
        logger.error(f"Error during optimization: {e}", exc_info=True)

if __name__ == "__main__":
    main() 