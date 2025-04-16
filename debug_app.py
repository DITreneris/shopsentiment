"""
Simple debug script to run the application with minimal configuration.
"""

import os
import sys
import logging

try:
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: python-dotenv package not installed. Installing now...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    from dotenv import load_dotenv

# Configure logging - show ALL logs
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Force SQLite mode for simplicity
os.environ['USE_SQLITE'] = 'True'
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

# Import the application factory
from src import create_app

# Create the app
app = create_app()

if __name__ == '__main__':
    print("Starting application in DEBUG mode with SQLite database")
    print("App URL: http://localhost:5000")
    print("Dashboard URL: http://localhost:5000/dashboard")
    app.run(host='127.0.0.1', port=5000, debug=True) 