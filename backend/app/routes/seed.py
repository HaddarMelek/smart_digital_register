"""
Database Seeding Routes for Intelligent Attendance Register
Handles initialization of demo data for development and testing
"""

from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt

from app.utils.demo_data import initialize_demo_data
from app.utils.api_response import (
    success_response, error_response, forbidden_response, server_error_response
)

seed_bp = Blueprint('seed', __name__)


@seed_bp.route('', methods=['POST'])
def seed_database():
    """Seed the database with demo data"""
    try:
        # Check if data already exists
        user_count = current_app.db.users.count_documents({})
        
        if user_count > 0:
            return success_response(
                data={
                    'users_existing': user_count,
                    'message': 'Database already contains data - seeding skipped'
                },
                message="Data already exists in database"
            )
        
        # Initialize demo data
        result = initialize_demo_data(current_app.db)
        
        return success_response(
            data=result,
            message="Database seeded successfully with demo data"
        )
        
    except Exception as e:
        print(f"❌ Error seeding database: {str(e)}")
        return server_error_response("Failed to seed database")


@seed_bp.route('/reset', methods=['POST'])
@jwt_required()
def reset_database():
    """Reset database (admin only)"""
    try:
        claims = get_jwt()
        user_role = claims.get('role')
        
        if user_role != 'admin':
            return forbidden_response('Admin access required')
        
        # Clear all data and reinitialize (MongoDB collections)
        current_app.db.users.delete_many({})
        current_app.db.students.delete_many({})
        current_app.db.classes.delete_many({})
        current_app.db.attendance.delete_many({})
        
        result = initialize_demo_data(current_app.db)
        
        return success_response(
            data=result,
            message="Database reset and reseeded successfully"
        )
        
    except Exception as e:
        print(f"❌ Error resetting database: {str(e)}")
        return server_error_response("Failed to reset database")