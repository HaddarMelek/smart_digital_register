"""
Database Models for Intelligent Attendance Register
Using PyMongo for MongoDB operations
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
import bcrypt


class BaseModel:
    """Base model with common functionality"""
    
    def __init__(self, db):
        self.db = db
    
    def to_dict(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to dictionary with ObjectId conversion"""
        if not obj:
            return obj
            
        # Create a copy to avoid modifying the original
        result = obj.copy()
        
        # Convert _id to string id
        if '_id' in result:
            result['id'] = str(result['_id'])
            del result['_id']
        
        # Convert any other ObjectId fields to strings
        for key, value in result.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, list):
                # Handle lists of ObjectIds
                result[key] = [str(item) if isinstance(item, ObjectId) else item for item in value]
            elif isinstance(value, dict):
                # Handle nested dictionaries
                result[key] = self.to_dict(value)
        
        return result
    
    def to_object_id(self, id_string: str):
        """Convert string to ObjectId if valid, otherwise return string as-is"""
        try:
            # Try to convert to ObjectId first
            return ObjectId(id_string)
        except Exception:
            # If conversion fails, return the string ID as-is for compatibility
            return id_string


class User(BaseModel):
    """User model for teachers, admins, and parents"""
    
    def __init__(self, db):
        super().__init__(db)
        self.collection = db.users
    
    def create(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        # Hash password using werkzeug (consistent with demo data)
        if 'password' in user_data:
            from werkzeug.security import generate_password_hash
            user_data['password'] = generate_password_hash(user_data['password'], method='pbkdf2:sha256')
        
        # Add timestamps
        user_data['created_at'] = datetime.utcnow()
        user_data['updated_at'] = datetime.utcnow()
        
        # Insert user
        result = self.collection.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        
        return self.to_dict(user_data)
    
    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email"""
        user = self.collection.find_one({'email': email})
        return self.to_dict(user) if user else None
    
    def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find user by ID"""
        user = self.collection.find_one({'_id': self.to_object_id(user_id)})
        return self.to_dict(user) if user else None
    
    def verify_password(self, email: str, password: str) -> bool:
        """Verify user password"""
        user = self.collection.find_one({'email': email})
        if not user:
            print(f"🔍 Password verification failed: User not found")
            return False
        
        # Use only the 'password' field (consistent with demo data)
        stored_hash = user.get('password')
        if not stored_hash:
            print(f"🔍 Password verification failed: No password field found")
            return False
        
        print(f"🔍 Stored hash type: {type(stored_hash)}")
        print(f"🔍 Stored hash length: {len(stored_hash) if stored_hash else 0}")
        
        try:
            # Use werkzeug's check_password_hash (consistent with demo data)
            from werkzeug.security import check_password_hash
            result = check_password_hash(stored_hash, password)
            print(f"🔍 Werkzeug verification result: {result}")
            return result
        except Exception as e:
            print(f"🔍 Password verification error: {e}")
            return False
    
    def update(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user"""
        update_data['updated_at'] = datetime.utcnow()
        
        result = self.collection.update_one(
            {'_id': self.to_object_id(user_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0


class Student(BaseModel):
    """Student model"""
    
    def __init__(self, db):
        super().__init__(db)
        self.collection = db.students
    
    def create(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new student"""
        student_data['created_at'] = datetime.utcnow()
        student_data['updated_at'] = datetime.utcnow()
        
        result = self.collection.insert_one(student_data)
        student_data['_id'] = result.inserted_id
        
        return self.to_dict(student_data)
    
    def find_all(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Find all students with optional filters"""
        query = filters or {}
        
        students = list(self.collection.find(query).sort('last_name', 1))
        return [self.to_dict(student) for student in students]
    
    def find_by_id(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Find student by ID"""
        student = self.collection.find_one({
            '_id': self.to_object_id(student_id)
        })
        return self.to_dict(student) if student else None
    
    def find_by_class(self, class_id: str) -> List[Dict[str, Any]]:
        """Find students by class"""
        try:
            print(f"🔍 Finding students for class: {class_id}")
            # First, get the class to find the student IDs
            class_object_id = self.to_object_id(class_id)
            class_doc = self.db.classes.find_one({'_id': class_object_id})
            
            print(f"   - Class document found: {class_doc is not None}")
            if class_doc:
                print(f"   - Class name: {class_doc.get('name', 'N/A')}")
                print(f"   - Students in class: {class_doc.get('students', [])}")
            
            if not class_doc or 'students' not in class_doc:
                print("   - No class or no students field")
                return []
            
            student_ids = class_doc.get('students', [])
            if not student_ids:
                print("   - No student IDs in class")
                return []
            
            print(f"   - Looking for {len(student_ids)} students")
            # Find students by their IDs
            students = list(self.collection.find({
                '_id': {'$in': student_ids}
            }).sort('last_name', 1))
            
            print(f"   - Found {len(students)} students")
            result = [self.to_dict(student) for student in students]
            print(f"   - Returning {len(result)} students after to_dict")
            return result
        except Exception as e:
            print(f"❌ Error in find_by_class: {e}")
            return []
    
    def update(self, student_id: str, update_data: Dict[str, Any]) -> bool:
        """Update student"""
        update_data['updated_at'] = datetime.utcnow()
        
        result = self.collection.update_one(
            {'_id': self.to_object_id(student_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0
    
    def delete(self, student_id: str) -> bool:
        """Delete student"""
        result = self.collection.delete_one(
            {'_id': self.to_object_id(student_id)}
        )
        return result.deleted_count > 0


class Class(BaseModel):
    """Class/Course model"""
    
    def __init__(self, db):
        super().__init__(db)
        self.collection = db.classes
    
    def create(self, class_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new class"""
        class_data['created_at'] = datetime.utcnow()
        class_data['updated_at'] = datetime.utcnow()
        
        result = self.collection.insert_one(class_data)
        class_data['_id'] = result.inserted_id
        
        return self.to_dict(class_data)
    
    def find_all(self) -> List[Dict[str, Any]]:
        """Find all classes"""
        classes = list(self.collection.find({}).sort('name', 1))
        return [self.to_dict(cls) for cls in classes]
    
    def find_by_id(self, class_id: str) -> Optional[Dict[str, Any]]:
        """Find class by ID"""
        cls = self.collection.find_one({
            '_id': self.to_object_id(class_id)
        })
        return self.to_dict(cls) if cls else None
    
    def find_by_teacher(self, teacher_id: str) -> List[Dict[str, Any]]:
        """Find classes by teacher"""
        # Convert teacher_id to ObjectId for the query
        try:
            teacher_object_id = self.to_object_id(teacher_id)
        except ValueError:
            # If conversion fails, return empty list
            return []
            
        classes = list(self.collection.find({
            'teacher_id': teacher_object_id
        }).sort('name', 1))
        return [self.to_dict(cls) for cls in classes]


class Attendance(BaseModel):
    """Attendance model"""
    
    def __init__(self, db):
        super().__init__(db)
        self.collection = db.attendance
    
    def mark_attendance(self, attendance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mark attendance for a student"""
        attendance_data['created_at'] = datetime.utcnow()
        attendance_data['updated_at'] = datetime.utcnow()
        
        # Check if attendance already exists for this student/class/date
        existing = self.collection.find_one({
            'student_id': attendance_data['student_id'],
            'class_id': attendance_data['class_id'],
            'date': attendance_data['date']
        })
        
        if existing:
            # Update existing record
            result = self.collection.update_one(
                {'_id': existing['_id']},
                {'$set': {
                    'status': attendance_data['status'],
                    'notes': attendance_data.get('notes', ''),
                    'marked_by': attendance_data['marked_by'],
                    'updated_at': datetime.utcnow()
                }}
            )
            existing.update(attendance_data)
            return self.to_dict(existing)
        else:
            # Create new record
            result = self.collection.insert_one(attendance_data)
            attendance_data['_id'] = result.inserted_id
            return self.to_dict(attendance_data)
    
    def find_by_date_and_class(self, date: str, class_id: str) -> List[Dict[str, Any]]:
        """Find attendance records by date and class"""
        records = list(self.collection.find({
            'date': date,
            'class_id': class_id
        }))
        return [self.to_dict(record) for record in records]
    
    def find_student_history(self, student_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Find student attendance history"""
        records = list(self.collection.find({
            'student_id': student_id
        }).sort('date', -1).limit(limit))
        return [self.to_dict(record) for record in records]
    
    def get_statistics(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get attendance statistics"""
        pipeline = []
        
        if filters:
            pipeline.append({'$match': filters})
        
        pipeline.extend([
            {
                '$group': {
                    '_id': '$status',
                    'count': {'$sum': 1}
                }
            }
        ])
        
        results = list(self.collection.aggregate(pipeline))
        stats = {result['_id']: result['count'] for result in results}
        
        total = sum(stats.values())
        if total > 0:
            for status in stats:
                stats[f'{status}_percentage'] = round((stats[status] / total) * 100, 2)
        
        stats['total'] = total
        return stats


class Alert(BaseModel):
    """Alert model for parent notifications"""
    
    def __init__(self, db):
        super().__init__(db)
        self.collection = db.alerts
    
    def create(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new alert"""
        alert_data['created_at'] = datetime.utcnow()
        alert_data['sent_at'] = None
        alert_data['status'] = 'pending'
        
        result = self.collection.insert_one(alert_data)
        alert_data['_id'] = result.inserted_id
        
        return self.to_dict(alert_data)
    
    def mark_sent(self, alert_id: str) -> bool:
        """Mark alert as sent"""
        result = self.collection.update_one(
            {'_id': self.to_object_id(alert_id)},
            {'$set': {
                'status': 'sent',
                'sent_at': datetime.utcnow()
            }}
        )
        return result.modified_count > 0
    
    def find_by_student(self, student_id: str) -> List[Dict[str, Any]]:
        """Find alerts by student"""
        alerts = list(self.collection.find({
            'student_id': student_id
        }).sort('created_at', -1))
        return [self.to_dict(alert) for alert in alerts]