"""
Add Text Indexes for Keyword Search Operations

This script adds text indexes to the MongoDB reviews collection for efficient
keyword searching and implements a test function to verify the performance
improvement.
"""

import logging
import time
from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import OperationFailure

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mongodb_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# MongoDB connection
uri = "mongodb+srv://tomasstaniulis76:JaLhUd1NLZUtwVb5@shop1.11tjwh5.mongodb.net/?retryWrites=true&w=majority&appName=Shop1"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.shopsentiment

def add_text_indexes():
    """Add text indexes for efficient keyword searching."""
    try:
        logger.info("Adding text index to reviews collection...")
        
        # Create text index on the content field and keywords array
        db.reviews.create_index(
            [("content", "text"), ("keywords", "text")],
            weights={"content": 1, "keywords": 10},
            name="reviews_text_search"
        )
        logger.info("Successfully created text index on reviews collection")
        
        # Create text index on product name and description
        db.products.create_index(
            [("name", "text"), ("description", "text")],
            weights={"name": 10, "description": 5},
            name="products_text_search"
        )
        logger.info("Successfully created text index on products collection")
        
        return True
    except OperationFailure as e:
        if "already exists" in str(e):
            logger.info("Text indexes already exist, skipping creation")
            return True
        else:
            logger.error(f"Error creating text indexes: {e}")
            return False

def test_text_search_performance():
    """Test performance of text search with new indexes."""
    # Test keywords to search for
    test_keywords = ["great", "terrible", "excellent", "disappointed", "recommend"]
    
    results = {}
    
    for keyword in test_keywords:
        logger.info(f"Testing search for keyword: {keyword}")
        
        # Measure performance of text search
        start_time = time.time()
        text_search_results = list(db.reviews.find(
            {"$text": {"$search": keyword}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(20))
        text_search_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Measure performance of regular expression search (without text index)
        start_time = time.time()
        regex_search_results = list(db.reviews.find(
            {"content": {"$regex": keyword, "$options": "i"}}
        ).limit(20))
        regex_search_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Compare results
        improvement = ((regex_search_time - text_search_time) / regex_search_time) * 100
        
        results[keyword] = {
            "text_search_time_ms": round(text_search_time, 2),
            "regex_search_time_ms": round(regex_search_time, 2),
            "improvement_percentage": round(improvement, 2),
            "text_results_count": len(text_search_results),
            "regex_results_count": len(regex_search_results)
        }
        
        logger.info(f"Keyword: {keyword}")
        logger.info(f"  Text search: {text_search_time:.2f}ms for {len(text_search_results)} results")
        logger.info(f"  Regex search: {regex_search_time:.2f}ms for {len(regex_search_results)} results")
        logger.info(f"  Improvement: {improvement:.2f}%")
    
    return results

def main():
    """Main function to add text indexes and test performance."""
    logger.info("Starting text index optimization")
    
    # Add text indexes
    success = add_text_indexes()
    if not success:
        logger.error("Failed to add text indexes, exiting")
        return
    
    # Test performance
    logger.info("Testing text search performance...")
    results = test_text_search_performance()
    
    # Print summary
    logger.info("Text Search Performance Summary:")
    for keyword, data in results.items():
        logger.info(f"Keyword: {keyword}")
        logger.info(f"  Text search: {data['text_search_time_ms']}ms")
        logger.info(f"  Regex search: {data['regex_search_time_ms']}ms")
        logger.info(f"  Improvement: {data['improvement_percentage']}%")
    
    logger.info("Text index optimization completed")

if __name__ == "__main__":
    main() 