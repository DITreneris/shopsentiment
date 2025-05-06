"""
SQLAlchemy models for Product and Review.
"""

from datetime import datetime
from typing import List, Optional # Added List/Optional for relationships
from sqlalchemy import Integer, String, Float, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

# Import the db object from where it will be initialized (e.g., app_factory or database module)
# We remove the placeholder definition from here.
from .database import db # Example assuming db = SQLAlchemy() is in src/database.py
# If db is initialized directly in app_factory.py, the import path might differ
# Or we might need to pass db into the models definition.
# For now, let's assume it comes from a central place like `src.database`

class Product(db.Model):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asin: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Use Numeric for price to avoid floating point issues, specify precision
    price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Simplified Sentiment fields directly on Product
    overall_sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overall_sentiment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default='neutral')
    positive_reviews_count: Mapped[int] = mapped_column(Integer, default=0)
    neutral_reviews_count: Mapped[int] = mapped_column(Integer, default=0)
    negative_reviews_count: Mapped[int] = mapped_column(Integer, default=0)
    reviews_analyzed_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to reviews (one-to-many)
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Product {self.asin} {self.name}>'


class Review(db.Model):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # Sentiment score for THIS review
    sentiment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # positive/neutral/negative

    # Store original date string if available, otherwise use scraped time
    date_from_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # No updated_at needed for reviews typically

    # Relationship back to product (many-to-one)
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")

    def __repr__(self):
        return f'<Review {self.id} for Product {self.product_id}>'

# Remove Pydantic models if they are no longer needed elsewhere
# class SentimentDistribution(BaseModel):
#     ...
# class SentimentAnalysis(BaseModel):
#     ... 