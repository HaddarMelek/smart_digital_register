"""
Authentication Routes for Intelligent Attendance Register
Handles user login, registration, token refresh, and logout
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    jwt_required, 
    get_jwt_identity,
    get_jwt
)
from datetime import datetime
import re

from app.models import User
from app.utils.validation import validate_email, validate_password
from app.utils.api_response import (
    success_response, error_response, validation_error_response,
    unauthorized_response, forbidden_response, server_error_response
)

auth_bp = Blueprint('auth', __name__)

# Blacklisted tokens (in production, use Redis or database)
blacklisted_tokens = set()

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return error_response("No data provided")
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not email or not password:
            return validation_error_response(["Email and password are required"])
        
        if not validate_email(email):
            return validation_error_response(["Invalid email format"])
        
        # Initialize user model
        user_model = User(current_app.db)
        
        # Get user details first
        user = user_model.find_by_email(email)
        print(f"🔍 Login attempt for {email}")
        print(f"🔍 User found: {user is not None}")
        
        if not user:
            print(f"❌ User not found for email: {email}")
            return unauthorized_response("Invalid email or password")
        
        print(f"🔍 User active: {user.get('is_active', True)}")
        if not user.get('is_active', True):
            return forbidden_response("Account is deactivated")
        
        # Verify credentials
        print(f"🔍 Attempting password verification...")
        password_valid = user_model.verify_password(email, password)
        print(f"🔍 Password valid: {password_valid}")
        
        if not password_valid:
            print(f"❌ Invalid password for email: {email}")
            return unauthorized_response("Invalid email or password")
        
        # Create tokens
        user_id = user.get('id', str(user.get('_id', '')))
        additional_claims = {
            'role': user.get('role', 'teacher'),
            'first_name': user.get('first_name', ''),
            'last_name': user.get('last_name', '')
        }
        
        print(f"🔍 Creating tokens for user ID: {user_id}")
        access_token = create_access_token(
            identity=user_id,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(identity=user_id)
        
        # Update last login
        user_model.update(user_id, {'last_login': datetime.utcnow()})
        
        print(f"✅ Login successful for {email}")
        return success_response(
            data={
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user_id,
                    'email': user['email'],
                    'first_name': user.get('first_name', ''),
                    'last_name': user.get('last_name', ''),
                    'role': user.get('role', 'teacher'),
                    'school_id': user.get('school_id', '')
                }
            },
            message="Login successful"
        )
        
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return server_error_response("Login failed")


@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint (admin only in production)"""
    try:
        data = request.get_json()
        
        if not data:
            return error_response("No data provided")
        
        # Extract and validate data
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        role = data.get('role', 'teacher').lower()
        
        # Validation
        if not all([email, password, first_name, last_name]):
            return validation_error_response(["All fields are required"])
        
        if not validate_email(email):
            return validation_error_response(["Invalid email format"])
        
        if not validate_password(password):
            return validation_error_response([
                "Password must be at least 8 characters with letters and numbers"
            ])
        
        if role not in ['teacher', 'admin', 'parent']:
            return validation_error_response(["Invalid role"])
        
        # Initialize user model
        user_model = User(current_app.db)
        
        # Check if user already exists
        existing_user = user_model.find_by_email(email)
        if existing_user:
            return error_response("User with this email already exists", 409)
        
        # Create user
        user_data = {
            'email': email,
            'password': password,  # Will be hashed in model
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
            'is_active': True,
            'school_id': 'alexander_academy'
        }
        
        created_user = user_model.create(user_data)
        
        return success_response(
            data={
                'user': {
                    'id': created_user['id'],
                    'email': created_user['email'],
                    'first_name': created_user['first_name'],
                    'last_name': created_user['last_name'],
                    'role': created_user['role']
                }
            },
            message='User registered successfully',
            status_code=201
        )
        
    except Exception as e:
        return server_error_response("Registration failed")
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user details for claims
        user_model = User(current_app.db)
        user = user_model.find_by_id(current_user_id)
        
        if not user or not user.get('is_active', True):
            return not_found_response("User not found or inactive")
        
        # Create new access token
        additional_claims = {
            'role': user.get('role', 'teacher'),
            'first_name': user.get('first_name', ''),
            'last_name': user.get('last_name', '')
        }
        
        access_token = create_access_token(
            identity=current_user_id,
            additional_claims=additional_claims
        )
        
        return success_response(
            data={'access_token': access_token},
            message='Token refreshed successfully'
        )
        
    except Exception as e:
        return server_error_response("Token refresh failed")


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout endpoint"""
    try:
        jti = get_jwt()['jti']
        blacklisted_tokens.add(jti)
        
        return success_response(
            data={},
            message='Successfully logged out'
        )
        
    except Exception as e:
        return server_error_response("Logout failed")


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        
        user_model = User(current_app.db)
        user = user_model.find_by_id(current_user_id)
        
        if not user:
            return not_found_response("User")
        
        return success_response(
            data={
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'first_name': user.get('first_name', ''),
                    'last_name': user.get('last_name', ''),
                    'role': user.get('role', 'teacher'),
                    'school_id': user.get('school_id', ''),
                    'created_at': user.get('created_at'),
                    'last_login': user.get('last_login')
                }
            },
            message="Profile retrieved successfully"
        )
        
    except Exception as e:
        return server_error_response("Failed to get profile")


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return error_response("No data provided")
        
        # Extract updatable fields
        update_data = {}
        if 'first_name' in data:
            update_data['first_name'] = data['first_name'].strip()
        if 'last_name' in data:
            update_data['last_name'] = data['last_name'].strip()
        
        # Validate email if provided
        if 'email' in data:
            email = data['email'].strip().lower()
            if not validate_email(email):
                return validation_error_response(["Invalid email format"])
            
            # Check if email is already taken
            user_model = User(current_app.db)
            existing = user_model.find_by_email(email)
            if existing and existing['id'] != current_user_id:
                return error_response("Email already taken", 409)
            
            update_data['email'] = email
        
        if not update_data:
            return validation_error_response(["No valid fields to update"])
        
        # Update user
        user_model = User(current_app.db)
        if user_model.update(current_user_id, update_data):
            updated_user = user_model.find_by_id(current_user_id)
            return success_response(
                data={
                    'user': {
                        'id': updated_user['id'],
                        'email': updated_user['email'],
                        'first_name': updated_user.get('first_name', ''),
                        'last_name': updated_user.get('last_name', ''),
                        'role': updated_user.get('role', 'teacher')
                    }
                },
                message='Profile updated successfully'
            )
        else:
            return server_error_response("Failed to update profile")
            
    except Exception as e:
        return server_error_response("Profile update failed")


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return error_response("No data provided")
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return validation_error_response(["Current and new passwords are required"])
        
        if not validate_password(new_password):
            return validation_error_response([
                "New password must be at least 8 characters with letters and numbers"
            ])
        
        user_model = User(current_app.db)
        user = user_model.find_by_id(current_user_id)
        
        if not user:
            return not_found_response("User")
        
        # Verify current password
        if not user_model.verify_password(user['email'], current_password):
            return validation_error_response(["Current password is incorrect"])
        
        # Hash and update new password using werkzeug (consistent with demo data)
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        
        if user_model.update(current_user_id, {'password': password_hash}):
            return success_response(
                data={},
                message='Password changed successfully'
            )
        else:
            return server_error_response("Failed to change password")
            
    except Exception as e:
        return server_error_response("Password change failed")

# JWT token check callback
@auth_bp.before_app_request
def check_if_token_revoked():
    """Check if token is blacklisted"""
    pass  # Implement token blacklist check if needed