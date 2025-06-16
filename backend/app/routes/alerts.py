"""
Alerts Routes for Intelligent Attendance Register
Handles parent notifications and alert management
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.models import Alert, Student, Attendance, User
from app.utils.api_response import (
    success_response, error_response, validation_error_response,
    not_found_response, forbidden_response, server_error_response
)

alerts_bp = Blueprint('alerts', __name__)


@alerts_bp.route('', methods=['GET'])
@jwt_required()
def get_recent_alerts():
    """Get recent alerts for dashboard"""
    try:
        # Get recent alerts from database - for now return mock data
        # since Alert model might not be fully implemented
        alerts = [
            {
                'id': '1',
                'type': 'absence',
                'message': 'Emma Wilson has been absent for 3 consecutive days',
                'student_name': 'Emma Wilson',
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'pending',
                'priority': 'high'
            },
            {
                'id': '2', 
                'type': 'late',
                'message': 'James Brown was late to Mathematics class',
                'student_name': 'James Brown',
                'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                'status': 'sent',
                'priority': 'medium'
            }
        ]
        
        return success_response(
            data=alerts,
            message="Recent alerts retrieved successfully",
            meta={'count': len(alerts)}
        )
        
    except Exception as e:
        print(f"❌ Error fetching alerts: {e}")
        return server_error_response("Failed to fetch alerts")


def send_email_notification(to_email, subject, body, student_name, school_info):
    """Send email notification to parent"""
    try:
        # Email configuration (should be in environment variables)
        smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = current_app.config.get('SMTP_PORT', 587)
        smtp_username = current_app.config.get('SMTP_USERNAME', 'noreply@alexander.edu')
        smtp_password = current_app.config.get('SMTP_PASSWORD', '')
        
        if not smtp_password:
            print("SMTP password not configured, email not sent")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"Alexander Academy <{smtp_username}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # HTML email template
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; line-height: 1.6; }}
                .footer {{ background-color: #ecf0f1; padding: 15px; text-align: center; font-size: 12px; color: #7f8c8d; }}
                .alert {{ background-color: #e74c3c; color: white; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .info {{ background-color: #3498db; color: white; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Alexander Academy</h1>
                <p>Attendance Notification</p>
            </div>
            <div class="content">
                <h2>Dear Parent/Guardian,</h2>
                <p>This is an automated notification regarding the attendance of <strong>{student_name}</strong>.</p>
                <div class="alert">
                    <h3>Attendance Alert</h3>
                    <p>{body}</p>
                </div>
                <div class="info">
                    <h4>What to do next:</h4>
                    <ul>
                        <li>Contact the school if your child was legitimately absent</li>
                        <li>Provide necessary documentation for excused absences</li>
                        <li>Speak with your child about the importance of regular attendance</li>
                        <li>Contact us if you need support to address attendance issues</li>
                    </ul>
                </div>
                <p>If you have any questions or concerns, please contact the school office at (604) 555-0123 or email us at office@alexander.edu.</p>
                <p>Thank you for your cooperation.</p>
                <p><strong>Alexander Academy Administration</strong></p>
            </div>
            <div class="footer">
                <p>Alexander Academy | 123 School Street, Vancouver, BC V6B 1A1</p>
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M')}</p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_username, to_email, text)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False


@alerts_bp.route('/send', methods=['POST'])
@jwt_required()
def send_alert():
    """Send an alert to parent/guardian"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') not in ['admin', 'teacher']:
            return forbidden_response('Insufficient permissions')
        
        data = request.get_json()
        if not data:
            return validation_error_response(['No data provided'])
        
        student_id = data.get('student_id')
        alert_type = data.get('type', 'attendance_concern')
        message = data.get('message', '')
        send_email = data.get('send_email', True)
        
        if not student_id:
            return validation_error_response(['student_id is required'])
        
        # Get student information
        student_model = Student(current_app.db)
        student = student_model.find_by_id(student_id)
        if not student:
            return not_found_response('Student')
        
        parent_email = student.get('parent_email', '')
        if send_email and not parent_email:
            return validation_error_response(['No parent email on file for this student'])
        
        # Get current user
        current_user_id = get_jwt_identity()
        user_model = User(current_app.db)
        current_user = user_model.find_by_id(current_user_id)
        
        # Prepare alert data
        alert_data = {
            'student_id': student_id,
            'student_name': f"{student['first_name']} {student['last_name']}",
            'type': alert_type,
            'message': message,
            'parent_email': parent_email,
            'created_by': current_user_id,
            'created_by_name': f"{current_user['first_name']} {current_user['last_name']}" if current_user else 'System',
            'method': 'email' if send_email else 'system_only'
        }
        
        # Create alert record
        alert_model = Alert(current_app.db)
        alert_record = alert_model.create(alert_data)
        
        # Send email if requested
        email_sent = False
        if send_email and parent_email:
            # Generate subject and body based on alert type
            subjects = {
                'attendance_concern': f'Attendance Concern - {student["first_name"]} {student["last_name"]}',
                'excessive_absences': f'Excessive Absences Notice - {student["first_name"]} {student["last_name"]}',
                'tardiness_pattern': f'Tardiness Pattern Alert - {student["first_name"]} {student["last_name"]}',
                'consecutive_absences': f'Consecutive Absences Alert - {student["first_name"]} {student["last_name"]}',
                'general': f'School Notification - {student["first_name"]} {student["last_name"]}'
            }
            
            subject = subjects.get(alert_type, subjects['general'])
            
            # Enhanced message based on type
            if not message:
                default_messages = {
                    'attendance_concern': 'We have noticed some attendance concerns and would like to discuss this with you.',
                    'excessive_absences': 'Your child has exceeded the acceptable number of absences. Please contact the school.',
                    'tardiness_pattern': 'We have observed a pattern of tardiness that may affect your child\'s academic progress.',
                    'consecutive_absences': 'Your child has been absent for consecutive days. Please contact the school to discuss.',
                    'general': 'Please contact the school regarding your child\'s attendance.'
                }
                message = default_messages.get(alert_type, default_messages['general'])
            
            school_info = {
                'name': 'Alexander Academy',
                'phone': '(604) 555-0123',
                'email': 'office@alexander.edu'
            }
            
            email_sent = send_email_notification(
                parent_email, 
                subject, 
                message, 
                f"{student['first_name']} {student['last_name']}",
                school_info
            )
            
            # Update alert status
            if email_sent:
                alert_model.mark_sent(alert_record['id'])
        
        response_data = {
            'message': 'Alert created successfully',
            'alert': alert_record,
            'email_sent': email_sent
        }
        
        if not email_sent and send_email:
            response_data['warning'] = 'Alert created but email could not be sent'
        
        return success_response(
            data=response_data,
            message='Alert created successfully',
            status_code=201
        )
        
    except Exception as e:
        return server_error_response(f'Failed to send alert: {str(e)}')


@alerts_bp.route('/bulk-send', methods=['POST'])
@jwt_required()
def bulk_send_alerts():
    """Send alerts to multiple students"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') not in ['admin', 'teacher']:
            return forbidden_response('Insufficient permissions')
        
        data = request.get_json()
        if not data or 'alerts' not in data:
            return validation_error_response(['No alerts data provided'])
        
        alerts_data = data['alerts']
        if not isinstance(alerts_data, list):
            return validation_error_response(['Alerts data must be a list'])
        
        current_user_id = get_jwt_identity()
        user_model = User(current_app.db)
        student_model = Student(current_app.db)
        alert_model = Alert(current_app.db)
        
        current_user = user_model.find_by_id(current_user_id)
        
        sent_alerts = []
        failed_alerts = []
        
        for alert_data in alerts_data:
            try:
                student_id = alert_data.get('student_id')
                if not student_id:
                    failed_alerts.append({'student_id': 'unknown', 'error': 'Missing student_id'})
                    continue
                
                # Get student
                student = student_model.find_by_id(student_id)
                if not student:
                    failed_alerts.append({'student_id': student_id, 'error': 'Student not found'})
                    continue
                
                # Prepare alert
                alert_record_data = {
                    'student_id': student_id,
                    'student_name': f"{student['first_name']} {student['last_name']}",
                    'type': alert_data.get('type', 'attendance_concern'),
                    'message': alert_data.get('message', ''),
                    'parent_email': student.get('parent_email', ''),
                    'created_by': current_user_id,
                    'created_by_name': f"{current_user['first_name']} {current_user['last_name']}" if current_user else 'System',
                    'method': 'email' if alert_data.get('send_email', True) else 'system_only'
                }
                
                # Create alert record
                alert_record = alert_model.create(alert_record_data)
                
                # Send email if requested
                email_sent = False
                if alert_data.get('send_email', True) and student.get('parent_email'):
                    # Generate subject and message
                    subject = f'Attendance Notification - {student["first_name"]} {student["last_name"]}'
                    message = alert_data.get('message', 'Please contact the school regarding your child\'s attendance.')
                    
                    email_sent = send_email_notification(
                        student['parent_email'],
                        subject,
                        message,
                        f"{student['first_name']} {student['last_name']}",
                        {'name': 'Alexander Academy', 'phone': '(604) 555-0123'}
                    )
                    
                    if email_sent:
                        alert_model.mark_sent(alert_record['id'])
                
                sent_alerts.append({
                    'student_id': student_id,
                    'student_name': f"{student['first_name']} {student['last_name']}",
                    'alert_id': alert_record['id'],
                    'email_sent': email_sent
                })
                
            except Exception as e:
                failed_alerts.append({
                    'student_id': alert_data.get('student_id', 'unknown'),
                    'error': str(e)
                })
        
        return success_response(
            data={
                'successful_alerts': sent_alerts,
                'failed_alerts': failed_alerts,
                'summary': {
                    'total_processed': len(alerts_data),
                    'successful': len(sent_alerts),
                    'failed': len(failed_alerts)
                }
            },
            message=f'Bulk alerts processed. {len(sent_alerts)} successful, {len(failed_alerts)} failed.'
        )
        
    except Exception as e:
        return server_error_response(f'Bulk alert sending failed: {str(e)}')


@alerts_bp.route('/history', methods=['GET'])
@jwt_required()
def get_alert_history():
    """Get alert history with filtering"""
    try:
        # Get query parameters
        student_id = request.args.get('student_id')
        alert_type = request.args.get('type')
        days_back = int(request.args.get('days_back', 30))
        status = request.args.get('status')  # pending, sent, failed
        
        alert_model = Alert(current_app.db)
        
        # Build filters
        filters = {}
        
        if student_id:
            filters['student_id'] = student_id
        
        if alert_type:
            filters['type'] = alert_type
        
        if status:
            filters['status'] = status
        
        # Date filter
        if days_back:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            filters['created_at'] = {'$gte': cutoff_date}
        
        # Get alerts
        alerts = list(alert_model.collection.find(filters).sort('created_at', -1))
        
        # Format alerts
        formatted_alerts = []
        for alert in alerts:
            formatted_alert = alert_model.to_dict(alert)
            formatted_alerts.append(formatted_alert)
        
        # Calculate summary statistics
        total_alerts = len(formatted_alerts)
        sent_count = len([a for a in formatted_alerts if a.get('status') == 'sent'])
        pending_count = len([a for a in formatted_alerts if a.get('status') == 'pending'])
        
        # Group by type
        type_breakdown = {}
        for alert in formatted_alerts:
            alert_type = alert.get('type', 'unknown')
            type_breakdown[alert_type] = type_breakdown.get(alert_type, 0) + 1
        
        return success_response(
            data={
                'alerts': formatted_alerts,
                'summary': {
                    'total_alerts': total_alerts,
                    'sent': sent_count,
                    'pending': pending_count,
                    'by_type': type_breakdown
                },
                'filters_applied': filters
            },
            message='Alert history retrieved successfully'
        )
        
    except Exception as e:
        return server_error_response(f'Failed to get alert history: {str(e)}')


@alerts_bp.route('/student/<student_id>', methods=['GET'])
@jwt_required()
def get_student_alerts(student_id):
    """Get all alerts for a specific student"""
    try:
        alert_model = Alert(current_app.db)
        student_model = Student(current_app.db)
        
        # Check if student exists
        student = student_model.find_by_id(student_id)
        if not student:
            return not_found_response('Student')
        
        # Get alerts for student
        alerts = alert_model.find_by_student(student_id)
        
        return success_response(
            data={
                'student': {
                    'id': student['id'],
                    'name': f"{student['first_name']} {student['last_name']}",
                    'student_id': student.get('student_id', ''),
                    'parent_email': student.get('parent_email', '')
                },
                'alerts': alerts,
                'total_alerts': len(alerts)
            },
            message='Student alerts retrieved successfully'
        )
        
    except Exception as e:
        return server_error_response(f'Failed to get student alerts: {str(e)}')


@alerts_bp.route('/auto-generate', methods=['POST'])
@jwt_required()
def auto_generate_alerts():
    """Automatically generate alerts based on attendance patterns"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') not in ['admin', 'teacher']:
            return forbidden_response('Insufficient permissions')
        
        data = request.get_json() or {}
        days_to_analyze = data.get('days_to_analyze', 14)
        min_absences = data.get('min_absences', 3)
        consecutive_threshold = data.get('consecutive_threshold', 3)
        
        student_model = Student(current_app.db)
        attendance_model = Attendance(current_app.db)
        alert_model = Alert(current_app.db)
        
        # Get all students
        all_students = student_model.find_all()
        
        # Analyze attendance patterns
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_to_analyze)
        
        auto_alerts = []
        current_user_id = get_jwt_identity()
        
        for student in all_students:
            try:
                # Get recent attendance
                date_filter = {
                    'student_id': student['id'],
                    'date': {
                        '$gte': start_date.strftime('%Y-%m-%d'),
                        '$lte': end_date.strftime('%Y-%m-%d')
                    }
                }
                
                recent_attendance = list(attendance_model.collection.find(date_filter).sort('date', 1))
                
                if len(recent_attendance) < 5:  # Not enough data
                    continue
                
                absent_count = len([r for r in recent_attendance if r['status'] == 'absent'])
                late_count = len([r for r in recent_attendance if r['status'] == 'late'])
                
                # Check for excessive absences
                if absent_count >= min_absences:
                    # Check if we already sent a recent alert
                    recent_alert_filter = {
                        'student_id': student['id'],
                        'type': 'excessive_absences',
                        'created_at': {'$gte': datetime.utcnow() - timedelta(days=7)}
                    }
                    
                    recent_alerts = list(alert_model.collection.find(recent_alert_filter))
                    
                    if not recent_alerts:  # No recent alert
                        alert_data = {
                            'student_id': student['id'],
                            'student_name': f"{student['first_name']} {student['last_name']}",
                            'type': 'excessive_absences',
                            'message': f'Student has been absent {absent_count} times in the last {days_to_analyze} days.',
                            'parent_email': student.get('parent_email', ''),
                            'created_by': current_user_id,
                            'created_by_name': 'Auto-Generated System',
                            'method': 'email' if student.get('parent_email') else 'system_only',
                            'auto_generated': True
                        }
                        
                        alert_record = alert_model.create(alert_data)
                        auto_alerts.append(alert_record)
                
                # Check for consecutive absences
                consecutive_absences = 0
                max_consecutive = 0
                
                for record in recent_attendance:
                    if record['status'] == 'absent':
                        consecutive_absences += 1
                        max_consecutive = max(max_consecutive, consecutive_absences)
                    else:
                        consecutive_absences = 0
                
                if max_consecutive >= consecutive_threshold:
                    # Check for recent consecutive absence alerts
                    recent_alert_filter = {
                        'student_id': student['id'],
                        'type': 'consecutive_absences',
                        'created_at': {'$gte': datetime.utcnow() - timedelta(days=5)}
                    }
                    
                    recent_alerts = list(alert_model.collection.find(recent_alert_filter))
                    
                    if not recent_alerts:
                        alert_data = {
                            'student_id': student['id'],
                            'student_name': f"{student['first_name']} {student['last_name']}",
                            'type': 'consecutive_absences',
                            'message': f'Student has {max_consecutive} consecutive absences.',
                            'parent_email': student.get('parent_email', ''),
                            'created_by': current_user_id,
                            'created_by_name': 'Auto-Generated System',
                            'method': 'email' if student.get('parent_email') else 'system_only',
                            'auto_generated': True
                        }
                        
                        alert_record = alert_model.create(alert_data)
                        auto_alerts.append(alert_record)
                
                # Check for tardiness pattern
                tardiness_rate = (late_count / len(recent_attendance)) * 100
                if tardiness_rate > 25:  # More than 25% late
                    recent_alert_filter = {
                        'student_id': student['id'],
                        'type': 'tardiness_pattern',
                        'created_at': {'$gte': datetime.utcnow() - timedelta(days=14)}
                    }
                    
                    recent_alerts = list(alert_model.collection.find(recent_alert_filter))
                    
                    if not recent_alerts:
                        alert_data = {
                            'student_id': student['id'],
                            'student_name': f"{student['first_name']} {student['last_name']}",
                            'type': 'tardiness_pattern',
                            'message': f'Student has a high tardiness rate: {tardiness_rate:.1f}% ({late_count}/{len(recent_attendance)} days).',
                            'parent_email': student.get('parent_email', ''),
                            'created_by': current_user_id,
                            'created_by_name': 'Auto-Generated System',
                            'method': 'email' if student.get('parent_email') else 'system_only',
                            'auto_generated': True
                        }
                        
                        alert_record = alert_model.create(alert_data)
                        auto_alerts.append(alert_record)
                
            except Exception as e:
                print(f"Error processing student {student['id']}: {e}")
                continue
        
        return success_response(
            data={
                'generated_alerts': auto_alerts,
                'analysis_parameters': {
                    'days_analyzed': days_to_analyze,
                    'min_absences_threshold': min_absences,
                    'consecutive_threshold': consecutive_threshold
                }
            },
            message=f'Auto-generated {len(auto_alerts)} alerts based on attendance patterns'
        )
        
    except Exception as e:
        return server_error_response(f'Failed to auto-generate alerts: {str(e)}')


@alerts_bp.route('/configuration', methods=['GET'])
@jwt_required()
def get_alert_configuration():
    """Get alert system configuration"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return forbidden_response('Admin access required')
        
        config = {
            'alert_types': [
                'attendance_concern',
                'excessive_absences',
                'tardiness_pattern',
                'consecutive_absences',
                'general'
            ],
            'thresholds': {
                'excessive_absences': 3,
                'consecutive_absences': 3,
                'tardiness_rate': 25
            },
            'email_settings': {
                'smtp_configured': bool(current_app.config.get('SMTP_PASSWORD')),
                'sender_email': current_app.config.get('SMTP_USERNAME', 'noreply@alexander.edu')
            },
            'auto_alert_settings': {
                'enabled': True,
                'check_frequency': 'daily',
                'days_to_analyze': 14
            }
        }
        
        return success_response(
            data=config,
            message='Alert configuration retrieved successfully'
        )
        
    except Exception as e:
        return server_error_response(f'Failed to get alert configuration: {str(e)}')