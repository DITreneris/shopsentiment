"""
MongoDB Optimization Implementation Script

This script orchestrates the implementation of the MongoDB optimization plan
according to the morning session plan, running all the necessary components
in the correct order.
"""

import logging
import time
import os
import subprocess
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mongodb_optimization_implementation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_name, description):
    """Run a Python script and log the result."""
    logger.info(f"Running {description}...")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        elapsed = time.time() - start_time
        
        logger.info(f"Successfully completed {description} in {elapsed:.2f} seconds")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {script_name}: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False

def implement_performance_optimization():
    """Implement performance optimization tasks."""
    logger.info("Starting performance optimization tasks")
    
    # Add text indexes for keyword search
    success = run_script(
        "add_text_indexes.py",
        "text index implementation for keyword search"
    )
    if not success:
        logger.warning("Text index implementation failed, continuing with next task")
    
    # Implement incremental updates for large collections
    success = run_script(
        "implement_incremental_updates.py",
        "incremental updates for large collections"
    )
    if not success:
        logger.warning("Incremental updates implementation failed, continuing with next task")
    
    logger.info("Completed performance optimization tasks")

def implement_monitoring_setup():
    """Implement monitoring and maintenance tasks."""
    logger.info("Starting monitoring and maintenance setup")
    
    # Enhanced slow query logging
    success = run_script(
        "enhance_slow_query_logging.py",
        "enhanced slow query logging"
    )
    if not success:
        logger.warning("Slow query logging setup failed, continuing with next task")
    
    # Cache hit/miss ratio tracking
    success = run_script(
        "implement_cache_monitoring.py",
        "cache hit/miss ratio tracking"
    )
    if not success:
        logger.warning("Cache monitoring setup failed, continuing with next task")
    
    logger.info("Completed monitoring and maintenance setup")

def run_performance_tests():
    """Run comprehensive performance tests."""
    logger.info("Starting performance testing")
    
    success = run_script(
        "run_comprehensive_performance_tests.py",
        "comprehensive performance tests"
    )
    if not success:
        logger.warning("Performance testing failed")
    
    logger.info("Completed performance testing")

def generate_implementation_report():
    """Generate a comprehensive implementation report."""
    logger.info("Generating implementation report")
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    report_file = f"mongodb_optimization_implementation_report_{timestamp}.md"
    
    try:
        with open(report_file, 'w') as f:
            f.write("# MongoDB Optimization Implementation Report\n\n")
            f.write(f"Generated: {datetime.utcnow()}\n\n")
            
            f.write("## Implementation Summary\n\n")
            f.write("This report summarizes the implementation of MongoDB optimization tasks according to the morning session plan.\n\n")
            
            # Get logs from the implementation
            f.write("## Implementation Log Highlights\n\n")
            f.write("```\n")
            try:
                with open('mongodb_optimization_implementation.log', 'r') as log_file:
                    # Get last 50 lines of the log
                    lines = log_file.readlines()
                    for line in lines[-50:]:
                        f.write(line)
            except Exception as e:
                f.write(f"Error reading log file: {e}\n")
            f.write("```\n\n")
            
            # Add links to performance reports
            f.write("## Performance Test Results\n\n")
            performance_reports = os.path.join("performance_reports")
            if os.path.exists(performance_reports):
                report_files = [f for f in os.listdir(performance_reports) if f.endswith('.txt')]
                if report_files:
                    latest_report = max(report_files)
                    f.write(f"The latest performance report can be found at: `{os.path.join(performance_reports, latest_report)}`\n\n")
                    
                    # Try to extract summary from the report
                    try:
                        with open(os.path.join(performance_reports, latest_report), 'r') as perf_report:
                            content = perf_report.read()
                            summary_start = content.find("Performance Summary")
                            summary_end = content.find("Detailed Test Results")
                            if summary_start >= 0 and summary_end >= 0:
                                summary = content[summary_start:summary_end]
                                f.write("### Summary of Performance Tests\n\n")
                                f.write("```\n")
                                f.write(summary)
                                f.write("```\n\n")
                    except Exception as e:
                        f.write(f"Error extracting performance summary: {e}\n\n")
                else:
                    f.write("No performance reports generated yet.\n\n")
            else:
                f.write("Performance reports directory not found.\n\n")
            
            # Add links to slow query reports
            f.write("## Slow Query Analysis\n\n")
            slow_query_reports = os.path.join("slow_query_reports")
            if os.path.exists(slow_query_reports):
                report_files = [f for f in os.listdir(slow_query_reports) if f.endswith('.txt')]
                if report_files:
                    latest_report = max(report_files)
                    f.write(f"The latest slow query analysis can be found at: `{os.path.join(slow_query_reports, latest_report)}`\n\n")
                else:
                    f.write("No slow query reports generated yet.\n\n")
            else:
                f.write("Slow query reports directory not found.\n\n")
            
            # Add next steps
            f.write("## Next Steps\n\n")
            f.write("1. **Fine-tune refresh frequency**: Adjust refresh schedules based on actual usage patterns\n")
            f.write("2. **Monitor query performance**: Continue monitoring in production environment\n")
            f.write("3. **Optimize incremental updates**: Further refine incremental update process\n")
            f.write("4. **Expand text index coverage**: Evaluate additional fields for text indexing\n")
            f.write("5. **Enhance cache monitoring**: Integrate cache monitoring with alerting system\n")
        
        logger.info(f"Implementation report generated: {report_file}")
        return report_file
    except Exception as e:
        logger.error(f"Error generating implementation report: {e}")
        return None

def main():
    """Run the MongoDB optimization implementation according to the session plan."""
    logger.info("Starting MongoDB optimization implementation")
    start_time = time.time()
    
    # Step 1: Performance Optimization
    implement_performance_optimization()
    
    # Step 2: Monitoring Setup
    implement_monitoring_setup()
    
    # Step 3: Performance Testing
    run_performance_tests()
    
    # Generate implementation report
    report_file = generate_implementation_report()
    
    # Calculate total elapsed time
    elapsed = time.time() - start_time
    logger.info(f"MongoDB optimization implementation completed in {elapsed:.2f} seconds")
    
    if report_file:
        logger.info(f"Implementation report generated: {report_file}")
    
    logger.info("Implementation complete. Check the logs and reports for detailed results.")

if __name__ == "__main__":
    main() 