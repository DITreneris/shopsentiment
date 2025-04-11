#!/usr/bin/env python
import os
import time
import json
import logging
import smtplib
import requests
import schedule
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from prometheus_client import start_http_server, Gauge, Counter, Histogram, Summary

# Import Redis and Celery libraries
import redis
from celery.app.control import Control
from celery import Celery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='redis_celery_monitoring.log',
    filemode='a'
)
logger = logging.getLogger("redis_celery_monitoring")

# Load environment variables
REDIS_URI = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Alert thresholds
THRESHOLD_REDIS_MEMORY_USAGE = 0.8  # 80% of max memory
THRESHOLD_REDIS_CONNECTIONS = 80  # Alert if more than 80% of max connections
THRESHOLD_QUEUE_SIZE = 100  # Alert if any queue has more than 100 tasks
THRESHOLD_TASK_DURATION_SEC = 30  # Alert if tasks take longer than 30 seconds
THRESHOLD_WORKER_COUNT_MIN = 2  # Alert if less than 2 workers are active

# Email alert configuration
EMAIL_CONFIG = {
    'enabled': False,  # Set to True to enable
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'username': 'your-email@gmail.com',
    'password': 'your-app-password',
    'from_email': 'your-email@gmail.com',
    'to_emails': ['admin@example.com']
}

# Slack alert configuration
SLACK_CONFIG = {
    'enabled': False,  # Set to True to enable
    'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
}

# Initialize Redis client
redis_client = redis.Redis.from_url(REDIS_URI)

# Initialize Celery app
app = Celery(broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
control = Control(app)

# Define Prometheus metrics

# Redis metrics
redis_memory_usage = Gauge('redis_memory_usage_bytes', 'Redis memory usage in bytes')
redis_memory_limit = Gauge('redis_memory_limit_bytes', 'Redis memory limit in bytes')
redis_memory_usage_percent = Gauge('redis_memory_usage_percent', 'Redis memory usage as percentage of limit')
redis_connected_clients = Gauge('redis_connected_clients', 'Number of clients connected to Redis')
redis_max_clients = Gauge('redis_max_clients', 'Maximum number of clients Redis can handle')
redis_connections_percent = Gauge('redis_connections_percent', 'Percentage of max Redis connections in use')
redis_ops_per_second = Gauge('redis_ops_per_second', 'Redis operations per second')
redis_hit_ratio = Gauge('redis_hit_ratio', 'Redis cache hit ratio')
redis_keyspace_hits = Counter('redis_keyspace_hits_total', 'Redis keyspace hits total')
redis_keyspace_misses = Counter('redis_keyspace_misses_total', 'Redis keyspace misses total')
redis_expired_keys = Counter('redis_expired_keys_total', 'Redis expired keys total')
redis_evicted_keys = Counter('redis_evicted_keys_total', 'Redis evicted keys total')
redis_command_latency = Histogram('redis_command_latency_seconds', 'Redis command latency in seconds', 
                                 buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0])

# Celery metrics
celery_queue_size = Gauge('celery_queue_size', 'Number of tasks in Celery queue', ['queue_name'])
celery_active_workers = Gauge('celery_active_workers', 'Number of active Celery workers')
celery_processed_tasks = Counter('celery_processed_tasks_total', 'Total number of processed Celery tasks', ['task_name'])
celery_failed_tasks = Counter('celery_failed_tasks_total', 'Total number of failed Celery tasks', ['task_name'])
celery_task_execution_time = Histogram('celery_task_execution_time_seconds', 'Celery task execution time in seconds', 
                                      ['task_name'], buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0])
celery_tasks_in_progress = Gauge('celery_tasks_in_progress', 'Number of Celery tasks currently in progress')

def send_email_alert(subject, message):
    """Send an email alert"""
    if not EMAIL_CONFIG.get('enabled'):
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG.get('from_email')
        msg['To'] = ', '.join(EMAIL_CONFIG.get('to_emails'))
        msg['Subject'] = f"[ALERT] {subject}"
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP(EMAIL_CONFIG.get('smtp_server'), EMAIL_CONFIG.get('smtp_port'))
        server.starttls()
        server.login(EMAIL_CONFIG.get('username'), EMAIL_CONFIG.get('password'))
        server.send_message(msg)
        server.quit()
        logger.info(f"Email alert sent: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email alert: {str(e)}")

def send_slack_alert(subject, message):
    """Send a Slack alert"""
    if not SLACK_CONFIG.get('enabled'):
        return
    
    try:
        webhook_url = SLACK_CONFIG.get('webhook_url')
        payload = {
            "text": f"*[ALERT] {subject}*\n```\n{message}\n```",
            "mrkdwn": True
        }
        response = requests.post(webhook_url, json=payload)
        if response.status_code != 200:
            logger.error(f"Failed to send Slack alert: {response.text}")
        else:
            logger.info(f"Slack alert sent: {subject}")
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {str(e)}")

def collect_redis_metrics():
    """Collect Redis metrics"""
    try:
        # Get Redis info
        info = redis_client.info()
        
        # Memory metrics
        used_memory = info.get('used_memory', 0)
        max_memory = info.get('maxmemory', 0)
        redis_memory_usage.set(used_memory)
        redis_memory_limit.set(max_memory if max_memory else 0)
        
        memory_percent = 0
        if max_memory and int(max_memory) > 0:
            memory_percent = float(used_memory) / float(max_memory)
        redis_memory_usage_percent.set(memory_percent)
        
        # Check if memory usage exceeds threshold
        if memory_percent > THRESHOLD_REDIS_MEMORY_USAGE:
            alert_msg = f"Redis memory usage is at {memory_percent:.1%}, which exceeds the threshold of {THRESHOLD_REDIS_MEMORY_USAGE:.1%}"
            logger.warning(alert_msg)
            send_email_alert("High Redis Memory Usage", alert_msg)
            send_slack_alert("High Redis Memory Usage", alert_msg)
        
        # Connection metrics
        connected_clients = info.get('connected_clients', 0)
        maxclients = info.get('maxclients', 10000)  # Default Redis maxclients
        redis_connected_clients.set(connected_clients)
        redis_max_clients.set(maxclients)
        
        connections_percent = float(connected_clients) / float(maxclients)
        redis_connections_percent.set(connections_percent)
        
        # Check if connections exceed threshold
        if connections_percent > (THRESHOLD_REDIS_CONNECTIONS / 100.0):
            alert_msg = f"Redis has {connected_clients} connections ({connections_percent:.1%} of max), which exceeds the threshold of {THRESHOLD_REDIS_CONNECTIONS}%"
            logger.warning(alert_msg)
            send_email_alert("High Redis Connection Count", alert_msg)
            send_slack_alert("High Redis Connection Count", alert_msg)
        
        # Performance metrics
        instantaneous_ops_per_sec = info.get('instantaneous_ops_per_sec', 0)
        redis_ops_per_second.set(instantaneous_ops_per_sec)
        
        keyspace_hits = info.get('keyspace_hits', 0)
        keyspace_misses = info.get('keyspace_misses', 0)
        expired_keys = info.get('expired_keys', 0)
        evicted_keys = info.get('evicted_keys', 0)
        
        redis_keyspace_hits.inc(keyspace_hits)
        redis_keyspace_misses.inc(keyspace_misses)
        redis_expired_keys.inc(expired_keys)
        redis_evicted_keys.inc(evicted_keys)
        
        # Calculate hit ratio
        hit_ratio = 0
        if keyspace_hits + keyspace_misses > 0:
            hit_ratio = float(keyspace_hits) / (float(keyspace_hits) + float(keyspace_misses))
        redis_hit_ratio.set(hit_ratio)
        
        # Measure Redis command latency
        start_time = time.time()
        redis_client.ping()
        latency = time.time() - start_time
        redis_command_latency.observe(latency)
        
        logger.info(f"Collected Redis metrics: Memory: {used_memory}B ({memory_percent:.1%}), Connections: {connected_clients}, OPS: {instantaneous_ops_per_sec}")
    
    except Exception as e:
        logger.error(f"Failed to collect Redis metrics: {str(e)}")

def collect_celery_metrics():
    """Collect Celery metrics"""
    try:
        # Get active queues
        active_queues = {}
        i = app.control.inspect()
        
        # Get active workers
        workers = i.active_queues() or {}
        celery_active_workers.set(len(workers))
        
        # Check if worker count is below threshold
        if len(workers) < THRESHOLD_WORKER_COUNT_MIN:
            alert_msg = f"Only {len(workers)} Celery workers are active, which is below the threshold of {THRESHOLD_WORKER_COUNT_MIN}"
            logger.warning(alert_msg)
            send_email_alert("Low Celery Worker Count", alert_msg)
            send_slack_alert("Low Celery Worker Count", alert_msg)
        
        # Extract queue names from active queues
        for worker, queues in workers.items():
            for queue in queues:
                active_queues[queue['name']] = 0
        
        # Get queue sizes
        for queue_name in active_queues.keys():
            try:
                # Using Redis to check queue size
                queue_key = f'celery:{queue_name}'
                queue_size = redis_client.llen(queue_key)
                active_queues[queue_name] = queue_size
                celery_queue_size.labels(queue_name=queue_name).set(queue_size)
                
                # Check if queue size exceeds threshold
                if queue_size > THRESHOLD_QUEUE_SIZE:
                    alert_msg = f"Celery queue '{queue_name}' has {queue_size} tasks, which exceeds the threshold of {THRESHOLD_QUEUE_SIZE}"
                    logger.warning(alert_msg)
                    send_email_alert("Large Celery Queue", alert_msg)
                    send_slack_alert("Large Celery Queue", alert_msg)
            except Exception as e:
                logger.error(f"Failed to get size for queue {queue_name}: {str(e)}")
        
        # Get tasks in progress
        active_tasks = i.active() or {}
        tasks_in_progress = sum(len(tasks) for worker, tasks in active_tasks.items())
        celery_tasks_in_progress.set(tasks_in_progress)
        
        # Get task statistics
        stats = i.stats() or {}
        for worker, stat in stats.items():
            processed = stat.get('total', {}).get('processed', 0)
            # Use a counter per task name if available, or just total processed
            celery_processed_tasks.labels(task_name="total").inc(processed)
        
        # Get task execution times (if available)
        revoked = i.revoked() or {}
        reserved = i.reserved() or {}
        scheduled = i.scheduled() or {}
        
        logger.info(f"Collected Celery metrics: Workers: {len(workers)}, Tasks in progress: {tasks_in_progress}")
        
        # Log queue sizes
        queue_sizes_str = ", ".join([f"{q}: {s}" for q, s in active_queues.items()])
        logger.info(f"Queue sizes: {queue_sizes_str}")
        
    except Exception as e:
        logger.error(f"Failed to collect Celery metrics: {str(e)}")

def run_monitoring():
    """Run all monitoring tasks"""
    logger.info("Starting monitoring cycle")
    collect_redis_metrics()
    collect_celery_metrics()
    logger.info("Completed monitoring cycle")

if __name__ == "__main__":
    try:
        # Start HTTP server for Prometheus metrics
        start_http_server(8001)  # Using port 8001 (MongoDB uses 8000)
        logger.info("Prometheus metrics server started on port 8001")
        
        # Initial run
        run_monitoring()
        
        # Schedule regular monitoring
        schedule.every(15).seconds.do(run_monitoring)
        
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Monitoring stopped due to error: {str(e)}") 