@echo off
setlocal enabledelayedexpansion

echo ShopSentiment MongoDB Setup Script for Windows
echo ==============================================
echo.

echo Checking prerequisites...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python is installed
    set PYTHON_CMD=python
) else (
    python3 --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Python 3 is installed
        set PYTHON_CMD=python3
    ) else (
        echo [ERROR] Python is not installed. Please install Python 3.8 or higher
        exit /b 1
    )
)

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] pip is installed
    set PIP_CMD=pip
) else (
    pip3 --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] pip3 is installed
        set PIP_CMD=pip3
    ) else (
        echo [ERROR] pip is not installed. Please install pip
        exit /b 1
    )
)

REM Check if MongoDB is installed locally (only needed for local development)
mongod --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] MongoDB is installed locally
    set MONGO_LOCAL=true
) else (
    echo [WARNING] MongoDB is not installed locally. Using Docker or remote MongoDB Atlas is recommended.
    set MONGO_LOCAL=false
)

REM Check if Docker is installed (optional)
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Docker is installed
    set DOCKER_AVAILABLE=true
) else (
    echo [WARNING] Docker is not installed. Local installation will be used.
    set DOCKER_AVAILABLE=false
)

echo.
echo Setting up environment...

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated

REM Install requirements
echo Installing requirements...
%PIP_CMD% install -r requirements.txt
echo [OK] Requirements installed

REM Download NLTK data
echo Downloading NLTK data...
%PYTHON_CMD% -c "import nltk; nltk.download('vader_lexicon')"
echo [OK] NLTK data downloaded

echo.
echo MongoDB Configuration
echo =====================

REM Ask for MongoDB URI
echo Enter your MongoDB connection URI:
echo - For MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/
echo - For local MongoDB: mongodb://localhost:27017/
echo - Press Enter to use default (mongodb://localhost:27017/)
set /p MONGODB_URI="MongoDB URI: "
if "!MONGODB_URI!"=="" set MONGODB_URI=mongodb://localhost:27017/

REM Ask for database name
echo Enter the MongoDB database name (default: shopsentiment):
set /p MONGODB_DB_NAME="Database name: "
if "!MONGODB_DB_NAME!"=="" set MONGODB_DB_NAME=shopsentiment

REM Create or update .env file
echo Updating .env file...
if exist .env (
    REM Create a temporary file without the MongoDB lines
    findstr /v "MONGODB_URI MONGODB_DB_NAME" .env > .env.tmp
    echo MONGODB_URI=!MONGODB_URI! >> .env.tmp
    echo MONGODB_DB_NAME=!MONGODB_DB_NAME! >> .env.tmp
    del .env
    rename .env.tmp .env
) else (
    REM Create a new .env file
    echo FLASK_APP=app > .env
    echo FLASK_ENV=development >> .env
    echo SECRET_KEY=dev_key_change_me_in_production >> .env
    echo MONGODB_URI=!MONGODB_URI! >> .env
    echo MONGODB_DB_NAME=!MONGODB_DB_NAME! >> .env
)
echo [OK] .env file updated

echo.
echo Database Migration
echo ==================
echo Do you want to migrate data from SQLite to MongoDB? (y/n)
set /p MIGRATE_DATA="Migrate data: "
if /i "!MIGRATE_DATA!"=="y" (
    echo Running migration script...
    %PYTHON_CMD% scripts\migrate_to_mongodb.py --sqlite-path=data\shopsentiment.db --mongo-uri="!MONGODB_URI!" --mongo-db="!MONGODB_DB_NAME!"
    echo [OK] Data migration completed
)

echo.
echo Starting Application
echo ====================
echo Choose how to start the application:
echo 1^) Run with Flask development server (local development^)
echo 2^) Run with Docker Compose (recommended for testing production setup^)
echo 3^) Exit without starting
set /p START_OPTION="Select option (1-3): "

if "!START_OPTION!"=="1" (
    echo Starting Flask development server...
    set FLASK_APP=app
    set FLASK_ENV=development
    set MONGODB_URI=!MONGODB_URI!
    set MONGODB_DB_NAME=!MONGODB_DB_NAME!
    
    REM Check if Redis is available
    where redis-server >nul 2>&1
    if %errorlevel% equ 0 (
        echo Starting Redis server in a new window...
        start cmd /k "title Redis Server && redis-server"
        set CELERY_BROKER_URL=redis://localhost:6379/0
        set CELERY_RESULT_BACKEND=redis://localhost:6379/0
    ) else if "!DOCKER_AVAILABLE!"=="true" (
        echo Starting Redis with Docker...
        docker run -d -p 6379:6379 --name redis-shopsentiment redis:7-alpine
        set CELERY_BROKER_URL=redis://localhost:6379/0
        set CELERY_RESULT_BACKEND=redis://localhost:6379/0
    ) else (
        echo [ERROR] Redis is not available. Celery will not work.
    )
    
    REM Start Celery worker in a new window
    echo Starting Celery worker in a new window...
    start cmd /k "title Celery Worker && call venv\Scripts\activate.bat && celery -A app.tasks.celery worker --loglevel=info"
    
    REM Start Flask app
    echo [OK] Starting Flask development server...
    echo [OK] Access the application at http://127.0.0.1:5000
    echo [WARNING] Press Ctrl+C to stop the server
    flask run
    
    REM Clean up (Docker Redis if used)
    if "!DOCKER_AVAILABLE!"=="true" (
        docker stop redis-shopsentiment
        docker rm redis-shopsentiment
    )
) else if "!START_OPTION!"=="2" (
    if "!DOCKER_AVAILABLE!"=="true" (
        echo Starting with Docker Compose...
        
        REM Set environment variables for docker-compose
        set MONGODB_URI=!MONGODB_URI!
        set MONGODB_DB_NAME=!MONGODB_DB_NAME!
        set SECRET_KEY=docker_compose_secret_key
        
        REM Build and start containers
        docker-compose up --build
    ) else (
        echo [ERROR] Docker is not available. Cannot start with Docker Compose.
    )
) else if "!START_OPTION!"=="3" (
    echo Exiting without starting the application.
) else (
    echo [ERROR] Invalid option. Exiting.
)

echo.
echo Setup completed!
echo Thank you for using ShopSentiment with MongoDB.

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

endlocal 