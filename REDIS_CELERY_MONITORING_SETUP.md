# Redis & Celery Monitoring Setup Guide

This guide provides instructions for setting up Redis and Celery performance monitoring for the ShopSentiment application.

## Overview

The monitoring system consists of several components:

1. **Redis Monitoring**: Tracks Redis memory usage, connections, and performance metrics
2. **Celery Monitoring**: Monitors worker status, queue lengths, and task performance
3. **Prometheus**: Collects metrics for visualization and alerting
4. **Grafana**: Visualizes metrics in a dashboard
5. **Monitoring Agent**: Python script that collects and exposes metrics

## Prerequisites

- Python 3.7+
- pip
- Access to Redis instance
- Access to Celery workers
- Prometheus and Grafana (self-hosted or cloud)

## Installation Steps

### 1. Install Dependencies

```bash
# Create a virtual environment (optional but recommended)
python -m venv redis-celery-monitoring-env
source redis-celery-monitoring-env/bin/activate  # On Windows: redis-celery-monitoring-env\Scripts\activate

# Install required packages
pip install redis==4.5.4 celery==5.2.7 prometheus-client==0.16.0 schedule==1.1.0 requests==2.28.2
```

### 2. Configure Redis Monitoring

Redis monitoring doesn't require special configuration on the Redis server side. Our monitoring script collects metrics via the Redis INFO command.

If you're using Redis with maxmemory settings, ensure your configuration has appropriate values:

```
maxmemory 2gb
maxmemory-policy allkeys-lru
```

For production environments, it's recommended to set up Redis persistence:

```
save 900 1
save 300 10
save 60 10000
appendonly yes
```

### 3. Configure Celery Monitoring

Celery monitoring requires that your Celery workers are properly configured. Ensure that your Celery application has proper task monitoring enabled.

For better monitoring, enable events in your Celery workers by adding the `-E` flag:

```bash
celery -A app.tasks.celery worker --loglevel=info -E
```

In your Celery configuration, ensure task tracking is enabled:

```python
app.conf.task_track_started = True
app.conf.task_send_sent_event = True
```

### 4. Set Up Prometheus

If you're using a self-hosted Prometheus instance:

1. Add the following job to your `prometheus.yml` configuration:

```yaml
scrape_configs:
  - job_name: 'redis_celery'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8001']  # The port where our monitoring script exposes metrics
```

2. Restart Prometheus to apply the changes

If you're using a managed Prometheus service, follow your provider's instructions to add a new scrape target.

### 5. Set Up Grafana

1. Install Grafana or use a managed service
2. Add your Prometheus instance as a data source
3. Import the dashboard using the provided `redis_celery_dashboard.json` file:
   - In Grafana, go to Dashboards → Import
   - Upload the JSON file or paste its contents
   - Select your Prometheus data source and click Import

### 6. Configure the Monitoring Script

Review and update the configuration in `redis_celery_monitoring.py`:

1. **Redis Connection**: Update the Redis connection URI with your credentials
   ```python
   REDIS_URI = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
   ```

2. **Celery Configuration**: Update Celery broker and backend URIs
   ```python
   CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
   CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
   ```

3. **Alert Thresholds**: Adjust alert thresholds based on your application's needs
   ```python
   THRESHOLD_REDIS_MEMORY_USAGE = 0.8  # 80% of max memory
   THRESHOLD_REDIS_CONNECTIONS = 80  # Alert if more than 80% of max connections
   THRESHOLD_QUEUE_SIZE = 100  # Alert if any queue has more than 100 tasks
   THRESHOLD_TASK_DURATION_SEC = 30  # Alert if tasks take longer than 30 seconds
   THRESHOLD_WORKER_COUNT_MIN = 2  # Alert if less than 2 workers are active
   ```

4. **Email Alerts**: Configure email settings if you want email alerts
   ```python
   EMAIL_CONFIG = {
       'enabled': True,  # Set to True to enable
       'smtp_server': 'smtp.gmail.com',
       'smtp_port': 587,
       'username': 'your-email@gmail.com',
       'password': 'your-app-password',
       'from_email': 'your-email@gmail.com',
       'to_emails': ['admin@example.com']
   }
   ```

5. **Slack Alerts**: Configure Slack webhook if you want Slack alerts
   ```python
   SLACK_CONFIG = {
       'enabled': True,  # Set to True to enable
       'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
   }
   ```

### 7. Run the Monitoring Script

Start the monitoring script:

```bash
python redis_celery_monitoring.py
```

For production use, it's recommended to run this as a service using systemd, Supervisor, or a similar tool:

#### Example systemd service file `/etc/systemd/system/redis-celery-monitoring.service`:

```ini
[Unit]
Description=Redis & Celery Monitoring Service
After=network.target

[Service]
User=youruser
WorkingDirectory=/path/to/monitoring
ExecStart=/path/to/python /path/to/redis_celery_monitoring.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then enable and start the service:

```bash
sudo systemctl enable redis-celery-monitoring.service
sudo systemctl start redis-celery-monitoring.service
```

## Monitoring Metrics

The monitoring solution collects and visualizes the following metrics:

### Redis Metrics
- Memory usage (bytes and percentage)
- Connection count and utilization
- Operations per second
- Cache hit ratio
- Key expiration and eviction rates
- Command latency

### Celery Metrics
- Active worker count
- Tasks in progress
- Queue sizes
- Task execution time
- Task processing and failure rates

## Alerting

The monitoring system can alert on the following conditions:

1. **Redis Memory Usage**: Alert when memory usage exceeds threshold (default: 80%)
2. **Redis Connections**: Alert when connection count exceeds threshold
3. **Celery Worker Count**: Alert when number of active workers falls below threshold
4. **Celery Queue Size**: Alert when any queue exceeds size threshold
5. **Task Duration**: Alert when tasks take longer than threshold to complete

## Troubleshooting

### Common Issues

1. **Cannot connect to Redis**: 
   - Verify your connection string
   - Check network connectivity
   - Ensure Redis is running

2. **Cannot connect to Celery workers**:
   - Check that Celery workers are running
   - Verify broker connection settings
   - Ensure events are enabled with the `-E` flag

3. **Metrics not showing in Prometheus**:
   - Verify the monitoring script is running
   - Check that Prometheus is scraping the correct endpoint
   - Check that the script is binding to the correct port

4. **Dashboard not showing data**:
   - Verify Prometheus data source is correctly configured in Grafana
   - Check that metrics are being collected in Prometheus
   - Adjust the dashboard time range

## Maintenance

### Regular Tasks

1. **Log Rotation**: Set up log rotation for `redis_celery_monitoring.log`
2. **Data Retention**: Configure Prometheus data retention based on your needs
3. **Alert Tuning**: Periodically review and adjust alert thresholds
4. **Version Updates**: Keep dependencies up to date

### Dashboard Customization

You can customize the Grafana dashboard to:
- Add additional panels
- Adjust thresholds and colors
- Create additional dashboards for specific use cases
- Add annotations for deployments or maintenance events 