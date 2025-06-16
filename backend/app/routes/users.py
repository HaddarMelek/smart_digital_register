"""
Users Routes for Intelligent Attendance Register
Handles user management endpoints
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import User
from app.utils.api_response import (
    success_response, error_response, forbidden_response, server_error_response
)

users_bp = Blueprint('users', __name__)

@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    """Get users by role (admin only)"""
    try:
        # Get current user's role from JWT
        current_user = get_jwt_identity()
        if isinstance(current_user, dict):
            current_role = current_user.get('role')
        else:
            # If identity is just a string, we need to look up the user
            user_model = User(current_app.db)
            user_data = user_model.find_by_id(current_user)
            current_role = user_data.get('role') if user_data else None
        
        # Only admins can access this endpoint
        if current_role != 'admin':
            return forbidden_response("Access denied")
        
        # Get query parameters
        role_filter = request.args.get('role')
        
        # Build query
        query = {}
        if role_filter:
            query['role'] = role_filter
        
        # Get users
        users = list(current_app.db.users.find(query, {
            'password': 0  # Exclude password hash from response
        }))
        
        # Convert ObjectId to string for JSON serialization
        for user in users:
            if '_id' in user:
                user['id'] = str(user['_id'])
                del user['_id']
        
        return success_response(
            data={
                'users': users,
                'count': len(users)
            },
            message='Users retrieved successfully'
        )
        
    except Exception as e:
        print(f"Error fetching users: {e}")
        return server_error_response("Failed to fetch users")

@users_bp.route('/<user_id>', methods=['GET'])
@jwt_required()
def get_user_by_id(user_id):
    """Get a specific user by ID (admin only)"""
    try:
        # Get current user's role from JWT
        current_user = get_jwt_identity()
        if isinstance(current_user, dict):
            current_role = current_user.get('role')
        else:
            # If identity is just a string, we need to look up the user
            user_model = User(current_app.db)
            user_data = user_model.find_by_id(current_user)
            current_role = user_data.get('role') if user_data else None
        
        # Only admins can access this endpoint
        if current_role != 'admin':
            return forbidden_response("Access denied")
        
        # Get user by ID
        user_model = User(current_app.db)
        user = user_model.find_by_id(user_id)
        
        if not user:
            return error_response("User not found", 404)
        
        # Remove password hash (ObjectId already converted by model)
        if 'password' in user:
            del user['password']
        
        return success_response(
            data={'user': user},
            message='User retrieved successfully'
        )
        
    except Exception as e:
        print(f"Error fetching user: {e}")
        return server_error_response("Failed to fetch user")

@users_bp.route('/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update a user (admin only)"""
    try:
        # Get current user's role from JWT
        current_user = get_jwt_identity()
        if isinstance(current_user, dict):
            current_role = current_user.get('role')
        else:
            # If identity is just a string, we need to look up the user
            user_model = User(current_app.db)
            user_data = user_model.find_by_id(current_user)
            current_role = user_data.get('role') if user_data else None
        
        # Only admins can access this endpoint
        if current_role != 'admin':
            return forbidden_response("Access denied")
        
        data = request.get_json()
        if not data:
            return error_response("No data provided")
        
        # Get user by ID
        user_model = User(current_app.db)
        user = user_model.find_by_id(user_id)
        
        if not user:
            return error_response("User not found", 404)
        
        # Update user
        update_data = {}
        allowed_fields = ['first_name', 'last_name', 'email', 'role', 'phone', 'status']
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if update_data:
            current_app.db.users.update_one(
                {'_id': user['_id']},
                {'$set': update_data}
            )
        
        return success_response(
            message='User updated successfully'
        )
        
    except Exception as e:
        print(f"Error updating user: {e}")
        return server_error_response("Failed to update user")

@users_bp.route('/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete a user (admin only)"""
    try:
        # Get current user's role from JWT
        current_user = get_jwt_identity()
        if isinstance(current_user, dict):
            current_role = current_user.get('role')
        else:
            # If identity is just a string, we need to look up the user
            user_model = User(current_app.db)
            user_data = user_model.find_by_id(current_user)
            current_role = user_data.get('role') if user_data else None
        
        # Only admins can access this endpoint
        if current_role != 'admin':
            return forbidden_response("Access denied")
        
        # Get user by ID
        user_model = User(current_app.db)
        user = user_model.find_by_id(user_id)
        
        if not user:
            return error_response("User not found", 404)
        
        # Delete user
        current_app.db.users.delete_one({'_id': user['_id']})
        
        return success_response(
            message='User deleted successfully'
        )
        
    except Exception as e:
        print(f"Error deleting user: {e}")
        return server_error_response("Failed to delete user")