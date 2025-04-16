# Get the MongoDB password from the user
$mongoPassword = Read-Host -Prompt "Enter your MongoDB password" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($mongoPassword)
$plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Set environment variables
$env:FLASK_APP = "wsgi.py"
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"
$env:MONGODB_URI = "mongodb://tomasstaniulis76:$plainPassword@ac-pvab4o3-shard-00-00.11tjwh5.mongodb.net:27017,ac-pvab4o3-shard-00-01.11tjwh5.mongodb.net:27017,ac-pvab4o3-shard-00-02.11tjwh5.mongodb.net:27017/?replicaSet=atlas-d6w01g-shard-0&ssl=true&authSource=admin&retryWrites=true&w=majority&appName=Shop1"
$env:MONGODB_DB = "shopsentiment_dev"

Write-Host "Environment variables set successfully."
Write-Host "Starting the application..."

# Start the Flask application
python wsgi.py