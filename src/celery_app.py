import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Ensure required environment variables are set
broker_url = os.getenv('CELERY_BROKER_URL')
result_backend = os.getenv('CELERY_RESULT_BACKEND')

if not broker_url:
    raise ValueError("CELERY_BROKER_URL environment variable not set.")
# Result backend is optional for some use cases, but good practice to set
# if not result_backend:
#     raise ValueError("CELERY_RESULT_BACKEND environment variable not set.")

# Define the Celery application instance
# We use 'src' as the main name, assuming tasks will be in 'src.tasks'
celery = Celery(
    'src', # Use the main package name where tasks might reside
    broker=broker_url,
    backend=result_backend,
    include=['src.tasks.scraper_tasks'] # List task modules here
)

# Optional configuration settings
celery.conf.update(
    result_expires=3600, # Time (in seconds) until task results are kept
    task_serializer='json',
    accept_content=['json'],  # Allow json content
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Optional: Auto-discover tasks from installed apps (if using Django structure)
# celery.autodiscover_tasks()

if __name__ == '__main__':
    # This allows running the worker directly using: python -m src.celery_app worker --loglevel=info
    celery.start()

# Example of how to potentially integrate with Flask app context if needed later
# def create_celery(app=None):
#     app = app or create_app() # Assuming create_app exists in src/__init__.py
#     celery.conf.update(app.config)
#
#     class ContextTask(celery.Task):
#         def __call__(self, *args, **kwargs):
#             with app.app_context():
#                 return self.run(*args, **kwargs)
#
#     celery.Task = ContextTask
#     return celery 