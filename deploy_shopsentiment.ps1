# ShopSentiment Windows Deployment Script (PowerShell)

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "ShopSentiment Windows Deployment Script (PowerShell)" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "WARNING: This script is not running as Administrator." -ForegroundColor Yellow
    Write-Host "Some operations might fail. Consider rerunning as Administrator." -ForegroundColor Yellow
    Write-Host ""
}

# Check if Docker is installed
try {
    $dockerVersion = docker --version
    Write-Host "Docker detected: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Docker Desktop for Windows first." -ForegroundColor Red
    Write-Host "Visit: https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
try {
    $null = docker info
    Write-Host "Docker is running." -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker is not running." -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Check if Git is installed
$gitAvailable = $true
try {
    $gitVersion = git --version
    Write-Host "Git detected: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Git not found. Script will continue but you'll need to download the project manually." -ForegroundColor Yellow
    Write-Host "Visit: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host ""
    $gitAvailable = $false
}

Write-Host "STEP 1: Creating project directory" -ForegroundColor Cyan
$projectDir = Join-Path $env:USERPROFILE "ShopSentiment"
if (-not (Test-Path $projectDir)) {
    New-Item -Path $projectDir -ItemType Directory | Out-Null
}
Set-Location $projectDir
Write-Host "Created directory: $projectDir" -ForegroundColor Green
Write-Host ""

if ($gitAvailable) {
    Write-Host "STEP 2: Cloning the repository" -ForegroundColor Cyan
    try {
        git clone https://github.com/yourusername/shop-sentiment.git .
        Write-Host "Repository cloned successfully." -ForegroundColor Green
    } catch {
        Write-Host "Failed to clone repository. Please check the URL and your internet connection." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "STEP 2: Skipped repository cloning. Please download and extract the project files manually to:" -ForegroundColor Yellow
    Write-Host "$projectDir" -ForegroundColor Yellow
    Write-Host "Then press any key to continue..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
Write-Host ""

Write-Host "STEP 3: Creating environment file" -ForegroundColor Cyan
if (Test-Path ".env.example") {
    Copy-Item .env.example .env
    Write-Host "Created .env file from template." -ForegroundColor Green
} else {
    Write-Host "Creating new .env file..." -ForegroundColor Yellow
    @"
# Flask configuration
FLASK_APP=wsgi.py
FLASK_ENV=production
SECRET_KEY=powershell-deployment-change-this-key

# Database configuration
DATABASE_URL=sqlite:///data/shopsentiment.db

# Redis configuration
REDIS_URL=redis://redis:6379/0

# Celery configuration
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Security configuration
WTF_CSRF_ENABLED=True
WTF_CSRF_SECRET_KEY=powershell-csrf-key-change-this
SECURITY_PASSWORD_SALT=powershell-salt-change-this

# Rate limiting
RATELIMIT_STORAGE_URL=redis://redis:6379/3
RATELIMIT_STRATEGY=fixed-window
"@ | Out-File -FilePath .env -Encoding utf8
    Write-Host "Created basic .env file. You should edit this file to change the security keys." -ForegroundColor Green
}
Write-Host ""

Write-Host "STEP 4: Creating necessary directories" -ForegroundColor Cyan
if (-not (Test-Path "data")) {
    New-Item -Path "data" -ItemType Directory | Out-Null
    Write-Host "Created data directory." -ForegroundColor Green
} else {
    Write-Host "Data directory already exists." -ForegroundColor Green
}
Write-Host ""

Write-Host "STEP 5: Building Docker containers" -ForegroundColor Cyan
try {
    $buildOutput = docker-compose build
    Write-Host "Docker containers built successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to build Docker containers." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "STEP 6: Starting Docker containers" -ForegroundColor Cyan
try {
    $upOutput = docker-compose up -d
    Write-Host "Docker containers started successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to start Docker containers." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "STEP 7: Checking container status" -ForegroundColor Cyan
Start-Sleep -Seconds 5
docker-compose ps
Write-Host ""

Write-Host "STEP 8: Initializing the database" -ForegroundColor Cyan
try {
    docker-compose exec web flask init-db
    Write-Host "Database initialized successfully." -ForegroundColor Green
} catch {
    Write-Host "WARNING: Failed to initialize database. It might already be initialized." -ForegroundColor Yellow
}
Write-Host ""

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "ShopSentiment is now running at: http://localhost:5000" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Edit the .env file to set secure keys" -ForegroundColor Yellow
Write-Host "2. Create a user account through the web interface" -ForegroundColor Yellow
Write-Host "3. Start analyzing product reviews!" -ForegroundColor Yellow
Write-Host ""
Write-Host "To stop the application:    docker-compose down" -ForegroundColor Cyan
Write-Host "To view logs:               docker-compose logs" -ForegroundColor Cyan
Write-Host "To restart:                 docker-compose restart" -ForegroundColor Cyan
Write-Host ""
Write-Host "For more information, see the documentation in the docs/ directory." -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan 