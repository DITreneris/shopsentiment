"""
Celery configuration for ShopSentiment app
Includes task scheduling and Redis connection settings
"""

from celery import Celery
from celery.schedules import crontab
import os

# Create Celery app instance
celery_app = Celery('shop_sentiment')

# Configure Celery from environment variables with fallbacks
celery_app.conf.broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
celery_app.conf.result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Auto-discover tasks from all registered app modules
celery_app.autodiscover_tasks(['app.tasks'])

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    # Refresh popular product stats every 6 hours
    'refresh-popular-product-stats': {
        'task': 'refresh_popular_product_stats',
        'schedule': crontab(hour='*/6', minute=0),  # Every 6 hours
    },
    
    # Refresh platform-wide stats once a day
    'refresh-platform-stats': {
        'task': 'refresh_platform_stats',
        'schedule': crontab(hour=1, minute=30),  # 1:30 AM
    },
    
    # Refresh comparison stats three times a day
    'refresh-comparison-stats': {
        'task': 'refresh_comparison_stats',
        'schedule': crontab(hour='*/8', minute=45),  # Every 8 hours
    },
    
    # Run a complete refresh once a week
    'refresh-all-dashboard-stats': {
        'task': 'refresh_all_dashboard_stats',
        'schedule': crontab(day_of_week=6, hour=2, minute=0),  # Saturday at 2 AM
    }
}

# Task execution settings
celery_app.conf.task_time_limit = 300  # 5 minutes max runtime
celery_app.conf.task_soft_time_limit = 240  # 4 minutes soft limit
celery_app.conf.worker_prefetch_multiplier = 4
celery_app.conf.task_acks_late = True

# Task routing - defines which queue tasks are sent to
celery_app.conf.task_routes = {
    'refresh_popular_product_stats': {'queue': 'dashboard'},
    'refresh_platform_stats': {'queue': 'dashboard'},
    'refresh_comparison_stats': {'queue': 'dashboard'},
    'refresh_all_dashboard_stats': {'queue': 'dashboard'},
}

# Set a name for the workers
celery_app.conf.worker_proc_name = 'shopsentiment_worker' 