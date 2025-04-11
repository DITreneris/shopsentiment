import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')

# Data Collection Settings
COMPETITOR_SCRAPING_INTERVAL = 3600  # 1 hour in seconds
MAX_COMPETITOR_PRODUCTS = 1000
RATE_LIMIT_DELAY = 1  # seconds between requests

# ML Model Settings
MODEL_SAVE_PATH = 'models/recommendation_model.pkl'
TRAINING_INTERVAL = 86400  # 24 hours in seconds
MIN_TRAINING_SAMPLES = 100

# Feature Engineering Settings
PRICE_BINS = 10
CATEGORY_EMBEDDING_SIZE = 16

# API Settings
API_HOST = '0.0.0.0'
API_PORT = 8000
API_WORKERS = 4

# Logging Configuration
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/recommendation_system.log'

# Create necessary directories
os.makedirs('models', exist_ok=True)
os.makedirs('logs', exist_ok=True) 