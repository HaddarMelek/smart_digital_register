"""
Attendance Management Routes for Intelligent Attendance Register
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, date, timedelta

from app.models import Attendance, Student, Class
from app.utils.validation import validate_attendance_data, sanitize_input, validate_date_range
from app.utils.api_response import (
    success_response, error_response, validation_error_response,
    not_found_response, forbidden_response, server_error_response
)

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/mark', methods=['POST'])
@jwt_required()
def mark_attendance():
    """Mark attendance for a student"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') not in ['admin', 'teacher']:
            return forbidden_response("Insufficient permissions to mark attendance")
        
        data = request.get_json()
        if not data:
            return error_response("No data provided")
        
        # Sanitize input
        data = sanitize_input(data)
        
        # Validate data
        errors = validate_attendance_data(data)
        if errors:
            return validation_error_response(errors)
        
        # Get current user
        current_user_id = get_jwt_identity()
        
        # Prepare attendance data
        attendance_data = {
            'student_id': data['student_id'],
            'class_id': data['class_id'],
            'date': data['date'],
            'status': data['status'].lower(),
            'notes': data.get('notes', ''),
            'marked_by': current_user_id,
            'marked_at': datetime.utcnow()
        }
        
        # Mark attendance
        attendance_model = Attendance(current_app.db)
        attendance_record = attendance_model.mark_attendance(attendance_data)
        
        return success_response(
            data=attendance_record,
            message="Attendance marked successfully",
            status_code=201
        )
        
    except Exception as e:
        print(f"❌ Error marking attendance: {str(e)}")
        return server_error_response("Failed to mark attendance")


@attendance_bp.route('/bulk-mark', methods=['POST'])
@jwt_required()
def bulk_mark_attendance():
    """Mark attendance for multiple students"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') not in ['admin', 'teacher']:
            return forbidden_response("Insufficient permissions")
        
        data = request.get_json()
        if not data or 'attendance_records' not in data:
            return error_response("No attendance records provided")
        
        attendance_records = data['attendance_records']
        if not isinstance(attendance_records, list):
            return error_response("Attendance records must be a list")
        
        current_user_id = get_jwt_identity()
        attendance_model = Attendance(current_app.db)
        
        marked_records = []
        errors = []
        
        for i, record_data in enumerate(attendance_records):
            try:
                # Sanitize and validate
                record_data = sanitize_input(record_data)
                validation_errors = validate_attendance_data(record_data)
                
                if validation_errors:
                    errors.append({
                        'index': i,
                        'student_id': record_data.get('student_id', ''),
                        'errors': validation_errors
                    })
                    continue
                
                # Prepare data
                attendance_data = {
                    'student_id': record_data['student_id'],
                    'class_id': record_data['class_id'],
                    'date': record_data['date'],
                    'status': record_data['status'].lower(),
                    'notes': record_data.get('notes', ''),
                    'marked_by': current_user_id,
                    'marked_at': datetime.utcnow()
                }
                
                # Mark attendance
                attendance_record = attendance_model.mark_attendance(attendance_data)
                marked_records.append(attendance_record)
                
            except Exception as e:
                errors.append({
                    'index': i,
                    'student_id': record_data.get('student_id', ''),
                    'errors': [str(e)]
                })
        
        response_data = {
            'marked_records': marked_records,
            'errors': errors,
            'summary': {
                'total_processed': len(attendance_records),
                'successful': len(marked_records),
                'failed': len(errors)
            }
        }
        
        if not errors:
            return success_response(
                data=response_data,
                message=f'Bulk attendance marking completed. {len(marked_records)} records processed.'
            )
        else:
            return success_response(
                data=response_data,
                message=f'Bulk attendance marking completed. {len(marked_records)} records processed.',
                status_code=207
            )
        
    except Exception as e:
        return server_error_response("Bulk attendance marking failed")


@attendance_bp.route('', methods=['POST'])
@jwt_required()
def mark_class_attendance():
    """Mark attendance for a class (handles bulk attendance from frontend)"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') not in ['admin', 'teacher']:
            return forbidden_response("Insufficient permissions to mark attendance")
        
        data = request.get_json()
        if not data:
            return error_response("No data provided")
        
        # Validate required fields
        class_id = data.get('class_id')
        date_str = data.get('date')
        attendance_records = data.get('attendance', [])
        
        if not class_id:
            return error_response("class_id is required")
        
        if not date_str:
            return error_response("date is required")
        
        if not isinstance(attendance_records, list) or len(attendance_records) == 0:
            return error_response("attendance records are required")
        
        current_user_id = get_jwt_identity()
        attendance_model = Attendance(current_app.db)
        
        marked_records = []
        errors = []
        
        for i, record_data in enumerate(attendance_records):
            try:
                student_id = record_data.get('student_id')
                status = record_data.get('status')
                notes = record_data.get('notes', '')
                
                if not student_id:
                    errors.append({
                        'index': i,
                        'error': 'student_id is required'
                    })
                    continue
                
                if not status:
                    errors.append({
                        'index': i,
                        'student_id': student_id,
                        'error': 'status is required'
                    })
                    continue
                
                # Prepare attendance data
                attendance_data = {
                    'student_id': student_id,
                    'class_id': class_id,
                    'date': date_str,
                    'status': status.lower(),
                    'notes': notes,
                    'marked_by': current_user_id,
                    'marked_at': datetime.utcnow()
                }
                
                # Mark attendance
                attendance_record = attendance_model.mark_attendance(attendance_data)
                marked_records.append(attendance_record)
                
            except Exception as e:
                errors.append({
                    'index': i,
                    'student_id': record_data.get('student_id', ''),
                    'error': str(e)
                })
        
        response_data = {
            'marked_records': marked_records,
            'errors': errors,
            'summary': {
                'total_processed': len(attendance_records),
                'successful': len(marked_records),
                'failed': len(errors)
            }
        }
        
        if not errors:
            return success_response(
                data=response_data,
                message=f'Class attendance marked successfully. {len(marked_records)} records processed.',
                status_code=201
            )
        else:
            return success_response(
                data=response_data,
                message=f'Class attendance marking completed with some errors. {len(marked_records)} successful, {len(errors)} failed.',
                status_code=207
            )
        
    except Exception as e:
        print(f"❌ Error marking class attendance: {str(e)}")
        return server_error_response("Failed to mark class attendance")


@attendance_bp.route('', methods=['GET'])
@jwt_required()
def get_attendance_records():
    """Get attendance records with filtering"""
    try:
        # Get query parameters
        class_id = request.args.get('class_id')
        student_id = request.args.get('student_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        status = request.args.get('status')
        
        # Build filters
        filters = {}
        
        if class_id:
            filters['class_id'] = class_id
        
        if student_id:
            filters['student_id'] = student_id
        
        if status:
            filters['status'] = status.lower()
        
        # Date range filter
        date_filter = {}
        if date_from:
            date_filter['$gte'] = date_from
        if date_to:
            date_filter['$lte'] = date_to
        
        if date_filter:
            filters['date'] = date_filter
        
        # Get attendance records
        attendance_model = Attendance(current_app.db)
        
        # Use aggregation to include student and class details
        pipeline = []
        
        if filters:
            pipeline.append({'$match': filters})
        
        # Add student details
        pipeline.extend([
            {
                '$lookup': {
                    'from': 'students',
                    'localField': 'student_id',
                    'foreignField': '_id',
                    'as': 'student'
                }
            },
            {
                '$unwind': '$student'
            },
            # Add class details
            {
                '$lookup': {
                    'from': 'classes',
                    'localField': 'class_id',
                    'foreignField': '_id',
                    'as': 'class'
                }
            },
            {
                '$unwind': '$class'
            },
            # Sort by date and class
            {
                '$sort': {'date': -1, 'class.name': 1}
            }
        ])
        
        records = list(attendance_model.collection.aggregate(pipeline))
        
        # Format records
        formatted_records = []
        for record in records:
            formatted_record = attendance_model.to_dict(record)
            formatted_record['student'] = attendance_model.to_dict(record['student'])
            formatted_record['class'] = attendance_model.to_dict(record['class'])
            formatted_records.append(formatted_record)
        
        return success_response(
            data={
                'attendance_records': formatted_records,
                'total': len(formatted_records)
            }
        )
        
    except Exception as e:
        return server_error_response("Failed to get attendance records")


@attendance_bp.route('/class/<class_id>/date/<date_str>', methods=['GET'])
@jwt_required()
def get_class_attendance_by_date(class_id, date_str):
    """Get attendance for a specific class on a specific date"""
    try:
        # Validate date format
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return validation_error_response({"date": ["Invalid date format. Use YYYY-MM-DD"]})
        
        attendance_model = Attendance(current_app.db)
        student_model = Student(current_app.db)
        
        # Get attendance records for the class and date
        attendance_records = attendance_model.find_by_date_and_class(date_str, class_id)
        
        # Get all students in the class
        all_students = student_model.find_by_class(class_id)
        
        # Create a map of student attendance
        attendance_map = {record['student_id']: record for record in attendance_records}
        
        # Build complete attendance list
        class_attendance = []
        for student in all_students:
            student_attendance = attendance_map.get(student['id'])
            
            class_attendance.append({
                'student': student,
                'attendance': student_attendance,
                'status': student_attendance['status'] if student_attendance else 'absent'
            })
        
        # Sort by student name
        class_attendance.sort(key=lambda x: (x['student']['last_name'], x['student']['first_name']))
        
        return success_response(
            data={
                'class_id': class_id,
                'date': date_str,
                'attendance': class_attendance,
                'summary': {
                    'total_students': len(all_students),
                    'marked': len(attendance_records),
                    'not_marked': len(all_students) - len(attendance_records)
                }
            }
        )
        
    except Exception as e:
        return server_error_response("Failed to get class attendance")


@attendance_bp.route('/student/<student_id>/history', methods=['GET'])
@jwt_required()
def get_student_attendance_history(student_id):
    """Get attendance history for a specific student"""
    try:
        print(f"🔍 Getting attendance history for student: {student_id}")
        # Get query parameters
        limit = int(request.args.get('limit', 30))
        class_id = request.args.get('class_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        print(f"🔍 Query params: limit={limit}, class_id={class_id}, start_date={start_date}, end_date={end_date}")
        
        attendance_model = Attendance(current_app.db)
        
        # Build filters (convert student_id to ObjectId)
        try:
            student_object_id = attendance_model.to_object_id(student_id)
            print(f"🔍 Student ObjectId: {student_object_id}")
        except Exception as e:
            print(f"❌ Error converting student_id to ObjectId: {e}")
            return error_response(f"Invalid student_id format: {student_id}")
            
        filters = {'student_id': student_object_id}
        
        if class_id:
            try:
                class_object_id = attendance_model.to_object_id(class_id)
                filters['class_id'] = class_object_id
                print(f"🔍 Class ObjectId: {class_object_id}")
            except Exception as e:
                print(f"❌ Error converting class_id to ObjectId: {e}")
                return error_response(f"Invalid class_id format: {class_id}")
        
        # Add date range filter
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter['$gte'] = start_date
            if end_date:
                date_filter['$lte'] = end_date
            filters['date'] = date_filter
            
        print(f"🔍 Final filters: {filters}")
        
        # Get attendance history (simplified approach)
        try:
            # First, try to find any records for this student
            all_records = list(attendance_model.collection.find(filters).sort('date', -1).limit(limit))
            print(f"🔍 Found {len(all_records)} raw records")
            
            # Format records without lookup for now (simpler)
            formatted_records = []
            for record in all_records:
                formatted_record = attendance_model.to_dict(record)
                # Add a placeholder class name
                formatted_record['class_name'] = 'Class'
                formatted_records.append(formatted_record)
                
            print(f"🔍 Formatted {len(formatted_records)} records")
            
            # Simple statistics
            stats = {
                'total': len(formatted_records),
                'present': len([r for r in formatted_records if r.get('status') == 'present']),
                'absent': len([r for r in formatted_records if r.get('status') == 'absent']),
                'late': len([r for r in formatted_records if r.get('status') == 'late'])
            }
            
        except Exception as e:
            print(f"❌ Error in attendance query: {e}")
            formatted_records = []
            stats = {'total': 0, 'present': 0, 'absent': 0, 'late': 0}
        
        print(f"🔍 Found {len(formatted_records)} attendance records")
        print(f"🔍 Statistics: {stats}")
        
        return success_response(
            data={
                'student_id': student_id,
                'attendance_history': formatted_records,
                'statistics': stats
            }
        )
        
    except Exception as e:
        print(f"❌ Error in get_student_attendance_history: {e}")
        import traceback
        traceback.print_exc()
        return server_error_response("Failed to get student attendance history")


@attendance_bp.route('/<attendance_id>', methods=['PUT'])
@jwt_required()
def update_attendance(attendance_id):
    """Update an attendance record"""
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
        
        attendance_model = Attendance(current_app.db)
        
        # Check if record exists
        existing_record = attendance_model.collection.find_one({
            '_id': attendance_model.to_object_id(attendance_id)
        })
        
        if not existing_record:
            return not_found_response("Attendance record not found")
        
        # Prepare update data
        update_data = {}
        current_user_id = get_jwt_identity()
        
        if 'status' in data:
            valid_statuses = ['present', 'absent', 'late', 'excused']
            if data['status'].lower() in valid_statuses:
                update_data['status'] = data['status'].lower()
            else:
                return validation_error_response({"status": ["Invalid status"]})
        
        if 'notes' in data:
            update_data['notes'] = data['notes']
        
        update_data['updated_by'] = current_user_id
        update_data['updated_at'] = datetime.utcnow()
        
        # Update record
        result = attendance_model.collection.update_one(
            {'_id': attendance_model.to_object_id(attendance_id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            # Get updated record
            updated_record = attendance_model.collection.find_one({
                '_id': attendance_model.to_object_id(attendance_id)
            })
            
            return success_response(
                data={'attendance': attendance_model.to_dict(updated_record)},
                message='Attendance record updated successfully'
            )
        else:
            return success_response(
                data={},
                message='No changes made to attendance record'
            )
            
    except Exception as e:
        return server_error_response("Failed to update attendance")


@attendance_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_attendance_statistics():
    """Get attendance statistics with optional filtering"""
    try:
        # Get query parameters
        class_id = request.args.get('class_id')
        student_id = request.args.get('student_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build filters
        filters = {}
        
        if class_id:
            filters['class_id'] = class_id
        
        if student_id:
            filters['student_id'] = student_id
        
        # Date range filter
        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter['$gte'] = date_from
            if date_to:
                date_filter['$lte'] = date_to
            filters['date'] = date_filter
        
        # Get statistics
        attendance_model = Attendance(current_app.db)
        stats = attendance_model.get_statistics(filters)
        
        # Calculate additional metrics
        if stats['total'] > 0:
            attendance_rate = stats.get('present', 0) / stats['total'] * 100
            stats['attendance_rate'] = round(attendance_rate, 2)
            
            absence_rate = stats.get('absent', 0) / stats['total'] * 100
            stats['absence_rate'] = round(absence_rate, 2)
            
            tardiness_rate = stats.get('late', 0) / stats['total'] * 100
            stats['tardiness_rate'] = round(tardiness_rate, 2)
        
        return success_response(
            data={
                'statistics': stats,
                'filters': filters
            }
        )
        
    except Exception as e:
        return server_error_response("Failed to get attendance statistics")