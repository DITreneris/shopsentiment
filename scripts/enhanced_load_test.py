#!/usr/bin/env python3
"""
Enhanced Load Testing Script for ShopSentiment
This script performs a complete load testing workflow:
1. Generates synthetic test data at 10x production volume
2. Runs comprehensive MongoDB query performance tests
3. Tests API endpoints with simulated user load
4. Produces a detailed performance report

Usage:
    python enhanced_load_test.py [--users 50] [--duration 300] [--data-only] [--test-only]

Options:
    --users: Number of concurrent users to simulate (default: 50)
    --duration: Duration of the test in seconds (default: 300)
    --data-only: Only generate test data, don't run load tests
    --test-only: Only run load tests, don't generate data
"""

import os
import sys
import time
import json
import argparse
import logging
import subprocess
import statistics
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('load_test_results.log')
    ]
)
logger = logging.getLogger('load_testing')

# Constants for data generation
DEFAULT_USERS = 100
DEFAULT_PRODUCTS_PER_USER = 5
DEFAULT_REVIEWS_PER_PRODUCT = 200  # 10x normal volume

# Output directories
REPORT_DIR = os.path.join(parent_dir, 'reports', 'load_tests')
CHART_DIR = os.path.join(REPORT_DIR, 'charts')

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Enhanced Load Testing for ShopSentiment')
    parser.add_argument('--users', type=int, default=50, help='Number of concurrent users to simulate')
    parser.add_argument('--duration', type=int, default=300, help='Duration of the test in seconds')
    parser.add_argument('--data-only', action='store_true', help='Only generate test data, don\'t run load tests')
    parser.add_argument('--test-only', action='store_true', help='Only run load tests, don\'t generate data')
    return parser.parse_args()

def ensure_dirs():
    """Ensure output directories exist"""
    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(CHART_DIR, exist_ok=True)

def generate_synthetic_data():
    """Generate synthetic data using the existing data generator script"""
    logger.info("Generating synthetic test data at 10x production volume...")
    
    try:
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), 'load_test_data_generator.py'),
            '--users', str(DEFAULT_USERS),
            '--products-per-user', str(DEFAULT_PRODUCTS_PER_USER),
            '--reviews-per-product', str(DEFAULT_REVIEWS_PER_PRODUCT)
        ]
        
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True
        )
        
        logger.info("Data generation completed successfully")
        logger.debug(process.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Data generation failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def run_mongodb_performance_test():
    """Run MongoDB performance tests using the existing script"""
    logger.info("Running MongoDB performance tests...")
    
    try:
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), 'run_mongodb_performance_test.py'),
            '--output', os.path.join(REPORT_DIR, 'mongodb_performance_results.json')
        ]
        
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True
        )
        
        logger.info("MongoDB performance tests completed successfully")
        logger.debug(process.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"MongoDB performance tests failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def run_locust_load_test(users, duration):
    """Run Locust load tests on the API endpoints"""
    logger.info(f"Running Locust load tests with {users} users for {duration} seconds...")
    
    try:
        # First, ensure the application is running (this would be customized per environment)
        # For this example, we'll just check if we can run the load test directly
        
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), 'run_load_test.py'),
            '--no-web',
            '--users', str(users),
            '--spawn-rate', '10',
            '--run-time', f"{duration}s",
            '--csv', os.path.join(REPORT_DIR, 'locust_results')
        ]
        
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True
        )
        
        logger.info("Locust load tests completed successfully")
        logger.debug(process.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Locust load tests failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def analyze_results():
    """Analyze test results and generate visualizations"""
    logger.info("Analyzing test results...")
    
    results = {
        'mongodb': None,
        'locust': None
    }
    
    # Load MongoDB performance results
    mongodb_results_path = os.path.join(REPORT_DIR, 'mongodb_performance_results.json')
    if os.path.exists(mongodb_results_path):
        try:
            with open(mongodb_results_path, 'r') as f:
                results['mongodb'] = json.load(f)
            logger.info("Loaded MongoDB performance results")
        except Exception as e:
            logger.error(f"Failed to load MongoDB results: {e}")
    
    # Load Locust results
    locust_stats_path = os.path.join(REPORT_DIR, 'locust_results_stats.csv')
    if os.path.exists(locust_stats_path):
        try:
            results['locust'] = pd.read_csv(locust_stats_path)
            logger.info("Loaded Locust test results")
        except Exception as e:
            logger.error(f"Failed to load Locust results: {e}")
    
    # Generate visualizations
    if results['mongodb']:
        generate_mongodb_charts(results['mongodb'])
    
    if results['locust'] is not None:
        generate_locust_charts(results['locust'])
    
    # Generate overall performance report
    generate_performance_report(results)
    
    return results

def generate_mongodb_charts(results):
    """Generate charts for MongoDB performance results"""
    try:
        # Extract query times by type
        query_types = []
        avg_times = []
        p95_times = []
        
        for query_type, data in results.items():
            if isinstance(data, dict) and 'avg_time' in data:
                query_types.append(query_type)
                avg_times.append(data['avg_time'])
                p95_times.append(data['p95_time'])
        
        if not query_types:
            logger.warning("No MongoDB query performance data found for visualization")
            return
        
        # Create bar chart for query performance
        plt.figure(figsize=(12, 8))
        x = range(len(query_types))
        width = 0.35
        
        plt.bar(x, avg_times, width, label='Average Time (ms)')
        plt.bar([i + width for i in x], p95_times, width, label='95th Percentile (ms)')
        
        plt.xlabel('Query Type')
        plt.ylabel('Time (ms)')
        plt.title('MongoDB Query Performance')
        plt.xticks([i + width/2 for i in x], query_types, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        
        chart_path = os.path.join(CHART_DIR, 'mongodb_query_performance.png')
        plt.savefig(chart_path)
        logger.info(f"Generated MongoDB performance chart: {chart_path}")
        
        plt.close()
    except Exception as e:
        logger.error(f"Failed to generate MongoDB charts: {e}")

def generate_locust_charts(results):
    """Generate charts for Locust load test results"""
    try:
        # Create response time chart
        plt.figure(figsize=(12, 8))
        
        # Filter out aggregated stats (Total)
        endpoint_results = results[results['Name'] != 'Total']
        
        endpoints = endpoint_results['Name'].tolist()
        avg_response = endpoint_results['Average Response Time'].tolist()
        p95_response = endpoint_results['95%'].tolist()
        
        x = range(len(endpoints))
        width = 0.35
        
        plt.bar(x, avg_response, width, label='Average Response Time (ms)')
        plt.bar([i + width for i in x], p95_response, width, label='95th Percentile (ms)')
        
        plt.xlabel('Endpoint')
        plt.ylabel('Response Time (ms)')
        plt.title('API Endpoint Performance')
        plt.xticks([i + width/2 for i in x], endpoints, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        
        chart_path = os.path.join(CHART_DIR, 'locust_response_times.png')
        plt.savefig(chart_path)
        logger.info(f"Generated Locust response time chart: {chart_path}")
        
        # Create requests per second chart
        plt.figure(figsize=(12, 8))
        
        requests_per_sec = endpoint_results['Requests/s'].tolist()
        
        plt.bar(x, requests_per_sec, width)
        
        plt.xlabel('Endpoint')
        plt.ylabel('Requests/s')
        plt.title('API Throughput')
        plt.xticks(x, endpoints, rotation=45, ha='right')
        plt.tight_layout()
        
        chart_path = os.path.join(CHART_DIR, 'locust_throughput.png')
        plt.savefig(chart_path)
        logger.info(f"Generated Locust throughput chart: {chart_path}")
        
        plt.close()
    except Exception as e:
        logger.error(f"Failed to generate Locust charts: {e}")

def generate_performance_report(results):
    """Generate a comprehensive performance report"""
    try:
        report_path = os.path.join(REPORT_DIR, 'performance_report.md')
        
        with open(report_path, 'w') as f:
            f.write("# ShopSentiment Load Test Performance Report\n\n")
            f.write(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            f.write("## Test Parameters\n\n")
            f.write("- Test data volume: 10x production volume\n")
            f.write(f"- Number of users: {DEFAULT_USERS}\n")
            f.write(f"- Products per user: {DEFAULT_PRODUCTS_PER_USER}\n")
            f.write(f"- Reviews per product: {DEFAULT_REVIEWS_PER_PRODUCT}\n\n")
            
            # MongoDB Results
            f.write("## MongoDB Performance\n\n")
            if results['mongodb']:
                f.write("### Query Performance Summary\n\n")
                f.write("| Query Type | Average (ms) | Median (ms) | 95% (ms) | Max (ms) |\n")
                f.write("|------------|-------------|-------------|----------|----------|\n")
                
                for query_type, data in results['mongodb'].items():
                    if isinstance(data, dict) and 'avg_time' in data:
                        f.write(f"| {query_type} | {data['avg_time']:.2f} | {data['median_time']:.2f} | ")
                        f.write(f"{data['p95_time']:.2f} | {data['max_time']:.2f} |\n")
                
                f.write("\n![MongoDB Query Performance](charts/mongodb_query_performance.png)\n\n")
            else:
                f.write("*No MongoDB performance data available*\n\n")
            
            # Locust Results
            f.write("## API Endpoint Performance\n\n")
            if results['locust'] is not None:
                f.write("### Endpoint Performance Summary\n\n")
                f.write("| Endpoint | Requests/s | Average (ms) | 95% (ms) | Failures (%) |\n")
                f.write("|----------|------------|--------------|----------|-------------|\n")
                
                endpoint_results = results['locust'][results['locust']['Name'] != 'Total']
                for _, row in endpoint_results.iterrows():
                    f.write(f"| {row['Name']} | {row['Requests/s']:.2f} | {row['Average Response Time']:.2f} | ")
                    f.write(f"{row['95%']:.2f} | {row['Failure Rate']:.2f} |\n")
                
                # Include total row
                total_row = results['locust'][results['locust']['Name'] == 'Total'].iloc[0]
                f.write(f"| **Total** | {total_row['Requests/s']:.2f} | {total_row['Average Response Time']:.2f} | ")
                f.write(f"{total_row['95%']:.2f} | {total_row['Failure Rate']:.2f} |\n")
                
                f.write("\n![API Response Times](charts/locust_response_times.png)\n\n")
                f.write("\n![API Throughput](charts/locust_throughput.png)\n\n")
            else:
                f.write("*No API endpoint performance data available*\n\n")
            
            # Conclusions
            f.write("## Conclusions and Recommendations\n\n")
            
            # Add automatic recommendations based on results
            if results['mongodb'] and results['locust'] is not None:
                slowest_query = max(
                    [(k, v['avg_time']) for k, v in results['mongodb'].items() if isinstance(v, dict) and 'avg_time' in v],
                    key=lambda x: x[1],
                    default=(None, 0)
                )
                
                slowest_endpoint = endpoint_results.loc[endpoint_results['Average Response Time'].idxmax()] \
                    if not endpoint_results.empty else None
                
                if slowest_query[0]:
                    f.write(f"1. The slowest MongoDB query is **{slowest_query[0]}** with an average time of {slowest_query[1]:.2f}ms. ")
                    f.write("Consider optimizing this query through indexing or query restructuring.\n\n")
                
                if slowest_endpoint is not None:
                    f.write(f"2. The slowest API endpoint is **{slowest_endpoint['Name']}** with an average response time of ")
                    f.write(f"{slowest_endpoint['Average Response Time']:.2f}ms. This endpoint should be investigated for optimization.\n\n")
                
                # Add overall recommendations
                f.write("### General Recommendations\n\n")
                f.write("1. Implement additional caching for frequent queries\n")
                f.write("2. Consider adding indexes for frequently queried fields\n")
                f.write("3. Implement query result pagination where appropriate\n")
                f.write("4. Monitor application performance in production with APM tools\n")
            else:
                f.write("*Insufficient data to generate recommendations*\n\n")
        
        logger.info(f"Generated performance report: {report_path}")
        return report_path
    except Exception as e:
        logger.error(f"Failed to generate performance report: {e}")
        return None

def main():
    """Main function to orchestrate the load testing process"""
    args = parse_arguments()
    ensure_dirs()
    
    logger.info("Starting enhanced load testing process")
    
    # Generate synthetic data if needed
    if not args.test_only:
        if not generate_synthetic_data():
            logger.error("Failed to generate synthetic data. Aborting test.")
            return False
    
    if args.data_only:
        logger.info("Data generation completed. Skipping tests as requested.")
        return True
    
    # Run MongoDB performance tests
    if not run_mongodb_performance_test():
        logger.warning("MongoDB performance tests failed or were incomplete.")
    
    # Run Locust load tests
    if not run_locust_load_test(args.users, args.duration):
        logger.warning("Locust load tests failed or were incomplete.")
    
    # Analyze results and generate report
    results = analyze_results()
    
    logger.info("Enhanced load testing process completed")
    
    # Print report location
    report_path = os.path.join(REPORT_DIR, 'performance_report.md')
    if os.path.exists(report_path):
        logger.info(f"Performance report available at: {report_path}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 