@echo on
REM Deploy monitoring system for the ShopSentiment application

REM Create necessary directories
mkdir prometheus 2>nul
mkdir grafana\provisioning\datasources 2>nul
mkdir grafana\provisioning\dashboards 2>nul

REM Copy configuration files
copy prometheus.yml prometheus\
copy prometheus\prometheus.yml prometheus\
copy grafana\provisioning\datasources\prometheus.yml grafana\provisioning\datasources\
copy mongodb_dashboard.json grafana\provisioning\dashboards\
copy redis_celery_dashboard.json grafana\provisioning\dashboards\

REM Create dashboard provisioning config if it doesn't exist
if not exist grafana\provisioning\dashboards\dashboards.yml (
    echo apiVersion: 1 > grafana\provisioning\dashboards\dashboards.yml
    echo. >> grafana\provisioning\dashboards\dashboards.yml
    echo providers: >> grafana\provisioning\dashboards\dashboards.yml
    echo   - name: 'Default' >> grafana\provisioning\dashboards\dashboards.yml
    echo     orgId: 1 >> grafana\provisioning\dashboards\dashboards.yml
    echo     folder: '' >> grafana\provisioning\dashboards\dashboards.yml
    echo     type: file >> grafana\provisioning\dashboards\dashboards.yml
    echo     disableDeletion: false >> grafana\provisioning\dashboards\dashboards.yml
    echo     editable: true >> grafana\provisioning\dashboards\dashboards.yml
    echo     options: >> grafana\provisioning\dashboards\dashboards.yml
    echo       path: /etc/grafana/provisioning/dashboards >> grafana\provisioning\dashboards\dashboards.yml
)

REM Bring up monitoring stack
docker-compose up -d prometheus grafana mongodb-monitoring redis-celery-monitoring

REM Wait for services to become available
echo Waiting for monitoring services to start...
timeout /t 10 /nobreak > nul

REM Check if services are running
docker-compose ps

echo.
echo Monitoring system deployed successfully!
echo Grafana is available at: http://localhost:3000
echo Prometheus is available at: http://localhost:9090
echo Default Grafana credentials: admin / admin (or configured password)
echo Remember to change the default password on first login. 