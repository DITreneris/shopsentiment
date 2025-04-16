"""
SQLite Connection Module

This module provides SQLite database connection functionality for the ShopSentiment application.
"""

import os
import logging
import sqlite3
from typing import Any, Dict

logger = logging.getLogger(__name__)

def get_sqlite_db():
    """
    Get a SQLite database connection.
    
    Returns:
        SQLite connection object with row factory set to sqlite3.Row
    """
    db_path = os.environ.get('DATABASE_PATH', 'data/shopsentiment.db')
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    logger.debug(f"Using SQLite database at {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def close_sqlite_db(conn):
    """
    Close SQLite database connection.
    
    Args:
        conn: SQLite connection to close
    """
    if conn:
        conn.close()
        logger.debug("SQLite connection closed")
    return 