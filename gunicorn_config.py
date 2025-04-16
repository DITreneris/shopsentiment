"""
Gunicorn configuration file for ShopSentiment application.
Optimized for production deployment on Heroku.
"""

import multiprocessing
import os

# Server socket
try:
    port = int(os.environ.get("PORT", 5000))
except ValueError:
    port = 5000
    
bind = f"0.0.0.0:{port}"

# Worker processes - optimize for Heroku dynos
# If WEB_CONCURRENCY is set, use that value. Otherwise calculate based on CPU count
workers = int(os.environ.get("WEB_CONCURRENCY", 
                           multiprocessing.cpu_count() * 2 + 1))

# Worker settings
worker_class = "sync"  # Use sync worker as gevent might not be installed
worker_connections = 1000  # Maximum number of simultaneous connections
max_requests = 1000  # Restart workers after handling N requests to prevent memory leaks
max_requests_jitter = 50  # Add randomness to max_requests to prevent all workers from restarting at once

# Timeout settings - prevent hanging requests
timeout = int(os.environ.get("TIMEOUT", 30))  # 30s timeout to match Heroku's router timeout
graceful_timeout = int(os.environ.get("GRACEFUL_TIMEOUT", 30))  # Graceful worker shutdown timeout
keepalive = 5  # How long to keep connections alive

# Logging - Heroku captures logs from stdout/stderr
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = os.environ.get("LOG_LEVEL", "info")  # Log level
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "shopsentiment"

# Server mechanics
daemon = False  # Don't run in background
pidfile = None  # Don't create a pidfile
umask = 0       # Don't set file access permissions
user = None     # Don't set the user to run as
group = None    # Don't set the group to run as
tmp_upload_dir = None  # Don't set a temporary upload directory

# SSL
keyfile = None
certfile = None

# Security
limit_request_line = 4094  # Limit the size of the HTTP request line
limit_request_fields = 100  # Limit the number of HTTP request fields
limit_request_field_size = 8190  # Limit the size of each HTTP request field

# Preload application to prevent memory fragmentation
preload_app = True

# Configure for Heroku dyno recycling
def on_starting(server):
    """Log when server starts up."""
    server.log.info("Starting up ShopSentiment on Heroku")

def on_exit(server):
    """Log when server shuts down."""
    server.log.info("Shutting down ShopSentiment")

def pre_fork(server, worker):
    """Pre-fork worker configuration."""
    server.log.info("Pre-forking worker")

def post_fork(server, worker):
    """Post-fork worker configuration."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    """Pre-execution configuration."""
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    """When server is ready, log it."""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Worker interrupt handler."""
    worker.log.info("worker received INT or QUIT signal")

def worker_abort(worker):
    """Worker abort handler."""
    worker.log.info("Worker requested abort") 