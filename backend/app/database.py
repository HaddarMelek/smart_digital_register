"""
MongoDB Database Configuration
"""
import os
from pymongo import MongoClient
from datetime import datetime

class MongoDB:
    def __init__(self):
        """Initialize MongoDB connection"""
        # MongoDB connection URL (you can customize this)
        mongo_url = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        db_name = os.getenv('DB_NAME', 'alexander_academy_db')
        
        try:
            self.client = MongoClient(mongo_url)
            self.db = self.client[db_name]
            
            # Test connection
            self.client.admin.command('ping')
            print(f"✅ Connected to MongoDB: {db_name}")
            
            # Initialize collections
            self.users = self.db.users
            self.students = self.db.students
            self.classes = self.db.classes
            self.attendance = self.db.attendance
            self.alerts = self.db.alerts
            self.predictions = self.db.predictions
            self.reports = self.db.reports
            
            # Create indexes
            self._create_indexes()
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise

    def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Users collection indexes
            self.users.create_index("email", unique=True)
            
            # Students collection indexes
            self.students.create_index("student_id", unique=True)
            self.students.create_index("email", unique=True)
            
            # Attendance collection indexes
            self.attendance.create_index([("student_id", 1), ("date", 1)], unique=True)
            
            print("✅ Database indexes created")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not create indexes: {e}")

    def check_and_seed_data(self):
        """Check if data exists in database, if not seed it with demo data"""
        try:
            # Check if any users exist
            user_count = self.users.count_documents({})
            
            if user_count > 0:
                print("ℹ️ Database already contains data - skipping seed")
                return False
            
            print("📊 Database is empty - seeding with initial data...")
            
            # Import and use the comprehensive demo data
            from app.utils.demo_data import initialize_demo_data
            result = initialize_demo_data(self.db)
            
            print("✅ Database seeded successfully with demo data")
            print("📧 Demo Accounts:")
            print("   Teacher: teacher@alexander.academy / teacher123")
            print("   Admin: admin@alexander.academy / admin123")
            print("   Parent: parent@alexander.academy / parent123")
            
            return True
            
        except Exception as e:
            print(f"❌ Error checking/seeding data: {e}")
            return False

    def close_connection(self):
        """Close MongoDB connection"""
        if hasattr(self, 'client'):
            self.client.close()