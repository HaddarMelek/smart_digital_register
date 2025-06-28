"""
Database Configuration for MongoDB
Supports both local development and MongoDB Atlas (production)
"""

import os
from pymongo import MongoClient

class DatabaseManager:
    def __init__(self):
        self.setup_mongodb()
    
    def setup_mongodb(self):
        """Setup MongoDB for development and production"""
        # Try production MongoDB Atlas URL first, then fallback to local
        mongo_uri = os.getenv('MONGO_URI') or os.getenv('MONGODB_URI') or 'mongodb://localhost:27017/alexander_academy'
        
        try:
            self.client = MongoClient(mongo_uri)
            # Test connection
            self.client.server_info()
            self.db = self.client.alexander_academy
            
            if 'mongodb.net' in mongo_uri:
                print("🌍 Connected to MongoDB Atlas (Production)")
            else:
                print("🍃 Connected to MongoDB (Local)")
                
        except Exception as e:
            print(f"❌ MongoDB Connection Error: {e}")
            raise
    
    def get_mongodb(self):
        """Get MongoDB database"""
        return self.db

# Global database instance
db_manager = DatabaseManager()