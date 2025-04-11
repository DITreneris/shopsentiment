#!/usr/bin/env python
"""
MongoDB Performance Test Executor
Runs the data generation and load testing scripts in sequence with various configurations
"""

import os
import sys
import time
import json
import argparse
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mongodb_performance_test.log')
    ]
)
logger = logging.getLogger(__name__)

def execute_command(command, description):
    """Execute a shell command and log the output"""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {command}")
    
    start_time = time.time()
    process = subprocess.Popen(
        command, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Process output in real-time
    for line in process.stdout:
        line = line.strip()
        if line:
            logger.info(f"OUT: {line}")
    
    # Get any remaining output
    stdout, stderr = process.communicate()
    
    if stdout:
        for line in stdout.strip().split('\n'):
            if line:
                logger.info(f"OUT: {line}")
    
    if stderr:
        for line in stderr.strip().split('\n'):
            if line:
                logger.error(f"ERR: {line}")
    
    exit_code = process.returncode
    duration = time.time() - start_time
    
    logger.info(f"Command completed with exit code {exit_code} in {duration:.2f} seconds")
    
    return {
        "command": command,
        "description": description,
        "exit_code": exit_code,
        "duration": duration,
        "stderr": stderr
    }

def generate_test_data(args):
    """Generate test data with various configurations"""
    results = []
    
    # Small dataset for initial testing
    small_dataset_cmd = f"python scripts/load_test_data_generator.py --users 10 --products 3 --reviews 50 {args.clear_arg}"
    results.append(execute_command(small_dataset_cmd, "Generating small test dataset"))
    
    if args.skip_large:
        logger.info("Skipping large dataset generation as requested")
    else:
        # Production-scale dataset
        prod_dataset_cmd = f"python scripts/load_test_data_generator.py --users 50 --products 5 --reviews 100"
        results.append(execute_command(prod_dataset_cmd, "Generating production-scale dataset"))
        
        # 10x dataset for stress testing (only if explicitly requested)
        if args.generate_10x:
            large_dataset_cmd = f"python scripts/load_test_data_generator.py --users 100 --products 5 --reviews 200"
            results.append(execute_command(large_dataset_cmd, "Generating 10x production volume dataset"))
    
    return results

def run_load_tests(args):
    """Run load tests with various configurations"""
    results = []
    
    # Basic direct test
    basic_test_cmd = "python scripts/run_load_test.py --direct --duration 30 --users 5"
    results.append(execute_command(basic_test_cmd, "Running basic load test (5 users, 30 seconds)"))
    
    if args.skip_extended:
        logger.info("Skipping extended load tests as requested")
    else:
        # Medium load test
        medium_test_cmd = "python scripts/run_load_test.py --direct --duration 60 --users 10"
        results.append(execute_command(medium_test_cmd, "Running medium load test (10 users, 60 seconds)"))
        
        # Heavy load test (only if explicitly requested)
        if args.run_heavy:
            heavy_test_cmd = "python scripts/run_load_test.py --direct --duration 120 --users 20"
            results.append(execute_command(heavy_test_cmd, "Running heavy load test (20 users, 120 seconds)"))
    
    return results

def test_aggregation_pipelines(args):
    """Test the aggregation pipeline performance"""
    # Create a simple test script for measuring aggregation performance
    test_script = """
import os
import sys
import time
import logging
from dotenv import load_dotenv
from flask import Flask
from pymongo import MongoClient
from bson import ObjectId

# Add parent directory to path to import the aggregation utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "shopsentiment")

def test_aggregation_performance():
    # Create a Flask app context for testing
    app = Flask(__name__)
    
    with app.app_context():
        # Import the aggregation utilities
        try:
            from app.utils.mongodb_aggregations import AggregationPipelines
            logger.info("Successfully imported AggregationPipelines")
        except ImportError as e:
            logger.error(f"Failed to import AggregationPipelines: {e}")
            return
        
        # Connect to MongoDB
        try:
            client = MongoClient(MONGODB_URI)
            db = client[MONGODB_DB_NAME]
            
            # Make the database available to the current app
            app.mongodb = db
            
            logger.info(f"Connected to MongoDB. Database: {MONGODB_DB_NAME}")
            
            # Get a sample product to test with
            sample_product = db.products.find_one()
            if not sample_product:
                logger.warning("No products found in database")
                return
            
            product_id = sample_product["_id"]
            logger.info(f"Using product: {product_id}")
            
            # Test the sentiment over time aggregation
            start_time = time.time()
            sentiment_data = AggregationPipelines.sentiment_over_time(product_id)
            duration = time.time() - start_time
            logger.info(f"Sentiment over time: {len(sentiment_data)} data points in {duration:.2f} seconds")
            
            # Test the rating distribution by platform
            start_time = time.time()
            platform_data = AggregationPipelines.rating_distribution_by_platform()
            duration = time.time() - start_time
            logger.info(f"Rating distribution by platform: {len(platform_data)} platforms in {duration:.2f} seconds")
            
            # Test the keyword sentiment analysis
            start_time = time.time()
            keyword_data = AggregationPipelines.keyword_sentiment_analysis(min_count=5)
            duration = time.time() - start_time
            logger.info(f"Keyword sentiment analysis: {len(keyword_data)} keywords in {duration:.2f} seconds")
            
            # Test the product comparison
            # Find a few products to compare
            product_ids = [doc["_id"] for doc in db.products.find().limit(3)]
            
            start_time = time.time()
            comparison_data = AggregationPipelines.product_comparison(product_ids)
            duration = time.time() - start_time
            logger.info(f"Product comparison: {len(comparison_data)} products in {duration:.2f} seconds")
            
            # Create precomputed statistics
            start_time = time.time()
            success = AggregationPipelines.create_precomputed_stats_collection()
            duration = time.time() - start_time
            logger.info(f"Creating precomputed stats collection: {success} in {duration:.2f} seconds")
            
            # Store some precomputed stats
            if success:
                start_time = time.time()
                save_success = AggregationPipelines.store_precomputed_stats(
                    "sentiment_trend", 
                    str(product_id), 
                    sentiment_data
                )
                duration = time.time() - start_time
                logger.info(f"Storing precomputed stats: {save_success} in {duration:.2f} seconds")
                
                # Retrieve precomputed stats
                start_time = time.time()
                retrieved_data = AggregationPipelines.get_precomputed_stats(
                    "sentiment_trend", 
                    str(product_id)
                )
                duration = time.time() - start_time
                logger.info(f"Retrieving precomputed stats: {retrieved_data is not None} in {duration:.2f} seconds")
            
            # Close MongoDB connection
            client.close()
            logger.info("MongoDB connection closed")
        
        except Exception as e:
            logger.error(f"Error during aggregation testing: {e}")

if __name__ == "__main__":
    test_aggregation_performance()
"""
    
    # Write the test script to a file
    with open("scripts/test_aggregation_performance.py", "w") as f:
        f.write(test_script)
    
    # Execute the test script
    return execute_command("python scripts/test_aggregation_performance.py", "Testing aggregation pipeline performance")

def enable_dashboard(args):
    """Enable and initialize the dashboard with precomputed stats"""
    results = []
    
    # Run the dashboard initialization script
    dashboard_cmd = "python scripts/enable_dashboard.py"
    results.append(execute_command(dashboard_cmd, "Initializing dashboard with precomputed stats"))
    
    return results

def generate_performance_report(data_generation_results, load_test_results, aggregation_test_result, dashboard_results=None):
    """Generate a markdown report of the performance test results"""
    report = []
    
    # Add report header
    report.append("# MongoDB Performance Test Report")
    report.append(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Add data generation results
    report.append("## Data Generation Results")
    if data_generation_results:
        for result in data_generation_results:
            report.append(f"\n### {result['description']}")
            report.append(f"- Duration: {result['duration']:.2f} seconds")
            report.append(f"- Exit Code: {result['exit_code']}")
            if result['exit_code'] != 0:
                report.append(f"- Error: {result['stderr']}")
    else:
        report.append("\nData generation step was skipped.")
    
    # Add load test results
    report.append("\n## Load Test Results")
    if load_test_results:
        for result in load_test_results:
            report.append(f"\n### {result['description']}")
            report.append(f"- Duration: {result['duration']:.2f} seconds")
            report.append(f"- Exit Code: {result['exit_code']}")
            if result['exit_code'] != 0:
                report.append(f"- Error: {result['stderr']}")
    else:
        report.append("\nLoad testing step was skipped.")
    
    # Add aggregation test results
    report.append("\n## Aggregation Pipeline Performance")
    if aggregation_test_result:
        report.append(f"\n### {aggregation_test_result['description']}")
        report.append(f"- Duration: {aggregation_test_result['duration']:.2f} seconds")
        report.append(f"- Exit Code: {aggregation_test_result['exit_code']}")
        if aggregation_test_result['exit_code'] != 0:
            report.append(f"- Error: {aggregation_test_result['stderr']}")
    else:
        report.append("\nAggregation pipeline testing step was skipped.")
    
    # Add dashboard initialization results if available
    if dashboard_results:
        report.append("\n## Dashboard Initialization Results")
        for result in dashboard_results:
            report.append(f"\n### {result['description']}")
            report.append(f"- Duration: {result['duration']:.2f} seconds")
            report.append(f"- Exit Code: {result['exit_code']}")
            if result['exit_code'] != 0:
                report.append(f"- Error: {result['stderr']}")
    
    # Add recommendations section
    report.append("\n## Performance Recommendations")
    report.append("\nBased on the test results, consider the following recommendations:")
    report.append("\n1. **Database Indexing**: Ensure all queried fields are properly indexed")
    report.append("2. **Connection Pooling**: Optimize connection pool size based on concurrency requirements")
    report.append("3. **Query Optimization**: Review and optimize slow queries identified in the tests")
    report.append("4. **Caching Strategy**: Implement Redis caching for frequently accessed data and aggregation results")
    report.append("5. **Data Validation**: Consider moving non-critical data validation to background processes")
    
    if dashboard_results:
        report.append("6. **Dashboard Performance**: Monitor dashboard precomputed stats freshness and update frequency")
    
    return "\n".join(report)

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="MongoDB Performance Test Suite")
    parser.add_argument("--skip-data-generation", action="store_true", help="Skip the data generation step")
    parser.add_argument("--skip-load-tests", action="store_true", help="Skip the load testing step")
    parser.add_argument("--skip-aggregation-tests", action="store_true", help="Skip the aggregation pipeline tests")
    parser.add_argument("--generate-10x", action="store_true", help="Generate 10x production volume dataset")
    parser.add_argument("--run-heavy", action="store_true", help="Run heavy load tests")
    parser.add_argument("--skip-large", action="store_true", help="Skip large dataset generation")
    parser.add_argument("--skip-extended", action="store_true", help="Skip extended load tests")
    parser.add_argument("--clear", action="store_true", help="Clear existing collections before data generation")
    parser.add_argument("--report", type=str, default="mongodb_performance_report.md", help="Output report file")
    parser.add_argument("--enable-dashboard", action="store_true", help="Initialize dashboard with precomputed stats")
    
    args = parser.parse_args()
    args.clear_arg = "--clear" if args.clear else ""
    
    # Log the test configuration
    logger.info("Starting MongoDB Performance Test Suite")
    logger.info(f"Configuration: {args}")
    
    # Initialize result containers
    data_generation_results = []
    load_test_results = []
    aggregation_test_result = None
    dashboard_results = []
    
    # Step 1: Generate test data
    if args.skip_data_generation:
        logger.info("Skipping data generation step as requested")
    else:
        data_generation_results = generate_test_data(args)
    
    # Step 2: Run load tests
    if args.skip_load_tests:
        logger.info("Skipping load tests as requested")
    else:
        load_test_results = run_load_tests(args)
    
    # Step 3: Test aggregation pipelines
    if args.skip_aggregation_tests:
        logger.info("Skipping aggregation pipeline tests as requested")
    else:
        aggregation_test_result = test_aggregation_pipelines(args)
    
    # Step 4: Enable dashboard (if requested)
    if args.enable_dashboard:
        dashboard_results = enable_dashboard(args)
    else:
        logger.info("Skipping dashboard initialization as not requested")
    
    # Generate the performance report
    report = generate_performance_report(data_generation_results, load_test_results, aggregation_test_result, dashboard_results)
    
    # Write the report to a file
    with open(args.report, "w") as f:
        f.write(report)
    
    logger.info(f"Performance report written to {args.report}")
    logger.info("MongoDB Performance Test Suite completed")

if __name__ == "__main__":
    main() 