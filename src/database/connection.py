"""
Database Connection Module

This module provides database connection functionality for the ShopSentiment application.
"""

import os
import logging
import sqlite3
from typing import Any, Dict, Optional
from flask import g # Import g

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConfigurationError, ConnectionFailure

logger = logging.getLogger(__name__)

def get_mongodb_client():
    """Get a MongoDB client connection for the current request context."""
    # Use flask.g to store/retrieve the client for the current request
    if 'mongodb_client' not in g:
        mongo_uri = os.environ.get('MONGODB_URI')
        if not mongo_uri:
            logger.info("MONGODB_URI not set.")
            g.mongodb_client = None # Store None in g if no URI
            return None

        logger.info("Attempting to connect to MongoDB for this request...")
        try:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000) # 5 sec timeout
            # The ismaster command is cheap and does not require auth.
            client.admin.command('ismaster')
            logger.info("MongoDB connection successful for this request.")
            g.mongodb_client = client # Store the client in g
        except (ConfigurationError, ConnectionFailure) as e:
            logger.error(f"MongoDB connection failed: {str(e)}")
            g.mongodb_client = None # Store None in g on failure
        except Exception as e: # Catch other potential errors
            logger.error(f"An unexpected error occurred during MongoDB connection: {str(e)}")
            g.mongodb_client = None # Store None in g on failure
            
    return g.mongodb_client

def get_database() -> Database | sqlite3.Connection | None:
    """
    Get a database connection based on configuration for the current request context.
    Prioritizes MongoDB if MONGODB_URI is set and connection succeeds,
    otherwise falls back to SQLite if USE_SQLITE is true or MongoDB fails.
    
    Returns:
        MongoDB Database object, SQLite Connection object, or None
    """
    use_sqlite = os.environ.get('USE_SQLITE', 'false').lower() == 'true'
    mongo_uri = os.environ.get('MONGODB_URI')
    db_name = os.environ.get('MONGODB_DB', 'shopsentiment_prod') # Default prod DB name

    mongodb_client = None
    if not use_sqlite and mongo_uri:
        mongodb_client = get_mongodb_client()

    if mongodb_client:
        logger.info(f"Using MongoDB database: {db_name}")
        return mongodb_client[db_name]
    else:
        # Fallback to SQLite
        if mongo_uri and not use_sqlite:
             logger.warning("MongoDB connection failed or URI not set, falling back to SQLite.")
        
        db_path = os.environ.get('DATABASE_PATH', 'data/shopsentiment.db')
        # Avoid using SQLite on Heroku unless explicitly configured
        is_heroku = 'DYNO' in os.environ 
        if is_heroku and not use_sqlite:
             logger.error(f"SQLite fallback attempted on Heroku without USE_SQLITE=true. This is not recommended. DB Path: {db_path}")
             # Depending on desired behavior, could return None or raise error
             # For now, let's return None to indicate no suitable DB connection
             return None
        
        logger.info(f"Using SQLite database at {db_path}")
        try:
            # Ensure data directory exists for SQLite
            data_dir = os.path.dirname(db_path)
            if data_dir and not os.path.exists(data_dir):
                os.makedirs(data_dir)
                logger.info(f"Created directory for SQLite DB: {data_dir}")

            # Manage SQLite connection via flask.g as well for consistency
            if 'sqlite_db' not in g:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                g.sqlite_db = conn
            return g.sqlite_db
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to SQLite database at {db_path}: {e}")
            return None

def close_mongodb_connection(e=None):
    """Close MongoDB client connection stored in the request context (g)."""
    # Remove global logic
    # global _mongodb_client 
    client = g.pop('mongodb_client', None)
    if client:
        logger.info("Closing MongoDB connection for this request.")
        client.close()
        # No need to set global to None
        # _mongodb_client = None 

# Add a close_sqlite_db function if needed for consistency, 
# though connection objects usually handle their own closing.

def close_sqlite_db(e=None):
    # This function already correctly uses g
    db = g.pop('sqlite_db', None) # Use 'sqlite_db' to match get_database
    if db is not None:
        db.close()
        logger.info("Closed SQLite connection from g context.") 