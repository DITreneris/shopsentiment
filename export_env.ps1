$env:FLASK_APP = "wsgi.py"
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"
$env:MONGODB_URI = "mongodb://tomasstaniulis76:<db_password>@ac-pvab4o3-shard-00-00.11tjwh5.mongodb.net:27017,ac-pvab4o3-shard-00-01.11tjwh5.mongodb.net:27017,ac-pvab4o3-shard-00-02.11tjwh5.mongodb.net:27017/?replicaSet=atlas-d6w01g-shard-0&ssl=true&authSource=admin&retryWrites=true&w=majority&appName=Shop1"
$env:MONGODB_PASS = "your_actual_mongodb_password"
$env:MONGODB_DB = "shopsentiment_dev"

Write-Host "Environment variables set successfully." 