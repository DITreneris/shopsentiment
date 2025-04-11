"""
MongoDB Performance Monitoring System
Tracks connection pool stats, slow queries, and performance metrics
"""

import logging
import time
import json
import os
import sys
from datetime import datetime, timedelta
import schedule
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from prometheus_client import start_http_server, Gauge, Counter, Histogram, Summary
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mongodb_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# MongoDB connection
uri = "mongodb+srv://tomasstaniulis76:JaLhUd1NLZUtwVb5@shop1.11tjwh5.mongodb.net/?retryWrites=true&w=majority&appName=Shop1"
client = MongoClient(uri, server_api=ServerApi('1'), 
                    # Enable monitoring
                    connectTimeoutMS=5000, 
                    serverSelectionTimeoutMS=10000,
                    maxPoolSize=100,
                    minPoolSize=10,
                    maxIdleTimeMS=50000,
                    waitQueueTimeoutMS=10000,
                    waitQueueMultiple=10)

db = client.shopsentiment
db.set_profiling_level(2, 100)  # Level 2 = profile all operations that take > 100ms

# Define Prometheus metrics
CONNECTION_POOL_SIZE = Gauge('mongodb_connection_pool_size', 
                             'Current size of the MongoDB connection pool')
CONNECTION_POOL_CHECKEDOUT = Gauge('mongodb_connection_pool_checked_out', 
                                  'Number of connections currently checked out')
CONNECTION_POOL_WAITQUEUESIZE = Gauge('mongodb_connection_pool_waitqueue_size', 
                                    'Current size of the wait queue')

OPERATIONS_TOTAL = Counter('mongodb_operations_total', 
                         'Total number of MongoDB operations',
                         ['operation_type', 'collection'])

OPERATION_DURATION = Histogram('mongodb_operation_duration_ms', 
                              'Duration of MongoDB operations in milliseconds',
                              ['operation_type', 'collection'],
                              buckets=[10, 50, 100, 200, 500, 1000, 2000, 5000])

SLOW_QUERY_COUNT = Counter('mongodb_slow_query_count', 
                         'Count of slow queries (>100ms)',
                         ['collection', 'operation_type'])

# Alert thresholds
THRESHOLD_CONNECTION_POOL_UTILIZATION = 0.8  # 80%
THRESHOLD_SLOW_QUERY_COUNT = 10  # Alert if more than 10 slow queries in monitoring interval
THRESHOLD_OPERATION_DURATION_MS = 500  # Alert if average operation duration exceeds 500ms

# Email configuration for alerts
EMAIL_CONFIG = {
    'enabled': False,  # Set to True to enable email alerts
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'username': 'your-email@gmail.com',
    'password': 'your-app-password',
    'from_email': 'your-email@gmail.com',
    'to_emails': ['admin@example.com']
}

# Slack configuration for alerts
SLACK_CONFIG = {
    'enabled': False,  # Set to True to enable Slack alerts
    'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
}

class MongoDBMonitor:
    """MongoDB monitoring system implementation."""
    
    def __init__(self, client, db):
        self.client = client
        self.db = db
        self.last_alert_time = {}
        self.alert_cooldown = 3600  # seconds between repeated alerts (1 hour)
    
    def monitor_connection_pool(self):
        """Monitor the MongoDB connection pool stats."""
        try:
            server_status = self.db.command('serverStatus')
            connections = server_status.get('connections', {})
            
            current = connections.get('current', 0)
            available = connections.get('available', 0)
            
            CONNECTION_POOL_SIZE.set(current)
            CONNECTION_POOL_CHECKEDOUT.set(current - available)
            
            pool_stats = self.client._topology.get_server_descriptions()[0].pool
            if pool_stats:
                CONNECTION_POOL_WAITQUEUESIZE.set(pool_stats.wait_queue_size)
            
            # Check for high connection pool utilization
            if current > 0:
                pool_utilization = (current - available) / current
                if pool_utilization > THRESHOLD_CONNECTION_POOL_UTILIZATION:
                    self.alert_high_connection_pool_utilization(pool_utilization, current, available)
            
            logger.info(f"Connection pool stats - Current: {current}, Available: {available}")
            return connections
            
        except Exception as e:
            logger.error(f"Error monitoring connection pool: {e}", exc_info=True)
            return {}
    
    def monitor_slow_queries(self):
        """Retrieve and analyze slow queries from the profiler."""
        try:
            # Get slow queries from the last monitoring interval
            one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
            
            # Find slow queries from system.profile collection
            slow_queries = list(self.db.system.profile.find({
                "ts": {"$gt": one_minute_ago}
            }).sort("millis", -1))
            
            slow_query_count = len(slow_queries)
            
            # Process slow queries
            collection_stats = {}
            operation_durations = []
            
            for query in slow_queries:
                collection_name = query.get('ns', '').split('.')[-1]
                op_type = query.get('op', 'unknown')
                duration_ms = query.get('millis', 0)
                
                # Update Prometheus metrics
                SLOW_QUERY_COUNT.labels(collection=collection_name, operation_type=op_type).inc()
                OPERATION_DURATION.labels(collection=collection_name, operation_type=op_type).observe(duration_ms)
                
                # Aggregate statistics
                if collection_name not in collection_stats:
                    collection_stats[collection_name] = {
                        'count': 0,
                        'total_duration_ms': 0,
                        'max_duration_ms': 0,
                        'operations': {}
                    }
                
                collection_stats[collection_name]['count'] += 1
                collection_stats[collection_name]['total_duration_ms'] += duration_ms
                collection_stats[collection_name]['max_duration_ms'] = max(
                    collection_stats[collection_name]['max_duration_ms'], duration_ms
                )
                
                # Track by operation type
                if op_type not in collection_stats[collection_name]['operations']:
                    collection_stats[collection_name]['operations'][op_type] = {
                        'count': 0,
                        'total_duration_ms': 0
                    }
                
                collection_stats[collection_name]['operations'][op_type]['count'] += 1
                collection_stats[collection_name]['operations'][op_type]['total_duration_ms'] += duration_ms
                
                operation_durations.append(duration_ms)
            
            # Alert if there are too many slow queries
            if slow_query_count > THRESHOLD_SLOW_QUERY_COUNT:
                self.alert_high_slow_query_count(slow_query_count, collection_stats)
            
            # Alert if average operation duration is too high
            if operation_durations:
                avg_duration = sum(operation_durations) / len(operation_durations)
                if avg_duration > THRESHOLD_OPERATION_DURATION_MS:
                    self.alert_high_operation_duration(avg_duration, operation_durations, collection_stats)
            
            # Log summary
            if slow_queries:
                logger.info(f"Found {slow_query_count} slow queries.")
                for collection, stats in collection_stats.items():
                    avg_duration = stats['total_duration_ms'] / stats['count'] if stats['count'] > 0 else 0
                    logger.info(f"Collection {collection}: {stats['count']} queries, avg: {avg_duration:.2f}ms, max: {stats['max_duration_ms']}ms")
            else:
                logger.info("No slow queries found.")
            
            return {
                'slow_query_count': slow_query_count,
                'collection_stats': collection_stats
            }
            
        except Exception as e:
            logger.error(f"Error monitoring slow queries: {e}", exc_info=True)
            return {'slow_query_count': 0, 'collection_stats': {}}
    
    def monitor_operations(self):
        """Monitor ongoing MongoDB operations."""
        try:
            current_op = self.db.command('currentOp')
            
            # Filter for active operations
            active_ops = [op for op in current_op.get('inprog', []) if op.get('active')]
            
            for op in active_ops:
                ns_parts = op.get('ns', '').split('.')
                collection = ns_parts[-1] if len(ns_parts) > 1 else 'unknown'
                op_type = op.get('op', 'unknown')
                
                # Update Prometheus metrics
                OPERATIONS_TOTAL.labels(operation_type=op_type, collection=collection).inc()
            
            # Log summary
            if active_ops:
                logger.info(f"Found {len(active_ops)} active operations")
            
            return active_ops
            
        except Exception as e:
            logger.error(f"Error monitoring operations: {e}", exc_info=True)
            return []
    
    def run_monitoring_pass(self):
        """Run a complete monitoring pass."""
        logger.info("Starting MongoDB monitoring pass")
        
        # Connection pool monitoring
        pool_stats = self.monitor_connection_pool()
        
        # Slow query monitoring
        slow_query_stats = self.monitor_slow_queries()
        
        # Operations monitoring
        active_ops = self.monitor_operations()
        
        # Save monitoring pass data to disk for the dashboard
        monitoring_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'connection_pool': pool_stats,
            'slow_queries': slow_query_stats,
            'active_operations': len(active_ops)
        }
        
        try:
            # Create monitoring directory if it doesn't exist
            os.makedirs('monitoring_data', exist_ok=True)
            
            # Save monitoring data
            filename = f"monitoring_data/mongodb_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(monitoring_data, f, default=str)
            
            # Clean up old monitoring data (keep only last 24 hours)
            self.cleanup_old_monitoring_data()
        except Exception as e:
            logger.error(f"Error saving monitoring data: {e}", exc_info=True)
        
        logger.info("Completed MongoDB monitoring pass")
    
    def cleanup_old_monitoring_data(self):
        """Clean up old monitoring data files."""
        try:
            now = datetime.utcnow()
            retention_period = timedelta(hours=24)
            
            for filename in os.listdir('monitoring_data'):
                if not filename.startswith('mongodb_'):
                    continue
                
                filepath = os.path.join('monitoring_data', filename)
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if now - file_mtime > retention_period:
                    os.remove(filepath)
                    logger.info(f"Removed old monitoring data file: {filename}")
        
        except Exception as e:
            logger.error(f"Error cleaning up old monitoring data: {e}", exc_info=True)
    
    def alert_high_connection_pool_utilization(self, utilization, current, available):
        """Send alert for high connection pool utilization."""
        alert_key = f"connection_pool_utilization_{utilization:.2f}"
        if self._should_send_alert(alert_key):
            message = (
                f"⚠️ *HIGH CONNECTION POOL UTILIZATION*\n"
                f"Current utilization: {utilization:.2%}\n"
                f"Total connections: {current}\n"
                f"Available connections: {available}\n"
                f"Time: {datetime.utcnow().isoformat()}"
            )
            
            self._send_alert("High MongoDB Connection Pool Utilization", message)
            logger.warning(f"Alert: High connection pool utilization - {utilization:.2%}")
    
    def alert_high_slow_query_count(self, count, collection_stats):
        """Send alert for high number of slow queries."""
        alert_key = f"slow_query_count_{count}"
        if self._should_send_alert(alert_key):
            # Format collection-specific information
            collection_details = []
            for collection, stats in collection_stats.items():
                avg_duration = stats['total_duration_ms'] / stats['count'] if stats['count'] > 0 else 0
                collection_details.append(
                    f"- {collection}: {stats['count']} queries, avg: {avg_duration:.2f}ms, max: {stats['max_duration_ms']}ms"
                )
            
            message = (
                f"⚠️ *HIGH NUMBER OF SLOW QUERIES*\n"
                f"Total slow queries in last minute: {count}\n"
                f"Collection breakdown:\n"
                f"{chr(10).join(collection_details)}\n"
                f"Time: {datetime.utcnow().isoformat()}"
            )
            
            self._send_alert("High MongoDB Slow Query Count", message)
            logger.warning(f"Alert: High slow query count - {count}")
    
    def alert_high_operation_duration(self, avg_duration, durations, collection_stats):
        """Send alert for high average operation duration."""
        alert_key = f"high_operation_duration_{int(avg_duration)}"
        if self._should_send_alert(alert_key):
            # Format collection-specific information
            collection_details = []
            for collection, stats in collection_stats.items():
                coll_avg_duration = stats['total_duration_ms'] / stats['count'] if stats['count'] > 0 else 0
                collection_details.append(
                    f"- {collection}: avg: {coll_avg_duration:.2f}ms, max: {stats['max_duration_ms']}ms"
                )
            
            message = (
                f"⚠️ *HIGH MONGODB OPERATION DURATION*\n"
                f"Average duration: {avg_duration:.2f}ms\n"
                f"Max duration: {max(durations)}ms\n"
                f"Collection breakdown:\n"
                f"{chr(10).join(collection_details)}\n"
                f"Time: {datetime.utcnow().isoformat()}"
            )
            
            self._send_alert("High MongoDB Operation Duration", message)
            logger.warning(f"Alert: High operation duration - avg: {avg_duration:.2f}ms")
    
    def _should_send_alert(self, alert_key):
        """Determine if an alert should be sent based on cooldown period."""
        now = time.time()
        if alert_key in self.last_alert_time:
            time_since_last_alert = now - self.last_alert_time[alert_key]
            if time_since_last_alert < self.alert_cooldown:
                return False
        
        self.last_alert_time[alert_key] = now
        return True
    
    def _send_alert(self, subject, message):
        """Send an alert via configured channels."""
        # Send email alert if enabled
        if EMAIL_CONFIG['enabled']:
            try:
                self._send_email_alert(subject, message)
            except Exception as e:
                logger.error(f"Error sending email alert: {e}", exc_info=True)
        
        # Send Slack alert if enabled
        if SLACK_CONFIG['enabled']:
            try:
                self._send_slack_alert(subject, message)
            except Exception as e:
                logger.error(f"Error sending Slack alert: {e}", exc_info=True)
    
    def _send_email_alert(self, subject, message):
        """Send an email alert."""
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['from_email']
        msg['To'] = ', '.join(EMAIL_CONFIG['to_emails'])
        msg['Subject'] = f"MongoDB Alert: {subject}"
        
        # Convert Slack-style formatting to plain text
        plain_message = message.replace('*', '')
        msg.attach(MIMEText(plain_message, 'plain'))
        
        # Connect to SMTP server and send email
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Sent email alert: {subject}")
    
    def _send_slack_alert(self, subject, message):
        """Send a Slack alert."""
        payload = {
            "text": f"*MongoDB Alert: {subject}*\n\n{message}"
        }
        
        response = requests.post(
            SLACK_CONFIG['webhook_url'],
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            logger.error(f"Error sending Slack alert. Status: {response.status_code}, Response: {response.text}")
        else:
            logger.info(f"Sent Slack alert: {subject}")

def start_monitoring():
    """Start the MongoDB monitoring system."""
    try:
        # Start Prometheus metrics HTTP server
        start_http_server(8000)
        logger.info("Started Prometheus metrics server on port 8000")
        
        # Create monitor instance
        monitor = MongoDBMonitor(client, db)
        
        # Schedule monitoring checks
        schedule.every(1).minutes.do(monitor.run_monitoring_pass)
        
        # Run initial monitoring pass
        monitor.run_monitoring_pass()
        
        # Keep running scheduled tasks
        logger.info("MongoDB monitoring system is running")
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("MongoDB monitoring stopped by user")
    except Exception as e:
        logger.critical(f"Error in MongoDB monitoring: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    start_monitoring() 