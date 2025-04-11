# ShopSentiment Deployment Guide

This document provides detailed instructions for deploying the ShopSentiment application using Docker in both development and production environments.

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)
- A server with at least 2GB RAM (for production)

## Deployment Options

There are two primary deployment methods:

1. **Docker Compose** (Recommended): Simplifies deployment by orchestrating multiple containers
2. **Manual Deployment**: For environments where Docker is not available

## 1. Docker Compose Deployment

### Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/shopsentiment.git
   cd shopsentiment
   ```

2. Create a `.env` file based on the example:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file with appropriate values for development:
   ```
   FLASK_ENV=development
   SECRET_KEY=your-dev-secret-key
   ```

4. Start the development environment:
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

5. Initialize the database:
   ```bash
   docker-compose exec web flask db upgrade
   ```

6. Access the application at http://localhost:5000

### Production Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/shopsentiment.git
   cd shopsentiment
   ```

2. Create a `.env` file based on the example:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file with secure values for production:
   ```
   FLASK_ENV=production
   SECRET_KEY=your-secure-random-key
   ```

4. Start the production environment:
   ```bash
   docker-compose up -d
   ```

5. Initialize the database:
   ```bash
   docker-compose exec web flask db upgrade
   ```

6. Configure a reverse proxy (Nginx or similar) to handle HTTPS termination. A sample Nginx configuration is provided in the `nginx/` directory.

### Environment Configuration

Key environment variables to configure:

| Variable | Description | Example |
|----------|-------------|---------|
| SECRET_KEY | Flask secret key | `9a8f7e6d5c4b3a2b1c0d9e8f` |
| FLASK_ENV | Application environment | `production` |
| REDIS_URL | Redis connection string | `redis://redis:6379/0` |
| DATABASE_URL | Database connection string | `sqlite:///data/shopsentiment.db` |
| CELERY_BROKER_URL | Celery broker URL | `redis://redis:6379/1` |
| CELERY_RESULT_BACKEND | Celery result backend URL | `redis://redis:6379/2` |
| WTF_CSRF_ENABLED | Enable CSRF protection | `True` |
| WTF_CSRF_SECRET_KEY | CSRF secret key | `your-secure-csrf-key` |
| SECURITY_PASSWORD_SALT | Password salt for security | `your-secure-password-salt` |

## 2. Manual Deployment

While Docker is recommended, here are instructions for manual deployment:

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/shopsentiment.git
   cd shopsentiment
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Redis server

5. Create a `.env` file with appropriate configuration

6. Initialize the database:
   ```bash
   flask db upgrade
   ```

### Starting Services

1. Start Redis server
2. Start Celery worker:
   ```bash
   celery -A app.tasks.celery worker --loglevel=info
   ```
3. Start Celery beat (if scheduled tasks are needed):
   ```bash
   celery -A app.tasks.celery beat --loglevel=info
   ```
4. Start the Flask application with Gunicorn:
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 wsgi:app
   ```

## Monitoring and Maintenance

### Logs

View logs for each service:

```bash
# Web application logs
docker-compose logs web

# Redis logs
docker-compose logs redis

# Celery worker logs
docker-compose logs worker

# Celery beat logs
docker-compose logs beat
```

### Database Backups

1. Create a backup:
   ```bash
   docker-compose exec web sh -c "sqlite3 data/shopsentiment.db .dump > /app/data/backup-$(date +%Y%m%d).sql"
   ```

2. Restore a backup:
   ```bash
   docker-compose exec web sh -c "cat /app/data/backup-file.sql | sqlite3 data/shopsentiment.db"
   ```

## Performance Tuning

### Gunicorn Workers

The number of Gunicorn workers should be adjusted based on your server's CPU cores:

```
workers = (2 * CPU cores) + 1
```

Modify the workers setting in the Dockerfile or command line.

### Redis Performance

For high-volume usage, consider tuning Redis configuration with:

```
maxmemory 256mb
maxmemory-policy allkeys-lru
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` files with sensitive information
2. **HTTPS**: Always use HTTPS in production
3. **Updates**: Regularly update dependencies with `pip install --upgrade -r requirements.txt`
4. **Database**: Set proper permissions on SQLite database files
5. **Secrets**: Use strong, randomly generated secrets for all keys

## Troubleshooting

### Common Issues

1. **Container fails to start**:
   - Check logs: `docker-compose logs web`
   - Verify environment variables

2. **Database connection issues**:
   - Ensure database file permissions are correct
   - Check database URL configuration

3. **Redis connection issues**:
   - Verify Redis is running: `docker-compose ps`
   - Check Redis connection URL

### Getting Help

If you encounter issues, please:

1. Check the logs for error messages
2. Refer to the project's issue tracker
3. Contact the maintainers with detailed information about your problem

## Updates and Upgrades

To update the application:

1. Pull the latest changes:
   ```bash
   git pull origin main
   ```

2. Rebuild and restart containers:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

3. Apply database migrations if necessary:
   ```bash
   docker-compose exec web flask db upgrade
   ``` 