# Shop Sentiment Analysis

A web application for analyzing sentiment in product reviews across different e-commerce platforms.

## Features

- User authentication (register, login, logout)
- Product management
- Review collection and analysis
- Sentiment analysis of product reviews
- API endpoints for integration with other services

## Setup

### Requirements

- Python 3.7+
- Flask
- Other dependencies listed in `requirements.txt`

### Installation

1. Clone this repository
2. Create a virtual environment:
```
python -m venv venv
```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies:
```
pip install -r requirements.txt
```

## Running the Application

### Backend API

Run the Flask application:

```
python -m flask run --host=0.0.0.0 --port=5000
```

The API will be available at `http://localhost:5000`.

### Frontend Application

To serve the frontend:

```
python serve_frontend.py
```

This will start a server on port 8000 and automatically open your browser to `http://localhost:8000`.

## API Endpoints

The following API endpoints are available:

- `/` - API status and endpoint list
- `/health` - Health check endpoint
- `/auth/login` - User login (POST)
- `/auth/register` - User registration (POST)
- `/auth/logout` - User logout (POST)
- `/auth/me` - Current user information (GET)
- `/api/products` - Product management (GET, POST)
- `/api/products/<id>` - Specific product (GET, PUT, DELETE)
- `/api/products/<id>/reviews` - Product reviews (GET)
- `/api/products/<id>/sentiment` - Product sentiment analysis (GET)
- `/api/reviews` - Review management (GET, POST)

## Frontend Structure

The frontend application provides a simple interface for interacting with the API:

- Authentication (register, login, logout)
- Product management (add, view, delete)
- Review viewing and sentiment analysis

## Development

### Adding New Features

1. Backend: Add new routes to the appropriate files in the `app/routes` directory
2. Frontend: Update the interface in `frontend/index.html`

## Deployment

### Heroku Deployment

The application is ready to be deployed to Heroku with the following steps:

1. Make sure you have the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed and are logged in:
```
heroku login
```

2. Create a new Heroku app:
```
heroku create your-app-name
```

3. Push your code to Heroku:
```
git push heroku main
```

4. Set environment variables (if needed):
```
heroku config:set SECRET_KEY=your-secret-key
```

5. Open your deployed application:
```
heroku open
```

### Accessing the Frontend

When deployed to Heroku, the frontend is accessible at:
- `/app` - Main application interface
- `/frontend` - Alternative access to the frontend

The backend API is accessible directly at the root path and other endpoints as listed above.