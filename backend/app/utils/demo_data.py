"""
Demo data initialization for development and testing
"""
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
from bson import ObjectId

def initialize_demo_data(db):
    """Initialize demo data for development/testing with MongoDB"""
    
    # Clear existing data in MongoDB collections
    try:
        db.users.delete_many({})
        db.students.delete_many({})
        db.classes.delete_many({})
        db.attendance.delete_many({})
        db.alerts.delete_many({})
        db.predictions.delete_many({})
        db.reports.delete_many({})
        print("🗑️  Cleared existing data")
    except Exception as e:
        print(f"⚠️  Warning: Could not clear data: {e}")
    
    # Pre-generate ObjectIds for consistent references
    admin_id = ObjectId()
    teacher_id = ObjectId()
    parent_id = ObjectId()
    student_1_id = ObjectId()
    student_2_id = ObjectId()
    student_3_id = ObjectId()
    class_1_id = ObjectId()
    class_2_id = ObjectId()
    
    # Demo users (using ObjectIds)
    demo_users = [
        {
            '_id': admin_id,
            'email': 'admin@alexander.academy',
            'password': generate_password_hash('admin123', method='pbkdf2:sha256'),
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'admin',
            'created_at': datetime.utcnow()
        },
        {
            '_id': teacher_id,
            'email': 'teacher@alexander.academy',
            'password': generate_password_hash('teacher123', method='pbkdf2:sha256'),
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'role': 'teacher',
            'employee_id': 'T001',
            'created_at': datetime.utcnow()
        },
        {
            '_id': parent_id,
            'email': 'parent@alexander.academy',
            'password': generate_password_hash('parent123', method='pbkdf2:sha256'),
            'first_name': 'Michael',
            'last_name': 'Smith',
            'role': 'parent',
            'children': [student_1_id, student_2_id],  # Using ObjectIds for references
            'created_at': datetime.utcnow()
        }
    ]
    
    # Demo classes (using ObjectIds)
    demo_classes = [
        {
            '_id': class_1_id,
            'name': 'Grade 10A Mathematics',
            'subject': 'Mathematics',
            'teacher_id': teacher_id,  # ObjectId reference
            'students': [student_1_id, student_2_id, student_3_id],  # ObjectId references
            'schedule': 'Monday, Wednesday, Friday - 9:00 AM',
            'created_at': datetime.utcnow()
        },
        {
            '_id': class_2_id,
            'name': 'Grade 10A English',
            'subject': 'English Literature',
            'teacher_id': teacher_id,  # ObjectId reference
            'students': [student_1_id, student_2_id, student_3_id],  # ObjectId references
            'schedule': 'Tuesday, Thursday - 10:00 AM',
            'created_at': datetime.utcnow()
        }
    ]
    
    # Demo students (using ObjectIds)
    demo_students = [
        {
            '_id': student_1_id,
            'student_id': 'AA2024001',  # Keep human-readable student ID separate
            'first_name': 'Emma',
            'last_name': 'Wilson',
            'email': 'emma.wilson@student.alexander.academy',
            'grade': '10',
            'parent_id': parent_id,  # ObjectId reference
            'classes': [class_1_id, class_2_id],  # ObjectId references
            'emergency_contact': {
                'name': 'Michael Smith',
                'phone': '+1-604-555-0101',
                'email': 'parent@alexander.academy'
            },
            'created_at': datetime.utcnow()
        },
        {
            '_id': student_2_id,
            'student_id': 'AA2024002',
            'first_name': 'James',
            'last_name': 'Brown',
            'email': 'james.brown@student.alexander.academy',
            'grade': '10',
            'parent_id': parent_id,  # ObjectId reference
            'classes': [class_1_id, class_2_id],  # ObjectId references
            'emergency_contact': {
                'name': 'Michael Smith',
                'phone': '+1-604-555-0101',
                'email': 'parent@alexander.academy'
            },
            'created_at': datetime.utcnow()
        },
        {
            '_id': student_3_id,
            'student_id': 'AA2024003',
            'first_name': 'Sophie',
            'last_name': 'Davis',
            'email': 'sophie.davis@student.alexander.academy',
            'grade': '10',
            'classes': [class_1_id, class_2_id],  # ObjectId references
            'emergency_contact': {
                'name': 'Lisa Davis',
                'phone': '+1-604-555-0102',
                'email': 'lisa.davis@gmail.com'
            },
            'created_at': datetime.utcnow()
        }
    ]
    
    # Generate demo attendance records for the last 30 days
    demo_attendance = []
    today = datetime.now().date()
    
    for i in range(30):
        date = today - timedelta(days=i)
        # Skip weekends
        if date.weekday() >= 5:
            continue
            
        for student in demo_students:
            # Create one attendance record per student per day (not per class)
            # 85% attendance rate (realistic for demo)
            overall_status = 'present' if random.random() < 0.85 else random.choice(['absent', 'late', 'excused'])
            
            # Create class-specific attendance within the same record
            class_attendance = {}
            for class_id in student['classes']:
                # If student is absent for the day, they're absent from all classes
                if overall_status == 'absent':
                    class_status = 'absent'
                elif overall_status == 'late':
                    # If late, might be late to first class but present to others
                    class_status = 'late' if class_id == student['classes'][0] else 'present'
                else:
                    # Small chance of being absent from individual classes even if generally present
                    class_status = 'present' if random.random() < 0.95 else 'absent'
                
                # Convert ObjectId to string for dictionary key
                class_attendance[str(class_id)] = {
                    'status': class_status,
                    'marked_at': datetime.combine(date, datetime.min.time().replace(hour=9)),
                    'marked_by': teacher_id  # ObjectId reference
                }
            
            attendance_record = {
                # Let MongoDB generate ObjectId for attendance records
                'student_id': student['_id'],  # ObjectId reference
                'date': date.isoformat(),
                'overall_status': overall_status,
                'class_attendance': class_attendance,
                'marked_by': teacher_id,  # ObjectId reference
                'marked_at': datetime.combine(date, datetime.min.time().replace(hour=9)),
                'notes': 'Demo data' if overall_status != 'present' else ''
            }
            demo_attendance.append(attendance_record)

    # Generate demo alerts
    demo_alerts = [
        {
            # Let MongoDB generate ObjectId for alerts
            'student_id': student_1_id,  # ObjectId reference
            'parent_id': parent_id,      # ObjectId reference
            'type': 'absence',
            'title': 'Multiple Absences Alert',
            'message': 'Emma Wilson has been absent for 3 consecutive days in Mathematics class.',
            'severity': 'high',
            'status': 'unread',
            'class_id': class_1_id,      # ObjectId reference
            'created_at': datetime.utcnow() - timedelta(days=2),
            'created_by': teacher_id     # ObjectId reference
        },
        {
            # Let MongoDB generate ObjectId for alerts
            'student_id': student_2_id,  # ObjectId reference
            'parent_id': parent_id,      # ObjectId reference
            'type': 'tardiness',
            'title': 'Frequent Tardiness Alert',
            'message': 'James Brown has been late to English Literature class 5 times this week.',
            'severity': 'medium',
            'status': 'read',
            'class_id': class_2_id,      # ObjectId reference
            'created_at': datetime.utcnow() - timedelta(days=1),
            'created_by': teacher_id,    # ObjectId reference
            'read_at': datetime.utcnow() - timedelta(hours=12)
        },
        {
            # Let MongoDB generate ObjectId for alerts
            'student_id': student_3_id,  # ObjectId reference
            'type': 'pattern',
            'title': 'Attendance Pattern Alert',
            'message': 'Sophie Davis shows irregular attendance pattern - frequently absent on Mondays.',
            'severity': 'low',
            'status': 'unread',
            'created_at': datetime.utcnow() - timedelta(hours=6),
            'created_by': 'system'  # Could be system or teacher_id
        }
    ]

    # Generate demo predictions
    demo_predictions = [
        {
            # Let MongoDB generate ObjectId for predictions
            'student_id': student_1_id,  # ObjectId reference
            'prediction_type': 'attendance_risk',
            'predicted_outcome': 'high_risk',
            'confidence': 0.87,
            'factors': [
                'Recent absence pattern',
                'Historical attendance trend',
                'Time of year correlation'
            ],
            'recommendations': [
                'Schedule parent-teacher conference',
                'Implement attendance monitoring plan',
                'Consider counseling support'
            ],
            'prediction_date': datetime.utcnow(),
            'valid_until': datetime.utcnow() + timedelta(days=30),
            'model_version': '1.2.0',
            'created_by': 'ml_system'
        },
        {
            # Let MongoDB generate ObjectId for predictions
            'student_id': student_2_id,  # ObjectId reference
            'prediction_type': 'attendance_improvement',
            'predicted_outcome': 'improving',
            'confidence': 0.73,
            'factors': [
                'Positive response to interventions',
                'Improved morning routine',
                'Increased parental engagement'
            ],
            'recommendations': [
                'Continue current support strategies',
                'Recognize improvement efforts',
                'Monitor progress weekly'
            ],
            'prediction_date': datetime.utcnow() - timedelta(days=3),
            'valid_until': datetime.utcnow() + timedelta(days=27),
            'model_version': '1.2.0',
            'created_by': 'ml_system'
        },
        {
            # Let MongoDB generate ObjectId for predictions
            'student_id': student_3_id,  # ObjectId reference
            'prediction_type': 'class_performance',
            'predicted_outcome': 'stable',
            'confidence': 0.92,
            'factors': [
                'Consistent attendance rate',
                'Good academic performance',
                'Strong family support'
            ],
            'recommendations': [
                'Maintain current approach',
                'Consider leadership opportunities',
                'Continue regular monitoring'
            ],
            'prediction_date': datetime.utcnow() - timedelta(days=1),
            'valid_until': datetime.utcnow() + timedelta(days=29),
            'model_version': '1.2.0',
            'created_by': 'ml_system'
        }
    ]

    # Generate demo reports
    demo_reports = [
        {
            # Let MongoDB generate ObjectId for reports
            'title': 'Weekly Attendance Summary',
            'type': 'attendance_summary',
            'period': {
                'start_date': (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
                'end_date': datetime.utcnow().date().isoformat()
            },
            'generated_by': teacher_id,  # ObjectId reference
            'generated_at': datetime.utcnow(),
            'status': 'completed',
            'data': {
                'total_students': 3,
                'average_attendance': 85.2,
                'present_count': 18,
                'absent_count': 2,
                'late_count': 1,
                'excused_count': 1
            },
            'filters': {
                'classes': [class_1_id, class_2_id],  # ObjectId references
                'date_range': 'last_7_days'
            }
        },
        {
            # Let MongoDB generate ObjectId for reports
            'title': 'Monthly Class Performance Report',
            'type': 'class_performance',
            'period': {
                'start_date': (datetime.utcnow() - timedelta(days=30)).date().isoformat(),
                'end_date': datetime.utcnow().date().isoformat()
            },
            'generated_by': admin_id,  # ObjectId reference
            'generated_at': datetime.utcnow() - timedelta(days=2),
            'status': 'completed',
            'data': {
                str(class_1_id): {  # Convert ObjectId to string for dictionary key
                    'name': 'Grade 10A Mathematics',
                    'attendance_rate': 88.5,
                    'total_sessions': 20,
                    'student_count': 3,
                    'alert_count': 2
                },
                str(class_2_id): {  # Convert ObjectId to string for dictionary key
                    'name': 'Grade 10A English',
                    'attendance_rate': 82.1,
                    'total_sessions': 16,
                    'student_count': 3,
                    'alert_count': 1
                }
            },
            'filters': {
                'period': 'monthly',
                'include_predictions': True
            }
        },
        {
            # Let MongoDB generate ObjectId for reports
            'title': 'Student Risk Assessment Report',
            'type': 'risk_assessment',
            'period': {
                'start_date': (datetime.utcnow() - timedelta(days=14)).date().isoformat(),
                'end_date': datetime.utcnow().date().isoformat()
            },
            'generated_by': 'system',
            'generated_at': datetime.utcnow() - timedelta(hours=6),
            'status': 'completed',
            'data': {
                'high_risk_students': [student_1_id],  # ObjectId reference
                'medium_risk_students': [student_2_id],  # ObjectId reference
                'low_risk_students': [student_3_id],  # ObjectId reference
                'recommendations': [
                    'Immediate intervention needed for high-risk students',
                    'Monitor medium-risk students closely',
                    'Continue regular tracking for low-risk students'
                ]
            },
            'filters': {
                'risk_levels': ['high', 'medium', 'low'],
                'include_predictions': True,
                'automated': True
            }
        }
    ]
    
    # Insert data into MongoDB collections
    try:
        db.users.insert_many(demo_users)
        db.classes.insert_many(demo_classes)
        db.students.insert_many(demo_students)
        db.attendance.insert_many(demo_attendance)
        db.alerts.insert_many(demo_alerts)
        db.predictions.insert_many(demo_predictions)
        db.reports.insert_many(demo_reports)
        
        print(f"📊 MongoDB demo data created:")
        print(f"   - {len(demo_users)} users")
        print(f"   - {len(demo_students)} students")
        print(f"   - {len(demo_classes)} classes")
        print(f"   - {len(demo_attendance)} attendance records")
        print(f"   - {len(demo_alerts)} alerts")
        print(f"   - {len(demo_predictions)} predictions")
        print(f"   - {len(demo_reports)} reports")
    except Exception as e:
        print(f"❌ Error inserting demo data: {e}")
        raise
    
    # Return summary for the API response
    return {
        'users_created': len(demo_users),
        'students_created': len(demo_students), 
        'classes_created': len(demo_classes),
        'attendance_records_created': len(demo_attendance),
        'alerts_created': len(demo_alerts),
        'predictions_created': len(demo_predictions),
        'reports_created': len(demo_reports),
        'demo_accounts': {
            'admin': 'admin@alexander.academy / admin123',
            'teacher': 'teacher@alexander.academy / teacher123', 
            'parent': 'parent@alexander.academy / parent123'
        }
    }
