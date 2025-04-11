bind = "0.0.0.0:$PORT"
workers = 2
threads = 2
timeout = 120
preload_app = True
accesslog = '-'
errorlog = '-'
loglevel = 'info'

def on_starting(server):
    """
    Log when the server is starting
    """
    server.log.info("Starting Gunicorn server") 