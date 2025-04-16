#!/usr/bin/env python3
"""
Test Runner Script for ShopSentiment

This script runs the test suite for the ShopSentiment application
with proper configuration and environment setup.
"""

import os
import sys
import subprocess
import argparse

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """Run the tests with the specified options."""
    parser = argparse.ArgumentParser(description='Run ShopSentiment tests')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--verbose', '-v', action='count', default=0, help='Increase verbosity')
    parser.add_argument('--fail-fast', '-x', action='store_true', help='Stop on first failure')
    parser.add_argument('testpaths', nargs='*', help='Specific test paths to run')
    
    args = parser.parse_args()
    
    # Set environment variables for testing
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['CACHE_ENABLED'] = 'false'
    
    # Base command
    cmd = ['pytest']
    
    # Add verbosity
    if args.verbose > 0:
        cmd.append('-' + 'v' * args.verbose)
    
    # Add fail-fast
    if args.fail_fast:
        cmd.append('-x')
    
    # Add coverage
    if args.coverage:
        cmd.extend(['--cov=src', '--cov-report=term', '--cov-report=html:coverage_html'])
    
    # Add test type markers
    if args.unit:
        cmd.append('-m unit')
    elif args.integration:
        cmd.append('-m integration')
    
    # Add specific test paths if provided
    if args.testpaths:
        cmd.extend(args.testpaths)
    
    # Run the tests
    try:
        print(f"Running tests with command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    

if __name__ == '__main__':
    main() 