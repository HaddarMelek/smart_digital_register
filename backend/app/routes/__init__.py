"""
Routes package initialization
Registers all route blueprints
"""

from .auth import auth_bp
from .users import users_bp
from .students import students_bp
from .classes import classes_bp
from .attendance import attendance_bp
from .predictions import predictions_bp
from .reports import reports_bp
from .alerts import alerts_bp
from .seed import seed_bp

def register_routes(app):
    """Register all route blueprints with the Flask app"""
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(students_bp, url_prefix='/api/students')
    app.register_blueprint(classes_bp, url_prefix='/api/classes')
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    app.register_blueprint(predictions_bp, url_prefix='/api/predictions')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(seed_bp, url_prefix='/api/seed')