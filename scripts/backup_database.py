#!/usr/bin/env python3
"""
Database Backup Script for ShopSentiment

This script creates backups of both MongoDB and SQLite databases used by the ShopSentiment application.
"""

import os
import sys
import time
import logging
import sqlite3
import subprocess
import shutil
from datetime import datetime
from pymongo import MongoClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("backup_database")

def get_backup_directory():
    """Get backup directory path, create if it doesn't exist."""
    backup_dir = os.environ.get("BACKUP_DIR", "backups")
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        logger.info(f"Created backup directory: {backup_dir}")
    
    # Create date-based subdirectory
    date_str = datetime.now().strftime("%Y-%m-%d")
    date_dir = os.path.join(backup_dir, date_str)
    
    if not os.path.exists(date_dir):
        os.makedirs(date_dir)
        logger.info(f"Created date-based backup directory: {date_dir}")
    
    return date_dir

def backup_mongodb():
    """Backup MongoDB database using mongodump."""
    try:
        backup_dir = get_backup_directory()
        mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/shopsentiment")
        
        # Extract database name from URI
        db_name = mongodb_uri.split('/')[-1]
        
        # Create MongoDB backup directory
        mongo_backup_dir = os.path.join(backup_dir, "mongodb")
        if not os.path.exists(mongo_backup_dir):
            os.makedirs(mongo_backup_dir)
        
        # Create timestamp for the backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(mongo_backup_dir, f"{db_name}_{timestamp}")
        
        # Run mongodump command
        cmd = [
            "mongodump", 
            "--uri", mongodb_uri,
            "--out", output_dir
        ]
        
        logger.info(f"Running MongoDB backup: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        logger.info(f"MongoDB backup completed: {output_dir}")
        logger.debug(result.stdout)
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"MongoDB backup failed: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error backing up MongoDB: {str(e)}")
        return False

def backup_sqlite():
    """Backup SQLite database."""
    try:
        backup_dir = get_backup_directory()
        db_path = os.environ.get("DATABASE_PATH", "data/shopsentiment.db")
        
        # Check if SQLite database exists
        if not os.path.exists(db_path):
            logger.warning(f"SQLite database not found at {db_path}, skipping backup")
            return True
        
        # Create SQLite backup directory
        sqlite_backup_dir = os.path.join(backup_dir, "sqlite")
        if not os.path.exists(sqlite_backup_dir):
            os.makedirs(sqlite_backup_dir)
        
        # Create timestamp for the backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_filename = os.path.basename(db_path)
        backup_filename = f"{os.path.splitext(db_filename)[0]}_{timestamp}.db"
        backup_path = os.path.join(sqlite_backup_dir, backup_filename)
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        
        # Create a backup using the SQLite .backup command
        with sqlite3.connect(backup_path) as backup_conn:
            conn.backup(backup_conn)
        
        conn.close()
        
        logger.info(f"SQLite backup completed: {backup_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error backing up SQLite database: {str(e)}")
        return False

def main():
    """Main function."""
    logger.info("Starting database backup process")
    
    mongodb_result = backup_mongodb()
    sqlite_result = backup_sqlite()
    
    if mongodb_result and sqlite_result:
        logger.info("All database backups completed successfully")
        sys.exit(0)
    elif mongodb_result:
        logger.warning("MongoDB backup completed, but SQLite backup failed")
        sys.exit(1)
    elif sqlite_result:
        logger.warning("SQLite backup completed, but MongoDB backup failed")
        sys.exit(1)
    else:
        logger.error("All database backups failed")
        sys.exit(2)

if __name__ == "__main__":
    main() 