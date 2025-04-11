@echo off
echo Starting ShopSentiment development environment...

REM Set environment variables for Redis cache
set CACHE_TYPE=simple
set FLASK_ENV=development
set FLASK_DEBUG=1

echo Starting Celery worker...
start cmd /k "celery -A celery_worker.celery worker --loglevel=info --pool=solo"

echo Starting Flask app...
python app.py

echo Development environment shutdown. 