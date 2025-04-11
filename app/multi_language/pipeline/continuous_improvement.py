import logging
import json
import os
import time
import datetime
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import schedule
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("multi_language_improvement.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("multi_language_improvement")

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

class ContinuousImprovementPipeline:
    """
    Continuous Improvement Pipeline for Multi-Language Sentiment Analysis
    
    This pipeline automatically:
    1. Monitors model performance across languages
    2. Identifies underperforming models/languages
    3. Triggers retraining when needed
    4. Updates lexicons with new terms
    5. Generates performance reports
    6. Maintains historical performance data
    """
    
    def __init__(self):
        """Initialize the continuous improvement pipeline"""
        self.metrics_history = {}
        self.current_metrics = {}
        self.underperforming_languages = []
        self.improvement_recommendations = {}
        
        # Create necessary directories
        METRICS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load historical metrics if available
        self._load_metrics_history()
    
    def _load_metrics_history(self) -> None:
        """Load historical performance metrics"""
        history_file = METRICS_DIR / "metrics_history.json"
        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    self.metrics_history = json.load(f)
                logger.info(f"Loaded metrics history for {len(self.metrics_history)} time periods")
            except Exception as e:
                logger.error(f"Error loading metrics history: {str(e)}")
                self.metrics_history = {}
    
    def _save_metrics_history(self) -> None:
        """Save historical performance metrics"""
        history_file = METRICS_DIR / "metrics_history.json"
        try:
            with open(history_file, "w") as f:
                json.dump(self.metrics_history, f, indent=2)
            logger.info(f"Saved metrics history with {len(self.metrics_history)} time periods")
        except Exception as e:
            logger.error(f"Error saving metrics history: {str(e)}")
    
    def collect_current_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Collect current performance metrics for all languages
        Returns a dictionary with language codes as keys and metrics as values
        """
        self.current_metrics = {}
        
        for lang in SUPPORTED_LANGUAGES:
            metrics_file = METRICS_DIR / f"{lang}_metrics.json"
            if metrics_file.exists():
                try:
                    with open(metrics_file, "r") as f:
                        lang_metrics = json.load(f)
                    self.current_metrics[lang] = lang_metrics
                    logger.info(f"Loaded current metrics for {LANGUAGE_NAMES.get(lang, lang)}")
                except Exception as e:
                    logger.error(f"Error loading metrics for {lang}: {str(e)}")
                    # Use default values if metrics file can't be loaded
                    self.current_metrics[lang] = {
                        "accuracy": 0.0,
                        "f1_score": 0.0,
                        "precision": 0.0,
                        "recall": 0.0,
                        "support": 0,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
            else:
                logger.warning(f"No metrics file found for {lang}")
                # Use default values if metrics file doesn't exist
                self.current_metrics[lang] = {
                    "accuracy": 0.0,
                    "f1_score": 0.0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "support": 0,
                    "timestamp": datetime.datetime.now().isoformat()
                }
        
        return self.current_metrics
    
    def identify_underperforming_languages(self) -> List[str]:
        """
        Identify languages with performance below thresholds
        Returns a list of language codes that need improvement
        """
        self.underperforming_languages = []
        
        if not self.current_metrics:
            self.collect_current_metrics()
        
        for lang, metrics in self.current_metrics.items():
            needs_improvement = False
            
            # Check each metric against threshold
            for metric_name, threshold in THRESHOLDS.items():
                if metric_name in metrics and metrics[metric_name] < threshold:
                    needs_improvement = True
                    logger.info(f"{LANGUAGE_NAMES.get(lang, lang)} {metric_name} ({metrics[metric_name]:.3f}) below threshold ({threshold:.3f})")
            
            if needs_improvement:
                self.underperforming_languages.append(lang)
        
        if self.underperforming_languages:
            logger.info(f"Identified {len(self.underperforming_languages)} underperforming languages: {', '.join([LANGUAGE_NAMES.get(lang, lang) for lang in self.underperforming_languages])}")
        else:
            logger.info("All languages performing above thresholds")
            
        return self.underperforming_languages
    
    def generate_improvement_recommendations(self) -> Dict[str, List[str]]:
        """
        Generate recommendations for improving underperforming languages
        Returns a dictionary with language codes as keys and lists of recommendations as values
        """
        self.improvement_recommendations = {}
        
        if not self.underperforming_languages:
            self.identify_underperforming_languages()
        
        for lang in self.underperforming_languages:
            recommendations = []
            metrics = self.current_metrics.get(lang, {})
            
            # Check for trends in metrics history
            if lang in self.metrics_history:
                history = self.metrics_history[lang]
                
                # Check if accuracy is decreasing
                if len(history) >= 3:
                    recent_accuracy = [entry.get("accuracy", 0) for entry in history[-3:]]
                    if recent_accuracy[0] > recent_accuracy[1] > recent_accuracy[2]:
                        recommendations.append("Accuracy is consistently decreasing - consider model architecture review")
            
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
            
            self.improvement_recommendations[lang] = recommendations
            logger.info(f"Generated {len(recommendations)} recommendations for {LANGUAGE_NAMES.get(lang, lang)}")
        
        return self.improvement_recommendations
    
    def update_metrics_history(self) -> None:
        """Update metrics history with current metrics"""
        timestamp = datetime.datetime.now().isoformat()
        
        if not self.current_metrics:
            self.collect_current_metrics()
        
        # Add current metrics to history for each language
        for lang, metrics in self.current_metrics.items():
            if lang not in self.metrics_history:
                self.metrics_history[lang] = []
            
            metrics_with_timestamp = metrics.copy()
            if "timestamp" not in metrics_with_timestamp:
                metrics_with_timestamp["timestamp"] = timestamp
            
            self.metrics_history[lang].append(metrics_with_timestamp)
            
            # Keep only the last 12 entries (e.g., monthly data for a year)
            if len(self.metrics_history[lang]) > 12:
                self.metrics_history[lang] = self.metrics_history[lang][-12:]
        
        # Save updated history
        self._save_metrics_history()
        logger.info("Updated metrics history with current data")
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report
        Returns a report dictionary
        """
        if not self.current_metrics:
            self.collect_current_metrics()
        
        if not self.underperforming_languages:
            self.identify_underperforming_languages()
        
        if not self.improvement_recommendations:
            self.generate_improvement_recommendations()
        
        # Create report
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "overall_status": "healthy" if not self.underperforming_languages else "needs_improvement",
            "language_metrics": self.current_metrics,
            "underperforming_languages": self.underperforming_languages,
            "improvement_recommendations": self.improvement_recommendations,
            "cross_language_comparison": {},
            "historical_trends": {}
        }
        
        # Add cross-language comparison
        for metric in ["accuracy", "f1_score", "precision", "recall"]:
            report["cross_language_comparison"][metric] = {
                lang: self.current_metrics.get(lang, {}).get(metric, 0)
                for lang in SUPPORTED_LANGUAGES
            }
        
        # Add historical trends
        for lang in SUPPORTED_LANGUAGES:
            if lang in self.metrics_history and len(self.metrics_history[lang]) > 1:
                history = self.metrics_history[lang]
                report["historical_trends"][lang] = {
                    "accuracy_trend": [entry.get("accuracy", 0) for entry in history],
                    "f1_score_trend": [entry.get("f1_score", 0) for entry in history],
                    "timestamps": [entry.get("timestamp", "") for entry in history]
                }
        
        # Save report to file
        report_file = METRICS_DIR / f"performance_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Generated performance report: {report_file}")
        except Exception as e:
            logger.error(f"Error saving performance report: {str(e)}")
        
        return report
    
    def trigger_retraining(self, languages: Optional[List[str]] = None) -> None:
        """
        Trigger retraining for specific languages or all underperforming languages
        """
        if languages is None:
            if not self.underperforming_languages:
                self.identify_underperforming_languages()
            languages = self.underperforming_languages
        
        if not languages:
            logger.info("No languages to retrain")
            return
        
        for lang in languages:
            logger.info(f"Triggering retraining for {LANGUAGE_NAMES.get(lang, lang)}")
            # Here you would call your model training code
            # For example:
            # from app.multi_language.models.train import train_model
            # train_model(lang)
            
            # Placeholder for actual training call
            logger.info(f"Retraining initiated for {LANGUAGE_NAMES.get(lang, lang)}")
    
    def update_lexicons(self, languages: Optional[List[str]] = None) -> None:
        """
        Update lexicons for specific languages or all underperforming languages
        """
        if languages is None:
            if not self.underperforming_languages:
                self.identify_underperforming_languages()
            languages = self.underperforming_languages
        
        if not languages:
            logger.info("No lexicons to update")
            return
        
        for lang in languages:
            logger.info(f"Updating lexicon for {LANGUAGE_NAMES.get(lang, lang)}")
            # Here you would call your lexicon update code
            # For example:
            # from app.multi_language.lexicons.update import update_lexicon
            # update_lexicon(lang)
            
            # Placeholder for actual lexicon update call
            logger.info(f"Lexicon update initiated for {LANGUAGE_NAMES.get(lang, lang)}")
    
    def run_full_improvement_cycle(self) -> Dict[str, Any]:
        """
        Run the complete improvement cycle
        """
        logger.info("Starting full improvement cycle")
        
        # Step 1: Collect current metrics
        self.collect_current_metrics()
        
        # Step 2: Identify underperforming languages
        self.identify_underperforming_languages()
        
        # Step 3: Generate improvement recommendations
        self.generate_improvement_recommendations()
        
        # Step 4: Update metrics history
        self.update_metrics_history()
        
        # Step 5: Generate performance report
        report = self.generate_performance_report()
        
        # Step 6: Trigger retraining for underperforming languages
        self.trigger_retraining()
        
        # Step 7: Update lexicons for underperforming languages
        self.update_lexicons()
        
        logger.info("Completed full improvement cycle")
        return report

    def schedule_improvement_cycles(self, 
                                   daily_time: str = "00:00", 
                                   weekly_day: str = "monday", 
                                   monthly_day: int = 1) -> None:
        """
        Schedule regular improvement cycles
        
        Parameters:
        daily_time: Time for daily job (HH:MM format)
        weekly_day: Day for weekly job (monday, tuesday, etc.)
        monthly_day: Day of month for monthly job (1-31)
        """
        # Schedule daily basic monitoring
        schedule.every().day.at(daily_time).do(self.collect_current_metrics)
        logger.info(f"Scheduled daily metrics collection at {daily_time}")
        
        # Schedule weekly improvement cycle
        schedule.every().__getattribute__(weekly_day).at(daily_time).do(self.run_full_improvement_cycle)
        logger.info(f"Scheduled weekly improvement cycle on {weekly_day} at {daily_time}")
        
        # Schedule monthly comprehensive report
        def monthly_job():
            if datetime.datetime.now().day == monthly_day:
                self.run_full_improvement_cycle()
                # Additional monthly tasks could be added here
        
        schedule.every().day.at(daily_time).do(monthly_job)
        logger.info(f"Scheduled monthly comprehensive improvement on day {monthly_day} at {daily_time}")

def main():
    """Main entry point for the continuous improvement pipeline"""
    pipeline = ContinuousImprovementPipeline()
    
    # Run an initial cycle
    pipeline.run_full_improvement_cycle()
    
    # Schedule regular runs
    pipeline.schedule_improvement_cycles()
    
    # Keep the scheduler running
    try:
        logger.info("Starting continuous improvement scheduler")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Continuous improvement scheduler stopped")

if __name__ == "__main__":
    main() 