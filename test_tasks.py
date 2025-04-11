import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
from app import app, get_db_connection
from app.tasks import analyze_sentiment

class TasksTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        app.app_context().push()
        
        # Create test database
        self.db_fd, app.config['DATABASE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_reviews.db')
        
        # Set up test database
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                product_id TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                rating FLOAT,
                date TEXT,
                sentiment FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # Insert test data
        conn.execute('INSERT INTO products (platform, product_id, url) VALUES (?, ?, ?)',
                    ('test', 'test123', 'http://example.com'))
        product_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Insert test reviews
        test_reviews = [
            (product_id, "This product is great! I love it.", 5, "2023-01-01", None),
            (product_id, "This product is okay.", 3, "2023-01-02", None),
            (product_id, "This product is terrible! I hate it.", 1, "2023-01-03", None)
        ]
        
        for review in test_reviews:
            conn.execute('''
                INSERT INTO reviews (product_id, text, rating, date, sentiment)
                VALUES (?, ?, ?, ?, ?)
            ''', review)
            
        conn.commit()
        conn.close()
        
    def tearDown(self):
        # Close and remove test database
        os.unlink(app.config['DATABASE'])
    
    @patch('app.tasks.SentimentIntensityAnalyzer')
    def test_analyze_sentiment(self, mock_sentiment_analyzer):
        # Mock sentiment analyzer
        mock_analyzer = MagicMock()
        mock_analyzer.polarity_scores.side_effect = [
            {'compound': 0.8}, # Positive
            {'compound': 0.0}, # Neutral
            {'compound': -0.8} # Negative
        ]
        mock_sentiment_analyzer.return_value = mock_analyzer
        
        # Get product ID from database
        conn = get_db_connection()
        product_id = conn.execute('SELECT id FROM products WHERE product_id = ?', ('test123',)).fetchone()[0]
        conn.close()
        
        # Call the task
        result = analyze_sentiment(product_id)
        
        # Verify task completed successfully
        self.assertTrue(result['success'])
        
        # Verify sentiment values were saved
        conn = get_db_connection()
        reviews = conn.execute('SELECT sentiment FROM reviews WHERE product_id = ?', (product_id,)).fetchall()
        conn.close()
        
        # Check sentiment values
        sentiments = [review[0] for review in reviews]
        self.assertEqual(len(sentiments), 3)
        self.assertAlmostEqual(sentiments[0], 0.8)
        self.assertAlmostEqual(sentiments[1], 0.0)
        self.assertAlmostEqual(sentiments[2], -0.8)
        
if __name__ == '__main__':
    unittest.main() 