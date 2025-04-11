#!/usr/bin/env python3
"""
Test MongoDB Atlas Connection

This script tests the connection to MongoDB Atlas.
"""

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://tomasstaniulis76:JaLhUd1NLZUtwVb5@shop1.11tjwh5.mongodb.net/?retryWrites=true&w=majority&appName=Shop1"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    
    # Let's also check if we can create a database and collection
    db = client["shopsentiment"]
    print(f"Connected to database: {db.name}")
    
    # List collections (if any)
    collections = db.list_collection_names()
    if collections:
        print(f"Collections in database: {', '.join(collections)}")
    else:
        print("No collections found in database.")
    
    # Create a test collection if it doesn't exist
    if "test_connection" not in collections:
        test_collection = db["test_connection"]
        result = test_collection.insert_one({"test": "connection", "status": "success"})
        print(f"Created test document with ID: {result.inserted_id}")
    
    # List all databases
    databases = client.list_database_names()
    print(f"Available databases: {', '.join(databases)}")
    
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Close the connection
    client.close()
    print("MongoDB connection closed.") 