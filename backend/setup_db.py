#!/usr/bin/env python3
"""
Setup script for MongoDB and initial data
"""
import sys
import os

# Add the backend directory to Python path
sys.path.append('/Users/macbookair/Documents/Projects/mey/smart_digital_register/backend')

from dotenv import load_dotenv
load_dotenv()

from app.database import MongoDB

def main():
    try:
        print("🚀 Setting up MongoDB database...")
        
        # Initialize MongoDB connection
        db = MongoDB()
        
        print("✅ MongoDB connection successful!")
        
        # Seed initial data
        db.check_and_seed_data()
        
        print("\n📋 Available demo users:")
        users = db.users.find({})
        for user in users:
            print(f"  - Email: {user['email']}")
            print(f"    Role: {user['role']}")
            print(f"    Password: {user['role']}123")
            print()
        
        print("🎉 Setup complete! You can now login with:")
        print("  Email: admin@alexander.academy")
        print("  Password: admin123")
        
        db.close_connection()
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())