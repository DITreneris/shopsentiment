import os

# Set Flask environment variables
os.environ['FLASK_APP'] = 'app'
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

# Import and run the app
from app import app

if __name__ == '__main__':
    app.run(debug=True) 