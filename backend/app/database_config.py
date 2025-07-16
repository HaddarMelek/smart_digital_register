"""
Database Configuration for MongoDB
Supports both local development and MongoDB Atlas (production)
"""

import os
import ssl
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

class DatabaseManager:
    def __init__(self):
        self.setup_mongodb()
    
    def setup_mongodb(self):
        """Setup MongoDB for development and production"""
        # Try production MongoDB Atlas URL first, then fallback to local
        mongo_uri = os.getenv('MONGO_URI') or os.getenv('MONGODB_URI') or 'mongodb://localhost:27017/alexander_academy'
        
        try:
            # Configure SSL context for better compatibility
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Connection options for better reliability
            client_options = {
                'ssl': True,
                'ssl_cert_reqs': ssl.CERT_NONE,  # For development/testing only
                'serverSelectionTimeoutMS': 5000,  # 5 second timeout
                'connectTimeoutMS': 10000,  # 10 second connection timeout
                'socketTimeoutMS': 45000,  # 45 second socket timeout
                'maxPoolSize': 10,
                'minPoolSize': 2,
                'maxIdleTimeMS': 30000,
                'retryWrites': True,
                'retryReads': True
            }
            
            # For MongoDB Atlas connections, ensure proper SSL handling
            if 'mongodb.net' in mongo_uri or 'mongodb+srv://' in mongo_uri:
                client_options.update({
                    'tls': True,
                    'tlsAllowInvalidCertificates': True,  # For development only
                    'tlsAllowInvalidHostnames': True,  # For development only
                })
            
            self.client = MongoClient(mongo_uri, **client_options)
            
            # Test connection with timeout
            self.client.server_info()
            self.db = self.client.alexander_academy
            
            if 'mongodb.net' in mongo_uri:
                print("🌍 Connected to MongoDB Atlas (Production)")
            else:
                print("🍃 Connected to MongoDB (Local)")
                
        except ServerSelectionTimeoutError as e:
            print(f"❌ MongoDB Connection Timeout: {e}")
            print("💡 Tip: Check your MONGO_URI and network connectivity")
            raise
        except Exception as e:
            print(f"❌ MongoDB Connection Error: {e}")
            print("💡 Tip: For MongoDB Atlas, ensure your IP is whitelisted")
            raise
    
    def get_mongodb(self):
        """Get MongoDB database"""
        return self.db

# Global database instance
db_manager = DatabaseManager()