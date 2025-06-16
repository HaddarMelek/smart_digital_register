"""
Validation utilities for the Attendance Register API
"""

import re
from typing import Any, Dict, List
from datetime import datetime


def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> bool:
    """Validate password strength"""
    if not password or len(password) < 8:
        return False
    
    # Must contain at least one letter and one number
    has_letter = re.search(r'[a-zA-Z]', password)
    has_number = re.search(r'\d', password)
    
    return has_letter and has_number


def validate_student_data(data: Dict[str, Any]) -> List[str]:
    """Validate student data"""
    errors = []
    
    # Required fields
    required_fields = ['first_name', 'last_name', 'student_id', 'grade', 'date_of_birth']
    for field in required_fields:
        if not data.get(field):
            errors.append(f'{field} is required')
    
    # Email validation (optional)
    if data.get('email') and not validate_email(data['email']):
        errors.append('Invalid email format')
    
    # Grade validation
    grade = data.get('grade')
    if grade and (not isinstance(grade, int) or grade < 9 or grade > 12):
        errors.append('Grade must be between 9 and 12')
    
    # Student ID validation
    student_id = data.get('student_id')
    if student_id and not re.match(r'^[A-Z0-9]{6,10}$', student_id.upper()):
        errors.append('Student ID must be 6-10 alphanumeric characters')
    
    return errors


def validate_class_data(data: Dict[str, Any]) -> List[str]:
    """Validate class data"""
    errors = []
    
    # Required fields
    required_fields = ['name', 'subject', 'teacher_id']
    for field in required_fields:
        if not data.get(field):
            errors.append(f'{field} is required')
    
    # Class code validation
    class_code = data.get('class_code')
    if class_code and not re.match(r'^[A-Z]{2,4}\d{3,4}$', class_code.upper()):
        errors.append('Class code must be 2-4 letters followed by 3-4 numbers (e.g., MATH101)')
    
    return errors


def validate_attendance_data(data: Dict[str, Any]) -> List[str]:
    """Validate attendance data"""
    errors = []
    
    # Required fields
    required_fields = ['student_id', 'class_id', 'date', 'status']
    for field in required_fields:
        if not data.get(field):
            errors.append(f'{field} is required')
    
    # Status validation
    status = data.get('status')
    valid_statuses = ['present', 'absent', 'late', 'excused']
    if status and status.lower() not in valid_statuses:
        errors.append(f'Status must be one of: {", ".join(valid_statuses)}')
    
    # Date validation
    date_str = data.get('date')
    if date_str:
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            errors.append('Date must be in YYYY-MM-DD format')
    
    return errors


def sanitize_input(data: Any) -> Any:
    """Sanitize input data to prevent injection attacks"""
    if isinstance(data, str):
        # Remove potentially dangerous characters
        data = re.sub(r'[<>"\';]', '', data)
        return data.strip()
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    else:
        return data


def validate_date_range(start_date: str, end_date: str) -> bool:
    """Validate date range"""
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        return start <= end
    except ValueError:
        return False


def validate_pagination_params(page: str, per_page: str) -> tuple:
    """Validate and convert pagination parameters"""
    try:
        page_num = max(1, int(page) if page else 1)
        per_page_num = min(100, max(1, int(per_page) if per_page else 20))
        return page_num, per_page_num
    except ValueError:
        return 1, 20


def validate_id_format(id_value: str, field_name: str = "ID") -> List[str]:
    """Validate ID format (ObjectId or UUID)"""
    errors = []
    
    if not id_value:
        errors.append(f"{field_name} is required")
        return errors
    
    if not isinstance(id_value, str):
        errors.append(f"{field_name} must be a string")
        return errors
    
    # Check for valid ObjectId format (24 hex characters) or UUID format
    if not (re.match(r'^[a-f0-9]{24}$', id_value, re.IGNORECASE) or 
            re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', id_value, re.IGNORECASE)):
        errors.append(f"{field_name} must be a valid ObjectId or UUID format")
    
    return errors


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate that all required fields are present and not empty"""
    errors = []
    
    for field in required_fields:
        if field not in data:
            errors.append(f"{field} is required")
        elif data[field] is None:
            errors.append(f"{field} cannot be null")
        elif isinstance(data[field], str) and not data[field].strip():
            errors.append(f"{field} cannot be empty")
    
    return errors


def validate_string_length(value: str, field_name: str, min_length: int = 0, max_length: int = 255) -> List[str]:
    """Validate string length"""
    errors = []
    
    if value and len(value) < min_length:
        errors.append(f"{field_name} must be at least {min_length} characters long")
    
    if value and len(value) > max_length:
        errors.append(f"{field_name} must be no more than {max_length} characters long")
    
    return errors