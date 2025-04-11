# MongoDB Performance Testing Tools

This directory contains scripts for testing MongoDB performance in the ShopSentiment application.

## Overview

The performance testing suite includes tools for:

1. **Data Generation**: Creating synthetic data for testing at different scales
2. **Load Testing**: Measuring MongoDB query performance under various loads
3. **Aggregation Pipeline Testing**: Evaluating the performance of complex analytics queries
4. **Python 3.10 Compatibility**: Checking the codebase for Python 3.7 to 3.10 upgrade compatibility
5. **Dashboard Initialization**: Setting up MongoDB collections and precomputing statistics for the dashboard

## Getting Started

Before running the scripts, make them executable by running:

```bash
# On all platforms
python make_scripts_executable.py

# On Unix/Linux/macOS
chmod +x *.py
```

This helper script will:
- Make all Python scripts executable on Unix systems
- Create .bat wrapper files for Windows
- Create venv activation helpers if a virtual environment is detected

## Available Scripts

### Data Generation

```bash
python load_test_data_generator.py [OPTIONS]
```

**Options:**
- `--users N`: Number of users to generate (default: 100)
- `--products N`: Products per user (default: 5)
- `--reviews N`: Reviews per product (default: 200)
- `--clear`: Clear existing collections before generating new data

**Example:**
```bash
# Generate a small test dataset
python load_test_data_generator.py --users 10 --products 3 --reviews 50

# Generate a production-scale dataset and clear existing data
python load_test_data_generator.py --users 50 --products 5 --reviews 100 --clear

# Generate a 10x production volume dataset
python load_test_data_generator.py --users 100 --products 5 --reviews 200
```

### Load Testing

```bash
python run_load_test.py [OPTIONS]
```

**Options:**
- `--direct`: Run direct test without Locust UI
- `--duration N`: Test duration in seconds (for direct test, default: 60)
- `--users N`: Number of concurrent users (for direct test, default: 10)

**Example:**
```bash
# Run a basic direct test
python run_load_test.py --direct --duration 30 --users 5

# Run with Locust web UI
locust -f run_load_test.py

# Run a headless Locust test with 10 users
locust -f run_load_test.py --headless -u 10 -r 1 --run-time 1m
```

### Python Upgrade Helper

```bash
python upgrade_python.py [OPTIONS]
```

**Options:**
- `--base-dir DIR`: Base directory to scan (default: current directory)
- `--output FILE`: Output report file (default: python_310_compatibility_report.txt)
- `--format FORMAT`: Output format (text, markdown) (default: text)
- `--max-workers N`: Maximum number of worker threads (default: 4)

**Example:**
```bash
# Scan current directory and generate report
python upgrade_python.py

# Scan app directory and output markdown report
python upgrade_python.py --base-dir app --output python_upgrade.md --format markdown
```

### Dashboard Initialization

```bash
python enable_dashboard.py
```

This script initializes the dashboard functionality by:
- Creating necessary MongoDB collections (time series and precomputed stats)
- Precomputing initial statistics for frequently accessed products and metrics
- Setting up data for all dashboard visualizations

**When to run:**
- After initial MongoDB setup
- After significant data changes
- When deploying the dashboard to a new environment

**Example:**
```bash
# Initialize the dashboard with precomputed stats
python enable_dashboard.py
```

### Combined Testing Suite

For convenience, a script is provided to run all tests in sequence:

```bash
python run_mongodb_performance_test.py [OPTIONS]
```

**Options:**
- `--skip-data-generation`: Skip the data generation step
- `--skip-load-tests`: Skip the load testing step
- `--skip-aggregation-tests`: Skip the aggregation pipeline tests
- `--generate-10x`: Generate 10x production volume dataset
- `--run-heavy`: Run heavy load tests
- `--skip-large`: Skip large dataset generation
- `--skip-extended`: Skip extended load tests
- `--clear`: Clear existing collections before data generation
- `--report FILE`: Output report file (default: mongodb_performance_report.md)
- `--enable-dashboard`: Initialize the dashboard after tests complete

**Example:**
```bash
# Run all tests with default settings
python run_mongodb_performance_test.py

# Run only load tests and aggregation tests
python run_mongodb_performance_test.py --skip-data-generation

# Run a quick test (skip large datasets and extended tests)
python run_mongodb_performance_test.py --skip-large --skip-extended

# Run comprehensive tests including 10x data, heavy load, and dashboard initialization
python run_mongodb_performance_test.py --generate-10x --run-heavy --clear --enable-dashboard
```

## Running on Windows vs. Unix

After running `make_scripts_executable.py`, you can run the scripts as follows:

### On Windows
```bash
# Using the batch files
load_test_data_generator.bat --users 10
run_load_test.bat --direct
enable_dashboard.bat

# Or using Python directly
python load_test_data_generator.py --users 10
```

### On Unix (Linux/macOS)
```bash
# Using the executable scripts
./load_test_data_generator.py --users 10
./run_load_test.py --direct
./enable_dashboard.py

# Or using Python directly
python load_test_data_generator.py --users 10
```

## Output

Each script generates a detailed log file and, when applicable, a report in text or markdown format. The combined testing suite generates a comprehensive report with results from all tests and recommendations for performance optimization.

## Prerequisites

Before running these scripts, make sure:

1. MongoDB connection is configured in your `.env` file
2. Required Python packages are installed:
   ```bash
   pip install pymongo dnspython tqdm locust python-dotenv statistics redis
   ```
3. You have sufficient disk space for data generation (especially for 10x tests)
4. Redis is installed and running for dashboard caching functionality 

## Interpreting Results

The performance reports include:

- **Query Times**: Average, median, and 95th percentile times for various operations
- **Resource Usage**: Memory and CPU utilization during tests
- **Scaling Recommendations**: Suggestions for optimizing configuration based on test results
- **Aggregation Performance**: Performance metrics for complex analytics queries
- **Python Compatibility Issues**: Identified issues when migrating to Python 3.10
- **Dashboard Performance**: Loading times for dashboard components with and without precomputed stats 