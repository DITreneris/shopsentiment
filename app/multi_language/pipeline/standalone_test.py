#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Standalone test script for the multi-language continuous improvement pipeline.
This script tests the core functionality without requiring the app module imports.
"""

import os
import sys
import json
import logging
import datetime
from pathlib import Path
import numpy as np

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("standalone_test")

# Constants
SUPPORTED_LANGUAGES = ["en", "fr", "de", "es", "it"]
LANGUAGE_NAMES = {
    "en": "English",
    "fr": "French",
    "de": "German", 
    "es": "Spanish",
    "it": "Italian"
}
METRICS_DIR = Path("app/multi_language/evaluation/metrics")
MODELS_DIR = Path("app/multi_language/models")
LEXICONS_DIR = Path("app/multi_language/lexicons")
THRESHOLDS = {
    "accuracy": 0.85,
    "f1_score": 0.80,
    "precision": 0.80,
    "recall": 0.75
}

def test_metrics_collection():
    """Test collection of metrics from files"""
    logger.info("Testing metrics collection...")
    current_metrics = {}
    
    for lang in SUPPORTED_LANGUAGES:
        metrics_file = METRICS_DIR / f"{lang}_metrics.json"
        if metrics_file.exists():
            try:
                with open(metrics_file, "r") as f:
                    lang_metrics = json.load(f)
                current_metrics[lang] = lang_metrics
                logger.info(f"Loaded metrics for {LANGUAGE_NAMES.get(lang, lang)}")
            except Exception as e:
                logger.error(f"Error loading metrics for {lang}: {str(e)}")
                current_metrics[lang] = {
                    "accuracy": 0.0,
                    "f1_score": 0.0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "support": 0,
                    "timestamp": datetime.datetime.now().isoformat()
                }
    
    assert len(current_metrics) > 0, "No metrics collected"
    return current_metrics

def identify_underperforming_languages(current_metrics):
    """Test identification of underperforming languages"""
    logger.info("Testing underperforming language identification...")
    underperforming_languages = []
    
    for lang, metrics in current_metrics.items():
        needs_improvement = False
        
        # Check each metric against threshold
        for metric_name, threshold in THRESHOLDS.items():
            if metric_name in metrics and metrics[metric_name] < threshold:
                needs_improvement = True
                logger.info(f"{LANGUAGE_NAMES.get(lang, lang)} {metric_name} ({metrics[metric_name]:.3f}) below threshold ({threshold:.3f})")
        
        if needs_improvement:
            underperforming_languages.append(lang)
    
    logger.info(f"Identified {len(underperforming_languages)} underperforming languages: {', '.join([LANGUAGE_NAMES.get(lang, lang) for lang in underperforming_languages]) if underperforming_languages else 'None'}")
    return underperforming_languages

def generate_improvement_recommendations(underperforming_languages, current_metrics):
    """Test generation of improvement recommendations"""
    logger.info("Testing improvement recommendation generation...")
    improvement_recommendations = {}
    
    for lang in underperforming_languages:
        recommendations = []
        metrics = current_metrics.get(lang, {})
        
        # Check specific metrics and provide targeted recommendations
        if metrics.get("precision", 0) < THRESHOLDS["precision"]:
            recommendations.append("Low precision - model might need more negative examples or stricter classification thresholds")
        
        if metrics.get("recall", 0) < THRESHOLDS["recall"]:
            recommendations.append("Low recall - model might need more positive examples or more comprehensive lexicons")
        
        if metrics.get("f1_score", 0) < THRESHOLDS["f1_score"]:
            recommendations.append("Low F1 score - consider balanced dataset improvements and ensemble techniques")
        
        # Add language-specific recommendations
        if lang == "fr":
            recommendations.append("Consider French-specific lemmatization to handle conjugation complexity")
        elif lang == "de":
            recommendations.append("Consider handling compound words common in German")
        elif lang == "es":
            recommendations.append("Consider improving handling of Spanish dialectal variations")
        elif lang == "it":
            recommendations.append("Consider improving handling of Italian formal/informal distinctions")
        
        # Add general recommendations
        recommendations.append("Expand language-specific lexicons with domain-specific terms")
        recommendations.append("Collect more training samples for this language")
        
        improvement_recommendations[lang] = recommendations
        logger.info(f"Generated {len(recommendations)} recommendations for {LANGUAGE_NAMES.get(lang, lang)}")
    
    return improvement_recommendations

def generate_performance_report(current_metrics, underperforming_languages, improvement_recommendations):
    """Test generation of performance report"""
    logger.info("Testing performance report generation...")
    
    # Create report
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "overall_status": "healthy" if not underperforming_languages else "needs_improvement",
        "language_metrics": current_metrics,
        "underperforming_languages": underperforming_languages,
        "improvement_recommendations": improvement_recommendations,
        "cross_language_comparison": {}
    }
    
    # Add cross-language comparison
    for metric in ["accuracy", "f1_score", "precision", "recall"]:
        report["cross_language_comparison"][metric] = {
            lang: current_metrics.get(lang, {}).get(metric, 0)
            for lang in SUPPORTED_LANGUAGES
        }
    
    # Print summary
    logger.info(f"Generated performance report")
    print("\nPerformance Report Summary:")
    print(f"Overall status: {report['overall_status']}")
    print(f"Languages analyzed: {', '.join(report['language_metrics'].keys())}")
    print(f"Underperforming languages: {', '.join(report['underperforming_languages']) if report['underperforming_languages'] else 'None'}")
    
    print("\nCross-language comparison (accuracy):")
    for lang, acc in report["cross_language_comparison"]["accuracy"].items():
        print(f"  {lang}: {acc:.3f}")
    
    return report

def run_standalone_test():
    """Run the standalone test pipeline"""
    logger.info("Starting standalone pipeline test")
    
    # Check directories existence
    if not METRICS_DIR.exists():
        print("Error: Metrics directory not found. Please run setup_continuous_improvement.py first.")
        sys.exit(1)
    
    # Step 1: Test metrics collection
    metrics = test_metrics_collection()
    
    # Step 2: Test underperforming language identification
    underperforming = identify_underperforming_languages(metrics)
    
    # Step 3: Test recommendation generation
    recommendations = generate_improvement_recommendations(underperforming, metrics)
    
    # Step 4: Test report generation
    report = generate_performance_report(metrics, underperforming, recommendations)
    
    logger.info("Standalone pipeline test completed successfully")
    return report

if __name__ == "__main__":
    run_standalone_test() 