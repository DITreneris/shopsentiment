"""
Database Connection Module

This module provides database connection functionality for the ShopSentiment application.
"""

import os
import logging
import sqlite3
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

def get_database():
    """
    Get a database connection based on configuration.
    For now, this is a simple SQLite connection.
    
    Returns:
        Database connection object
    """
    db_path = os.environ.get('DATABASE_PATH', 'data/shopsentiment.db')
    logger.debug(f"Using SQLite database at {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_mongodb_client():
    """
    Get a MongoDB client connection.
    This function is a stub that returns None, as we're using SQLite by default.
    
    Returns:
        None as we're not using MongoDB
    """
    logger.warning("MongoDB client requested but not configured - using SQLite instead")
    return None

def close_mongodb_connection(client):
    """
    Close MongoDB client connection.
    This function is a stub that does nothing, as we're using SQLite by default.
    
    Args:
        client: MongoDB client to close (not used)
    """
    logger.warning("MongoDB connection close requested but not configured")
    return 