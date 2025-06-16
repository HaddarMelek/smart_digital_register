"""
Class Management Routes for Intelligent Attendance Register
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime

from app.models import Class, Student, User
from app.utils.validation import validate_class_data, sanitize_input
from app.utils.api_response import (
    success_response, error_response, validation_error_response,
    not_found_response, forbidden_response, server_error_response
)

classes_bp = Blueprint('classes', __name__)


@classes_bp.route('', methods=['GET'])
@jwt_required()
def get_classes():
    """Get all classes"""
    try:
        claims = get_jwt()
        user_role = claims.get('role')
        current_user_id = get_jwt_identity()
        
        class_model = Class(current_app.db)
        
        # Teachers can only see their own classes
        if user_role == 'teacher':
            classes = class_model.find_by_teacher(current_user_id)
        else:
            # Admins can see all classes
            classes = class_model.find_all()
        
        return success_response(
            data=classes,
            message="Classes retrieved successfully"
        )
        
    except Exception as e:
        print(f"❌ Error getting classes: {str(e)}")
        return server_error_response("Failed to get classes")


@classes_bp.route('/<class_id>', methods=['GET'])
@jwt_required()
def get_class(class_id):
    """Get a specific class by ID"""
    try:
        class_model = Class(current_app.db)
        cls = class_model.find_by_id(class_id)
        
        if not cls:
            return not_found_response("Class")
        
        # Check permissions
        claims = get_jwt()
        user_role = claims.get('role')
        current_user_id = get_jwt_identity()
        
        if user_role == 'teacher' and cls.get('teacher_id') != current_user_id:
            return forbidden_response("Access denied")
        
        # Get students in this class
        student_model = Student(current_app.db)
        students = student_model.find_by_class(class_id)
        
        cls['students'] = students
        cls['student_count'] = len(students)
        
        return success_response(
            data=cls,
            message="Class retrieved successfully"
        )
        
    except Exception as e:
        print(f"❌ Error getting class {class_id}: {str(e)}")
        return server_error_response("Failed to get class")


@classes_bp.route('', methods=['POST'])
@jwt_required()
def create_class():
    """Create a new class (admin only)"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return forbidden_response("Admin access required")
        
        data = request.get_json()
        if not data:
            return error_response("No data provided")
        
        # Sanitize input
        data = sanitize_input(data)
        
        # Validate data
        errors = validate_class_data(data)
        if errors:
            return validation_error_response(errors)
        
        # Check if teacher exists
        user_model = User(current_app.db)
        teacher = user_model.find_by_id(data['teacher_id'])
        if not teacher or teacher.get('role') != 'teacher':
            return validation_error_response(["Invalid teacher ID"])
        
        # Prepare class data
        class_data = {
            'name': data['name'],
            'subject': data['subject'],
            'class_code': data.get('class_code', '').upper(),
            'teacher_id': data['teacher_id'],
            'teacher_name': f"{teacher['first_name']} {teacher['last_name']}",
            'grade': data.get('grade', 10),
            'room': data.get('room', ''),
            'schedule': data.get('schedule', {}),  # e.g., {"monday": "09:00-10:00", "wednesday": "14:00-15:00"}
            'description': data.get('description', ''),
            'max_students': data.get('max_students', 30),
            'school_year': data.get('school_year', '2024-2025')
        }
        
        # Create class
        class_model = Class(current_app.db)
        created_class = class_model.create(class_data)
        
        return success_response(
            data=created_class,
            message="Class created successfully",
            status_code=201
        )
        
    except Exception as e:
        print(f"❌ Error creating class: {str(e)}")
        return server_error_response("Failed to create class")


@classes_bp.route('/<class_id>', methods=['PUT'])
@jwt_required()
def update_class(class_id):
    """Update a class (admin only)"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return forbidden_response("Admin access required")
        
        data = request.get_json()
        if not data:
            return error_response("No data provided")
        
        # Sanitize input
        data = sanitize_input(data)
        
        # Check if class exists
        class_model = Class(current_app.db)
        existing_class = class_model.find_by_id(class_id)
        if not existing_class:
            return not_found_response("Class")
        
        # Prepare update data
        update_data = {}
        
        updatable_fields = [
            'name', 'subject', 'class_code', 'grade', 'room', 
            'schedule', 'description', 'max_students', 'school_year'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'class_code':
                    update_data[field] = data[field].upper()
                elif field == 'grade':
                    try:
                        update_data[field] = int(data[field])
                    except ValueError:
                        return validation_error_response(["Invalid grade value"])
                elif field == 'max_students':
                    try:
                        update_data[field] = int(data[field])
                    except ValueError:
                        return validation_error_response(["Invalid max_students value"])
                else:
                    update_data[field] = data[field]
        
        # Handle teacher change
        if 'teacher_id' in data:
            user_model = User(current_app.db)
            teacher = user_model.find_by_id(data['teacher_id'])
            if not teacher or teacher.get('role') != 'teacher':
                return validation_error_response(["Invalid teacher ID"])
            
            update_data['teacher_id'] = data['teacher_id']
            update_data['teacher_name'] = f"{teacher['first_name']} {teacher['last_name']}"
        
        if not update_data:
            return validation_error_response(["No valid fields to update"])
        
        # Update class
        result = class_model.collection.update_one(
            {'_id': class_model.to_object_id(class_id)},
            {'$set': {**update_data, 'updated_at': datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            updated_class = class_model.find_by_id(class_id)
            return success_response(
                data={'class': updated_class},
                message='Class updated successfully'
            )
        else:
            return success_response(
                data={},
                message='No changes made to class'
            )
            
    except Exception as e:
        return server_error_response("Failed to update class")


@classes_bp.route('/<class_id>/students', methods=['GET'])
@jwt_required()
def get_class_students(class_id):
    """Get all students in a specific class"""
    try:
        class_model = Class(current_app.db)
        student_model = Student(current_app.db)
        
        # Check if class exists
        cls = class_model.find_by_id(class_id)
        if not cls:
            return not_found_response("Class")
        
        # Check permissions - teachers can only see their own classes
        claims = get_jwt()
        user_role = claims.get('role')
        current_user_id = get_jwt_identity()
        
        print(f"🔍 Class students permission check:")
        print(f"   - User role: {user_role}")
        print(f"   - Current user ID: {current_user_id}")
        print(f"   - Class teacher ID: {cls.get('teacher_id', '')}")
        print(f"   - Comparison: {str(cls.get('teacher_id', ''))} == {str(current_user_id)}")
        
        if user_role == 'teacher' and str(cls.get('teacher_id', '')) != str(current_user_id):
            print(f"❌ Access denied for teacher {current_user_id} to class {class_id}")
            return forbidden_response("Access denied")
        
        # Get students in this class
        students = student_model.find_by_class(class_id)
        
        return success_response(
            data={
                'class': cls,
                'students': students,
                'student_count': len(students)
            },
            message="Class students retrieved successfully"
        )
        
    except Exception as e:
        return server_error_response("Failed to get class students")


@classes_bp.route('/<class_id>/students', methods=['POST'])
@jwt_required()
def add_student_to_class(class_id):
    """Add a student to a class (admin/teacher)"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') not in ['admin', 'teacher']:
            return forbidden_response("Insufficient permissions")
        
        data = request.get_json()
        if not data or 'student_id' not in data:
            return validation_error_response(["student_id is required"])
        
        student_id = data['student_id']
        
        # Check if class exists
        class_model = Class(current_app.db)
        cls = class_model.find_by_id(class_id)
        if not cls:
            return not_found_response("Class")
        
        # Check permissions for teachers
        current_user_id = get_jwt_identity()
        if claims.get('role') == 'teacher' and cls.get('teacher_id') != current_user_id:
            return forbidden_response("Access denied")
        
        # Check if student exists
        student_model = Student(current_app.db)
        student = student_model.find_by_id(student_id)
        if not student:
            return not_found_response("Student")
        
        # Check class capacity
        current_students = student_model.find_by_class(class_id)
        max_students = cls.get('max_students', 30)
        
        if len(current_students) >= max_students:
            return validation_error_response(["Class is at maximum capacity"])
        
        # Check if student is already in the class
        if student.get('class_id') == class_id:
            return error_response("Student is already in this class", 409)
        
        # Add student to class
        if student_model.update(student_id, {'class_id': class_id}):
            return success_response(
                data={
                    'student': student,
                    'class': cls
                },
                message='Student added to class successfully'
            )
        else:
            return server_error_response("Failed to add student to class")
            
    except Exception as e:
        return server_error_response("Failed to add student to class")


@classes_bp.route('/<class_id>/students/<student_id>', methods=['DELETE'])
@jwt_required()
def remove_student_from_class(class_id, student_id):
    """Remove a student from a class (admin/teacher)"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') not in ['admin', 'teacher']:
            return forbidden_response("Insufficient permissions")
        
        # Check if class exists
        class_model = Class(current_app.db)
        cls = class_model.find_by_id(class_id)
        if not cls:
            return not_found_response("Class")
        
        # Check permissions for teachers
        current_user_id = get_jwt_identity()
        if claims.get('role') == 'teacher' and cls.get('teacher_id') != current_user_id:
            return forbidden_response("Access denied")
        
        # Check if student exists and is in the class
        student_model = Student(current_app.db)
        student = student_model.find_by_id(student_id)
        if not student:
            return not_found_response("Student")
        
        if student.get('class_id') != class_id:
            return validation_error_response(["Student is not in this class"])
        
        # Remove student from class
        if student_model.update(student_id, {'class_id': ''}):
            return success_response(
                data={},
                message='Student removed from class successfully'
            )
        else:
            return server_error_response("Failed to remove student from class")
            
    except Exception as e:
        return server_error_response("Failed to remove student from class")


@classes_bp.route('/<class_id>/schedule', methods=['GET'])
@jwt_required()
def get_class_schedule(class_id):
    """Get class schedule"""
    try:
        class_model = Class(current_app.db)
        cls = class_model.find_by_id(class_id)
        
        if not cls:
            return not_found_response("Class")
        
        # Check permissions
        claims = get_jwt()
        user_role = claims.get('role')
        current_user_id = get_jwt_identity()
        
        if user_role == 'teacher' and cls.get('teacher_id') != current_user_id:
            return forbidden_response("Access denied")
        
        schedule = cls.get('schedule', {})
        
        return success_response(
            data={
                'class_id': class_id,
                'class_name': cls.get('name'),
                'schedule': schedule
            },
            message="Class schedule retrieved successfully"
        )
        
    except Exception as e:
        return server_error_response("Failed to get class schedule")


@classes_bp.route('/teacher/<teacher_id>', methods=['GET'])
@jwt_required()
def get_teacher_classes(teacher_id):
    """Get all classes for a specific teacher"""
    try:
        # Check permissions
        claims = get_jwt()
        current_user_id = get_jwt_identity()
        
        # Teachers can only see their own classes, admins can see any teacher's classes
        if claims.get('role') == 'teacher' and current_user_id != teacher_id:
            return forbidden_response("Access denied")
        
        class_model = Class(current_app.db)
        classes = class_model.find_by_teacher(teacher_id)
        
        # Add student count for each class
        student_model = Student(current_app.db)
        for cls in classes:
            students = student_model.find_by_class(cls['id'])
            cls['student_count'] = len(students)
        
        return success_response(
            data={
                'teacher_id': teacher_id,
                'classes': classes,
                'total_classes': len(classes)
            },
            message="Teacher classes retrieved successfully"
        )
        
    except Exception as e:
        return server_error_response("Failed to get teacher classes")