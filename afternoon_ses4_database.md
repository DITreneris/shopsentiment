# Database Integration Implementation Plan

## Overview
This document outlines the detailed implementation plan for integrating MongoDB with the ShopSentiment application, focusing on data models, connection management, and data access patterns.

## 1. MongoDB Configuration

```python
# config/database.py
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_DB = os.environ.get('MONGODB_DB', 'shopsentiment')
MONGODB_USER = os.environ.get('MONGODB_USER')
MONGODB_PASS = os.environ.get('MONGODB_PASS')

def get_mongodb_client():
    """Create and return MongoDB client with proper configuration."""
    try:
        client = MongoClient(
            MONGODB_URI,
            username=MONGODB_USER,
            password=MONGODB_PASS,
            serverSelectionTimeoutMS=5000
        )
        # Test the connection
        client.admin.command('ping')
        return client
    except ConnectionFailure as e:
        raise Exception(f"Failed to connect to MongoDB: {str(e)}")
```

## 2. Data Models

```python
# models/product.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class Review(BaseModel):
    id: str
    text: str
    rating: float
    sentiment_score: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    reviews: List[Review] = []
    average_sentiment: float = 0.0
    total_reviews: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
```

## 3. Data Access Layer

```python
# dal/product_dal.py
from typing import List, Optional
from datetime import datetime
from pymongo import MongoClient
from models.product import Product, Review

class ProductDAL:
    def __init__(self, client: MongoClient):
        self.db = client[MONGODB_DB]
        self.products = self.db.products
        
    async def get_product(self, product_id: str) -> Optional[Product]:
        """Retrieve a product by ID."""
        product_data = await self.products.find_one({"_id": product_id})
        return Product(**product_data) if product_data else None
        
    async def get_products(self, skip: int = 0, limit: int = 10) -> List[Product]:
        """Retrieve multiple products with pagination."""
        cursor = self.products.find().skip(skip).limit(limit)
        return [Product(**doc) for doc in await cursor.to_list(length=limit)]
        
    async def add_review(self, product_id: str, review: Review) -> bool:
        """Add a review to a product and update its statistics."""
        result = await self.products.update_one(
            {"_id": product_id},
            {
                "$push": {"reviews": review.dict()},
                "$inc": {"total_reviews": 1},
                "$set": {
                    "updated_at": datetime.utcnow(),
                    "average_sentiment": self._calculate_new_average(product_id, review)
                }
            }
        )
        return result.modified_count > 0
        
    def _calculate_new_average(self, product_id: str, new_review: Review) -> float:
        """Calculate new average sentiment after adding a review."""
        product = self.get_product(product_id)
        if not product:
            return new_review.sentiment_score
            
        total_sentiment = sum(r.sentiment_score for r in product.reviews)
        total_sentiment += new_review.sentiment_score
        return total_sentiment / (len(product.reviews) + 1)
```

## 4. Integration with Application

```python
# app.py
from config.database import get_mongodb_client
from dal.product_dal import ProductDAL

def create_app():
    app = Flask(__name__)
    
    # Initialize MongoDB connection
    try:
        client = get_mongodb_client()
        app.mongodb_client = client
        app.product_dal = ProductDAL(client)
    except Exception as e:
        app.logger.error(f"Failed to initialize MongoDB: {str(e)}")
        raise
        
    @app.teardown_appcontext
    def close_mongodb_connection(exception=None):
        """Close MongoDB connection when application context ends."""
        if hasattr(app, 'mongodb_client'):
            app.mongodb_client.close()
            
    # API Routes
    @app.route('/api/v1/products', methods=['GET'])
    async def get_products():
        try:
            products = await app.product_dal.get_products()
            return jsonify([p.dict() for p in products])
        except Exception as e:
            app.logger.error(f"Error fetching products: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500
            
    return app
```

## 5. Indexes and Performance Optimization

```python
# scripts/create_indexes.py
from config.database import get_mongodb_client

def create_indexes():
    client = get_mongodb_client()
    db = client[MONGODB_DB]
    
    # Create indexes for common queries
    db.products.create_index("name")
    db.products.create_index("average_sentiment")
    db.products.create_index("total_reviews")
    db.products.create_index([("reviews.created_at", -1)])
    
    # Text index for search
    db.products.create_index([
        ("name", "text"),
        ("description", "text")
    ])
```

## 6. Data Migration

```python
# scripts/migrate_data.py
from config.database import get_mongodb_client
from models.product import Product

def migrate_mock_data():
    """Migrate mock data to MongoDB."""
    client = get_mongodb_client()
    db = client[MONGODB_DB]
    
    # Example migration of mock products
    mock_products = [...]  # Your mock data
    
    for product_data in mock_products:
        product = Product(**product_data)
        db.products.insert_one(product.dict())
```

## 7. Testing Strategy

1. **Unit Tests**:
   - Test ProductDAL methods
   - Test data model validation
   - Test connection handling

2. **Integration Tests**:
   - Test API endpoints with MongoDB
   - Test data consistency
   - Test error handling

3. **Performance Tests**:
   - Test query performance
   - Test concurrent access
   - Test connection pooling

## 8. Monitoring & Maintenance

1. **Set up monitoring for**:
   - Connection pool usage
   - Query performance
   - Index usage
   - Storage growth

2. **Regular maintenance tasks**:
   - Index optimization
   - Data cleanup
   - Connection health checks

## 9. Documentation

1. **Developer Documentation**:
   - Data model structure
   - Query patterns
   - Error handling
   - Performance optimization tips

2. **Operations Documentation**:
   - MongoDB setup
   - Backup procedures
   - Scaling guidelines
   - Troubleshooting guide 