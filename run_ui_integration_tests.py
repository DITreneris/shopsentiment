#!/usr/bin/env python
"""
Script to run UI, Integration, and Performance tests for the Shop Sentiment application.
"""

import os
import sys
import argparse
import pytest


def run_tests(test_type="all", headless=True, browser="chrome", verbose=False, skip_slow=False):
    """
    Run UI, Integration, and/or Performance tests.
    
    Args:
        test_type: Type of tests to run ("ui", "integration", "performance", or "all")
        headless: Whether to run browser tests in headless mode
        browser: Browser to use for tests ("chrome" or "firefox")
        verbose: Whether to show verbose output
        skip_slow: Whether to skip slow network tests
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    args = []
    
    # Add test directories based on test_type
    if test_type == "ui" or test_type == "all":
        args.append("tests/ui/")
    
    if test_type == "integration" or test_type == "all":
        args.append("tests/integration/")
    
    if test_type == "performance" or test_type == "all":
        args.append("tests/performance/")
    
    # Set browser options
    args.append(f"--browser={browser}")
    
    if headless:
        args.append("--headless")
    
    # Skip slow network tests if requested
    if skip_slow:
        args.append("-m")
        args.append("not slow_network")
    
    # Set verbosity
    if verbose:
        args.append("-v")
    
    # Print test command
    cmd = f"pytest {' '.join(args)}"
    print(f"Running: {cmd}")
    
    # Run tests
    exit_code = pytest.main(args)
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run UI, Integration, and Performance tests")
    parser.add_argument(
        "--test-type", 
        choices=["ui", "integration", "performance", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser with GUI (not headless)"
    )
    parser.add_argument(
        "--browser",
        choices=["chrome", "firefox"],
        default="chrome",
        help="Browser to use for tests"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output"
    )
    parser.add_argument(
        "--skip-slow",
        action="store_true",
        help="Skip slow network simulation tests"
    )
    
    args = parser.parse_args()
    
    exit_code = run_tests(
        test_type=args.test_type, 
        headless=not args.no_headless,
        browser=args.browser,
        verbose=args.verbose,
        skip_slow=args.skip_slow
    )
    
    sys.exit(exit_code) 