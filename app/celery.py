from celery import Celery

def make_celery(app=None):
    """
    Create a Celery application configured to work with Flask.
    """
    # Use Redis as the broker
    redis_url = app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    
    celery = Celery(
        app.import_name,
        broker=redis_url,
        backend=redis_url,
    )
    
    # Update Celery config from Flask config
    celery.conf.update(app.config)
    
    # Create a Flask application context for each Celery task
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    return celery 