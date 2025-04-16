#!/bin/bash
# Heroku deployment script for ShopSentiment

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo -e "${RED}Error: Heroku CLI is not installed. Please install it first.${NC}"
    echo "Visit https://devcenter.heroku.com/articles/heroku-cli for installation instructions."
    exit 1
fi

# Check if user is logged in to Heroku
heroku_login_status=$(heroku auth:whoami 2>&1)
if [[ $heroku_login_status == *"not logged in"* ]]; then
    echo -e "${YELLOW}You need to login to Heroku first.${NC}"
    heroku login
fi

# Get app name from command line or use default
APP_NAME=${1:-shopsentiment}

# Check if the app exists
if heroku apps:info --app "$APP_NAME" &> /dev/null; then
    echo -e "${GREEN}Deploying to existing app: $APP_NAME${NC}"
else
    echo -e "${YELLOW}App '$APP_NAME' not found. Creating new app...${NC}"
    heroku apps:create "$APP_NAME"
fi

# Add MongoDB add-on if not already present
if ! heroku addons:info --app "$APP_NAME" mongolab &> /dev/null; then
    echo -e "${YELLOW}Adding MongoDB add-on...${NC}"
    heroku addons:create --app "$APP_NAME" mongolab:sandbox
fi

# Add Redis add-on if not already present
if ! heroku addons:info --app "$APP_NAME" heroku-redis &> /dev/null; then
    echo -e "${YELLOW}Adding Redis add-on...${NC}"
    heroku addons:create --app "$APP_NAME" heroku-redis:hobby-dev
fi

# Set environment variables
echo -e "${YELLOW}Setting environment variables...${NC}"
heroku config:set --app "$APP_NAME" \
    FLASK_ENV=production \
    SECRET_KEY=$(openssl rand -hex 24) \
    FLASK_APP=app.py

# Push to Heroku
echo -e "${YELLOW}Deploying application to Heroku...${NC}"
git push heroku main

# Run database initialization script
echo -e "${YELLOW}Initializing database...${NC}"
heroku run --app "$APP_NAME" python scripts/init_db.py

# Scale dynos
echo -e "${YELLOW}Scaling dynos...${NC}"
heroku ps:scale --app "$APP_NAME" web=1

# Open the app in browser
echo -e "${GREEN}Deployment completed! Opening app in browser...${NC}"
heroku open --app "$APP_NAME"

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "Your app is running at: ${YELLOW}https://$APP_NAME.herokuapp.com${NC}"
echo -e "To view logs: ${YELLOW}heroku logs --tail --app $APP_NAME${NC}"
echo -e "To open MongoDB dashboard: ${YELLOW}heroku addons:open mongolab --app $APP_NAME${NC}" 