"""
Prediction routes for ML-based absence predictions
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
import os

from app.utils.simple_ml import predict_absence_risk, detect_unusual_patterns

try:
    import joblib
    import numpy as np
    import pandas as pd
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    # Create dummy modules for unavailable packages
    class DummyModule:
        pass
    joblib = DummyModule()
    np = DummyModule() 
    pd = DummyModule()
    
from app.utils.simple_ml import SimplePredictor, train_simple_model

from app.models import Attendance, Student
from app.utils.api_response import (
    success_response, error_response, validation_error_response,
    not_found_response, forbidden_response, server_error_response
)

predictions_bp = Blueprint('predictions', __name__)

# Cache for loaded ML models
_models_cache = {}


def load_ml_model(model_name='absence_predictor.pkl'):
    """Load ML model with caching"""
    if model_name in _models_cache:
        return _models_cache[model_name]
    
    try:
        model_path = os.path.join(
            current_app.config.get('ML_MODEL_PATH', '/app/models'),
            model_name
        )
        
        if not os.path.exists(model_path):
            return None
        
        model = joblib.load(model_path)
        _models_cache[model_name] = model
        return model
    
    except Exception as e:
        print(f"Error loading model {model_name}: {e}")
        return None


def prepare_prediction_features(student_id, date_str=None):
    """Prepare features for absence prediction"""
    try:
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Get student information
        student_model = Student(current_app.db)
        student = student_model.find_by_id(student_id)
        
        if not student:
            return None
        
        # Get attendance history (last 30 days)
        attendance_model = Attendance(current_app.db)
        end_date = target_date - timedelta(days=1)
        start_date = end_date - timedelta(days=30)
        
        history_filter = {
            'student_id': student_id,
            'date': {
                '$gte': start_date.strftime('%Y-%m-%d'),
                '$lte': end_date.strftime('%Y-%m-%d')
            }
        }
        
        attendance_records = list(attendance_model.collection.find(history_filter))
        
        # Calculate features
        features = {}
        
        # Basic student features
        features['grade'] = student.get('grade', 10)
        features['day_of_week'] = target_date.weekday()  # 0=Monday, 6=Sunday
        features['month'] = target_date.month
        features['day_of_month'] = target_date.day
        
        # Historical attendance features
        if attendance_records:
            total_records = len(attendance_records)
            absent_count = sum(1 for r in attendance_records if r.get('status') == 'absent')
            late_count = sum(1 for r in attendance_records if r.get('status') == 'late')
            
            features['attendance_rate_30d'] = (total_records - absent_count) / max(total_records, 1)
            features['absence_rate_30d'] = absent_count / max(total_records, 1)
            features['tardiness_rate_30d'] = late_count / max(total_records, 1)
            
            # Recent pattern (last 7 days)
            recent_records = [r for r in attendance_records 
                            if datetime.strptime(r['date'], '%Y-%m-%d') >= target_date - timedelta(days=7)]
            
            if recent_records:
                recent_absent = sum(1 for r in recent_records if r.get('status') == 'absent')
                features['recent_absence_rate'] = recent_absent / len(recent_records)
                
                # Consecutive absences
                sorted_recent = sorted(recent_records, key=lambda x: x['date'], reverse=True)
                consecutive_absences = 0
                for record in sorted_recent:
                    if record.get('status') == 'absent':
                        consecutive_absences += 1
                    else:
                        break
                features['consecutive_absences'] = consecutive_absences
            else:
                features['recent_absence_rate'] = 0
                features['consecutive_absences'] = 0
        else:
            # No history available
            features['attendance_rate_30d'] = 1.0
            features['absence_rate_30d'] = 0.0
            features['tardiness_rate_30d'] = 0.0
            features['recent_absence_rate'] = 0.0
            features['consecutive_absences'] = 0
        
        # Day type features (weekday vs weekend - though school is typically weekdays)
        features['is_weekend'] = 1 if target_date.weekday() >= 5 else 0
        features['is_monday'] = 1 if target_date.weekday() == 0 else 0
        features['is_friday'] = 1 if target_date.weekday() == 4 else 0
        
        # Seasonal features
        features['is_winter'] = 1 if target_date.month in [12, 1, 2] else 0
        features['is_spring'] = 1 if target_date.month in [3, 4, 5] else 0
        features['is_fall'] = 1 if target_date.month in [9, 10, 11] else 0
        
        return features
    
    except Exception as e:
        print(f"Error preparing features: {e}")
        return None


@predictions_bp.route('/absence', methods=['POST'])
@jwt_required()
def predict_absence():
    """Predict absence probability for a student"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') not in ['admin', 'teacher']:
            return forbidden_response("Insufficient permissions")
        
        data = request.get_json()
        if not data:
            return error_response("No data provided")
        
        student_id = data.get('student_id')
        date_str = data.get('date')  # Optional, defaults to tomorrow
        
        if not student_id:
            return validation_error_response(["student_id is required"])
        
        # Load ML model
        model = load_ml_model('absence_predictor.pkl')
        if not model:
            # Fallback prediction based on historical data
            return predict_absence_fallback(student_id, date_str)
        
        # Prepare features
        features = prepare_prediction_features(student_id, date_str)
        if not features:
            return server_error_response("Could not prepare prediction features")
        
        # Convert features to the format expected by the model
        feature_names = [
            'grade', 'day_of_week', 'month', 'day_of_month',
            'attendance_rate_30d', 'absence_rate_30d', 'tardiness_rate_30d',
            'recent_absence_rate', 'consecutive_absences',
            'is_weekend', 'is_monday', 'is_friday',
            'is_winter', 'is_spring', 'is_fall'
        ]
        
        feature_vector = np.array([[features.get(name, 0) for name in feature_names]])
        
        # Make prediction
        try:
            # Get probability of absence (assuming binary classifier)
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(feature_vector)[0]
                absence_probability = probabilities[1] if len(probabilities) > 1 else probabilities[0]
            else:
                # Fallback to regular prediction
                prediction = model.predict(feature_vector)[0]
                absence_probability = float(prediction)
        
        except Exception as e:
            print(f"Model prediction error: {e}")
            return predict_absence_fallback(student_id, date_str)
        
        # Classify risk level
        if absence_probability >= 0.7:
            risk_level = 'high'
        elif absence_probability >= 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Get student info
        student_model = Student(current_app.db)
        student = student_model.find_by_id(student_id)
        
        return success_response(
            data={
                'student_id': student_id,
                'student_name': f"{student['first_name']} {student['last_name']}" if student else 'Unknown',
                'prediction_date': date_str or datetime.now().strftime('%Y-%m-%d'),
                'absence_probability': round(absence_probability, 4),
                'risk_level': risk_level,
                'confidence': 'model_based',
                'features_used': len(feature_names),
                'recommendation': get_recommendation(risk_level, absence_probability)
            },
            message="Absence prediction completed successfully"
        )
        
    except Exception as e:
        return server_error_response("Failed to predict absence")


def predict_absence_fallback(student_id, date_str=None):
    """Fallback prediction based on historical patterns"""
    try:
        attendance_model = Attendance(current_app.db)
        student_model = Student(current_app.db)
        
        # Get student
        student = student_model.find_by_id(student_id)
        if not student:
            return not_found_response("Student")
        
        # Get recent attendance history (last 14 days)
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=14)
        
        history_filter = {
            'student_id': student_id,
            'date': {
                '$gte': start_date.strftime('%Y-%m-%d'),
                '$lte': end_date.strftime('%Y-%m-%d')
            }
        }
        
        recent_records = list(attendance_model.collection.find(history_filter))
        
        if not recent_records:
            # No history, assume low risk
            absence_probability = 0.1
        else:
            # Calculate absence rate from recent history
            absent_count = sum(1 for r in recent_records if r.get('status') == 'absent')
            absence_probability = absent_count / len(recent_records)
            
            # Adjust based on consecutive absences
            sorted_records = sorted(recent_records, key=lambda x: x['date'], reverse=True)
            consecutive_absences = 0
            for record in sorted_records:
                if record.get('status') == 'absent':
                    consecutive_absences += 1
                else:
                    break
            
            # Increase probability if there are consecutive absences
            if consecutive_absences > 0:
                absence_probability = min(1.0, absence_probability + (consecutive_absences * 0.2))
        
        # Classify risk level
        if absence_probability >= 0.6:
            risk_level = 'high'
        elif absence_probability >= 0.3:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return success_response(
            data={
                'student_id': student_id,
                'student_name': f"{student['first_name']} {student['last_name']}",
                'prediction_date': date_str or datetime.now().strftime('%Y-%m-%d'),
                'absence_probability': round(absence_probability, 4),
                'risk_level': risk_level,
                'confidence': 'historical_pattern',
                'historical_records': len(recent_records),
                'recommendation': get_recommendation(risk_level, absence_probability)
            },
            message="Fallback prediction completed successfully"
        )
        
    except Exception as e:
        return server_error_response("Fallback prediction failed")


def get_recommendation(risk_level, probability):
    """Get recommendation based on risk level"""
    if risk_level == 'high':
        return {
            'action': 'contact_parent',
            'message': 'High absence risk detected. Consider contacting parent/guardian.',
            'urgency': 'high'
        }
    elif risk_level == 'medium':
        return {
            'action': 'monitor_closely',
            'message': 'Moderate absence risk. Monitor student closely and be prepared to intervene.',
            'urgency': 'medium'
        }
    else:
        return {
            'action': 'normal_monitoring',
            'message': 'Low absence risk. Continue normal attendance monitoring.',
            'urgency': 'low'
        }


@predictions_bp.route('/batch', methods=['POST'])
@jwt_required()
def batch_predict_absence():
    """Predict absence for multiple students"""
    try:
        # Check permissions
        claims = get_jwt()
        if claims.get('role') not in ['admin', 'teacher']:
            return forbidden_response("Insufficient permissions")
        
        data = request.get_json()
        if not data or 'student_ids' not in data:
            return validation_error_response(["student_ids list is required"])
        
        student_ids = data['student_ids']
        date_str = data.get('date')
        
        if not isinstance(student_ids, list):
            return validation_error_response(["student_ids must be a list"])
        
        predictions = []
        errors = []
        
        for student_id in student_ids:
            try:
                # Prepare features
                features = prepare_prediction_features(student_id, date_str)
                if not features:
                    errors.append({'student_id': student_id, 'error': 'Could not prepare features'})
                    continue
                
                # Load model and predict (or use fallback)
                model = load_ml_model('absence_predictor.pkl')
                
                if model:
                    # Use ML model
                    feature_names = [
                        'grade', 'day_of_week', 'month', 'day_of_month',
                        'attendance_rate_30d', 'absence_rate_30d', 'tardiness_rate_30d',
                        'recent_absence_rate', 'consecutive_absences',
                        'is_weekend', 'is_monday', 'is_friday',
                        'is_winter', 'is_spring', 'is_fall'
                    ]
                    
                    feature_vector = np.array([[features.get(name, 0) for name in feature_names]])
                    
                    if hasattr(model, 'predict_proba'):
                        probabilities = model.predict_proba(feature_vector)[0]
                        absence_probability = probabilities[1] if len(probabilities) > 1 else probabilities[0]
                    else:
                        prediction = model.predict(feature_vector)[0]
                        absence_probability = float(prediction)
                else:
                    # Use fallback method
                    absence_probability = features['absence_rate_30d']
                
                # Classify risk
                if absence_probability >= 0.7:
                    risk_level = 'high'
                elif absence_probability >= 0.4:
                    risk_level = 'medium'
                else:
                    risk_level = 'low'
                
                predictions.append({
                    'student_id': student_id,
                    'absence_probability': round(absence_probability, 4),
                    'risk_level': risk_level
                })
                
            except Exception as e:
                errors.append({'student_id': student_id, 'error': str(e)})
        
        return success_response(
            data={
                'predictions': predictions,
                'errors': errors,
                'summary': {
                    'total_requested': len(student_ids),
                    'successful_predictions': len(predictions),
                    'failed_predictions': len(errors)
                }
            },
            message="Batch predictions completed"
        )
        
    except Exception as e:
        return server_error_response("Batch prediction failed")


@predictions_bp.route('/patterns/unusual', methods=['GET'])
@jwt_required()
def detect_unusual_patterns():
    """Detect unusual attendance patterns"""
    try:
        # Get query parameters
        days_back = int(request.args.get('days_back', 30))
        min_records = int(request.args.get('min_records', 5))
        
        attendance_model = Attendance(current_app.db)
        student_model = Student(current_app.db)
        
        # Date range for analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get all attendance records in the period
        date_filter = {
            'date': {
                '$gte': start_date.strftime('%Y-%m-%d'),
                '$lte': end_date.strftime('%Y-%m-%d')
            }
        }
        
        # Aggregate attendance by student
        pipeline = [
            {'$match': date_filter},
            {
                '$group': {
                    '_id': '$student_id',
                    'total_records': {'$sum': 1},
                    'absent_count': {
                        '$sum': {'$cond': [{'$eq': ['$status', 'absent']}, 1, 0]}
                    },
                    'late_count': {
                        '$sum': {'$cond': [{'$eq': ['$status', 'late']}, 1, 0]}
                    },
                    'records': {'$push': '$$ROOT'}
                }
            },
            {'$match': {'total_records': {'$gte': min_records}}}
        ]
        
        student_stats = list(attendance_model.collection.aggregate(pipeline))
        
        unusual_patterns = []
        
        for stats in student_stats:
            student_id = stats['_id']
            total_records = stats['total_records']
            absent_count = stats['absent_count']
            late_count = stats['late_count']
            
            absence_rate = absent_count / total_records
            tardiness_rate = late_count / total_records
            
            # Get student info
            student = student_model.find_by_id(student_id)
            if not student:
                continue
            
            patterns_detected = []
            
            # High absence rate (> 30%)
            if absence_rate > 0.3:
                patterns_detected.append({
                    'type': 'high_absence_rate',
                    'severity': 'high' if absence_rate > 0.5 else 'medium',
                    'description': f'High absence rate: {absence_rate:.1%}',
                    'value': absence_rate
                })
            
            # High tardiness rate (> 25%)
            if tardiness_rate > 0.25:
                patterns_detected.append({
                    'type': 'high_tardiness_rate',
                    'severity': 'medium',
                    'description': f'High tardiness rate: {tardiness_rate:.1%}',
                    'value': tardiness_rate
                })
            
            # Check for consecutive absences
            records = sorted(stats['records'], key=lambda x: x['date'])
            consecutive_absences = 0
            max_consecutive = 0
            
            for record in records:
                if record['status'] == 'absent':
                    consecutive_absences += 1
                    max_consecutive = max(max_consecutive, consecutive_absences)
                else:
                    consecutive_absences = 0
            
            if max_consecutive >= 3:
                patterns_detected.append({
                    'type': 'consecutive_absences',
                    'severity': 'high' if max_consecutive >= 5 else 'medium',
                    'description': f'Maximum consecutive absences: {max_consecutive}',
                    'value': max_consecutive
                })
            
            # Sudden increase in absences (comparing first half to second half)
            mid_point = len(records) // 2
            first_half_absences = sum(1 for r in records[:mid_point] if r['status'] == 'absent')
            second_half_absences = sum(1 for r in records[mid_point:] if r['status'] == 'absent')
            
            if mid_point > 0:
                first_half_rate = first_half_absences / mid_point
                second_half_rate = second_half_absences / (len(records) - mid_point)
                
                if second_half_rate > first_half_rate * 2 and second_half_rate > 0.2:
                    patterns_detected.append({
                        'type': 'increasing_absences',
                        'severity': 'medium',
                        'description': f'Absence rate increased from {first_half_rate:.1%} to {second_half_rate:.1%}',
                        'value': second_half_rate - first_half_rate
                    })
            
            if patterns_detected:
                unusual_patterns.append({
                    'student': {
                        'id': student['id'],
                        'name': f"{student['first_name']} {student['last_name']}",
                        'grade': student.get('grade'),
                        'student_id': student.get('student_id')
                    },
                    'patterns': patterns_detected,
                    'statistics': {
                        'total_records': total_records,
                        'absence_rate': round(absence_rate, 3),
                        'tardiness_rate': round(tardiness_rate, 3),
                        'attendance_rate': round(1 - absence_rate, 3)
                    }
                })
        
        # Sort by severity (high severity first)
        unusual_patterns.sort(key=lambda x: len([p for p in x['patterns'] if p['severity'] == 'high']), reverse=True)
        
        return success_response(
            data={
                'unusual_patterns': unusual_patterns,
                'analysis_period': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'days_analyzed': days_back
                },
                'summary': {
                    'students_analyzed': len(student_stats),
                    'unusual_patterns_found': len(unusual_patterns),
                    'high_severity_cases': len([p for p in unusual_patterns 
                                              if any(pattern['severity'] == 'high' for pattern in p['patterns'])])
                }
            },
            message="Unusual patterns analysis completed"
        )
        
    except Exception as e:
        return server_error_response("Failed to detect unusual patterns")


@predictions_bp.route('/class/<class_id>', methods=['GET'])
@jwt_required()
def get_class_predictions(class_id):
    """Get predictions for students in a specific class"""
    try:
        # Check permissions
        claims = get_jwt()
        current_user_id = get_jwt_identity()
        
        if claims.get('role') not in ['admin', 'teacher']:
            return forbidden_response("Insufficient permissions")
        
        # If teacher, verify they teach this class
        if claims.get('role') == 'teacher':
            from app.models import Class
            class_model = Class(current_app.db)
            class_doc = class_model.find_by_id(class_id)
            
            if not class_doc or str(class_doc.get('teacher_id')) != current_user_id:
                return forbidden_response("Access denied to this class")
        
        # Get students in the class
        from app.models import Student
        student_model = Student(current_app.db)
        students = student_model.find_by_class(class_id)
        
        if not students:
            return success_response(
                data={
                    'class_id': class_id,
                    'predictions': [],
                    'summary': {
                        'total_students': 0,
                        'high_risk': 0,
                        'medium_risk': 0,
                        'low_risk': 0
                    }
                },
                message='No students found in this class'
            )
        
        # Generate simple predictions for each student
        predictions = []
        for student in students:
            try:
                # Get recent attendance for this student
                attendance_model = Attendance(current_app.db)
                
                # Look at last 30 days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                
                student_attendance = attendance_model.find({
                    'student_id': student['id'],
                    'date': {
                        '$gte': start_date.strftime('%Y-%m-%d'),
                        '$lte': end_date.strftime('%Y-%m-%d')
                    }
                })
                
                # Calculate attendance rate
                total_records = len(student_attendance)
                if total_records == 0:
                    attendance_rate = 1.0  # Default to good attendance if no records
                    risk_level = 'low'
                else:
                    present_count = len([a for a in student_attendance if a['status'] == 'present'])
                    attendance_rate = present_count / total_records
                    
                    # Simple risk assessment
                    if attendance_rate >= 0.9:
                        risk_level = 'low'
                    elif attendance_rate >= 0.7:
                        risk_level = 'medium'
                    else:
                        risk_level = 'high'
                
                # Count recent absences (last 7 days)
                recent_start = end_date - timedelta(days=7)
                recent_attendance = [a for a in student_attendance 
                                   if datetime.strptime(a['date'], '%Y-%m-%d') >= recent_start]
                recent_absences = len([a for a in recent_attendance if a['status'] == 'absent'])
                
                prediction = {
                    'student_id': student['id'],
                    'student_name': f"{student['first_name']} {student['last_name']}",
                    'risk_level': risk_level,
                    'attendance_rate': round(attendance_rate * 100, 1),
                    'recent_absences': recent_absences,
                    'total_records': total_records,
                    'recommendation': get_recommendation(risk_level, recent_absences)
                }
                
                predictions.append(prediction)
                
            except Exception as e:
                print(f"Error generating prediction for student {student['id']}: {e}")
                # Continue with other students
                continue
        
        # Sort by risk level (high risk first)
        risk_order = {'high': 0, 'medium': 1, 'low': 2}
        predictions.sort(key=lambda x: risk_order.get(x['risk_level'], 3))
        
        return success_response(
            data={
                'class_id': class_id,
                'predictions': predictions,
                'summary': {
                    'total_students': len(students),
                    'high_risk': len([p for p in predictions if p['risk_level'] == 'high']),
                    'medium_risk': len([p for p in predictions if p['risk_level'] == 'medium']),
                    'low_risk': len([p for p in predictions if p['risk_level'] == 'low'])
                }
            },
            message="Class predictions generated successfully"
        )
        
    except Exception as e:
        print(f"Error in get_class_predictions: {e}")
        return server_error_response("Failed to generate class predictions")


def get_recommendation(risk_level, recent_absences):
    """Get recommendation based on risk level and recent absences"""
    if risk_level == 'high':
        return "Immediate intervention recommended - contact parents and consider support plan"
    elif risk_level == 'medium':
        if recent_absences >= 2:
            return "Monitor closely - recent absences indicate potential issues"
        else:
            return "Keep monitoring - attendance rate below optimal"
    else:
        if recent_absences >= 3:
            return "Check for recent issues despite overall good attendance"
        else:
            return "Good attendance - continue current approach"