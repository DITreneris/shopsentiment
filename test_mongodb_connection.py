from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test MongoDB Atlas connection"""
    uri = "mongodb+srv://tomasstaniulis76:JaLhUd1NLZUtwVb5@shop1.11tjwh5.mongodb.net/?retryWrites=true&w=majority&appName=Shop1"

    try:
        # Create a new client and connect to the server
        client = MongoClient(uri, server_api=ServerApi('1'))
        
        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # Get database statistics
        db = client.shopsentiment
        stats = db.command("dbstats")
        print("\nDatabase Statistics:")
        print(f"- Database Size: {stats['dataSize']/1024/1024:.2f} MB")
        print(f"- Collections: {stats['collections']}")
        print(f"- Objects: {stats['objects']}")
        
        # List collections
        collections = db.list_collection_names()
        if collections:
            print("\nExisting Collections:")
            for collection in collections:
                count = db[collection].count_documents({})
                print(f"- {collection}: {count} documents")
        else:
            print("\nNo collections found in the database.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to MongoDB Atlas: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection() 