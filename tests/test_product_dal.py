"""
Unit tests for the ProductDAL class.
"""

import pytest
import os
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add the parent directory to the Python path to import the application modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.product_dal import ProductDAL
from src.models.product import Product, Review, SentimentAnalysis


@pytest.fixture
def mock_db():
    """Create a mock database with collections for testing."""
    mock_db = MagicMock()
    mock_db.products = MagicMock()
    mock_db.reviews = MagicMock()
    return mock_db


@pytest.fixture
def product_dal(mock_db):
    """Create a ProductDAL instance with mocked database for testing."""
    with patch('src.database.product_dal.get_database', return_value=mock_db):
        product_dal = ProductDAL()
        return product_dal


@pytest.fixture
def sample_product():
    """Create a sample product for testing."""
    return Product(
        id="1",
        name="Test Product",
        description="A test product for unit testing",
        price=99.99,
        category="Test"
    )


@pytest.fixture
def sample_review():
    """Create a sample review for testing."""
    return Review(
        id="101",
        text="This is a test review",
        rating=4.5,
        sentiment_score=0.8,
        user="TestUser",
        date="2023-12-01"
    )


class TestProductDAL:
    """Test cases for the ProductDAL class."""

    def test_init_creates_indexes(self, product_dal, mock_db):
        """Test that indexes are created during initialization."""
        # Check that product indexes were created
        mock_db.products.create_index.assert_any_call("name")
        mock_db.products.create_index.assert_any_call([("name", "text"), ("description", "text")])
        mock_db.products.create_index.assert_any_call("sentiment.score")
        mock_db.products.create_index.assert_any_call("sentiment.reviews_count")
        
        # Check that review indexes were created
        mock_db.reviews.create_index.assert_any_call("product_id")
        mock_db.reviews.create_index.assert_any_call("sentiment_score")
        mock_db.reviews.create_index.assert_any_call("created_at")

    @pytest.mark.asyncio
    async def test_get_product_returns_product_with_reviews(self, product_dal, mock_db):
        """Test that get_product returns a product with its reviews."""
        # Setup
        product_id = "1"
        product_data = {
            "_id": product_id,
            "name": "Test Product",
            "description": "Test Description",
            "price": 99.99
        }
        reviews_data = [
            {"_id": "101", "text": "Great product", "rating": 5.0, "sentiment_score": 0.9},
            {"_id": "102", "text": "Good product", "rating": 4.0, "sentiment_score": 0.7}
        ]
        
        # Mock the find_one method to return the product data
        mock_db.products.find_one = MagicMock(return_value=product_data)
        
        # Mock the reviews cursor
        mock_cursor = MagicMock()
        mock_cursor.to_list = MagicMock(return_value=reviews_data)
        mock_db.reviews.find = MagicMock(return_value=mock_cursor)
        
        # Execute
        result = await product_dal.get_product(product_id)
        
        # Assert
        assert result is not None
        assert result["_id"] == product_id
        assert result["name"] == "Test Product"
        assert "reviews" in result
        assert len(result["reviews"]) == 2
        
        # Verify the correct methods were called
        mock_db.products.find_one.assert_called_once_with({"_id": product_id})
        mock_db.reviews.find.assert_called_once_with({"product_id": product_id})

    @pytest.mark.asyncio
    async def test_create_product(self, product_dal, mock_db, sample_product):
        """Test creating a new product."""
        # Setup
        mock_result = MagicMock()
        mock_result.inserted_id = "1"
        mock_db.products.insert_one.return_value = mock_result
        
        # Execute
        result = await product_dal.create_product(sample_product)
        
        # Assert
        assert result == "1"
        mock_db.products.insert_one.assert_called_once()
        
        # Check the arguments passed to insert_one
        args, _ = mock_db.products.insert_one.call_args
        inserted_data = args[0]
        assert inserted_data["name"] == sample_product.name
        assert inserted_data["description"] == sample_product.description
        assert inserted_data["price"] == sample_product.price
        assert inserted_data["category"] == sample_product.category
        assert "_id" in inserted_data

    @pytest.mark.asyncio
    async def test_update_product(self, product_dal, mock_db):
        """Test updating a product."""
        # Setup
        product_id = "1"
        update_data = {
            "name": "Updated Product Name",
            "price": 129.99
        }
        
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_db.products.update_one.return_value = mock_result
        
        # Execute
        result = await product_dal.update_product(product_id, update_data)
        
        # Assert
        assert result is True
        mock_db.products.update_one.assert_called_once()
        
        # Check the arguments passed to update_one
        args, kwargs = mock_db.products.update_one.call_args
        filter_dict, update_dict = args
        assert filter_dict == {"_id": product_id}
        assert "name" in update_dict["$set"]
        assert "price" in update_dict["$set"]
        assert "updated_at" in update_dict["$set"]

    @pytest.mark.asyncio
    async def test_delete_product(self, product_dal, mock_db):
        """Test deleting a product and its reviews."""
        # Setup
        product_id = "1"
        
        mock_product_result = MagicMock()
        mock_product_result.deleted_count = 1
        mock_db.products.delete_one.return_value = mock_product_result
        
        mock_review_result = MagicMock()
        mock_review_result.deleted_count = 2
        mock_db.reviews.delete_many.return_value = mock_review_result
        
        # Execute
        result = await product_dal.delete_product(product_id)
        
        # Assert
        assert result is True
        mock_db.products.delete_one.assert_called_once_with({"_id": product_id})
        mock_db.reviews.delete_many.assert_called_once_with({"product_id": product_id})

    @pytest.mark.asyncio
    async def test_add_review(self, product_dal, mock_db, sample_review):
        """Test adding a review to a product."""
        # Setup
        product_id = "1"
        product_data = {
            "_id": product_id,
            "name": "Test Product",
            "description": "Test Description",
            "price": 99.99,
            "sentiment": {
                "score": 0.7,
                "type": "positive",
                "reviews_count": 1
            }
        }
        
        # Mock the product retrieval
        product_dal.get_product = MagicMock(return_value=product_data)
        
        # Mock the sentiment calculation
        sentiment_data = {
            "score": 0.75,
            "type": "positive",
            "reviews_count": 2,
            "distribution": {
                "positive": 0.8,
                "neutral": 0.2,
                "negative": 0.0
            }
        }
        product_dal._calculate_product_sentiment = MagicMock(return_value=sentiment_data)
        
        # Execute
        result = await product_dal.add_review(product_id, sample_review)
        
        # Assert
        assert result is True
        mock_db.reviews.insert_one.assert_called_once()
        
        # Check the arguments passed to insert_one
        args, _ = mock_db.reviews.insert_one.call_args
        inserted_data = args[0]
        assert inserted_data["text"] == sample_review.text
        assert inserted_data["rating"] == sample_review.rating
        assert inserted_data["sentiment_score"] == sample_review.sentiment_score
        assert inserted_data["product_id"] == product_id
        
        # Check the product update
        mock_db.products.update_one.assert_called_once()
        args, _ = mock_db.products.update_one.call_args
        filter_dict, update_dict = args
        assert filter_dict == {"_id": product_id}
        assert update_dict["$set"]["sentiment"] == sentiment_data 