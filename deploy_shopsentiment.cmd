@echo off
echo ======================================================
echo ShopSentiment Windows Deployment Script
echo ======================================================
echo.

REM Check if Docker is installed
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not installed or not in PATH.
    echo Please install Docker Desktop for Windows first.
    echo Visit: https://www.docker.com/products/docker-desktop
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not running.
    echo Please start Docker Desktop and try again.
    exit /b 1
)

REM Check if Git is installed
where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Git not found. Script will continue but you'll need to download the project manually.
    echo Visit: https://git-scm.com/download/win
    echo.
    set GIT_AVAILABLE=0
) else (
    set GIT_AVAILABLE=1
)

echo STEP 1: Creating project directory
set PROJECT_DIR=%USERPROFILE%\ShopSentiment
if not exist "%PROJECT_DIR%" mkdir "%PROJECT_DIR%"
cd /d "%PROJECT_DIR%"
echo Created directory: %PROJECT_DIR%
echo.

if %GIT_AVAILABLE% EQU 1 (
    echo STEP 2: Cloning the repository
    git clone https://github.com/yourusername/shop-sentiment.git .
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to clone repository. Please check the URL and your internet connection.
        exit /b 1
    )
    echo Repository cloned successfully.
) else (
    echo STEP 2: Skipped repository cloning. Please download and extract the project files manually to:
    echo %PROJECT_DIR%
    echo Then press any key to continue...
    pause >nul
)
echo.

echo STEP 3: Creating environment file
if exist .env.example (
    copy .env.example .env
    echo Created .env file from template.
) else (
    echo Creating new .env file...
    echo # Flask configuration > .env
    echo FLASK_APP=wsgi.py >> .env
    echo FLASK_ENV=production >> .env
    echo SECRET_KEY=windows-deployment-change-this-key >> .env
    echo # Database configuration >> .env
    echo DATABASE_URL=sqlite:///data/shopsentiment.db >> .env
    echo # Redis configuration >> .env
    echo REDIS_URL=redis://redis:6379/0 >> .env
    echo # Celery configuration >> .env
    echo CELERY_BROKER_URL=redis://redis:6379/1 >> .env
    echo CELERY_RESULT_BACKEND=redis://redis:6379/2 >> .env
    echo # Security configuration >> .env
    echo WTF_CSRF_ENABLED=True >> .env
    echo WTF_CSRF_SECRET_KEY=windows-csrf-key-change-this >> .env
    echo SECURITY_PASSWORD_SALT=windows-salt-change-this >> .env
    echo # Rate limiting >> .env
    echo RATELIMIT_STORAGE_URL=redis://redis:6379/3 >> .env
    echo RATELIMIT_STRATEGY=fixed-window >> .env
    echo Created basic .env file. You should edit this file to change the security keys.
)
echo.

echo STEP 4: Creating necessary directories
if not exist data mkdir data
echo Created data directory.
echo.

echo STEP 5: Building Docker containers
docker-compose build
if %ERRORLEVEL% NEQ 0 (
    echo Failed to build Docker containers.
    exit /b 1
)
echo Docker containers built successfully.
echo.

echo STEP 6: Starting Docker containers
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo Failed to start Docker containers.
    exit /b 1
)
echo Docker containers started successfully.
echo.

echo STEP 7: Checking container status
timeout /t 5 /nobreak >nul
docker-compose ps
echo.

echo STEP 8: Initializing the database
docker-compose exec web flask init-db
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Failed to initialize database. It might already be initialized.
)
echo.

echo ======================================================
echo DEPLOYMENT COMPLETE!
echo ======================================================
echo.
echo ShopSentiment is now running at: http://localhost:5000
echo.
echo IMPORTANT NEXT STEPS:
echo 1. Edit the .env file to set secure keys
echo 2. Create a user account through the web interface
echo 3. Start analyzing product reviews!
echo.
echo To stop the application:    docker-compose down
echo To view logs:               docker-compose logs
echo To restart:                 docker-compose restart
echo.
echo For more information, see the documentation in the docs/ directory.
echo ======================================================

:end 