#!/usr/bin/env python3
"""
Script to verify that all routes in the application are working.
"""

import os
import sys
import requests
from termcolor import colored
from urllib.parse import urljoin
import time

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Base URL
BASE_URL = "http://localhost:5000"

# Routes to test
ROUTES = [
    # Web routes
    {"path": "/", "method": "GET", "expected_status": 200},
    {"path": "/dashboard", "method": "GET", "expected_status": 200},
    {"path": "/about", "method": "GET", "expected_status": 200},
    {"path": "/health", "method": "GET", "expected_status": 200},
    
    # API routes
    {"path": "/api/v1/products", "method": "GET", "expected_status": 200},
    {"path": "/api/v1/sentiment/analyze", "method": "POST", "expected_status": 400},  # Missing text parameter
    
    # Auth routes
    {"path": "/auth/login", "method": "POST", "expected_status": 400},  # Missing credentials
    {"path": "/auth/register", "method": "POST", "expected_status": 400},  # Missing data
    {"path": "/auth/me", "method": "GET", "expected_status": 401},  # Not logged in
]

def test_route(route):
    """Test a single route and return the result."""
    url = f"{BASE_URL}{route['path']}"
    method = route.get('method', 'GET').lower()
    expected_status = route.get('expected_status', 200)
    
    print(f"Testing {method.upper()} {url}...")
    try:
        start_time = time.time()
        if method == 'get':
            response = requests.get(url)
        elif method == 'post':
            response = requests.post(url)
        elif method == 'put':
            response = requests.put(url)
        elif method == 'delete':
            response = requests.delete(url)
        else:
            print(f"Unsupported method: {method}")
            return False
        
        response_time = time.time() - start_time
        
        if response.status_code == expected_status:
            response_time_str = f" in {response_time:.3f}s" if response_time is not None else ""
            print(colored(f"✓ {method.upper()} {url} - {response.status_code}{response_time_str}", "green"))
            return True
        else:
            print(colored(f"✗ {method.upper()} {url} - Expected: {expected_status}, Got: {response.status_code}", "red"))
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to {url}: {e}")
        return False

def main():
    """Main function to verify routes."""
    print(f"Verifying routes at {BASE_URL}...")
    
    successes = 0
    failures = 0
    
    for route in ROUTES:
        path = route["path"]
        method = route["method"]
        expected_status = route["expected_status"]
        
        success = test_route(route)
        
        if success:
            successes += 1
            result = colored("PASS", "green")
        else:
            failures += 1
            result = colored("FAIL", "red")
            
        print(f"{result} - {method} {path} - Expected: {expected_status}")
    
    print(f"\nResults: {successes} passed, {failures} failed")
    
    return failures == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 