#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to run the continuous improvement pipeline for multi-language support.
This can be executed manually or scheduled as a cron job/scheduled task.

Examples:
- Run manually: python app/multi_language/run_improvement_pipeline.py
- Schedule as cron job: 0 0 * * 1 python /path/to/app/multi_language/run_improvement_pipeline.py
"""

import os
import sys
import logging
import argparse
import datetime
from pathlib import Path

# Set up logging
log_file = f"multi_language_pipeline_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("run_pipeline")

def run_pipeline(mode='full'):
    """
    Run the continuous improvement pipeline
    
    Args:
        mode (str): Pipeline execution mode
            - 'full': Run the complete improvement cycle
            - 'collect': Only collect metrics
            - 'report': Generate report without retraining
    """
    logger.info(f"Starting continuous improvement pipeline in '{mode}' mode")
    
    # Add current directory to path to ensure imports work
    sys.path.append(os.getcwd())
    
    # Import the pipeline
    try:
        from app.multi_language.pipeline.continuous_improvement import ContinuousImprovementPipeline
    except ImportError as e:
        logger.error(f"Failed to import ContinuousImprovementPipeline: {e}")
        print(f"Error: Failed to import required modules. Make sure you're running from the project root directory.")
        sys.exit(1)
    
    # Initialize the pipeline
    pipeline = ContinuousImprovementPipeline()
    
    # Run based on the specified mode
    if mode == 'full':
        logger.info("Running full improvement cycle")
        result = pipeline.run_full_improvement_cycle()
        logger.info("Full improvement cycle completed")
        return result
    elif mode == 'collect':
        logger.info("Collecting metrics only")
        metrics = pipeline.collect_current_metrics()
        pipeline.update_metrics_history()
        logger.info(f"Metrics collected for {len(metrics)} languages")
        return metrics
    elif mode == 'report':
        logger.info("Generating performance report only")
        pipeline.collect_current_metrics()
        pipeline.identify_underperforming_languages()
        pipeline.generate_improvement_recommendations()
        report = pipeline.generate_performance_report()
        logger.info("Performance report generated")
        return report
    else:
        logger.error(f"Unknown mode: {mode}")
        print(f"Error: Unknown mode '{mode}'. Use 'full', 'collect', or 'report'.")
        sys.exit(1)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run the multi-language continuous improvement pipeline')
    parser.add_argument('--mode', type=str, default='full', 
                        choices=['full', 'collect', 'report'],
                        help='Pipeline execution mode (full, collect, report)')
    return parser.parse_args()

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # Check if the necessary directories exist
    metrics_dir = Path("app/multi_language/evaluation/metrics")
    if not metrics_dir.exists():
        print("Error: Required directories not found. Please run setup_continuous_improvement.py first.")
        sys.exit(1)
    
    # Run the pipeline with the specified mode
    result = run_pipeline(args.mode)
    
    # Print completion message
    print(f"Continuous improvement pipeline ({args.mode} mode) completed successfully.")
    if args.mode in ['full', 'report']:
        print(f"Status: {result['overall_status']}")
        print(f"Underperforming languages: {', '.join(result['underperforming_languages']) if result['underperforming_languages'] else 'None'}")
    print(f"Log file: {log_file}") 