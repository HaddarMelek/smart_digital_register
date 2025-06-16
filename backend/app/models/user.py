"""
User model for MongoDB operations
"""
from werkzeug.security import check_password_hash
from bson import ObjectId
from datetime import datetime, timezone

class User:
    def __init__(self, db):
        """Initialize User model with database connection"""
        self.db = db
    
    def find_by_email(self, email):
        """Find user by email"""
        user = self.db.users.find_one({'email': email})
        if user:
            # Convert ObjectId to string for JSON serialization
            user['id'] = str(user['_id'])
            del user['_id']  # Remove original _id field
        return user
        
    def find_by_id(self, user_id):
        """Find user by ID"""
        try:
            # Convert string ID to ObjectId if needed
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            user = self.db.users.find_one({'_id': user_id})
            if user:
                user['id'] = str(user['_id'])
                del user['_id']  # Remove original _id field
            return user
        except Exception as e:
            print(f"Error finding user by ID: {e}")
            return None
    
    def verify_password(self, email, password):
        """Verify user password"""
        user = self.db.users.find_one({'email': email})
        if not user:
            return False
        # Check for both 'password' and 'password_hash' fields for backward compatibility
        stored_password = user.get('password') or user.get('password_hash')
        if not stored_password:
            return False
        return check_password_hash(stored_password, password)
    
    def update(self, user_id, data):
        """Update user data"""
        try:
            # Convert string ID to ObjectId if needed
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            query = {'_id': user_id}
            
            # Add updated timestamp
            data['updated_at'] = datetime.now(timezone.utc)
            
            result = self.db.users.update_one(query, {'$set': data})
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    @classmethod 
    def create(cls, db, user_data):
        """Create new user"""
        user_data['created_at'] = datetime.now(timezone.utc)
        result = db.users.insert_one(user_data)
        return result.inserted_id