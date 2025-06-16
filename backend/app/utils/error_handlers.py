"""
Error Handlers and Middleware for Flask Application
Provides consistent error handling across the application
"""

from flask import jsonify, request
from werkzeug.exceptions import HTTPException
import traceback
from app.utils.api_response import error_response, server_error_response


def register_error_handlers(app):
    """Register global error handlers for the Flask application"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors"""
        return error_response(
            message="Bad request",
            status_code=400,
            error_code="BAD_REQUEST"
        )
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors"""
        return error_response(
            message="Unauthorized access",
            status_code=401,
            error_code="UNAUTHORIZED"
        )
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors"""
        return error_response(
            message="Access forbidden",
            status_code=403,
            error_code="FORBIDDEN"
        )
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        return error_response(
            message="Resource not found",
            status_code=404,
            error_code="NOT_FOUND"
        )
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors"""
        return error_response(
            message="Method not allowed",
            status_code=405,
            error_code="METHOD_NOT_ALLOWED"
        )
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle 422 Unprocessable Entity errors"""
        return error_response(
            message="Unprocessable entity",
            status_code=422,
            error_code="UNPROCESSABLE_ENTITY"
        )
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error"""
        # Log the error for debugging
        app.logger.error(f"Internal Server Error: {error}")
        app.logger.error(traceback.format_exc())
        
        return server_error_response("An unexpected error occurred")
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle all other HTTP exceptions"""
        return error_response(
            message=error.description,
            status_code=error.code,
            error_code="HTTP_EXCEPTION"
        )
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle all unexpected exceptions"""
        # Log the error for debugging
        app.logger.error(f"Unexpected Error: {error}")
        app.logger.error(traceback.format_exc())
        
        return server_error_response("An unexpected error occurred")


def register_middleware(app):
    """Register middleware functions for the Flask application"""
    
    @app.before_request
    def log_request_info():
        """Log request information for debugging"""
        if app.config.get('DEBUG'):
            app.logger.info(f"Request: {request.method} {request.url}")
            if request.is_json:
                app.logger.info(f"JSON: {request.get_json()}")
    
    @app.after_request
    def after_request(response):
        """Add CORS headers and log response"""
        # Additional CORS headers if needed
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        
        if app.config.get('DEBUG'):
            app.logger.info(f"Response: {response.status_code}")
        
        return response


def validate_json_request():
    """Validate that request contains valid JSON"""
    if request.content_type == 'application/json':
        try:
            request.get_json(force=True)
        except Exception:
            return error_response(
                message="Invalid JSON format",
                status_code=400,
                error_code="INVALID_JSON"
            )
    return None


def require_json(f):
    """Decorator to require JSON content type"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return error_response(
                message="Content-Type must be application/json",
                status_code=400,
                error_code="MISSING_JSON"
            )
        return f(*args, **kwargs)
    return decorated_function