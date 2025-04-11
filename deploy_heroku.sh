#!/bin/bash

# Heroku Deployment Script for Shop Sentiment Analysis

echo "Deploying Shop Sentiment Analysis to Heroku..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "Error: Heroku CLI is not installed. Please install it first."
    echo "Visit: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if user is logged in to Heroku
heroku whoami &> /dev/null
if [ $? -ne 0 ]; then
    echo "You need to log in to Heroku first:"
    heroku login
fi

# Get app name from user or use default
read -p "Enter your Heroku app name (or press Enter to create a random name): " APP_NAME

if [ -z "$APP_NAME" ]; then
    # Create Heroku app with random name
    echo "Creating Heroku app with random name..."
    heroku create
else
    # Create Heroku app with specified name
    echo "Creating Heroku app: $APP_NAME..."
    heroku create $APP_NAME
fi

# Set environment variables
echo "Setting environment variables..."
heroku config:set SECRET_KEY=$(openssl rand -hex 32)

# Push code to Heroku
echo "Pushing code to Heroku..."
git push heroku main

# Run database migrations if necessary
# echo "Running database migrations..."
# heroku run python manage.py db upgrade

# Open the app in browser
echo "Opening app in browser..."
heroku open

echo "Deployment completed!"
echo "Frontend is available at: https://YOUR-APP-NAME.herokuapp.com/app"
echo "API is available at: https://YOUR-APP-NAME.herokuapp.com/" 