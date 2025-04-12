"""Database connection and management for Shop Sentiment Analysis"""
import os
import logging
import json
import pymongo
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

# Configure logging
logger = logging.getLogger(__name__)

# MongoDB connection string from environment variable
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/shopsentiment')

# Initialize connection
try:
    client = MongoClient(MONGODB_URI)
    db = client.get_database()
    logger.info(f"Connected to MongoDB: {db.name}")
    
    # Create collections if they don't exist
    if 'users' not in db.list_collection_names():
        db.create_collection('users')
        logger.info("Created users collection")
    
    if 'products' not in db.list_collection_names():
        db.create_collection('products')
        logger.info("Created products collection")
    
    if 'reviews' not in db.list_collection_names():
        db.create_collection('reviews')
        logger.info("Created reviews collection")
    
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    
    # Fallback to JSON file storage
    logger.info("Falling back to JSON file storage")
    db = None

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle MongoDB ObjectId and dates"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

def get_collection(collection_name):
    """Get a MongoDB collection or fallback to JSON file"""
    if db:
        return db[collection_name]
    else:
        # Fallback to JSON file storage
        return FileCollection(collection_name)

class FileCollection:
    """Fallback collection that stores data in JSON files"""
    def __init__(self, name):
        self.name = name
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.file_path = os.path.join(self.data_dir, f"{name}.json")
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Make sure the JSON file exists"""
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)
    
    def _load_data(self):
        """Load data from the JSON file"""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_data(self, data):
        """Save data to the JSON file"""
        with open(self.file_path, 'w') as f:
            json.dump(data, f, cls=JSONEncoder, indent=2)
    
    def find(self, query=None):
        """Simulate MongoDB find method"""
        data = self._load_data()
        if not query:
            return data
        
        # Simple query filtering
        result = []
        for item in data:
            match = True
            for key, value in query.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                result.append(item)
        return result
    
    def find_one(self, query):
        """Simulate MongoDB find_one method"""
        results = self.find(query)
        return results[0] if results else None
    
    def insert_one(self, document):
        """Simulate MongoDB insert_one method"""
        data = self._load_data()
        
        # Add _id if not present
        if '_id' not in document:
            document['_id'] = str(ObjectId())
        
        # Add timestamps
        document['created_at'] = datetime.now().isoformat()
        
        data.append(document)
        self._save_data(data)
        return InsertOneResult(document['_id'])
    
    def update_one(self, query, update):
        """Simulate MongoDB update_one method"""
        data = self._load_data()
        modified_count = 0
        
        for i, item in enumerate(data):
            match = True
            for key, value in query.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            
            if match:
                # Handle $set operator
                if '$set' in update:
                    for key, value in update['$set'].items():
                        item[key] = value
                
                # Add updated_at timestamp
                item['updated_at'] = datetime.now().isoformat()
                
                data[i] = item
                modified_count = 1
                break
        
        self._save_data(data)
        return UpdateResult(modified_count)
    
    def delete_one(self, query):
        """Simulate MongoDB delete_one method"""
        data = self._load_data()
        new_data = []
        deleted_count = 0
        
        for item in data:
            match = True
            for key, value in query.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            
            if match and deleted_count == 0:
                deleted_count = 1
                continue
            
            new_data.append(item)
        
        self._save_data(new_data)
        return DeleteResult(deleted_count)

class InsertOneResult:
    """Simulate MongoDB InsertOneResult"""
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id

class UpdateResult:
    """Simulate MongoDB UpdateResult"""
    def __init__(self, modified_count):
        self.modified_count = modified_count

class DeleteResult:
    """Simulate MongoDB DeleteResult"""
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count

# Initialize collections
users = get_collection('users')
products = get_collection('products')
reviews = get_collection('reviews') 