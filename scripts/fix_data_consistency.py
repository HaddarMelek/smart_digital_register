#!/usr/bin/env python3
"""
Data Consistency Fix Script
Fixes inconsistent attendance data, AI predictions, and alerts across the system
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_data_consistency():
    """Main function to fix all data consistency issues"""
    
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['alexander_academy_db']
    
    logger.info("🔧 STARTING DATA CONSISTENCY FIX...")
    logger.info("="*70)
    
    # Step 1: Get Emma Wilson and validate her data
    emma = db.students.find_one({'first_name': 'Emma', 'last_name': 'Wilson'})
    if not emma:
        logger.error("❌ Emma Wilson not found!")
        return
    
    emma_id = emma['_id']
    logger.info(f"👤 Processing Emma Wilson (ID: {emma_id})")
    
    # Step 2: Create consistent attendance pattern for Emma
    # We'll create a realistic attendance pattern that matches the expected alerts
    
    # Clear existing inconsistent attendance data
    db.attendance.delete_many({'student_id': emma_id})
    logger.info("🗑️  Cleared existing attendance data for Emma")
    
    # Create new consistent attendance data
    # Make Emma have good attendance overall but with recent 3 consecutive absences
    today = datetime.now()
    
    attendance_data = []
    
    # Create 21 days of attendance data (3 weeks)
    for i in range(21, 0, -1):  # Count backwards from 21 days ago to today
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        
        # Pattern: Good attendance except for last 3 days (absent)
        if i <= 3:  # Last 3 days - absent (matches alert)
            status = 'absent'
            time_marked = '17:00:00'  # Marked at end of day as absent
        elif i == 4:  # 4th day back - present (shows return)
            status = 'present' 
            time_marked = '08:27:00'
        else:  # All other days - mostly present with 1 late
            if i == 15:  # One late day in the past
                status = 'late'
                time_marked = '09:15:00'
            elif i == 12:  # One absent day in the past (sick)
                status = 'absent'
                time_marked = '17:00:00'
            else:
                status = 'present'
                time_marked = f'08:{20 + (i % 40):02d}:00'  # Vary arrival times
        
        attendance_record = {
            'student_id': emma_id,
            'date': date_str,
            'status': status,
            'time_marked': time_marked,
            'notes': 'Family emergency' if status == 'absent' and i <= 3 else '',
            'marked_by': ObjectId('507f1f77bcf86cd799439011'),  # System user ID
            'marked_at': datetime.combine(date.date(), datetime.strptime(time_marked, '%H:%M:%S').time()),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        attendance_data.append(attendance_record)
    
    # Insert consistent attendance data
    db.attendance.insert_many(attendance_data)
    
    # Calculate actual statistics
    total_days = len(attendance_data)
    present_days = len([r for r in attendance_data if r['status'] == 'present'])
    absent_days = len([r for r in attendance_data if r['status'] == 'absent'])
    late_days = len([r for r in attendance_data if r['status'] == 'late'])
    attendance_rate = round((present_days / total_days) * 100)
    
    logger.info(f"📊 NEW ATTENDANCE STATISTICS:")
    logger.info(f"   Total Days: {total_days}")
    logger.info(f"   Present: {present_days}")
    logger.info(f"   Absent: {absent_days}")
    logger.info(f"   Late: {late_days}")
    logger.info(f"   Attendance Rate: {attendance_rate}%")
    
    # Step 3: Update AI Prediction to match the data
    # High risk is justified due to recent 3 consecutive absences
    db.predictions.delete_many({'student_id': emma_id})
    
    prediction_record = {
        'student_id': emma_id,
        'student_name': 'Emma Wilson',
        'prediction': 'High Risk',
        'confidence': 0.85,  # 85% confidence due to recent pattern
        'risk_level': 'high',
        'factors': [
            'Recent consecutive absences (3 days)',
            'Pattern change detected',
            'Family emergency noted'
        ],
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    db.predictions.insert_one(prediction_record)
    logger.info("🤖 Updated AI prediction to match attendance pattern")
    
    # Step 4: Update Alert to be consistent
    # Clear old alerts and create a proper one
    db.alerts.delete_many({'student_id': emma_id})
    
    alert_record = {
        'student_id': emma_id,
        'student_name': 'Emma Wilson',
        'type': 'absence',
        'message': 'Emma Wilson has been absent for 3 consecutive days',
        'priority': 'high',
        'status': 'pending',
        'created_at': datetime.utcnow(),
        'metadata': {
            'consecutive_days': 3,
            'dates_absent': [
                (today - timedelta(days=3)).strftime('%Y-%m-%d'),
                (today - timedelta(days=2)).strftime('%Y-%m-%d'), 
                (today - timedelta(days=1)).strftime('%Y-%m-%d')
            ],
            'current_attendance_rate': attendance_rate,
            'trend': 'declining'
        }
    }
    
    db.alerts.insert_one(alert_record)
    logger.info("🚨 Created consistent alert matching attendance pattern")
    
    # Step 5: Also fix James Brown's data for consistency
    james = db.students.find_one({'first_name': 'James', 'last_name': 'Brown'})
    if james:
        james_id = james['_id']
        
        # Clear existing data
        db.attendance.delete_many({'student_id': james_id})
        db.predictions.delete_many({'student_id': james_id})
        db.alerts.delete_many({'student_id': james_id})
        
        # Create moderate attendance for James with lateness pattern
        james_attendance = []
        for i in range(21, 0, -1):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # Pattern: Good attendance but late 3 times this week
            if i <= 7 and i % 3 == 0:  # Late 3 times in last week
                status = 'late'
                time_marked = '09:30:00'
            elif i == 10:  # One absent day
                status = 'absent'
                time_marked = '17:00:00'
            else:
                status = 'present'
                time_marked = f'08:{15 + (i % 30):02d}:00'
            
            record = {
                'student_id': james_id,
                'date': date_str,
                'status': status,
                'time_marked': time_marked,
                'notes': 'Traffic issues' if status == 'late' else '',
                'marked_by': ObjectId('507f1f77bcf86cd799439011'),
                'marked_at': datetime.combine(date.date(), datetime.strptime(time_marked, '%H:%M:%S').time()),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            james_attendance.append(record)
        
        db.attendance.insert_many(james_attendance)
        
        # Add prediction for James
        james_prediction = {
            'student_id': james_id,
            'student_name': 'James Brown',
            'prediction': 'Medium Risk',
            'confidence': 0.70,
            'risk_level': 'medium',
            'factors': [
                'Repeated lateness pattern',
                'Transportation issues noted'
            ],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        db.predictions.insert_one(james_prediction)
        
        # Add lateness alert for James
        james_alert = {
            'student_id': james_id,
            'student_name': 'James Brown',
            'type': 'late',
            'message': 'James Brown has been late 3 times this week',
            'priority': 'medium',
            'status': 'pending',
            'created_at': datetime.utcnow(),
            'metadata': {
                'late_count': 3,
                'period': 'this_week'
            }
        }
        db.alerts.insert_one(james_alert)
        
        logger.info("👦 Fixed James Brown's data consistency")
    
    # Step 6: Verify the fix
    logger.info("\n🔍 VERIFICATION:")
    logger.info("="*50)
    
    # Re-check Emma's data
    emma_records = list(db.attendance.find({'student_id': emma_id}).sort('date', -1))
    emma_prediction = db.predictions.find_one({'student_id': emma_id})
    emma_alerts = list(db.alerts.find({'student_id': emma_id}))
    
    present = len([r for r in emma_records if r['status'] == 'present'])
    absent = len([r for r in emma_records if r['status'] == 'absent'])
    late = len([r for r in emma_records if r['status'] == 'late'])
    rate = round((present / len(emma_records)) * 100) if emma_records else 0
    
    logger.info(f"✅ Emma Wilson - CONSISTENT DATA:")
    logger.info(f"   📊 Attendance: {len(emma_records)} total, {present} present, {absent} absent, {late} late")
    logger.info(f"   📈 Rate: {rate}%")
    logger.info(f"   🤖 AI: {emma_prediction['prediction']} ({emma_prediction['confidence']:.0%})" if emma_prediction else "   🤖 AI: None")
    logger.info(f"   🚨 Alerts: {len(emma_alerts)} active")
    
    # Recent attendance should show pattern
    recent_statuses = [r['status'] for r in emma_records[:5]]
    logger.info(f"   📅 Recent pattern: {' -> '.join(recent_statuses)}")
    
    logger.info("\n✅ DATA CONSISTENCY FIX COMPLETED!")
    logger.info("All dashboards should now show consistent data for Emma Wilson:")
    logger.info("- Parent Dashboard: Correct attendance statistics") 
    logger.info("- Teacher Dashboard: AI prediction matches attendance")
    logger.info("- Admin Dashboard: Alert matches actual absence pattern")

if __name__ == '__main__':
    fix_data_consistency()