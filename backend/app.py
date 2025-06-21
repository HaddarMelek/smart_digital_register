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
    
    # API information endpoint
    @app.route('/api')
    def api_info():
        """API information and documentation"""
        return success_response(
            data={
                'name': 'Alexander Academy Attendance API',
                'version': '1.0.0',
                'status': 'running',
                'endpoints': [
                    'POST /api/auth/login',
                    'GET /api/students',
                    'POST /api/attendance/mark',
                    'GET /api/reports/daily',
                    'POST /api/predictions/absence',
                    'GET /api/alerts/history'
                ],
                'health': '/api/health',
                'seed_data': 'POST /api/seed'
            },
            message='Alexander Academy Attendance System API'
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