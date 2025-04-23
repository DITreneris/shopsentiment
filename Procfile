web: PYTHONPATH=$PYTHONPATH:. gunicorn --config gunicorn_config.py wsgi:app
worker: PYTHONPATH=$PYTHONPATH:. celery -A src.celery_app worker --loglevel=info 