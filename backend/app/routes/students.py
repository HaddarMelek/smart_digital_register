"""
Student Management Routes for Intelligent Attendance Register
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime

from app.models import Student
from app.utils.validation import validate_student_data, sanitize_input, validate_pagination_params
from app.utils.api_response import (
    success_response, error_response, validation_error_response,
    not_found_response, forbidden_response, server_error_response,
    paginated_response
)

students_bp = Blueprint('students', __name__)


@students_bp.route('', methods=['GET'])
@jwt_required()
def get_students():
    """Get all students with optional filtering and pagination"""
    try:
        # Get query parameters
        page = request.args.get('page', '1')
        per_page = request.args.get('per_page', '20')
        grade = request.args.get('grade')
        class_id = request.args.get('class_id')
        search = request.args.get('search', '').strip()
        
        # Validate pagination
        page_num, per_page_num = validate_pagination_params(page, per_page)
        
        # Build filters
        filters = {}
        if grade:
            try:
                filters['grade'] = int(grade)
            except ValueError:
                return validation_error_response(["Invalid grade parameter"])
        
        if class_id:
            filters['class_id'] = class_id
        
        # Add search filter
        if search:
            search_regex = {'$regex': search, '$options': 'i'}
            filters['$or'] = [
                {'first_name': search_regex},
                {'last_name': search_regex},
                {'student_id': search_regex}
            ]
        
        # Get students
        student_model = Student(current_app.db)
        students = student_model.find_all(filters)
        
        # Apply pagination
        total = len(students)
        start_idx = (page_num - 1) * per_page_num
        end_idx = start_idx + per_page_num
        paginated_students = students[start_idx:end_idx]
        
        return paginated_response(
            data=paginated_students,
            page=page_num,
            per_page=per_page_num,
            total=total,
            message="Students retrieved successfully"
        )
        
    except Exception as e:
        print(f"❌ Error getting students: {str(e)}")
        return server_error_response("Failed to get students")


@students_bp.route('/<student_id>', methods=['GET'])
@jwt_required()
def get_student(student_id):
    """Get a specific student by ID"""
    try:
        student_model = Student(current_app.db)
        student = student_model.find_by_id(student_id)
        
        if not student:
            return not_found_response("Student")
        
        return success_response(
            data=student,
            message="Student retrieved successfully"
        )
        
    except Exception as e:
        print(f"❌ Error getting student {student_id}: {str(e)}")
        return server_error_response("Failed to get student")


@students_bp.route('', methods=['POST'])
@jwt_required()
def create_student():
    """Create a new student (admin/teacher only)"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') not in ['admin', 'teacher']:
            return forbidden_response("Insufficient permissions to create students")
        
        data = request.get_json()
        if not data:
            return error_response("No data provided")
        
        # Sanitize input
        data = sanitize_input(data)
        
        # Validate data
        errors = validate_student_data(data)
        if errors:
            return validation_error_response(errors)
        
        # Check for duplicate student ID
        student_model = Student(current_app.db)
        existing_students = student_model.find_all({'student_id': data['student_id'].upper()})
        if existing_students:
            return error_response("Student ID already exists", 409)
        
        # Prepare student data
        student_data = {
            'first_name': data['first_name'].title(),
            'last_name': data['last_name'].title(),
            'student_id': data['student_id'].upper(),
            'grade': int(data['grade']),
            'date_of_birth': data['date_of_birth'],
            'email': data.get('email', '').lower() if data.get('email') else '',
            'phone': data.get('phone', ''),
            'address': data.get('address', ''),
            'parent_email': data.get('parent_email', '').lower() if data.get('parent_email') else '',
            'parent_phone': data.get('parent_phone', ''),
            'emergency_contact': data.get('emergency_contact', ''),
            'medical_info': data.get('medical_info', ''),
            'notes': data.get('notes', ''),
            'class_id': data.get('class_id', '')
        }
        
        # Create student
        created_student = student_model.create(student_data)
        
        return success_response(
            data={'student': created_student},
            message='Student created successfully',
            status_code=201
        )
        
    except Exception as e:
        return server_error_response("Failed to create student")


@students_bp.route('/<student_id>', methods=['PUT'])
@jwt_required()
def update_student(student_id):
    """Update a student (admin/teacher only)"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') not in ['admin', 'teacher']:
            return forbidden_response("Insufficient permissions")
        
        data = request.get_json()
        if not data:
            return error_response("No data provided")
        
        # Sanitize input
        data = sanitize_input(data)
        
        # Check if student exists
        student_model = Student(current_app.db)
        existing_student = student_model.find_by_id(student_id)
        if not existing_student:
            return not_found_response("Student")
        
        # Prepare update data
        update_data = {}
        
        # Updatable fields
        updatable_fields = [
            'first_name', 'last_name', 'grade', 'email', 'phone', 'address',
            'parent_email', 'parent_phone', 'emergency_contact', 'medical_info',
            'notes', 'class_id'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field in ['first_name', 'last_name']:
                    update_data[field] = data[field].title()
                elif field in ['email', 'parent_email']:
                    update_data[field] = data[field].lower() if data[field] else ''
                elif field == 'grade':
                    try:
                        update_data[field] = int(data[field])
                        if update_data[field] < 9 or update_data[field] > 12:
                            return validation_error_response(["Grade must be between 9 and 12"])
                    except ValueError:
                        return validation_error_response(["Invalid grade value"])
                else:
                    update_data[field] = data[field]
        
        # Check for duplicate student ID if being changed
        if 'student_id' in data and data['student_id'].upper() != existing_student['student_id']:
            existing_with_id = student_model.find_all({'student_id': data['student_id'].upper()})
            if existing_with_id:
                return error_response("Student ID already exists", 409)
            update_data['student_id'] = data['student_id'].upper()
        
        if not update_data:
            return validation_error_response(["No valid fields to update"])
        
        # Update student
        if student_model.update(student_id, update_data):
            updated_student = student_model.find_by_id(student_id)
            return success_response(
                data={'student': updated_student},
                message='Student updated successfully'
            )
        else:
            return server_error_response("Failed to update student")
            
    except Exception as e:
        return server_error_response("Failed to update student")


@students_bp.route('/<student_id>', methods=['DELETE'])
@jwt_required()
def delete_student(student_id):
    """Delete (deactivate) a student (admin only)"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return forbidden_response("Admin access required")
        
        student_model = Student(current_app.db)
        
        # Check if student exists
        existing_student = student_model.find_by_id(student_id)
        if not existing_student:
            return not_found_response("Student")
        
        # Soft delete (deactivate)
        if student_model.delete(student_id):
            return success_response(
                data={},
                message='Student deactivated successfully'
            )
        else:
            return server_error_response("Failed to deactivate student")
            
    except Exception as e:
        return server_error_response("Failed to delete student")


@students_bp.route('/class/<class_id>', methods=['GET'])
@jwt_required()
def get_students_by_class(class_id):
    """Get all students in a specific class"""
    try:
        student_model = Student(current_app.db)
        students = student_model.find_by_class(class_id)
        
        return success_response(
            data={'students': students},
            message="Students retrieved successfully"
        )
        
    except Exception as e:
        return server_error_response("Failed to get students by class")


@students_bp.route('/bulk', methods=['POST'])
@jwt_required()
def bulk_import_students():
    """Bulk import students from CSV data (admin only)"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return forbidden_response("Admin access required")
        
        data = request.get_json()
        if not data or 'students' not in data:
            return validation_error_response(["No student data provided"])
        
        students_data = data['students']
        if not isinstance(students_data, list):
            return validation_error_response(["Students data must be a list"])
        
        student_model = Student(current_app.db)
        created_students = []
        errors = []
        
        for i, student_data in enumerate(students_data):
            try:
                # Sanitize and validate
                student_data = sanitize_input(student_data)
                validation_errors = validate_student_data(student_data)
                
                if validation_errors:
                    errors.append({
                        'row': i + 1,
                        'errors': validation_errors
                    })
                    continue
                
                # Check for duplicate student ID
                existing = student_model.find_all({'student_id': student_data['student_id'].upper()})
                if existing:
                    errors.append({
                        'row': i + 1,
                        'errors': [f"Student ID {student_data['student_id']} already exists"]
                    })
                    continue
                
                # Prepare data
                formatted_data = {
                    'first_name': student_data['first_name'].title(),
                    'last_name': student_data['last_name'].title(),
                    'student_id': student_data['student_id'].upper(),
                    'grade': int(student_data['grade']),
                    'date_of_birth': student_data['date_of_birth'],
                    'email': student_data.get('email', '').lower() if student_data.get('email') else '',
                    'parent_email': student_data.get('parent_email', '').lower() if student_data.get('parent_email') else '',
                    'class_id': student_data.get('class_id', '')
                }
                
                # Create student
                created_student = student_model.create(formatted_data)
                created_students.append(created_student)
                
            except Exception as e:
                errors.append({
                    'row': i + 1,
                    'errors': [str(e)]
                })
        
        status_code = 200 if not errors else 207  # 207 = Multi-Status
        return success_response(
            data={
                'created_students': created_students,
                'errors': errors,
                'summary': {
                    'total_processed': len(students_data),
                    'successful': len(created_students),
                    'failed': len(errors)
                }
            },
            message=f'Bulk import completed. {len(created_students)} students created.',
            status_code=status_code
        )
        
    except Exception as e:
        return server_error_response("Bulk import failed")