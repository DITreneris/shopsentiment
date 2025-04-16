@echo off
echo This script will:
echo 1. Install required packages
echo 2. Load sample data into SQLite
echo 3. Start the ShopSentiment application in debug mode

:: Set environment variables
set FLASK_APP=wsgi.py
set FLASK_ENV=development
set FLASK_DEBUG=1
set USE_SQLITE=True

echo.
echo Step 0: Installing required packages...
pip install flask sqlite3 python-dotenv

echo.
echo Step 1: Loading sample data...
python load_sample_data.py

echo.
echo Step 2: Starting the application...
echo.
echo Application will be available at: http://localhost:5000
echo Dashboard will be available at: http://localhost:5000/dashboard
echo.
echo Press Ctrl+C to stop the application
echo.

python debug_app.py

if %ERRORLEVEL% NEQ 0 (
  echo.
  echo Error starting the application.
  echo If you're seeing an "address already in use" error, try:
  echo 1. Close any other Python applications
  echo 2. Run 'netstat -ano | findstr :5000' to find processes using port 5000
  echo 3. Kill those processes with 'taskkill /F /PID [process-id]'
  echo.
  pause
) 