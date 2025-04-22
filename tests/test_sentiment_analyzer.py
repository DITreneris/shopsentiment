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

    def test_analyzer_is_deterministic(self):
        """Test that the analyzer gives consistent results for the same input."""
        # Instantiate analyzer directly (model_type is ignored by current implementation)
        analyzer = SentimentAnalyzer()
        
        # Analyze the same text multiple times to check for consistency
        text = "This is a good product with some nice features."
        # Get the full result dict to compare
        results = [analyzer.analyze(text) for _ in range(10)]
        
        # Check that all result dictionaries are identical
        first_result = results[0]
        all_same = all(result == first_result for result in results)
        assert all_same, "Analyzer should produce deterministic results"

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