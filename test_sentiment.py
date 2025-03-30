import unittest
import sys
import os
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import Counter
from nltk.tokenize import word_tokenize

# Ensure NLTK data is downloaded
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Import common stopwords from app.py
common_stopwords = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
    'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
    'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
    'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
    'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
    'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
    'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down',
    'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here',
    'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
    'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
}

class SentimentAnalysisTests(unittest.TestCase):
    """Tests for sentiment analysis functionality"""
    
    def setUp(self):
        """Set up the sentiment analyzer before each test"""
        self.analyzer = SentimentIntensityAnalyzer()
        
        # Sample review data for testing
        self.sample_reviews = [
            {"id": 1, "text": "This product is amazing! I love it so much.", "rating": 5, "date": "2023-01-01"},
            {"id": 2, "text": "Terrible quality, broke after one use.", "rating": 1, "date": "2023-01-02"},
            {"id": 3, "text": "It's okay, nothing special but it works.", "rating": 3, "date": "2023-01-03"},
            {"id": 4, "text": "Great value for the money, highly recommend!", "rating": 5, "date": "2023-01-04"},
            {"id": 5, "text": "Not worth the price, disappointed.", "rating": 2, "date": "2023-01-05"},
        ]
        
        # Convert to DataFrame for processing
        self.reviews_df = pd.DataFrame(self.sample_reviews)
        
    def test_sentiment_scores(self):
        """Test that sentiment scores are calculated correctly"""
        # Test positive sentiment
        positive_text = "This product is amazing! I love it so much."
        positive_score = self.analyzer.polarity_scores(positive_text)['compound']
        self.assertGreater(positive_score, 0.05, "Positive text should have score > 0.05")
        
        # Test negative sentiment
        negative_text = "Terrible quality, broke after one use."
        negative_score = self.analyzer.polarity_scores(negative_text)['compound']
        self.assertLess(negative_score, -0.05, "Negative text should have score < -0.05")
        
        # Test neutral sentiment
        neutral_text = "It's okay, nothing special but it works."
        neutral_score = self.analyzer.polarity_scores(neutral_text)['compound']
        self.assertGreaterEqual(neutral_score, -0.05, "Neutral text should have score >= -0.05")
        self.assertLessEqual(neutral_score, 0.05, "Neutral text should have score <= 0.05")
    
    def test_sentiment_distribution(self):
        """Test sentiment distribution calculation"""
        # Add sentiment scores to the DataFrame
        self.reviews_df['sentiment'] = self.reviews_df['text'].apply(
            lambda text: self.analyzer.polarity_scores(text)['compound']
        )
        
        # Calculate sentiment distribution
        sentiment_counts = {
            'Positive': len(self.reviews_df[self.reviews_df['sentiment'] > 0.05]),
            'Neutral': len(self.reviews_df[(self.reviews_df['sentiment'] >= -0.05) & (self.reviews_df['sentiment'] <= 0.05)]),
            'Negative': len(self.reviews_df[self.reviews_df['sentiment'] < -0.05])
        }
        
        # Check that distribution is as expected
        self.assertEqual(sentiment_counts['Positive'], 2, "Should have 2 positive reviews")
        self.assertEqual(sentiment_counts['Negative'], 2, "Should have 2 negative reviews")
        self.assertEqual(sentiment_counts['Neutral'], 1, "Should have 1 neutral review")
        
    def test_keyword_extraction(self):
        """Test keyword extraction functionality"""
        # Combine all review text
        all_text = ' '.join(self.reviews_df['text'].tolist())
        
        # Extract keywords
        words = [word.lower() for word in word_tokenize(all_text) 
                if word.isalpha() and len(word) > 3 and word.lower() not in common_stopwords]
        
        keywords = dict(Counter(words).most_common(10))
        
        # Check that expected keywords are present
        self.assertIn('product', keywords, "Common word 'product' should be in keywords")
        self.assertIn('quality', keywords, "Common word 'quality' should be in keywords")
        
        # Check that stopwords are filtered out
        self.assertNotIn('the', keywords, "Stopword 'the' should not be in keywords")
        self.assertNotIn('is', keywords, "Stopword 'is' should not be in keywords")
        
    def test_sentiment_correlation_with_ratings(self):
        """Test that sentiment scores generally correlate with star ratings"""
        # Add sentiment scores to the DataFrame
        self.reviews_df['sentiment'] = self.reviews_df['text'].apply(
            lambda text: self.analyzer.polarity_scores(text)['compound']
        )
        
        # Calculate correlation between sentiment and rating
        correlation = self.reviews_df['sentiment'].corr(self.reviews_df['rating'])
        
        # Verify strong positive correlation (> 0.7)
        self.assertGreater(correlation, 0.7, 
                          f"Sentiment and star rating should have strong correlation (got {correlation})")
    
    def test_sentiment_classification(self):
        """Test sentiment classification based on thresholds"""
        texts = {
            "positive": "This is excellent. I really love it!",
            "neutral": "It's okay I guess. Nothing special.",
            "negative": "I hate this product. Very disappointing."
        }
        
        # Calculate sentiment scores
        scores = {
            category: self.analyzer.polarity_scores(text)['compound'] 
            for category, text in texts.items()
        }
        
        # Classify using the same thresholds as the application
        classifications = {
            category: ("positive" if score > 0.05 else 
                      "negative" if score < -0.05 else 
                      "neutral")
            for category, score in scores.items()
        }
        
        # Check that classifications match expectations
        self.assertEqual(classifications["positive"], "positive", "Should classify positive text correctly")
        self.assertEqual(classifications["neutral"], "neutral", "Should classify neutral text correctly")
        self.assertEqual(classifications["negative"], "negative", "Should classify negative text correctly")

if __name__ == '__main__':
    unittest.main() 