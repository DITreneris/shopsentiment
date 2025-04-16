# Heroku Configuration Variables for ShopSentiment

This document lists all environment variables that need to be set in Heroku for the ShopSentiment application.

## Required Variables

| Variable Name | Description | Default Value | Source |
|---------------|-------------|---------------|--------|
| `SECRET_KEY` | Flask secret key for session security | N/A (Must be set manually) | Generate a secure random string |
| `WTF_CSRF_SECRET_KEY` | Secret key for CSRF protection | N/A (Must be set manually) | Generate a secure random string |
| `SECURITY_PASSWORD_SALT` | Salt for password hashing | N/A (Must be set manually) | Generate a secure random string |
| `DATABASE_PATH` | Path to SQLite database (fallback) | data/shopsentiment.db | Set only if using SQLite fallback |

## Variables Set Automatically by Add-ons

These variables will be set automatically when you add the corresponding add-ons to your Heroku app:

| Variable Name | Description | Add-on |
|---------------|-------------|--------|
| `MONGODB_URI` | MongoDB connection string | MongoDB Atlas (mLab) |
| `REDIS_URL` | Redis connection string | Heroku Redis |

## Optional Variables

| Variable Name | Description | Default Value | When to Set |
|---------------|-------------|---------------|-------------|
| `USE_SQLITE` | Flag to use SQLite instead of MongoDB | false | Set to "true" if MongoDB is not available |
| `LOG_LEVEL` | Application logging level | INFO | Change to "DEBUG" for troubleshooting |
| `FLASK_ENV` | Flask environment | production | Already set in .env.production |
| `TRUSTED_PROXIES` | Number of proxies in front of the app | 1 | Increase if using multiple proxies |

## Email Configuration (If Needed)

| Variable Name | Description | Default Value |
|---------------|-------------|---------------|
| `MAIL_SERVER` | SMTP server address | smtp.example.com |
| `MAIL_PORT` | SMTP port | 587 |
| `MAIL_USE_TLS` | Whether to use TLS | True |
| `MAIL_USERNAME` | SMTP username | your-email@example.com |
| `MAIL_PASSWORD` | SMTP password | N/A (Must be set manually) |
| `MAIL_DEFAULT_SENDER` | Default sender email | your-email@example.com |

## How to Set Configuration Variables in Heroku

### Using Heroku CLI

```bash
heroku config:set VARIABLE_NAME=value --app your-app-name
```

### Using Heroku Dashboard

1. Go to your app's dashboard on Heroku
2. Click on the "Settings" tab
3. Click on "Reveal Config Vars"
4. Add key-value pairs for each variable

### Setting Multiple Variables at Once

```bash
heroku config:set SECRET_KEY=your-secret-key WTF_CSRF_SECRET_KEY=another-secret-key --app your-app-name
```

## Generating Secure Keys

Use the following Python code to generate secure random keys:

```python
import secrets
print(secrets.token_hex(32))  # Generates a 64-character hexadecimal string
``` 