#!/usr/bin/env python3
"""
API Test Script for ShopSentiment

This script tests the API endpoints of the ShopSentiment application.
"""

import requests
import json
import sys
import logging
from time import sleep

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API base URL (default to localhost)
BASE_URL = "http://localhost:5000"

def test_health_endpoint():
    """Test the health endpoint."""
    logger.info("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        data = response.json()
        logger.info(f"Health endpoint response: {data}")
        
        assert 'status' in data, "Status field missing in response"
        assert data['status'] == 'healthy', f"Status is not healthy: {data['status']}"
        
        logger.info("✅ Health endpoint test passed!")
        return True
    except Exception as e:
        logger.error(f"❌ Health endpoint test failed: {str(e)}")
        return False

def test_products_endpoint():
    """Test the products API endpoint."""
    logger.info("Testing products endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/products")
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Products endpoint response: {json.dumps(data, indent=2)}")
        
        assert 'products' in data, "Products field missing in response"
        assert isinstance(data['products'], list), "Products is not a list"
        assert len(data['products']) > 0, "Products list is empty"
        
        # Check first product structure
        product = data['products'][0]
        assert 'id' in product, "Product ID missing"
        assert 'name' in product, "Product name missing"
        assert 'sentiment' in product, "Sentiment data missing"
        
        logger.info("✅ Products endpoint test passed!")
        return True
    except Exception as e:
        logger.error(f"❌ Products endpoint test failed: {str(e)}")
        return False

def test_product_detail_endpoint():
    """Test the product detail API endpoint."""
    logger.info("Testing product detail endpoint...")
    try:
        # Get first product from products endpoint
        response = requests.get(f"{BASE_URL}/api/v1/products")
        response.raise_for_status()
        
        products = response.json().get('products', [])
        if not products:
            logger.error("No products found to test product detail endpoint")
            return False
            
        product_id = products[0]['id']
        
        # Test product detail endpoint
        response = requests.get(f"{BASE_URL}/api/v1/products/{product_id}")
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Product detail endpoint response: {json.dumps(data, indent=2)}")
        
        assert 'id' in data, "Product ID missing in detail response"
        assert 'name' in data, "Product name missing in detail response"
        assert 'sentiment' in data, "Sentiment data missing in detail response"
        
        logger.info("✅ Product detail endpoint test passed!")
        return True
    except Exception as e:
        logger.error(f"❌ Product detail endpoint test failed: {str(e)}")
        return False

def test_sentiment_analysis_endpoint():
    """Test the sentiment analysis API endpoint."""
    logger.info("Testing sentiment analysis endpoint...")
    try:
        # Test positive sentiment
        positive_text = "This product is amazing! I love it and would definitely recommend it to everyone. The quality is excellent."
        response = requests.post(
            f"{BASE_URL}/api/v1/analyze",
            json={"text": positive_text}
        )
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Positive sentiment analysis response: {json.dumps(data, indent=2)}")
        
        assert 'sentiment' in data, "Sentiment field missing in response"
        assert 'score' in data['sentiment'], "Sentiment score missing"
        assert 'type' in data['sentiment'], "Sentiment type missing"
        
        # Test negative sentiment
        negative_text = "This product is terrible. It broke after one use and the customer service was awful. I'm very disappointed."
        response = requests.post(
            f"{BASE_URL}/api/v1/analyze",
            json={"text": negative_text}
        )
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Negative sentiment analysis response: {json.dumps(data, indent=2)}")
        
        logger.info("✅ Sentiment analysis endpoint test passed!")
        return True
    except Exception as e:
        logger.error(f"❌ Sentiment analysis endpoint test failed: {str(e)}")
        return False

def main():
    """Main function to run API tests."""
    logger.info(f"Starting API tests against {BASE_URL}")
    
    # Add a short delay to ensure the server is up
    sleep(2)
    
    tests = [
        test_health_endpoint,
        test_products_endpoint,
        test_product_detail_endpoint,
        test_sentiment_analysis_endpoint
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        
        # Add a short delay between tests
        sleep(1)
    
    # Calculate test statistics
    total = len(results)
    passed = results.count(True)
    failed = results.count(False)
    
    # Print summary
    logger.info(f"\nTest Results: {passed}/{total} tests passed, {failed} failed")
    
    # Return exit code based on test results
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    # Allow overriding the base URL
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
    
    sys.exit(main()) 