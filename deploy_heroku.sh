#!/bin/bash

# Shop Sentiment Heroku Deployment Script

echo "Shop Sentiment Heroku Deployment"
echo "================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not found. Please install Python 3."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is required but not found. Please install pip3."
    exit 1
fi

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "Heroku CLI is required but not found."
    echo "Please install Heroku CLI from: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "Git is required but not found. Please install Git."
    exit 1
fi

# Run the Python deployment script
echo "Running deployment script..."
python3 deploy_heroku.py

# Check the exit status
if [ $? -ne 0 ]; then
    echo "Deployment failed. Please check the error messages above."
    exit 1
fi

echo "Deployment process completed!" 