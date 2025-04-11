import logging
import json
import os
import time
import datetime
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("multi_language_evaluation.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("multi_language_evaluation")

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
TEST_DATA_DIR = Path("app/multi_language/evaluation/test_data")
MODELS_DIR = Path("app/multi_language/models")

# Ensure directories exist
METRICS_DIR.mkdir(parents=True, exist_ok=True)
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

class LanguageAccuracyMeasurement:
    """
    Measure sentiment analysis accuracy across different languages
    """
    
    def __init__(self):
        """Initialize the accuracy measurement system"""
        self.metrics = {}
        self.raw_results = {}
        self.test_data = {}
        self.load_test_data()
    
    def load_test_data(self) -> None:
        """Load test data for each language"""
        for lang in SUPPORTED_LANGUAGES:
            data_file = TEST_DATA_DIR / f"{lang}_test_data.csv"
            if data_file.exists():
                try:
                    self.test_data[lang] = pd.read_csv(data_file)
                    logger.info(f"Loaded test data for {LANGUAGE_NAMES.get(lang, lang)}: {len(self.test_data[lang])} samples")
                except Exception as e:
                    logger.error(f"Error loading test data for {lang}: {str(e)}")
            else:
                logger.warning(f"No test data file found for {lang}")
    
    def _create_dummy_predictions(self, lang: str) -> pd.DataFrame:
        """
        Create dummy predictions for testing the system
        In a real implementation, this would call your actual model
        """
        if lang not in self.test_data:
            raise ValueError(f"No test data available for {lang}")
        
        df = self.test_data[lang].copy()
        
        # Create dummy predictions that are correct ~85% of the time
        np.random.seed(42)  # For reproducibility
        correct_mask = np.random.random(len(df)) < 0.85
        
        # Start with true labels
        df['predicted_sentiment'] = df['true_sentiment'].copy()
        
        # For ~15% of samples, generate incorrect predictions
        incorrect_indices = df.index[~correct_mask]
        for idx in incorrect_indices:
            true_label = df.at[idx, 'true_sentiment']
            # Simple logic to flip the sentiment
            if true_label == 'positive':
                df.at[idx, 'predicted_sentiment'] = np.random.choice(['negative', 'neutral'])
            elif true_label == 'negative':
                df.at[idx, 'predicted_sentiment'] = np.random.choice(['positive', 'neutral'])
            else:  # neutral
                df.at[idx, 'predicted_sentiment'] = np.random.choice(['positive', 'negative'])
        
        return df
    
    def predict_sentiment(self, lang: str, texts: List[str]) -> List[str]:
        """
        Predict sentiment for a list of texts in the specified language
        This would call your actual model in a real implementation
        
        Returns a list of sentiment labels: 'positive', 'negative', 'neutral'
        """
        # Placeholder for actual model prediction
        # In a real implementation, this would:
        # 1. Load the language-specific model
        # 2. Preprocess the texts
        # 3. Run prediction
        # 4. Return the results
        
        np.random.seed(hash(str(texts)) % 1000)  # Semi-deterministic seed
        
        # Simulate different accuracy levels per language
        accuracy_levels = {
            "en": 0.92,  # English - highest accuracy
            "fr": 0.88,  # French
            "de": 0.86,  # German
            "es": 0.84,  # Spanish
            "it": 0.82,  # Italian - lowest accuracy
        }
        
        # Default accuracy if language not in our list
        accuracy = accuracy_levels.get(lang, 0.80)
        
        # Generate dummy predictions
        predictions = []
        for text in texts:
            # Simplified logic to generate predictions with language-specific accuracy
            if np.random.random() < accuracy:
                # For demonstration, use naive sentiment detection based on keywords
                text_lower = text.lower()
                if "good" in text_lower or "great" in text_lower or "excellent" in text_lower:
                    sentiment = "positive"
                elif "bad" in text_lower or "terrible" in text_lower or "poor" in text_lower:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
            else:
                # Random incorrect prediction
                sentiment = np.random.choice(["positive", "negative", "neutral"])
            
            predictions.append(sentiment)
        
        return predictions
    
    def evaluate_language(self, lang: str) -> Dict[str, float]:
        """
        Evaluate sentiment analysis accuracy for a specific language
        Returns a dictionary of metrics
        """
        if lang not in self.test_data:
            logger.error(f"No test data available for {lang}")
            return {
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "support": 0,
                "error_rate": 1.0,
                "timestamp": datetime.datetime.now().isoformat()
            }
        
        try:
            # Get test data
            test_df = self.test_data[lang]
            
            # Get texts and true labels
            texts = test_df['text'].tolist()
            true_labels = test_df['true_sentiment'].tolist()
            
            # Get predictions
            predicted_labels = self.predict_sentiment(lang, texts)
            
            # Store raw results for detailed analysis
            self.raw_results[lang] = {
                "texts": texts,
                "true_labels": true_labels,
                "predicted_labels": predicted_labels
            }
            
            # Calculate metrics
            accuracy = accuracy_score(true_labels, predicted_labels)
            precision, recall, f1, support = precision_recall_fscore_support(
                true_labels, 
                predicted_labels, 
                average='weighted'
            )
            conf_matrix = confusion_matrix(
                true_labels, 
                predicted_labels, 
                labels=["positive", "negative", "neutral"]
            )
            
            # Create metrics dictionary
            metrics = {
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
                "support": int(np.sum(support)),
                "error_rate": float(1.0 - accuracy),
                "confusion_matrix": conf_matrix.tolist(),
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Store metrics
            self.metrics[lang] = metrics
            
            # Save metrics to file
            self.save_metrics(lang)
            
            logger.info(f"Evaluated {LANGUAGE_NAMES.get(lang, lang)} sentiment analysis: accuracy={accuracy:.3f}, f1={f1:.3f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating language {lang}: {str(e)}")
            return {
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "support": 0,
                "error_rate": 1.0,
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def save_metrics(self, lang: str) -> None:
        """Save metrics for a language to file"""
        if lang not in self.metrics:
            logger.warning(f"No metrics to save for {lang}")
            return
        
        metrics_file = METRICS_DIR / f"{lang}_metrics.json"
        try:
            with open(metrics_file, "w") as f:
                json.dump(self.metrics[lang], f, indent=2)
            logger.info(f"Saved metrics for {LANGUAGE_NAMES.get(lang, lang)} to {metrics_file}")
        except Exception as e:
            logger.error(f"Error saving metrics for {lang}: {str(e)}")
    
    def generate_error_analysis(self, lang: str) -> Dict[str, Any]:
        """
        Generate detailed error analysis for a language
        """
        if lang not in self.raw_results:
            logger.warning(f"No results to analyze for {lang}")
            return {}
        
        raw_data = self.raw_results[lang]
        texts = raw_data["texts"]
        true_labels = raw_data["true_labels"]
        predicted_labels = raw_data["predicted_labels"]
        
        # Create DataFrame for analysis
        df = pd.DataFrame({
            "text": texts,
            "true_sentiment": true_labels,
            "predicted_sentiment": predicted_labels,
            "is_correct": [t == p for t, p in zip(true_labels, predicted_labels)]
        })
        
        # Analyze errors by sentiment class
        error_by_class = {}
        for sentiment in ["positive", "negative", "neutral"]:
            class_df = df[df["true_sentiment"] == sentiment]
            if len(class_df) > 0:
                error_rate = 1.0 - class_df["is_correct"].mean()
                error_by_class[sentiment] = {
                    "count": len(class_df),
                    "error_rate": error_rate,
                    "examples": class_df[~class_df["is_correct"]].head(5)["text"].tolist()
                }
        
        # Find most common misclassifications
        misclassifications = {}
        for true_sentiment in ["positive", "negative", "neutral"]:
            misclassifications[true_sentiment] = {}
            for pred_sentiment in ["positive", "negative", "neutral"]:
                if true_sentiment != pred_sentiment:
                    count = len(df[(df["true_sentiment"] == true_sentiment) & 
                                  (df["predicted_sentiment"] == pred_sentiment)])
                    if count > 0:
                        misclassifications[true_sentiment][pred_sentiment] = count
        
        # Create final analysis report
        analysis = {
            "language": lang,
            "language_name": LANGUAGE_NAMES.get(lang, lang),
            "total_samples": len(df),
            "accuracy": df["is_correct"].mean(),
            "error_rate": 1.0 - df["is_correct"].mean(),
            "error_by_class": error_by_class,
            "misclassifications": misclassifications,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Save analysis to file
        analysis_file = METRICS_DIR / f"{lang}_error_analysis.json"
        try:
            with open(analysis_file, "w") as f:
                # Convert DataFrame examples to lists for JSON serialization
                json_analysis = analysis.copy()
                for sentiment in json_analysis["error_by_class"]:
                    if "examples" in json_analysis["error_by_class"][sentiment]:
                        examples = json_analysis["error_by_class"][sentiment]["examples"]
                        if isinstance(examples, pd.Series):
                            json_analysis["error_by_class"][sentiment]["examples"] = examples.tolist()
                
                json.dump(json_analysis, f, indent=2)
            logger.info(f"Saved error analysis for {LANGUAGE_NAMES.get(lang, lang)} to {analysis_file}")
        except Exception as e:
            logger.error(f"Error saving analysis for {lang}: {str(e)}")
        
        return analysis
    
    def evaluate_all_languages(self) -> Dict[str, Dict[str, float]]:
        """
        Evaluate sentiment analysis accuracy for all supported languages
        Returns a dictionary of language metrics
        """
        all_metrics = {}
        
        for lang in SUPPORTED_LANGUAGES:
            logger.info(f"Evaluating {LANGUAGE_NAMES.get(lang, lang)} sentiment analysis...")
            metrics = self.evaluate_language(lang)
            all_metrics[lang] = metrics
            
            # Generate error analysis
            self.generate_error_analysis(lang)
        
        return all_metrics
    
    def generate_cross_language_report(self) -> Dict[str, Any]:
        """
        Generate a report comparing accuracy across languages
        """
        if not self.metrics:
            logger.warning("No metrics available for cross-language report")
            self.evaluate_all_languages()
        
        # Extract key metrics for comparison
        comparison = {
            "accuracy": {},
            "f1_score": {},
            "precision": {},
            "recall": {},
            "error_rate": {}
        }
        
        for lang, metrics in self.metrics.items():
            for metric_name in comparison:
                if metric_name in metrics:
                    comparison[metric_name][lang] = metrics[metric_name]
        
        # Generate rankings
        rankings = {}
        for metric_name, values in comparison.items():
            if metric_name == "error_rate":
                # Lower is better for error rate
                rankings[metric_name] = {k: i+1 for i, (k, _) in 
                                        enumerate(sorted(values.items(), key=lambda x: x[1]))}
            else:
                # Higher is better for other metrics
                rankings[metric_name] = {k: i+1 for i, (k, _) in 
                                        enumerate(sorted(values.items(), key=lambda x: x[1], reverse=True))}
        
        # Calculate average ranking
        avg_rankings = {}
        for lang in SUPPORTED_LANGUAGES:
            if lang in self.metrics:
                ranks = [rankings[m].get(lang, len(SUPPORTED_LANGUAGES)) for m in comparison if lang in rankings.get(m, {})]
                avg_rankings[lang] = sum(ranks) / len(ranks) if ranks else float('inf')
        
        # Create final report
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics_by_language": self.metrics,
            "cross_language_comparison": comparison,
            "rankings": rankings,
            "average_rankings": avg_rankings,
            "best_performing_language": min(avg_rankings.items(), key=lambda x: x[1])[0] if avg_rankings else None,
            "worst_performing_language": max(avg_rankings.items(), key=lambda x: x[1])[0] if avg_rankings else None
        }
        
        # Save report to file
        report_file = METRICS_DIR / f"cross_language_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Saved cross-language report to {report_file}")
        except Exception as e:
            logger.error(f"Error saving cross-language report: {str(e)}")
        
        return report

def generate_sample_test_data():
    """
    Generate sample test data for each language
    This is for demonstration purposes only
    """
    samples_per_language = 1000
    
    # Sample texts for each language (very simplified)
    language_samples = {
        "en": [
            "This product is amazing!",
            "I'm very disappointed with the quality.",
            "It's an average product, nothing special."
        ],
        "fr": [
            "Ce produit est incroyable!",
            "Je suis très déçu de la qualité.",
            "C'est un produit moyen, rien de spécial."
        ],
        "de": [
            "Dieses Produkt ist erstaunlich!",
            "Ich bin sehr enttäuscht von der Qualität.",
            "Es ist ein durchschnittliches Produkt, nichts Besonderes."
        ],
        "es": [
            "¡Este producto es increíble!",
            "Estoy muy decepcionado con la calidad.",
            "Es un producto promedio, nada especial."
        ],
        "it": [
            "Questo prodotto è incredibile!",
            "Sono molto deluso dalla qualità.",
            "È un prodotto medio, niente di speciale."
        ]
    }
    
    # Sentiment labels
    sentiments = ["positive", "negative", "neutral"]
    
    # Create test data for each language
    for lang, samples in language_samples.items():
        data = []
        
        # Generate random test data based on samples
        for _ in range(samples_per_language):
            # Select a random sample and its corresponding sentiment
            idx = np.random.randint(0, len(samples))
            text = samples[idx]
            sentiment = sentiments[idx]
            
            # Add some random variations
            if np.random.random() < 0.3:
                # Add some random words
                words = text.split()
                position = np.random.randint(0, len(words) + 1)
                extra_words = ["very", "really", "somewhat", "extremely", "slightly"]
                words.insert(position, np.random.choice(extra_words))
                text = " ".join(words)
            
            data.append({
                "text": text,
                "true_sentiment": sentiment
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Save to CSV
        file_path = TEST_DATA_DIR / f"{lang}_test_data.csv"
        df.to_csv(file_path, index=False)
        logger.info(f"Generated sample test data for {LANGUAGE_NAMES.get(lang, lang)}: {len(df)} samples")

def main():
    """Main entry point for accuracy measurement"""
    # Create test directories if they don't exist
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate sample test data if needed
    if not any(TEST_DATA_DIR.glob("*_test_data.csv")):
        logger.info("Generating sample test data...")
        generate_sample_test_data()
    
    # Create accuracy measurement instance
    accuracy_measurement = LanguageAccuracyMeasurement()
    
    # Evaluate all languages
    logger.info("Evaluating sentiment analysis across all languages...")
    all_metrics = accuracy_measurement.evaluate_all_languages()
    
    # Generate cross-language report
    logger.info("Generating cross-language comparison report...")
    report = accuracy_measurement.generate_cross_language_report()
    
    logger.info("Language evaluation complete")
    
    return report

if __name__ == "__main__":
    main() 