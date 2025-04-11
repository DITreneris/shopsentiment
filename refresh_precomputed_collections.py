#!/usr/bin/env python
import os
import sys
import logging
from datetime import datetime
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('precomputed_refresh.log')
    ]
)
logger = logging.getLogger(__name__)

def refresh_precomputed_collections():
    '''Refresh all precomputed collections.'''
    # Create MongoDB connection
    uri = os.getenv('MONGO_URI', 
                   "mongodb+srv://tomasstaniulis76:JaLhUd1NLZUtwVb5@shop1.11tjwh5.mongodb.net/")
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client.shopsentiment
    
    logger.info("Starting refresh of precomputed collections")
    
    try:
        # Re-run the bottleneck resolution script
        cmd = "python identify_resolve_bottlenecks.py --refresh-only"
        logger.info(f"Executing: {cmd}")
        exit_code = os.system(cmd)
        
        if exit_code == 0:
            logger.info("Successfully refreshed precomputed collections")
        else:
            logger.error(f"Failed to refresh collections, exit code: {exit_code}")
    
    except Exception as e:
        logger.error(f"Error refreshing precomputed collections: {e}")
    
if __name__ == '__main__':
    refresh_precomputed_collections()
