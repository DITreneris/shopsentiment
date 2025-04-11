#!/bin/bash

# Start Redis (if not already running)
echo "Checking if Redis is running..."
if ! command -v redis-cli &> /dev/null; then
    echo "Redis CLI not found. Please install Redis."
    exit 1
fi

redis-cli ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Starting Redis server..."
    redis-server --daemonize yes
else
    echo "Redis server is already running."
fi

# Start Celery worker
echo "Starting Celery worker..."
celery -A celery_worker.celery worker --loglevel=info --pool=solo &
CELERY_PID=$!

# Set environment variables for Redis cache
export CACHE_TYPE=redis
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0

# Start Flask app
echo "Starting Flask app..."
python app.py

# Cleanup on exit
echo "Shutting down services..."
kill $CELERY_PID
echo "Done." 