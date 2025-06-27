"""
Database Configuration for Production and Development
Supports both MongoDB (development) and PostgreSQL (production)
"""

import os
from pymongo import MongoClient
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

class DatabaseManager:
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.setup_database()
    
    def setup_database(self):
        if self.environment == 'production':
            self.setup_postgresql()
        else:
            self.setup_mongodb()
    
    def setup_postgresql(self):
        """Setup PostgreSQL for production (Render)"""
        database_url = os.getenv('DATABASE_URL')
        if database_url and database_url.startswith('postgres://'):
            # Fix for SQLAlchemy 1.4+ compatibility
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()
        
        print("🗄️ Connected to PostgreSQL (Production)")
    
    def setup_mongodb(self):
        """Setup MongoDB for development"""
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/alexander_academy')
        self.client = MongoClient(mongo_uri)
        self.db = self.client.alexander_academy
        
        print("🍃 Connected to MongoDB (Development)")
    
    def get_session(self):
        """Get database session for PostgreSQL"""
        if hasattr(self, 'SessionLocal'):
            return self.SessionLocal()
        return None
    
    def get_mongodb(self):
        """Get MongoDB database"""
        if hasattr(self, 'db'):
            return self.db
        return None

# Global database instance
db_manager = DatabaseManager()