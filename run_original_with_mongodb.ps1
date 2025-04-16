# This script restores the original application configuration and runs it with MongoDB

Write-Host "Setting up original ShopSentiment application with MongoDB Atlas" -ForegroundColor Green

# Get MongoDB password
$mongoPassword = Read-Host -Prompt "Enter your MongoDB password" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($mongoPassword)
$password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Set environment variables
$env:FLASK_APP = "wsgi.py"
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"
$env:MONGODB_URI = "mongodb://tomasstaniulis76:$password@ac-pvab4o3-shard-00-00.11tjwh5.mongodb.net:27017,ac-pvab4o3-shard-00-01.11tjwh5.mongodb.net:27017,ac-pvab4o3-shard-00-02.11tjwh5.mongodb.net:27017/?replicaSet=atlas-d6w01g-shard-0&ssl=true&authSource=admin&retryWrites=true&w=majority&appName=Shop1"
$env:MONGODB_DB = "shopsentiment"
$env:USE_SQLITE = "False"
$env:FLASK_HOST = "127.0.0.1"
$env:FLASK_PORT = "5000"

# Ensure required packages are installed
Write-Host "Installing required packages..." -ForegroundColor Yellow
pip install pymongo[srv] dnspython flask-limiter redis python-dotenv

# Display information
Write-Host "Running original ShopSentiment application" -ForegroundColor Green
Write-Host "MongoDB URI: [MASKED]" -ForegroundColor Cyan
Write-Host "Database: $env:MONGODB_DB" -ForegroundColor Cyan
Write-Host "Mode: Development with MongoDB" -ForegroundColor Cyan
Write-Host "Access URL: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "Dashboard URL: http://127.0.0.1:5000/dashboard" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the application" -ForegroundColor Yellow
Write-Host ""

# Run the application with wsgi
python wsgi.py 