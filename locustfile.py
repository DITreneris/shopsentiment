import time
import random
import json
from locust import HttpUser, task, between
from faker import Faker

# Initialize Faker for generating test data
fake = Faker()

class ShopSentimentUser(HttpUser):
    """
    Simulates a user interacting with the Shop Sentiment application.
    This class defines the user behavior for load testing.
    """
    
    # Wait between 1 and 5 seconds between tasks
    wait_time = between(1, 5)
    
    def on_start(self):
        """
        Initialize user session - login if needed
        """
        # Uncomment if you want to test with authentication
        # self.login()
        self.product_ids = []  # Store product IDs for later use

    def login(self):
        """
        Simulates user login
        """
        response = self.client.post("/login", {
            "email": "test@example.com", 
            "password": "password123"
        })
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
    
    @task(1)
    def visit_homepage(self):
        """
        Visit the homepage
        Weight: 1 (baseline)
        """
        response = self.client.get("/")
        if response.status_code == 200:
            # Extract product IDs from homepage if available
            # This is a simplified example - adjust based on your actual HTML structure
            if "<div class='product'" in response.text:
                # Simple parsing - in real tests, use proper HTML parsing
                for line in response.text.split("\n"):
                    if "data-product-id" in line:
                        try:
                            product_id = line.split('data-product-id="')[1].split('"')[0]
                            if product_id not in self.product_ids:
                                self.product_ids.append(product_id)
                        except:
                            pass
    
    @task(3)
    def view_dashboard(self):
        """
        View product dashboard
        Weight: 3 (3x more frequent than homepage visits)
        """
        if not self.product_ids and random.random() < 0.7:
            # If no products found, use some test IDs 70% of the time
            test_ids = ["1", "2", "3", "4", "5"]
            product_id = random.choice(test_ids)
        elif self.product_ids:
            # Use a product ID we've seen
            product_id = random.choice(self.product_ids)
        else:
            # Skip this task if we have no product IDs
            return
            
        self.client.get(f"/dashboard/{product_id}")
    
    @task(2)
    def check_api_reviews(self):
        """
        Get reviews via API
        Weight: 2 (2x more frequent than homepage visits)
        """
        if not self.product_ids and random.random() < 0.7:
            # If no products found, use some test IDs 70% of the time
            test_ids = ["1", "2", "3", "4", "5"]
            product_id = random.choice(test_ids)
        elif self.product_ids:
            # Use a product ID we've seen
            product_id = random.choice(self.product_ids)
        else:
            # Skip this task if we have no product IDs
            return
            
        self.client.get(f"/api/reviews/{product_id}", 
                        name="/api/reviews/[product_id]")
    
    @task(1)
    def analyze_product(self):
        """
        Submit a product for analysis
        Weight: 1 (same frequency as homepage visits)
        """
        # Generate a random product ID format
        platform = random.choice(["amazon", "ebay"])
        
        if platform == "amazon":
            product_id = fake.bothify(text="B#########")
        else:  # ebay
            product_id = fake.numerify(text="##########")
            
        # Product URL
        url = f"https://{platform}.com/dp/{product_id}"
        
        # Submit analysis form
        response = self.client.post(
            "/analyze",
            {
                "platform": platform,
                "product_id": product_id,
                "url": url
            },
            name="/analyze"
        )
        
        # If response is a redirect to dashboard, extract product ID
        if response.status_code == 302 and "dashboard" in response.headers.get('Location', ''):
            try:
                new_product_id = response.headers['Location'].split('/')[-1]
                if new_product_id not in self.product_ids:
                    self.product_ids.append(new_product_id)
            except:
                pass
    
    @task(1)
    def filter_reviews(self):
        """
        Apply filters to review list
        Weight: 1 (same frequency as homepage visits)
        """
        if not self.product_ids:
            # Skip if no products
            return
            
        product_id = random.choice(self.product_ids)
        
        # Apply random filter
        sentiment = random.choice(["positive", "negative", "neutral", "all"])
        verified = random.choice([True, False, "all"])
        min_rating = random.choice([1, 2, 3, 4, 5, 0])
        max_rating = random.choice([5, 4, 3, 2, 1])
        
        # Ensure min_rating <= max_rating
        if min_rating > max_rating:
            min_rating, max_rating = max_rating, min_rating
            
        # Submit filter form
        self.client.post(
            f"/filter/{product_id}",
            {
                "sentiment": sentiment,
                "verified": verified,
                "min_rating": min_rating,
                "max_rating": max_rating
            },
            name="/filter/[product_id]"
        )
    
    @task(0.5)
    def export_data(self):
        """
        Export product data
        Weight: 0.5 (half as frequent as homepage visits)
        """
        if not self.product_ids:
            # Skip if no products
            return
            
        product_id = random.choice(self.product_ids)
        
        # Randomly choose export format
        export_format = random.choice(["csv", "json"])
        
        if export_format == "csv":
            self.client.get(f"/export/csv/{product_id}", 
                           name="/export/csv/[product_id]")
        else:
            self.client.get(f"/export/json/{product_id}", 
                           name="/export/json/[product_id]")

class APIUser(HttpUser):
    """
    Simulates API client traffic specifically targeting API endpoints.
    This class is more focused on backend performance.
    """
    
    # Wait between 0.1 and 3 seconds between tasks
    wait_time = between(0.1, 3)
    
    def on_start(self):
        """Get some product IDs to work with"""
        self.product_ids = ["1", "2", "3", "4", "5"]  # Default test IDs
        
        # Try to get actual product IDs
        response = self.client.get("/api/products?limit=10")
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and data:
                    self.product_ids = [product['id'] for product in data if 'id' in product]
            except:
                pass
    
    @task(10)
    def get_reviews(self):
        """
        Get reviews via API - highest frequency task
        """
        product_id = random.choice(self.product_ids)
        limit = random.choice([10, 25, 50, 100])
        offset = random.randint(0, 5) * limit if random.random() < 0.3 else 0
        
        url = f"/api/reviews/{product_id}?limit={limit}&offset={offset}"
        self.client.get(url, name="/api/reviews/[product_id]")
    
    @task(5)
    def get_dashboard_data(self):
        """
        Get dashboard data
        """
        product_id = random.choice(self.product_ids)
        self.client.get(f"/dashboard/{product_id}/data", 
                       name="/dashboard/[product_id]/data")
    
    @task(3)
    def get_sentiment_summary(self):
        """
        Get sentiment summary data
        """
        product_id = random.choice(self.product_ids)
        self.client.get(f"/api/sentiment-summary/{product_id}", 
                       name="/api/sentiment-summary/[product_id]") 