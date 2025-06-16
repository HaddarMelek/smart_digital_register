"""
Main Flask Application for Intelligent Attendance Register
Alexander Academy - Private High School, Vancouver
"""

import os
from datetime import timedelta
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routes
from app.routes import register_routes
from app.database import MongoDB
from app.utils.api_response import (
    success_response, error_response
)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-string')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-string')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # Disable strict slashes to prevent 308 redirects
    app.url_map.strict_slashes = False

    # Initialize extensions
    CORS(app, 
         origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization'],
         supports_credentials=True)
    jwt = JWTManager(app)
    
    # Initialize MongoDB database
    print("📊 Connecting to MongoDB...")
    mongodb = MongoDB()
    app.db = mongodb.db
    app.mongodb = mongodb
    
    # Check and seed data if database is empty
    mongodb.check_and_seed_data()
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return error_response('Token has expired', 401)
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return error_response('Invalid token', 401)
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return error_response('Authorization token is required', 401)
    
    # Register all route blueprints
    register_routes(app)
    
    # Home route
    @app.route('/')
    def home():
        return success_response(
            data={
                'status': 'running',
                'database': 'MongoDB',
                'endpoints': [
                    '/api/auth/login',
                    '/api/users',
                    '/api/seed',
                    '/api/students',
                    '/api/classes',
                    '/api/attendance',
                    '/api/predictions',
                    '/api/reports',
                    '/api/alerts'
                ]
            },
            message='Alexander Academy Attendance System API'
        )

    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        """Health check endpoint for monitoring"""
        return success_response(
            data={
                'status': 'healthy',
                'database': 'MongoDB',
                'version': '1.0.0'
            },
            message='Attendance API is running'
        )
    
    # Root endpoint
    @app.route('/api')
    def api_info():
        """API information endpoint"""
        return success_response(
            data={
                'name': 'Intelligent Attendance Register API',
                'version': '1.0.0',
                'school': 'Alexander Academy',
                'location': 'Vancouver, BC',
                'endpoints': {
                    'auth': '/api/auth/*',
                    'students': '/api/students/*',
                    'attendance': '/api/attendance/*',
                    'predictions': '/api/predictions/*',
                    'reports': '/api/reports/*',
                    'alerts': '/api/alerts/*',
                    'classes': '/api/classes/*'
                },
                'documentation': '/api/docs'
            },
            message='API information'
        )
    
    # API documentation endpoint
    @app.route('/api/docs')
    def api_docs():
        """API documentation"""
        return success_response(
            data={
                'title': 'Intelligent Attendance Register API Documentation',
                'version': '1.0.0',
                'description': 'RESTful API for managing attendance at Alexander Academy',
                'endpoints': {
                    'Authentication': {
                        'POST /api/auth/login': 'User login',
                        'POST /api/auth/register': 'User registration',
                        'POST /api/auth/refresh': 'Refresh JWT token',
                        'POST /api/auth/logout': 'User logout'
                    },
                    'Database': {
                        'POST /api/seed': 'Seed database with demo data'
                    },
                    'Students': {
                        'GET /api/students': 'List all students',
                        'POST /api/students': 'Create new student',
                        'GET /api/students/{id}': 'Get student by ID',
                        'PUT /api/students/{id}': 'Update student',
                        'DELETE /api/students/{id}': 'Delete student'
                    },
                    'Attendance': {
                        'GET /api/attendance': 'Get attendance records',
                        'POST /api/attendance/mark': 'Mark attendance',
                        'PUT /api/attendance/{id}': 'Update attendance',
                        'GET /api/attendance/student/{student_id}': 'Get student attendance history'
                    },
                    'Predictions': {
                        'POST /api/predictions/absence': 'Predict absence probability',
                        'GET /api/predictions/patterns/unusual': 'Detect unusual patterns'
                    },
                    'Reports': {
                        'GET /api/reports/daily': 'Daily attendance report',
                        'GET /api/reports/weekly': 'Weekly attendance report',
                        'GET /api/reports/monthly': 'Monthly attendance report'
                    },
                    'Alerts': {
                        'POST /api/alerts/send': 'Send parent notification',
                        'GET /api/alerts/history': 'Get alert history'
                    },
                    'Classes': {
                        'GET /api/classes': 'List all classes',
                        'POST /api/classes': 'Create new class',
                        'GET /api/classes/{id}': 'Get class details',
                        'PUT /api/classes/{id}': 'Update class'
                    }
                }
            },
            message='API Documentation'
        )
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print("🚀 Starting Alexander Academy Attendance System")
    print(f"🌐 Backend running on http://localhost:{port}")
    print(f"📚 API Documentation: http://localhost:{port}/api/docs")
    print(f"🌱 Seed endpoint: POST http://localhost:{port}/api/seed")

    
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=True, threaded=True)