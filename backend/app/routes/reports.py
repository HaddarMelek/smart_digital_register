"""
Reports Routes for Intelligent Attendance Register
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime, timedelta
from collections import defaultdict

from app.models import Attendance, Student, Class
from app.utils.api_response import (
    success_response, error_response, validation_error_response,
    not_found_response, forbidden_response, server_error_response
)

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/daily', methods=['GET'])
@jwt_required()
def daily_report():
    """Generate daily attendance report"""
    try:
        # Get query parameters
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        class_id = request.args.get('class_id')
        
        # Validate date
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return validation_error_response(["Invalid date format. Use YYYY-MM-DD"])
        
        attendance_model = Attendance(current_app.db)
        student_model = Student(current_app.db)
        class_model = Class(current_app.db)
        
        # Build filters
        filters = {'date': date_str}
        if class_id:
            filters['class_id'] = class_id
        
        # Get attendance records for the date
        attendance_records = list(attendance_model.collection.find(filters))
        
        # Get class information
        if class_id:
            classes = [class_model.find_by_id(class_id)]
            classes = [cls for cls in classes if cls]  # Filter out None
        else:
            classes = class_model.find_all()
        
        report_data = {
            'date': date_str,
            'summary': {
                'total_students': 0,
                'present': 0,
                'absent': 0,
                'late': 0,
                'excused': 0,
                'not_marked': 0
            },
            'classes': []
        }
        
        overall_stats = defaultdict(int)
        
        for cls in classes:
            # Get students in this class
            class_students = student_model.find_by_class(cls['id'])
            
            # Get attendance for this class
            class_attendance = [r for r in attendance_records if r.get('class_id') == cls['id']]
            
            # Create attendance map
            attendance_map = {r['student_id']: r for r in class_attendance}
            
            class_summary = {
                'present': 0,
                'absent': 0,
                'late': 0,
                'excused': 0,
                'not_marked': 0
            }
            
            student_list = []
            
            for student in class_students:
                attendance_record = attendance_map.get(student['id'])
                
                if attendance_record:
                    status = attendance_record['status']
                    class_summary[status] += 1
                    overall_stats[status] += 1
                else:
                    status = 'not_marked'
                    class_summary['not_marked'] += 1
                    overall_stats['not_marked'] += 1
                
                student_list.append({
                    'id': student['id'],
                    'name': f"{student['first_name']} {student['last_name']}",
                    'student_id': student.get('student_id', ''),
                    'status': status,
                    'notes': attendance_record.get('notes', '') if attendance_record else '',
                    'marked_at': attendance_record.get('marked_at') if attendance_record else None
                })
            
            # Sort students by name
            student_list.sort(key=lambda x: x['name'])
            
            class_data = {
                'id': cls['id'],
                'name': cls['name'],
                'subject': cls.get('subject', ''),
                'teacher_name': cls.get('teacher_name', ''),
                'total_students': len(class_students),
                'summary': class_summary,
                'attendance_rate': round(class_summary['present'] / max(len(class_students), 1) * 100, 1),
                'students': student_list
            }
            
            report_data['classes'].append(class_data)
            report_data['summary']['total_students'] += len(class_students)
        
        # Update overall summary
        report_data['summary'].update(dict(overall_stats))
        
        if report_data['summary']['total_students'] > 0:
            total = report_data['summary']['total_students']
            report_data['summary']['attendance_rate'] = round(
                report_data['summary']['present'] / total * 100, 1
            )
            report_data['summary']['absence_rate'] = round(
                report_data['summary']['absent'] / total * 100, 1
            )
        
        return success_response(
            data={
                'report_type': 'daily',
                'generated_at': datetime.utcnow().isoformat(),
                'data': report_data
            },
            message="Daily report generated successfully"
        )
        
    except Exception as e:
        return server_error_response("Failed to generate daily report")


@reports_bp.route('/weekly', methods=['GET'])
@jwt_required()
def weekly_report():
    """Generate weekly attendance report"""
    try:
        # Get query parameters
        week_start = request.args.get('week_start')
        class_id = request.args.get('class_id')
        
        if not week_start:
            # Default to current week (Monday)
            today = datetime.now()
            days_since_monday = today.weekday()
            monday = today - timedelta(days=days_since_monday)
            week_start = monday.strftime('%Y-%m-%d')
        
        # Calculate week end
        try:
            start_date = datetime.strptime(week_start, '%Y-%m-%d')
            end_date = start_date + timedelta(days=6)
        except ValueError:
            return validation_error_response(["Invalid date format. Use YYYY-MM-DD"])
        
        attendance_model = Attendance(current_app.db)
        student_model = Student(current_app.db)
        class_model = Class(current_app.db)
        
        # Build date range filter
        date_filter = {
            'date': {
                '$gte': start_date.strftime('%Y-%m-%d'),
                '$lte': end_date.strftime('%Y-%m-%d')
            }
        }
        
        if class_id:
            date_filter['class_id'] = class_id
        
        # Get all attendance records for the week
        attendance_records = list(attendance_model.collection.find(date_filter))
        
        # Group by student and date
        student_attendance = defaultdict(lambda: defaultdict(list))
        for record in attendance_records:
            student_attendance[record['student_id']][record['date']].append(record)
        
        # Get classes
        if class_id:
            classes = [class_model.find_by_id(class_id)]
            classes = [cls for cls in classes if cls]
        else:
            classes = class_model.find_all()
        
        report_data = {
            'week_start': week_start,
            'week_end': end_date.strftime('%Y-%m-%d'),
            'summary': {
                'total_students': 0,
                'days_analyzed': 0,
                'average_attendance_rate': 0,
                'total_absences': 0,
                'total_tardiness': 0
            },
            'daily_breakdown': [],
            'student_summaries': []
        }
        
        # Generate daily breakdown
        current_date = start_date
        daily_stats = []
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            day_records = [r for r in attendance_records if r['date'] == date_str]
            
            day_stats = {
                'date': date_str,
                'day_name': current_date.strftime('%A'),
                'present': len([r for r in day_records if r['status'] == 'present']),
                'absent': len([r for r in day_records if r['status'] == 'absent']),
                'late': len([r for r in day_records if r['status'] == 'late']),
                'excused': len([r for r in day_records if r['status'] == 'excused'])
            }
            
            day_stats['total'] = sum([day_stats['present'], day_stats['absent'], 
                                    day_stats['late'], day_stats['excused']])
            
            if day_stats['total'] > 0:
                day_stats['attendance_rate'] = round(day_stats['present'] / day_stats['total'] * 100, 1)
            else:
                day_stats['attendance_rate'] = 0
            
            daily_stats.append(day_stats)
            current_date += timedelta(days=1)
        
        report_data['daily_breakdown'] = daily_stats
        
        # Generate student summaries
        all_students = set()
        for cls in classes:
            class_students = student_model.find_by_class(cls['id'])
            all_students.update(student['id'] for student in class_students)
        
        student_summaries = []
        total_attendance_rates = []
        
        for student_id in all_students:
            student = student_model.find_by_id(student_id)
            if not student:
                continue
            
            student_records = []
            for date_str in [d['date'] for d in daily_stats]:
                records = student_attendance[student_id].get(date_str, [])
                if records:
                    student_records.extend(records)
            
            # Calculate student statistics
            present_count = len([r for r in student_records if r['status'] == 'present'])
            absent_count = len([r for r in student_records if r['status'] == 'absent'])
            late_count = len([r for r in student_records if r['status'] == 'late'])
            excused_count = len([r for r in student_records if r['status'] == 'excused'])
            total_records = len(student_records)
            
            attendance_rate = (present_count / max(total_records, 1)) * 100
            total_attendance_rates.append(attendance_rate)
            
            student_summary = {
                'student': {
                    'id': student['id'],
                    'name': f"{student['first_name']} {student['last_name']}",
                    'student_id': student.get('student_id', ''),
                    'grade': student.get('grade', '')
                },
                'statistics': {
                    'total_days': total_records,
                    'present': present_count,
                    'absent': absent_count,
                    'late': late_count,
                    'excused': excused_count,
                    'attendance_rate': round(attendance_rate, 1),
                    'absence_rate': round((absent_count / max(total_records, 1)) * 100, 1)
                }
            }
            
            student_summaries.append(student_summary)
        
        # Sort by attendance rate (lowest first for attention)
        student_summaries.sort(key=lambda x: x['statistics']['attendance_rate'])
        
        report_data['student_summaries'] = student_summaries
        
        # Calculate overall summary
        report_data['summary']['total_students'] = len(all_students)
        report_data['summary']['days_analyzed'] = len([d for d in daily_stats if d['total'] > 0])
        
        if total_attendance_rates:
            report_data['summary']['average_attendance_rate'] = round(
                sum(total_attendance_rates) / len(total_attendance_rates), 1
            )
        
        report_data['summary']['total_absences'] = sum(s['statistics']['absent'] 
                                                      for s in student_summaries)
        report_data['summary']['total_tardiness'] = sum(s['statistics']['late'] 
                                                       for s in student_summaries)
        
        return success_response(
            data={
                'report_type': 'weekly',
                'generated_at': datetime.utcnow().isoformat(),
                'data': report_data
            },
            message="Weekly report generated successfully"
        )
        
    except Exception as e:
        return server_error_response("Failed to generate weekly report")


@reports_bp.route('/monthly', methods=['GET'])
@jwt_required()
def monthly_report():
    """Generate monthly attendance report"""
    try:
        # Get query parameters
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        class_id = request.args.get('class_id')
        
        # Calculate month start and end
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        attendance_model = Attendance(current_app.db)
        student_model = Student(current_app.db)
        class_model = Class(current_app.db)
        
        # Build date filter
        date_filter = {
            'date': {
                '$gte': start_date.strftime('%Y-%m-%d'),
                '$lte': end_date.strftime('%Y-%m-%d')
            }
        }
        
        if class_id:
            date_filter['class_id'] = class_id
        
        # Get attendance statistics using aggregation
        pipeline = [
            {'$match': date_filter},
            {
                '$group': {
                    '_id': {
                        'student_id': '$student_id',
                        'status': '$status'
                    },
                    'count': {'$sum': 1}
                }
            }
        ]
        
        aggregated_data = list(attendance_model.collection.aggregate(pipeline))
        
        # Process aggregated data
        student_stats = defaultdict(lambda: defaultdict(int))
        for item in aggregated_data:
            student_id = item['_id']['student_id']
            status = item['_id']['status']
            count = item['count']
            student_stats[student_id][status] = count
        
        # Get classes and students
        if class_id:
            classes = [class_model.find_by_id(class_id)]
            classes = [cls for cls in classes if cls]
        else:
            classes = class_model.find_all()
        
        all_students = set()
        for cls in classes:
            class_students = student_model.find_by_class(cls['id'])
            all_students.update(student['id'] for student in class_students)
        
        # Calculate trends (compare with previous month)
        prev_month_start = start_date - timedelta(days=32)  # Go back more than a month
        prev_month_start = prev_month_start.replace(day=1)  # First day of previous month
        prev_month_end = start_date - timedelta(days=1)  # Last day of previous month
        
        prev_filter = {
            'date': {
                '$gte': prev_month_start.strftime('%Y-%m-%d'),
                '$lte': prev_month_end.strftime('%Y-%m-%d')
            }
        }
        
        if class_id:
            prev_filter['class_id'] = class_id
        
        prev_pipeline = [
            {'$match': prev_filter},
            {
                '$group': {
                    '_id': '$status',
                    'count': {'$sum': 1}
                }
            }
        ]
        
        prev_month_data = list(attendance_model.collection.aggregate(prev_pipeline))
        prev_month_stats = {item['_id']: item['count'] for item in prev_month_data}
        
        # Build report
        report_data = {
            'month': month,
            'year': year,
            'month_name': start_date.strftime('%B'),
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'total_days': (end_date - start_date).days + 1,
                'school_days': len(set(r['date'] for r in attendance_model.collection.find(date_filter)))
            },
            'summary': {
                'total_students': len(all_students),
                'total_records': sum(len(student_stats[sid].values()) for sid in student_stats),
                'present': sum(student_stats[sid]['present'] for sid in student_stats),
                'absent': sum(student_stats[sid]['absent'] for sid in student_stats),
                'late': sum(student_stats[sid]['late'] for sid in student_stats),
                'excused': sum(student_stats[sid]['excused'] for sid in student_stats)
            },
            'trends': {},
            'top_performers': [],
            'students_at_risk': [],
            'class_breakdown': []
        }
        
        # Calculate rates
        total_records = report_data['summary']['total_records']
        if total_records > 0:
            report_data['summary']['attendance_rate'] = round(
                report_data['summary']['present'] / total_records * 100, 1
            )
            report_data['summary']['absence_rate'] = round(
                report_data['summary']['absent'] / total_records * 100, 1
            )
        
        # Calculate trends
        current_total = total_records
        prev_total = sum(prev_month_stats.values())
        
        if prev_total > 0:
            current_attendance_rate = report_data['summary']['present'] / current_total * 100
            prev_attendance_rate = prev_month_stats.get('present', 0) / prev_total * 100
            
            report_data['trends'] = {
                'attendance_rate_change': round(current_attendance_rate - prev_attendance_rate, 1),
                'total_absences_change': report_data['summary']['absent'] - prev_month_stats.get('absent', 0),
                'comparison_period': f"{prev_month_start.strftime('%B %Y')}"
            }
        
        # Student performance analysis
        student_performance = []
        
        for student_id in all_students:
            student = student_model.find_by_id(student_id)
            if not student:
                continue
            
            stats = student_stats[student_id]
            total_student_records = sum(stats.values())
            
            if total_student_records > 0:
                attendance_rate = (stats['present'] / total_student_records) * 100
                
                student_performance.append({
                    'student': {
                        'id': student['id'],
                        'name': f"{student['first_name']} {student['last_name']}",
                        'student_id': student.get('student_id', ''),
                        'grade': student.get('grade', '')
                    },
                    'statistics': {
                        'total_days': total_student_records,
                        'present': stats['present'],
                        'absent': stats['absent'],
                        'late': stats['late'],
                        'excused': stats['excused'],
                        'attendance_rate': round(attendance_rate, 1)
                    }
                })
        
        # Sort for top performers and at-risk students
        student_performance.sort(key=lambda x: x['statistics']['attendance_rate'], reverse=True)
        
        report_data['top_performers'] = student_performance[:10]  # Top 10
        report_data['students_at_risk'] = [
            s for s in student_performance 
            if s['statistics']['attendance_rate'] < 85  # Below 85% attendance
        ]
        
        return success_response(
            data={
                'report_type': 'monthly',
                'generated_at': datetime.utcnow().isoformat(),
                'data': report_data
            },
            message="Monthly report generated successfully"
        )
        
    except Exception as e:
        return server_error_response("Failed to generate monthly report")


@reports_bp.route('/student/<student_id>', methods=['GET'])
@jwt_required()
def student_report(student_id):
    """Generate individual student attendance report"""
    try:
        # Get query parameters
        days_back = int(request.args.get('days_back', 30))
        
        student_model = Student(current_app.db)
        attendance_model = Attendance(current_app.db)
        
        # Get student info
        student = student_model.find_by_id(student_id)
        if not student:
            return not_found_response("Student")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get attendance history
        attendance_history = attendance_model.find_student_history(student_id, limit=100)
        
        # Filter by date range
        filtered_history = [
            record for record in attendance_history
            if start_date.strftime('%Y-%m-%d') <= record['date'] <= end_date.strftime('%Y-%m-%d')
        ]
        
        # Calculate statistics
        total_records = len(filtered_history)
        if total_records > 0:
            present_count = len([r for r in filtered_history if r['status'] == 'present'])
            absent_count = len([r for r in filtered_history if r['status'] == 'absent'])
            late_count = len([r for r in filtered_history if r['status'] == 'late'])
            excused_count = len([r for r in filtered_history if r['status'] == 'excused'])
            
            statistics = {
                'total_days': total_records,
                'present': present_count,
                'absent': absent_count,
                'late': late_count,
                'excused': excused_count,
                'attendance_rate': round((present_count / total_records) * 100, 1),
                'absence_rate': round((absent_count / total_records) * 100, 1),
                'tardiness_rate': round((late_count / total_records) * 100, 1)
            }
        else:
            statistics = {
                'total_days': 0,
                'present': 0,
                'absent': 0,
                'late': 0,
                'excused': 0,
                'attendance_rate': 0,
                'absence_rate': 0,
                'tardiness_rate': 0
            }
        
        # Identify patterns
        patterns = []
        
        # Check for consecutive absences
        sorted_history = sorted(filtered_history, key=lambda x: x['date'])
        consecutive_absences = 0
        max_consecutive = 0
        
        for record in sorted_history:
            if record['status'] == 'absent':
                consecutive_absences += 1
                max_consecutive = max(max_consecutive, consecutive_absences)
            else:
                consecutive_absences = 0
        
        if max_consecutive >= 3:
            patterns.append({
                'type': 'consecutive_absences',
                'description': f'Maximum consecutive absences: {max_consecutive} days',
                'severity': 'high' if max_consecutive >= 5 else 'medium'
            })
        
        # Check for frequent tardiness
        if statistics['tardiness_rate'] > 20:
            patterns.append({
                'type': 'frequent_tardiness',
                'description': f'High tardiness rate: {statistics["tardiness_rate"]}%',
                'severity': 'medium'
            })
        
        # Check day-of-week patterns
        day_stats = defaultdict(list)
        for record in filtered_history:
            date_obj = datetime.strptime(record['date'], '%Y-%m-%d')
            day_name = date_obj.strftime('%A')
            day_stats[day_name].append(record['status'])
        
        for day, statuses in day_stats.items():
            if len(statuses) >= 3:  # Enough data
                absent_rate = (statuses.count('absent') / len(statuses)) * 100
                if absent_rate > 40:  # More than 40% absences on this day
                    patterns.append({
                        'type': 'day_pattern',
                        'description': f'High absence rate on {day}: {absent_rate:.1f}%',
                        'severity': 'medium'
                    })
        
        report_data = {
            'student': {
                'id': student['id'],
                'name': f"{student['first_name']} {student['last_name']}",
                'student_id': student.get('student_id', ''),
                'grade': student.get('grade', ''),
                'class_id': student.get('class_id', '')
            },
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'days_analyzed': days_back
            },
            'statistics': statistics,
            'patterns': patterns,
            'recent_history': filtered_history[:20],  # Last 20 records
            'recommendations': []
        }
        
        # Generate recommendations
        if statistics['attendance_rate'] < 85:
            report_data['recommendations'].append({
                'type': 'attendance_intervention',
                'message': 'Student attendance is below acceptable threshold. Consider parent conference.',
                'priority': 'high'
            })
        
        if statistics['tardiness_rate'] > 20:
            report_data['recommendations'].append({
                'type': 'tardiness_support',
                'message': 'Student shows pattern of tardiness. Investigate potential causes.',
                'priority': 'medium'
            })
        
        if max_consecutive >= 3:
            report_data['recommendations'].append({
                'type': 'absence_follow_up',
                'message': 'Student has had consecutive absences. Follow up on reasons and provide support.',
                'priority': 'high'
            })
        
        return success_response(
            data={
                'report_type': 'student_individual',
                'generated_at': datetime.utcnow().isoformat(),
                'data': report_data
            },
            message="Student report generated successfully"
        )
        
    except Exception as e:
        return server_error_response("Failed to generate student report")


@reports_bp.route('/range', methods=['GET'])
@jwt_required()
def range_report():
    """Generate attendance report for a date range"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        class_id = request.args.get('class_id')
        
        if not start_date or not end_date:
            return validation_error_response(["start_date and end_date parameters are required"])
        
        # Validate dates
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return validation_error_response(["Invalid date format. Use YYYY-MM-DD"])
        
        if start > end:
            return validation_error_response(["start_date must be before end_date"])
        
        attendance_model = Attendance(current_app.db)
        student_model = Student(current_app.db)
        class_model = Class(current_app.db)
        
        # Build filters for date range
        filters = {
            'date': {
                '$gte': start_date,
                '$lte': end_date
            }
        }
        if class_id:
            filters['class_id'] = class_id
        
        # Get attendance records
        attendance_records = list(attendance_model.collection.find(filters))
        
        # Get all students and classes
        students = student_model.find_all()
        if class_id:
            classes = [class_model.find_by_id(class_id)]
            classes = [cls for cls in classes if cls]
        else:
            classes = class_model.find_all()
        
        # Process data by date
        daily_stats = defaultdict(lambda: {
            'date': '',
            'total_expected': 0,
            'present': 0,
            'absent': 0,
            'late': 0,
            'excused': 0,
            'attendance_rate': 0
        })
        
        # Calculate daily statistics
        for record in attendance_records:
            date = record['date'] if isinstance(record['date'], str) else record['date'].strftime('%Y-%m-%d')
            daily_stats[date]['date'] = date
            daily_stats[date]['total_expected'] += 1
            
            status = record.get('status', 'present')
            if status in daily_stats[date]:
                daily_stats[date][status] += 1
        
        # Calculate attendance rates and format data for frontend
        daily_reports = []
        for date_data in daily_stats.values():
            if date_data['total_expected'] > 0:
                date_data['attendance_rate'] = round(
                    (date_data['present'] / date_data['total_expected']) * 100, 2
                )
            
            # Format the data structure to match frontend expectations
            daily_reports.append({
                'date': date_data['date'],
                'total_present': date_data['present'],
                'total_absent': date_data['absent'],
                'attendance_rate': date_data['attendance_rate'],
                'total_expected': date_data['total_expected'],
                'late': date_data['late'],
                'excused': date_data['excused']
            })
        
        # Sort by date (most recent first)
        daily_reports.sort(key=lambda x: x['date'], reverse=True)
        
        return success_response(
            data=daily_reports,
            message="Range report generated successfully"
        )
        
    except Exception as e:
        return server_error_response("Failed to generate range report")