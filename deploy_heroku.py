#!/usr/bin/env python3
"""
Heroku Deployment Helper for ShopSentiment

This script helps with deploying the ShopSentiment application to Heroku.
It performs checks and provides guidance on the deployment process.
"""

import os
import sys
import subprocess
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("deploy_heroku")

def check_heroku_cli():
    """Check if Heroku CLI is installed."""
    try:
        result = subprocess.run(
            ["heroku", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Heroku CLI detected: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Heroku CLI not found. Please install it from https://devcenter.heroku.com/articles/heroku-cli")
        return False

def check_git():
    """Check if git is installed and repository is initialized."""
    try:
        result = subprocess.run(
            ["git", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Git detected: {result.stdout.strip()}")
        
        # Check if git repository exists
        if not os.path.exists(".git"):
            logger.warning("Git repository not initialized. Initializing...")
            subprocess.run(["git", "init"], check=True)
            logger.info("Git repository initialized.")
            
            # Basic gitignore
            if not os.path.exists(".gitignore"):
                with open(".gitignore", "w") as f:
                    f.write("__pycache__/\n*.py[cod]\n*$py.class\n.env\n.venv\nenv/\nvenv/\nENV/\n*.log\n.DS_Store\n")
                logger.info("Created .gitignore file")
        
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Git not found. Please install git.")
        return False

def check_files():
    """Check if required files for Heroku deployment exist."""
    required_files = {
        "Procfile": "Defines process types and commands (web: gunicorn wsgi:app)",
        "requirements.txt": "Lists dependencies",
        "runtime.txt": "Specifies Python version (python-3.10.12)",
        "wsgi.py": "WSGI entry point"
    }
    
    missing_files = []
    for file_name, description in required_files.items():
        if not os.path.exists(file_name):
            missing_files.append((file_name, description))
    
    if missing_files:
        logger.error("Missing required files for Heroku deployment:")
        for file_name, description in missing_files:
            logger.error(f"  - {file_name}: {description}")
        return False
    
    logger.info("All required files for Heroku deployment exist.")
    return True

def create_heroku_app(app_name=None):
    """Create Heroku app if it doesn't exist."""
    try:
        if app_name:
            # Check if app exists
            result = subprocess.run(
                ["heroku", "apps:info", "-a", app_name],
                check=False,
                capture_output=True,
                text=True
            )
            
            if "Couldn't find that app" in result.stderr:
                # Create app with specified name
                subprocess.run(["heroku", "apps:create", app_name], check=True)
                logger.info(f"Created Heroku app: {app_name}")
            else:
                logger.info(f"Using existing Heroku app: {app_name}")
        else:
            # Create app with generated name
            result = subprocess.run(
                ["heroku", "apps:create"],
                check=True,
                capture_output=True,
                text=True
            )
            app_name = result.stdout.strip().split(" ")[-1].strip()
            logger.info(f"Created Heroku app: {app_name}")
        
        return app_name
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating Heroku app: {e}")
        return None

def setup_mongodb(app_name):
    """Set up MongoDB addon."""
    try:
        # Add MongoDB addon
        subprocess.run(
            ["heroku", "addons:create", "mongolab:sandbox", "-a", app_name],
            check=False,  # Don't exit if it fails (might already exist)
            capture_output=True,
            text=True
        )
        logger.info("Added MongoDB addon or using existing one.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error setting up MongoDB: {e}")
        return False

def deploy_to_heroku(app_name):
    """Deploy application to Heroku."""
    try:
        # Add git remote if not exists
        subprocess.run(
            ["heroku", "git:remote", "-a", app_name],
            check=True
        )
        logger.info(f"Added Heroku remote for {app_name}")
        
        # Commit changes if needed
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True
        ).stdout.strip()
        
        if status:
            logger.info("Uncommitted changes detected. Committing...")
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(
                ["git", "commit", "-m", "Prepare for Heroku deployment"],
                check=True
            )
            logger.info("Changes committed.")
        
        # Push to Heroku
        logger.info("Deploying to Heroku... This may take a few minutes.")
        subprocess.run(["git", "push", "heroku", "main:main"], check=False)
        subprocess.run(["git", "push", "heroku", "master:main"], check=False)
        
        logger.info("Deployment complete!")
        
        # Show app URL
        subprocess.run(["heroku", "open", "-a", app_name], check=False)
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error deploying to Heroku: {e}")
        return False

def main():
    """Main function for deploying to Heroku."""
    logger.info("Starting ShopSentiment Heroku deployment helper")
    
    # Check prerequisites
    if not check_heroku_cli() or not check_git() or not check_files():
        logger.error("Please fix the issues above before continuing.")
        sys.exit(1)
    
    # Get app name
    app_name = input("Enter Heroku app name (leave blank for auto-generated name): ").strip()
    
    # Create Heroku app
    app_name = create_heroku_app(app_name)
    if not app_name:
        logger.error("Failed to create Heroku app. Exiting.")
        sys.exit(1)
    
    # Set up MongoDB
    if not setup_mongodb(app_name):
        logger.warning("MongoDB setup had issues. You may need to configure it manually.")
    
    # Deploy to Heroku
    if deploy_to_heroku(app_name):
        logger.info(f"Application deployed successfully to https://{app_name}.herokuapp.com")
        logger.info(f"You can manage your app at https://dashboard.heroku.com/apps/{app_name}")
    else:
        logger.error("Deployment failed. Please check the logs.")
        sys.exit(1)

if __name__ == "__main__":
    main() 