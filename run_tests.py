#!/usr/bin/env python
"""
ShopSentiment Test Runner

This script runs all tests for the ShopSentiment application and generates
a coverage report.
"""

import unittest
import sys
import os
import subprocess

try:
    import coverage
except ImportError:
    print("Coverage module not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "coverage"])
    import coverage

def run_python_tests():
    """Run all Python unit and integration tests"""
    # Start coverage monitoring
    cov = coverage.Coverage(
        source=['app.py', 'app/'],
        omit=['*/tests/*', '*/test_*', '*/venv/*', '*/shopenv/*']
    )
    cov.start()

    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover('.', pattern='test_*.py')
    
    print("\n" + "="*50)
    print("Running Python tests...")
    print("="*50)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Stop coverage monitoring
    cov.stop()
    cov.save()
    
    # Generate coverage report
    print("\n" + "="*50)
    print("Python Test Coverage Report")
    print("="*50)
    cov.report()
    
    # Generate HTML report
    cov.html_report(directory='coverage_html')
    print(f"\nDetailed HTML coverage report: {os.path.abspath('coverage_html/index.html')}")
    
    return result.wasSuccessful()

def run_js_tests():
    """Run JavaScript tests using Node.js if available"""
    print("\n" + "="*50)
    print("Running JavaScript tests...")
    print("="*50)
    
    try:
        # Check if Node.js is available
        subprocess.check_call(["node", "--version"], stdout=subprocess.PIPE)
        
        # Run the JavaScript tests
        result = subprocess.run(["node", "test_client_cache.js"], capture_output=True, text=True)
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"JavaScript tests failed with error code {result.returncode}")
            print(f"Error: {result.stderr}")
            return False
        
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Node.js not found or error running JavaScript tests.")
        print("To run JavaScript tests, please install Node.js and try again.")
        print("JavaScript tests skipped.")
        return True  # Don't fail overall testing if JS environment is not available

def main():
    """Run all tests and report results"""
    print("\n" + "="*50)
    print("ShopSentiment Test Runner")
    print("="*50)
    
    # Make sure the current directory is in the Python path
    sys.path.insert(0, os.path.abspath('.'))
    
    # Run all tests
    python_success = run_python_tests()
    js_success = run_js_tests()
    
    # Report overall status
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    print(f"Python Tests: {'PASSED' if python_success else 'FAILED'}")
    print(f"JavaScript Tests: {'PASSED' if js_success else 'FAILED'}")
    print("-"*50)
    overall = python_success and js_success
    print(f"Overall Status: {'PASSED' if overall else 'FAILED'}")
    
    # Return appropriate exit code
    return 0 if overall else 1

if __name__ == "__main__":
    sys.exit(main()) 