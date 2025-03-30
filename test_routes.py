import unittest
import os
import sys
import tempfile
import shutil
import json
from app import app, init_db

class FlaskRoutesTests(unittest.TestCase):
    """Tests for Flask routes and API endpoints"""
    
    def setUp(self):
        """Set up test client and temp database"""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test database path
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Configure Flask app for testing
        app.config['TESTING'] = True
        app.config['DATABASE'] = self.db_path
        
        # Create test client
        self.client = app.test_client()
        
        # Initialize the database
        with app.app_context():
            init_db()
        
        # Insert test data
        self.insert_test_data()
    
    def tearDown(self):
        """Clean up after tests"""
        os.close(self.db_fd)
        os.unlink(self.db_path)
        shutil.rmtree(self.test_dir)
    
    def insert_test_data(self):
        """Insert test product and reviews into the database"""
        # Connect to database
        from app import get_db_connection
        conn = get_db_connection()
        
        # Insert test product
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO products (platform, product_id, url) VALUES (?, ?, ?)',
            ('test_platform', 'test123', 'http://example.com/test123')
        )
        product_id = cursor.lastrowid
        
        # Insert test reviews
        test_reviews = [
            (product_id, "This is a great product!", 5.0, "2023-01-01", 0.8),
            (product_id, "It's okay, nothing special.", 3.0, "2023-01-02", 0.0),
            (product_id, "Very disappointed with this.", 1.0, "2023-01-03", -0.7),
        ]
        
        for review in test_reviews:
            cursor.execute(
                'INSERT INTO reviews (product_id, text, rating, date, sentiment) VALUES (?, ?, ?, ?, ?)',
                review
            )
        
        conn.commit()
        conn.close()
        
        # Store product_id for later tests
        self.test_product_id = product_id
    
    def test_index_route(self):
        """Test the index route returns 200 OK"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200, "Index route should return 200 OK")
        self.assertIn(b'ShopSentiment', response.data, "Index page should contain the app name")
    
    def test_dashboard_route(self):
        """Test the dashboard route with a valid product ID"""
        response = self.client.get(f'/dashboard/{self.test_product_id}')
        self.assertEqual(response.status_code, 200, "Dashboard route should return 200 OK")
        self.assertIn(b'Analysis Results', response.data, "Dashboard should show analysis results")
        self.assertIn(b'test_platform', response.data, "Dashboard should show platform name")
        self.assertIn(b'test123', response.data, "Dashboard should show product ID")
    
    def test_dashboard_invalid_product(self):
        """Test the dashboard route with an invalid product ID"""
        invalid_id = 9999  # Assuming this ID doesn't exist
        response = self.client.get(f'/dashboard/{invalid_id}')
        self.assertEqual(response.status_code, 302, "Invalid product ID should redirect")
        self.assertIn('/index', response.location, "Should redirect to index page")
    
    def test_api_reviews_endpoint(self):
        """Test the API endpoint for getting reviews"""
        response = self.client.get(f'/api/reviews/{self.test_product_id}')
        self.assertEqual(response.status_code, 200, "API endpoint should return 200 OK")
        
        # Parse JSON response
        data = json.loads(response.data)
        
        # Check response structure
        self.assertIsInstance(data, list, "Response should be a list")
        self.assertEqual(len(data), 3, "Should return 3 test reviews")
        
        # Check review data
        for review in data:
            self.assertIn('id', review, "Review should have an ID")
            self.assertIn('text', review, "Review should have text")
            self.assertIn('rating', review, "Review should have a rating")
            self.assertIn('sentiment', review, "Review should have a sentiment score")
    
    def test_export_csv_endpoint(self):
        """Test the CSV export endpoint"""
        response = self.client.get(f'/export/csv/{self.test_product_id}')
        self.assertEqual(response.status_code, 200, "CSV export should return 200 OK")
        self.assertEqual(response.mimetype, 'text/csv', "Response should be CSV")
        self.assertIn('attachment', response.headers['Content-Disposition'], "Should be an attachment")
        
        # Check CSV content
        csv_data = response.data.decode('utf-8')
        self.assertIn('id,date,rating,sentiment,text', csv_data, "CSV should have headers")
        self.assertIn('This is a great product', csv_data, "CSV should contain review text")
    
    def test_export_json_endpoint(self):
        """Test the JSON export endpoint"""
        response = self.client.get(f'/export/json/{self.test_product_id}')
        self.assertEqual(response.status_code, 200, "JSON export should return 200 OK")
        self.assertEqual(response.mimetype, 'application/json', "Response should be JSON")
        self.assertIn('attachment', response.headers['Content-Disposition'], "Should be an attachment")
        
        # Parse JSON content
        try:
            json_data = json.loads(response.data)
            self.assertIn('product', json_data, "JSON should have product info")
            self.assertIn('reviews', json_data, "JSON should have reviews")
            self.assertEqual(len(json_data['reviews']), 3, "Should have 3 reviews")
            self.assertIn('export_date', json_data, "JSON should have export date")
            self.assertEqual(json_data['total_reviews'], 3, "Should have 3 total reviews")
        except json.JSONDecodeError:
            self.fail("Response is not valid JSON")
    
    def test_analyze_endpoint(self):
        """Test the analyze endpoint with form data"""
        form_data = {
            'platform': 'test_platform',
            'product_id': 'new_test456',
            'url': 'http://example.com/new_test456'
        }
        
        response = self.client.post('/analyze', data=form_data, follow_redirects=False)
        self.assertEqual(response.status_code, 302, "Should redirect after submission")
        self.assertIn('/dashboard/', response.location, "Should redirect to dashboard")
        
        # Verify that a new product was created in the database
        from app import get_db_connection
        conn = get_db_connection()
        product = conn.execute(
            'SELECT * FROM products WHERE product_id = ?', 
            ('new_test456',)
        ).fetchone()
        conn.close()
        
        self.assertIsNotNone(product, "New product should be created in database")
        self.assertEqual(product['platform'], 'test_platform', "Platform should match form data")
        self.assertEqual(product['url'], 'http://example.com/new_test456', "URL should match form data")

if __name__ == '__main__':
    unittest.main() 