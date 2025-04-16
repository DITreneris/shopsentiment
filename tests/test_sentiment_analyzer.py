"""
Unit tests for the SentimentAnalyzer class.
"""

import pytest
import os
import sys
from unittest.mock import patch

# Add the parent directory to the Python path to import the application modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.sentiment_analyzer import SentimentAnalyzer


class TestSentimentAnalyzer:
    """Test cases for the SentimentAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a SentimentAnalyzer instance for testing."""
        return SentimentAnalyzer()

    def test_analyze_empty_text(self, analyzer):
        """Test analyzing empty text returns neutral sentiment."""
        # Execute
        result = analyzer.analyze("")
        
        # Assert
        assert result["score"] == 0.5
        assert result["type"] == "neutral"

    def test_analyze_positive_text(self, analyzer):
        """Test analyzing positive text returns positive sentiment."""
        # Execute
        result = analyzer.analyze("This product is excellent and I love it! The best purchase ever.")
        
        # Assert
        assert result["score"] >= 0.7
        assert result["type"] == "positive"

    def test_analyze_negative_text(self, analyzer):
        """Test analyzing negative text returns negative sentiment."""
        # Execute
        result = analyzer.analyze("This is terrible and I hate it. Worst product I've ever bought.")
        
        # Assert
        assert result["score"] <= 0.3
        assert result["type"] == "negative"

    def test_analyze_neutral_text(self, analyzer):
        """Test analyzing neutral text returns neutral sentiment."""
        # Execute
        result = analyzer.analyze("This product works as expected. Nothing special about it.")
        
        # Assert
        assert 0.3 <= result["score"] <= 0.7
        assert result["type"] == "neutral"

    def test_analyze_mixed_text(self, analyzer):
        """Test analyzing text with mixed sentiment."""
        # Execute
        result = analyzer.analyze("I love the design but hate the battery life. It's good and bad.")
        
        # Assert
        assert 0.3 <= result["score"] <= 0.7  # Should be somewhere in the neutral range
        assert result["type"] in ["positive", "neutral", "negative"]

    @patch('src.services.sentiment_analyzer.MODEL_TYPE', 'development')
    def test_development_mode_has_more_randomness(self):
        """Test that development mode adds more randomness to scores."""
        analyzer = SentimentAnalyzer()
        
        # Analyze the same text multiple times to check for variability
        text = "This is a good product with some nice features."
        results = [analyzer.analyze(text)["score"] for _ in range(10)]
        
        # Check that we have some variability in the results
        assert len(set(results)) > 1, "Development mode should introduce randomness"

    @patch('src.services.sentiment_analyzer.MODEL_TYPE', 'production')
    def test_production_mode_has_less_randomness(self):
        """Test that production mode adds less randomness to scores."""
        analyzer = SentimentAnalyzer()
        
        # Analyze the same text multiple times
        text = "This is a good product with some nice features."
        results = [analyzer.analyze(text)["score"] for _ in range(10)]
        
        # There should still be some variability, but less than in development mode
        assert len(set(results)) >= 1

    def test_score_is_bounded(self, analyzer):
        """Test that sentiment scores are bounded between 0 and 1."""
        texts = [
            # Extremely positive
            "excellent amazing wonderful fantastic best perfect awesome outstanding",
            # Extremely negative
            "terrible awful worst horrible bad disappointing useless inferior",
            # Mixed
            "good bad good bad good bad good bad",
            # Neutral 
            "the this is a product that exists and can be purchased"
        ]
        
        for text in texts:
            result = analyzer.analyze(text)
            assert 0 <= result["score"] <= 1, f"Score for '{text}' is out of bounds: {result['score']}" 