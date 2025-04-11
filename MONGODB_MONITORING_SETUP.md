# MongoDB Monitoring Setup Guide

This guide provides instructions for setting up MongoDB performance monitoring for the ShopSentiment application.

## Overview

The monitoring system consists of several components:

1. **MongoDB Profiling**: Tracks slow queries in the database
2. **Prometheus**: Collects metrics for visualization and alerting
3. **Grafana**: Visualizes metrics in a dashboard
4. **Monitoring Agent**: Python script that collects and exposes metrics

## Prerequisites

- Python 3.7+
- pip
- Access to MongoDB Atlas cluster
- Prometheus and Grafana (self-hosted or cloud)

## Installation Steps

### 1. Install Dependencies

```bash
# Create a virtual environment (optional but recommended)
python -m venv mongodb-monitoring-env
source mongodb-monitoring-env/bin/activate  # On Windows: mongodb-monitoring-env\Scripts\activate

# Install required packages
pip install pymongo==4.3.3 prometheus-client==0.14.1 schedule==1.1.0 requests==2.28.1
```

### 2. Configure MongoDB Profiling

MongoDB profiling needs to be enabled to track slow queries. This is already configured in the monitoring script with:

```python
db.set_profiling_level(2, 100)  # Level 2 = profile all operations that take > 100ms
```

For MongoDB Atlas, you can also set this up in the Atlas UI:
1. Go to the Atlas dashboard
2. Select your cluster
3. Click "..." (ellipsis) and select "Profiler Settings"
4. Set the threshold to 100ms

### 3. Set Up Prometheus

If you're using a self-hosted Prometheus instance:

1. Add the following job to your `prometheus.yml` configuration:

```yaml
scrape_configs:
  - job_name: 'mongodb'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']  # The port where our monitoring script exposes metrics
```

2. Restart Prometheus to apply the changes

If you're using a managed Prometheus service, follow your provider's instructions to add a new scrape target.

### 4. Set Up Grafana

1. Install Grafana or use a managed service
2. Add your Prometheus instance as a data source
3. Import the dashboard using the provided `mongodb_dashboard.json` file:
   - In Grafana, go to Dashboards → Import
   - Upload the JSON file or paste its contents
   - Select your Prometheus data source and click Import

### 5. Configure the Monitoring Script

Review and update the configuration in `mongodb_monitoring.py`:

1. **MongoDB Connection**: Update the MongoDB connection URI with your credentials
   ```python
   uri = "mongodb+srv://username:password@your-cluster.mongodb.net/?retryWrites=true&w=majority"
   ```

2. **Alert Thresholds**: Adjust alert thresholds based on your application's needs
   ```python
   THRESHOLD_CONNECTION_POOL_UTILIZATION = 0.8  # 80%
   THRESHOLD_SLOW_QUERY_COUNT = 10  # Alert if more than 10 slow queries in monitoring interval
   THRESHOLD_OPERATION_DURATION_MS = 500  # Alert if average operation duration exceeds 500ms
   ```

3. **Email Alerts**: Configure email settings if you want email alerts
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

4. **Slack Alerts**: Configure Slack webhook if you want Slack alerts
   ```python
   SLACK_CONFIG = {
       'enabled': True,  # Set to True to enable
       'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
   }
   ```

### 6. Run the Monitoring Script

Start the monitoring script:

```bash
python mongodb_monitoring.py
```

For production use, it's recommended to run this as a service using systemd, Supervisor, or a similar tool:

#### Example systemd service file `/etc/systemd/system/mongodb-monitoring.service`:

```ini
[Unit]
Description=MongoDB Monitoring Service
After=network.target

[Service]
User=youruser
WorkingDirectory=/path/to/monitoring
ExecStart=/path/to/python /path/to/mongodb_monitoring.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then enable and start the service:

```bash
sudo systemctl enable mongodb-monitoring.service
sudo systemctl start mongodb-monitoring.service
```

## Monitoring Metrics

The monitoring solution collects and visualizes the following metrics:

### Connection Pool
- Current pool size
- Connections checked out
- Wait queue size
- Pool utilization percentage

### Query Performance
- Slow query count by collection
- Slow query count by operation type
- Operation duration (p95, p99)
- Operation duration distribution heatmap

### Operation Metrics
- Operation count by type
- Operation count by collection

## Troubleshooting

### Common Issues

1. **Cannot connect to MongoDB**: 
   - Verify your connection string
   - Check network connectivity
   - Ensure IP whitelist includes your monitoring server

2. **Metrics not showing in Prometheus**:
   - Verify the monitoring script is running
   - Check that Prometheus is scraping the correct endpoint
   - Review Prometheus logs for errors

3. **Dashboard not showing data**:
   - Verify Prometheus data source is correctly configured in Grafana
   - Check that metrics are being collected in Prometheus
   - Adjust the dashboard time range

## Maintenance

### Regular Tasks

1. **Log Rotation**: Set up log rotation for `mongodb_monitoring.log`
2. **Data Retention**: Configure Prometheus data retention based on your needs
3. **Alert Tuning**: Periodically review and adjust alert thresholds
4. **Version Updates**: Keep dependencies up to date

### Dashboard Customization

You can customize the Grafana dashboard to:
- Add additional panels
- Adjust thresholds and colors
- Create additional dashboards for specific use cases
- Add annotations for deployments or maintenance events 