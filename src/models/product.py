"""
Product and Review models for the ShopSentiment application.
These models define the data structure for products and reviews.
"""

from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class Review(BaseModel):
    """Model representing a product review with sentiment analysis."""
    id: str
    text: str
    rating: float
    sentiment_score: float
    user: Optional[str] = None
    date: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class SentimentDistribution(BaseModel):
    """Model representing sentiment distribution statistics."""
    positive: float = 0.0
    neutral: float = 0.0
    negative: float = 0.0


class SentimentAnalysis(BaseModel):
    """Model representing sentiment analysis results for a product."""
    score: float = 0.0
    type: str = "neutral"
    reviews_count: int = 0
    distribution: SentimentDistribution = Field(default_factory=SentimentDistribution)


class Product(BaseModel):
    """Model representing a product with sentiment analysis data."""
    id: str
    name: str
    description: str
    price: float
    category: Optional[str] = None
    reviews: List[Review] = []
    sentiment: SentimentAnalysis = Field(default_factory=SentimentAnalysis)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        } 