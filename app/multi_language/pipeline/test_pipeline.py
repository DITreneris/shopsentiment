#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for the multi-language continuous improvement pipeline.
This script tests the main functionality of the pipeline:
1. Metrics collection and analysis
2. Underperforming language identification
3. Improvement recommendations
4. Report generation
"""

import os
import sys
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_pipeline")

# Import the ContinuousImprovementPipeline
sys.path.append(os.getcwd())  # Add current directory to path
from app.multi_language.pipeline.continuous_improvement import ContinuousImprovementPipeline

def test_pipeline():
    """Test the continuous improvement pipeline functionality"""
    logger.info("Starting pipeline test")
    
    # Create the pipeline
    pipeline = ContinuousImprovementPipeline()
    
    # Step 1: Test metrics collection
    logger.info("Testing metrics collection...")
    metrics = pipeline.collect_current_metrics()
    assert metrics is not None, "Metrics collection failed"
    logger.info(f"Collected metrics for {len(metrics)} languages")
    
    # Step 2: Test underperforming language identification
    logger.info("Testing underperforming language identification...")
    underperforming = pipeline.identify_underperforming_languages()
    logger.info(f"Identified {len(underperforming)} underperforming languages: {underperforming}")
    
    # Step 3: Test recommendation generation
    logger.info("Testing improvement recommendation generation...")
    recommendations = pipeline.generate_improvement_recommendations()
    for lang, recs in recommendations.items():
        logger.info(f"Generated {len(recs)} recommendations for {lang}")
    
    # Step 4: Test metrics history update
    logger.info("Testing metrics history update...")
    pipeline.update_metrics_history()
    logger.info("Metrics history updated")
    
    # Step 5: Test report generation
    logger.info("Testing performance report generation...")
    report = pipeline.generate_performance_report()
    logger.info(f"Generated report with {len(report['language_metrics'])} language entries")
    
    # Print a summary of the report
    print("\nPerformance Report Summary:")
    print(f"Overall status: {report['overall_status']}")
    print(f"Languages analyzed: {', '.join(report['language_metrics'].keys())}")
    print(f"Underperforming languages: {', '.join(report['underperforming_languages']) if report['underperforming_languages'] else 'None'}")
    
    print("\nCross-language comparison (accuracy):")
    for lang, acc in report['cross_language_comparison']['accuracy'].items():
        print(f"  {lang}: {acc:.3f}")
    
    logger.info("Pipeline test completed successfully")
    return report

if __name__ == "__main__":
    # Check if the necessary directories exist
    metrics_dir = Path("app/multi_language/evaluation/metrics")
    if not metrics_dir.exists():
        print("Error: Metrics directory not found. Please run setup_continuous_improvement.py first.")
        sys.exit(1)
    
    # Run the test
    test_pipeline() 