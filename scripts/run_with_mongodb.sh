#!/bin/bash
# This script helps set up and run the ShopSentiment application with MongoDB

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}ShopSentiment MongoDB Setup Script${NC}"
echo "=================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check if Python is installed
if command -v python3 &>/dev/null; then
    echo -e "${GREEN}✓${NC} Python 3 is installed"
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    echo -e "${GREEN}✓${NC} Python is installed"
    PYTHON_CMD="python"
else
    echo -e "${RED}✗${NC} Python is not installed. Please install Python 3.8 or higher"
    exit 1
fi

# Check if pip is installed
if command -v pip3 &>/dev/null; then
    echo -e "${GREEN}✓${NC} pip3 is installed"
    PIP_CMD="pip3"
elif command -v pip &>/dev/null; then
    echo -e "${GREEN}✓${NC} pip is installed"
    PIP_CMD="pip"
else
    echo -e "${RED}✗${NC} pip is not installed. Please install pip"
    exit 1
fi

# Check if MongoDB is installed locally (only needed for local development)
if command -v mongod &>/dev/null; then
    echo -e "${GREEN}✓${NC} MongoDB is installed locally"
    MONGO_LOCAL=true
else
    echo -e "${YELLOW}!${NC} MongoDB is not installed locally. Using Docker or remote MongoDB Atlas is recommended."
    MONGO_LOCAL=false
fi

# Check if Docker is installed (optional)
if command -v docker &>/dev/null; then
    echo -e "${GREEN}✓${NC} Docker is installed"
    DOCKER_AVAILABLE=true
else
    echo -e "${YELLOW}!${NC} Docker is not installed. Local installation will be used."
    DOCKER_AVAILABLE=false
fi

echo ""
echo "Setting up environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi
echo -e "${GREEN}✓${NC} Virtual environment activated"

# Install requirements
echo "Installing requirements..."
$PIP_CMD install -r requirements.txt
echo -e "${GREEN}✓${NC} Requirements installed"

# Download NLTK data
echo "Downloading NLTK data..."
$PYTHON_CMD -c "import nltk; nltk.download('vader_lexicon')"
echo -e "${GREEN}✓${NC} NLTK data downloaded"

echo ""
echo "MongoDB Configuration"
echo "====================="

# Ask for MongoDB URI
echo "Enter your MongoDB connection URI:"
echo "- For MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/"
echo "- For local MongoDB: mongodb://localhost:27017/"
echo "- Press Enter to use default (mongodb://localhost:27017/)"
read -p "MongoDB URI: " MONGODB_URI
MONGODB_URI=${MONGODB_URI:-mongodb://localhost:27017/}

# Ask for database name
echo "Enter the MongoDB database name (default: shopsentiment):"
read -p "Database name: " MONGODB_DB_NAME
MONGODB_DB_NAME=${MONGODB_DB_NAME:-shopsentiment}

# Create or update .env file
echo "Updating .env file..."
if [ -f ".env" ]; then
    # Update existing .env file
    grep -v "MONGODB_URI\|MONGODB_DB_NAME" .env > .env.tmp
    echo "MONGODB_URI=$MONGODB_URI" >> .env.tmp
    echo "MONGODB_DB_NAME=$MONGODB_DB_NAME" >> .env.tmp
    mv .env.tmp .env
else
    # Create new .env file
    echo "FLASK_APP=app" > .env
    echo "FLASK_ENV=development" >> .env
    echo "SECRET_KEY=dev_key_change_me_in_production" >> .env
    echo "MONGODB_URI=$MONGODB_URI" >> .env
    echo "MONGODB_DB_NAME=$MONGODB_DB_NAME" >> .env
fi
echo -e "${GREEN}✓${NC} .env file updated"

echo ""
echo "Database Migration"
echo "=================="
echo "Do you want to migrate data from SQLite to MongoDB? (y/n)"
read -p "Migrate data: " MIGRATE_DATA
if [[ $MIGRATE_DATA == "y" || $MIGRATE_DATA == "Y" ]]; then
    echo "Running migration script..."
    $PYTHON_CMD scripts/migrate_to_mongodb.py --sqlite-path=data/shopsentiment.db --mongo-uri="$MONGODB_URI" --mongo-db="$MONGODB_DB_NAME"
    echo -e "${GREEN}✓${NC} Data migration completed"
fi

echo ""
echo "Starting Application"
echo "===================="
echo "Choose how to start the application:"
echo "1) Run with Flask development server (local development)"
echo "2) Run with Docker Compose (recommended for testing production setup)"
echo "3) Exit without starting"
read -p "Select option (1-3): " START_OPTION

case $START_OPTION in
    1)
        echo "Starting Flask development server..."
        export FLASK_APP=app
        export FLASK_ENV=development
        export MONGODB_URI=$MONGODB_URI
        export MONGODB_DB_NAME=$MONGODB_DB_NAME
        
        # Check if Redis is installed or use Docker
        if command -v redis-server &>/dev/null; then
            echo "Starting Redis server in the background..."
            redis-server --daemonize yes
            export CELERY_BROKER_URL=redis://localhost:6379/0
            export CELERY_RESULT_BACKEND=redis://localhost:6379/0
        elif $DOCKER_AVAILABLE; then
            echo "Starting Redis with Docker..."
            docker run -d -p 6379:6379 --name redis-shopsentiment redis:7-alpine
            export CELERY_BROKER_URL=redis://localhost:6379/0
            export CELERY_RESULT_BACKEND=redis://localhost:6379/0
        else
            echo -e "${RED}✗${NC} Redis is not available. Celery will not work."
        fi
        
        # Start Celery worker in the background
        echo "Starting Celery worker in the background..."
        celery -A app.tasks.celery worker --loglevel=info &
        CELERY_PID=$!
        
        # Start Flask app
        echo -e "${GREEN}Starting Flask development server...${NC}"
        echo -e "${GREEN}Access the application at http://127.0.0.1:5000${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
        flask run
        
        # Clean up
        echo "Stopping Celery worker..."
        kill $CELERY_PID
        
        if [ ! command -v redis-server &>/dev/null ] && $DOCKER_AVAILABLE; then
            echo "Stopping Redis Docker container..."
            docker stop redis-shopsentiment
            docker rm redis-shopsentiment
        fi
        ;;
    2)
        if $DOCKER_AVAILABLE; then
            echo "Starting with Docker Compose..."
            
            # Set environment variables for docker-compose
            export MONGODB_URI=$MONGODB_URI
            export MONGODB_DB_NAME=$MONGODB_DB_NAME
            export SECRET_KEY="docker_compose_secret_key"
            
            # Build and start containers
            docker-compose up --build
        else
            echo -e "${RED}✗${NC} Docker is not available. Cannot start with Docker Compose."
        fi
        ;;
    3)
        echo "Exiting without starting the application."
        ;;
    *)
        echo -e "${RED}Invalid option.${NC} Exiting."
        ;;
esac

echo ""
echo -e "${GREEN}Setup completed!${NC}"
echo "Thank you for using ShopSentiment with MongoDB." 