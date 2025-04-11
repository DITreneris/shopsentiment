#!/bin/bash
# Deploy monitoring system for the ShopSentiment application

# Print command before executing and exit on error
set -xe

# Create necessary directories
mkdir -p prometheus
mkdir -p grafana/provisioning/datasources
mkdir -p grafana/provisioning/dashboards

# Copy configuration files
cp prometheus.yml prometheus/
cp prometheus/prometheus.yml prometheus/
cp grafana/provisioning/datasources/prometheus.yml grafana/provisioning/datasources/
cp mongodb_dashboard.json grafana/provisioning/dashboards/
cp redis_celery_dashboard.json grafana/provisioning/dashboards/

# Create dashboard provisioning config if it doesn't exist
if [ ! -f grafana/provisioning/dashboards/dashboards.yml ]; then
    cat > grafana/provisioning/dashboards/dashboards.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF
fi

# Set permissions
chmod +x mongodb_monitoring.py redis_celery_monitoring.py

# Bring up monitoring stack
docker-compose up -d prometheus grafana mongodb-monitoring redis-celery-monitoring

# Wait for services to become available
echo "Waiting for monitoring services to start..."
sleep 10

# Check if services are running
docker-compose ps

echo "Monitoring system deployed successfully!"
echo "Grafana is available at: http://localhost:3000"
echo "Prometheus is available at: http://localhost:9090"
echo "Default Grafana credentials: admin / admin (or configured password)"
echo "Remember to change the default password on first login." 