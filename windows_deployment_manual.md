# ShopSentiment Windows Deployment - Manual Guide

This guide provides step-by-step CMD commands for deploying ShopSentiment on Windows.

## Prerequisites

- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop) installed and running
- [Git for Windows](https://git-scm.com/download/win) (optional)

## Step-by-Step Deployment

Open Command Prompt (CMD) and run the following commands:

### 1. Create Project Directory

```cmd
mkdir %USERPROFILE%\ShopSentiment
cd /d %USERPROFILE%\ShopSentiment
```

### 2. Clone the Repository

If you have Git installed:

```cmd
git clone https://github.com/yourusername/shop-sentiment.git .
```

Otherwise, download and extract the repository manually to `%USERPROFILE%\ShopSentiment`

### 3. Create Environment File

If `.env.example` exists:

```cmd
copy .env.example .env
```

Otherwise, create a new `.env` file with:

```cmd
echo # Flask configuration > .env
echo FLASK_APP=wsgi.py >> .env
echo FLASK_ENV=production >> .env
echo SECRET_KEY=windows-manual-change-this-key >> .env
echo # Database configuration >> .env
echo DATABASE_URL=sqlite:///data/shopsentiment.db >> .env
echo # Redis configuration >> .env
echo REDIS_URL=redis://redis:6379/0 >> .env
echo # Celery configuration >> .env
echo CELERY_BROKER_URL=redis://redis:6379/1 >> .env
echo CELERY_RESULT_BACKEND=redis://redis:6379/2 >> .env
echo # Security configuration >> .env
echo WTF_CSRF_ENABLED=True >> .env
echo WTF_CSRF_SECRET_KEY=windows-manual-csrf-key-change-this >> .env
echo SECURITY_PASSWORD_SALT=windows-manual-salt-change-this >> .env
echo # Rate limiting >> .env
echo RATELIMIT_STORAGE_URL=redis://redis:6379/3 >> .env
echo RATELIMIT_STRATEGY=fixed-window >> .env
```

### 4. Create Data Directory

```cmd
mkdir data
```

### 5. Build Docker Containers

```cmd
docker-compose build
```

### 6. Start Docker Containers

```cmd
docker-compose up -d
```

### 7. Check Container Status

```cmd
docker-compose ps
```

### 8. Initialize the Database

```cmd
docker-compose exec web flask init-db
```

## Common Operations

### View Application Logs

```cmd
docker-compose logs
```

### Follow Logs in Real-time

```cmd
docker-compose logs -f
```

### Stop the Application

```cmd
docker-compose down
```

### Restart the Application

```cmd
docker-compose restart
```

### Update from Repository

```cmd
git pull
docker-compose down
docker-compose up -d --build
```

### Create a Backup

```cmd
mkdir backups
docker-compose exec web sh -c "sqlite3 data/shopsentiment.db .dump" > backups\backup-%date:~-4,4%%date:~-7,2%%date:~-10,2%.sql
```

### Restore from Backup

```cmd
docker-compose down
docker-compose up -d redis
type backups\your-backup-file.sql | docker-compose exec -T web sqlite3 data/shopsentiment.db
docker-compose up -d
```

## Troubleshooting

### Docker Daemon Not Running

If you see "Error response from daemon: dial unix docker.sock..."

1. Open Docker Desktop
2. Wait for it to start completely
3. Try the command again

### Docker Compose Not Found

If "docker-compose" is not recognized:

1. Ensure Docker Desktop is installed
2. Try using `docker compose` (with a space) instead of `docker-compose`

### Container Fails to Start

Check for port conflicts:

```cmd
netstat -ano | findstr :5000
```

If a process is using port 5000, modify the port in docker-compose.yml or stop the conflicting process.

### Accessing the Web Interface

Open your browser and navigate to:

```
http://localhost:5000
```

If you can't access it, check that:
1. Containers are running (`docker-compose ps`)
2. No firewall is blocking access
3. The web container is listening on port 5000

## Additional Resources

For more detailed instructions, refer to:
- The project's README.md file
- Documentation in the docs/ directory
- Docker documentation at [docs.docker.com](https://docs.docker.com/) 