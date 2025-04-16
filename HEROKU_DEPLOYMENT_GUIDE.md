# Heroku Deployment Guide for ShopSentiment

This document provides a comprehensive guide for deploying the ShopSentiment application to Heroku.

## Prerequisites

Before deploying to Heroku, ensure you have:

1. [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed
2. A Heroku account
3. Git installed
4. Your application code committed to a git repository

## Deployment Methods

### Automatic Deployment

The easiest way to deploy the application is using our deployment script:

```bash
./scripts/deploy_heroku.sh your-app-name
```

This script will:
- Create a new Heroku app or use an existing one
- Add the necessary add-ons (MongoDB and Redis)
- Configure environment variables
- Deploy the application
- Initialize the database
- Scale dynos

### Manual Deployment

If you prefer to deploy manually, follow these steps:

1. **Login to Heroku**:
   ```bash
   heroku login
   ```

2. **Create a new Heroku app**:
   ```bash
   heroku create your-app-name
   ```

3. **Add MongoDB add-on**:
   ```bash
   heroku addons:create mongolab:sandbox --app your-app-name
   ```

4. **Add Redis add-on** (for caching):
   ```bash
   heroku addons:create heroku-redis:hobby-dev --app your-app-name
   ```

5. **Configure environment variables**:
   ```bash
   heroku config:set SECRET_KEY=$(openssl rand -hex 24) --app your-app-name
   heroku config:set FLASK_ENV=production --app your-app-name
   heroku config:set FLASK_APP=app.py --app your-app-name
   ```

6. **Deploy the application**:
   ```bash
   git push heroku main
   ```

7. **Initialize the database**:
   ```bash
   heroku run python scripts/init_db.py --app your-app-name
   ```

8. **Scale dynos**:
   ```bash
   heroku ps:scale web=1 --app your-app-name
   ```

## Deployment Files

The following files are specifically configured for Heroku deployment:

- **Procfile**: Tells Heroku how to run the application
- **runtime.txt**: Specifies the Python version
- **requirements.txt**: Lists all dependencies
- **app.json**: Describes the application for Heroku dashboard
- **config/heroku.py**: Heroku-specific configuration
- **gunicorn_config.py**: Gunicorn configuration for Heroku
- **wsgi.py**: WSGI entry point

## Verifying Deployment

After deployment, verify that your application is running correctly:

```bash
heroku open --app your-app-name
```

Check the logs for any errors:

```bash
heroku logs --tail --app your-app-name
```

## Monitoring

Heroku provides several tools for monitoring your application:

- **Heroku Dashboard**: View application metrics, logs, and status
- **Heroku Metrics**: Detailed performance metrics
- **Heroku Add-ons**: Additional monitoring tools

Access the dashboard through:

```bash
heroku dashboard --app your-app-name
```

## Scaling

To scale your application, adjust the number of dynos:

```bash
# Scale up
heroku ps:scale web=2 --app your-app-name

# Scale down
heroku ps:scale web=1 --app your-app-name
```

## Database Management

To access your MongoDB database:

```bash
heroku addons:open mongolab --app your-app-name
```

## Troubleshooting

### Application Crashes

If your application crashes on startup:

1. Check the logs:
   ```bash
   heroku logs --tail --app your-app-name
   ```

2. Verify environment variables:
   ```bash
   heroku config --app your-app-name
   ```

3. Test locally in a Heroku-like environment:
   ```bash
   python scripts/test_heroku_local.py
   ```

### Connection Issues

If you have issues connecting to add-ons:

1. Verify add-ons are provisioned:
   ```bash
   heroku addons --app your-app-name
   ```

2. Check connection strings:
   ```bash
   heroku config:get MONGODB_URI --app your-app-name
   heroku config:get REDIS_URL --app your-app-name
   ```

## Resources

- [Heroku Dev Center](https://devcenter.heroku.com/)
- [Heroku Python Support](https://devcenter.heroku.com/articles/python-support)
- [Heroku MongoDB](https://devcenter.heroku.com/articles/mongolab)
- [Heroku Redis](https://devcenter.heroku.com/articles/heroku-redis) 