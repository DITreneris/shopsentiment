from app import celery, app

if __name__ == '__main__':
    celery.start() 