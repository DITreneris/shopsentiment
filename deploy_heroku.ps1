# PowerShell Script for Heroku Deployment
# Shop Sentiment Analysis Deployment Script

Write-Host "Deploying Shop Sentiment Analysis to Heroku..." -ForegroundColor Green

# Check if Heroku CLI is installed
try {
    $herokuVersion = heroku --version
    Write-Host "Found Heroku CLI: $herokuVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Heroku CLI is not installed. Please install it first." -ForegroundColor Red
    Write-Host "Visit: https://devcenter.heroku.com/articles/heroku-cli" -ForegroundColor Yellow
    exit 1
}

# Check if user is logged in to Heroku
try {
    $herokuUser = heroku whoami
    Write-Host "Logged in as: $herokuUser" -ForegroundColor Green
} catch {
    Write-Host "You need to log in to Heroku first:" -ForegroundColor Yellow
    heroku login
}

# Get app name from user or use default
$APP_NAME = Read-Host "Enter your Heroku app name (or press Enter to create a random name)"

if ([string]::IsNullOrEmpty($APP_NAME)) {
    # Create Heroku app with random name
    Write-Host "Creating Heroku app with random name..." -ForegroundColor Green
    heroku create
} else {
    # Create Heroku app with specified name
    Write-Host "Creating Heroku app: $APP_NAME..." -ForegroundColor Green
    heroku create $APP_NAME
}

# Set environment variables
Write-Host "Setting environment variables..." -ForegroundColor Green
$secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
heroku config:set SECRET_KEY=$secretKey

# Push code to Heroku
Write-Host "Pushing code to Heroku..." -ForegroundColor Green
git push heroku main

# Open the app in browser
Write-Host "Opening app in browser..." -ForegroundColor Green
heroku open

Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "Frontend is available at: https://YOUR-APP-NAME.herokuapp.com/app" -ForegroundColor Cyan
Write-Host "API is available at: https://YOUR-APP-NAME.herokuapp.com/" -ForegroundColor Cyan 