"""
Sample Data Generator for Intelligent Attendance Register
Generates realistic attendance data for demonstration and ML training
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration
STUDENTS_COUNT = 500
TEACHERS_COUNT = 20
CLASSES_COUNT = 30
DAYS_OF_DATA = 180  # 6 months
SCHOOL_YEAR = "2024-2025"

# Realistic attendance patterns
ATTENDANCE_PROBABILITIES = {
    'present': 0.85,
    'absent': 0.10,
    'late': 0.04,
    'excused': 0.01
}

# Day-of-week patterns (Monday = 0, Sunday = 6)
DAY_PATTERNS = {
    0: 0.82,  # Monday - slightly lower
    1: 0.88,  # Tuesday - normal
    2: 0.90,  # Wednesday - highest
    3: 0.89,  # Thursday - high
    4: 0.84,  # Friday - lower
    5: 0.0,   # Saturday - no school
    6: 0.0    # Sunday - no school
}

# Seasonal patterns
SEASONAL_FACTORS = {
    9: 0.92,   # September - new year enthusiasm
    10: 0.90,  # October - normal
    11: 0.87,  # November - getting tired
    12: 0.85,  # December - holidays approaching
    1: 0.83,   # January - post-holiday blues
    2: 0.88,   # February - recovering
    3: 0.90,   # March - spring energy
    4: 0.87,   # April - spring break
    5: 0.85,   # May - end of year fatigue
    6: 0.83    # June - summer anticipation
}

def generate_students():
    """Generate realistic student data"""
    first_names = [
        'Emma', 'Liam', 'Olivia', 'Noah', 'Ava', 'Ethan', 'Sophia', 'Mason', 'Isabella', 'William',
        'Mia', 'James', 'Charlotte', 'Benjamin', 'Amelia', 'Lucas', 'Emily', 'Henry', 'Abigail', 'Alexander',
        'Harper', 'Michael', 'Evelyn', 'Daniel', 'Elizabeth', 'Jacob', 'Sofia', 'Logan', 'Avery', 'Jackson',
        'Ella', 'Sebastian', 'Madison', 'Jack', 'Scarlett', 'Owen', 'Victoria', 'Samuel', 'Aria', 'Matthew',
        'Grace', 'Leo', 'Chloe', 'Luke', 'Camila', 'David', 'Penelope', 'Wyatt', 'Riley', 'Carter'
    ]
    
    last_names = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
        'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
        'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson',
        'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
        'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell', 'Carter', 'Roberts'
    ]
    
    students = []
    
    for i in range(STUDENTS_COUNT):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        grade = random.choices([9, 10, 11, 12], weights=[0.25, 0.25, 0.25, 0.25])[0]
        
        # Generate birth date based on grade
        birth_year = 2024 - (14 + (12 - grade))
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        
        student = {
            'first_name': first_name,
            'last_name': last_name,
            'student_id': f'AA{str(i + 1).zfill(6)}',
            'grade': grade,
            'date_of_birth': f'{birth_year}-{str(birth_month).zfill(2)}-{str(birth_day).zfill(2)}',
            'email': f'{first_name.lower()}.{last_name.lower()}{str(i + 1)}@student.alexander.edu',
            'phone': f'(604) {random.randint(100, 999)}-{random.randint(1000, 9999)}',
            'parent_email': f'{first_name.lower()}.parent{i + 1}@email.com',
            'parent_phone': f'(604) {random.randint(100, 999)}-{random.randint(1000, 9999)}',
            'address': f'{random.randint(100, 9999)} {random.choice(["Main St", "Oak Ave", "Pine Rd", "Cedar Blvd", "Maple Dr"])}',
            'emergency_contact': f'{first_name.lower()}.emergency{i + 1}@email.com',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            # Assign attendance personality (affects patterns)
            'attendance_personality': random.choices([
                'excellent',    # 90%+ attendance
                'good',         # 85-90% attendance
                'average',      # 80-85% attendance
                'concerning',   # 70-80% attendance
                'poor'          # <70% attendance
            ], weights=[0.3, 0.4, 0.2, 0.08, 0.02])[0]
        }
        
        students.append(student)
    
    return students

def generate_teachers():
    """Generate teacher data"""
    teacher_names = [
        ('Sarah', 'Johnson', 'Mathematics'),
        ('Michael', 'Chen', 'Science'),
        ('Emily', 'Davis', 'English'),
        ('David', 'Wilson', 'History'),
        ('Lisa', 'Anderson', 'French'),
        ('James', 'Brown', 'Physics'),
        ('Maria', 'Garcia', 'Chemistry'),
        ('Robert', 'Miller', 'Biology'),
        ('Jennifer', 'Taylor', 'Art'),
        ('Christopher', 'Moore', 'Physical Education'),
        ('Amanda', 'Jackson', 'Music'),
        ('Daniel', 'White', 'Computer Science'),
        ('Jessica', 'Harris', 'Psychology'),
        ('Matthew', 'Martin', 'Economics'),
        ('Ashley', 'Thompson', 'Geography'),
        ('Andrew', 'Garcia', 'Spanish'),
        ('Nicole', 'Martinez', 'Drama'),
        ('Kevin', 'Robinson', 'Photography'),
        ('Michelle', 'Clark', 'Philosophy'),
        ('Ryan', 'Rodriguez', 'Statistics')
    ]
    
    teachers = []
    
    for i, (first_name, last_name, subject) in enumerate(teacher_names):
        teacher = {
            'first_name': first_name,
            'last_name': last_name,
            'email': f'{first_name.lower()}.{last_name.lower()}@alexander.edu',
            'role': 'teacher',
            'subject': subject,
            'employee_id': f'T{str(i + 1).zfill(3)}',
            'phone': f'(604) {random.randint(100, 999)}-{random.randint(1000, 9999)}',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'school_id': 'alexander_academy'
        }
        
        teachers.append(teacher)
    
    return teachers

def generate_admin_users():
    """Generate admin users"""
    admins = [
        {
            'first_name': 'Alexander',
            'last_name': 'Principal',
            'email': 'admin@alexander.edu',
            'role': 'admin',
            'employee_id': 'A001',
            'phone': '(604) 555-0123',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'school_id': 'alexander_academy'
        },
        {
            'first_name': 'Mary',
            'last_name': 'Secretary',
            'email': 'secretary@alexander.edu',
            'role': 'admin',
            'employee_id': 'A002',
            'phone': '(604) 555-0124',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'school_id': 'alexander_academy'
        }
    ]
    
    return admins

def generate_classes(teachers):
    """Generate class/course data"""
    subjects_and_codes = [
        ('Mathematics', 'MATH', ['Pre-Calculus', 'Calculus', 'Statistics', 'Algebra']),
        ('Science', 'SCI', ['Biology', 'Chemistry', 'Physics', 'Environmental Science']),
        ('English', 'ENG', ['Literature', 'Composition', 'Creative Writing', 'Communications']),
        ('History', 'HIST', ['World History', 'Canadian History', 'European History', 'Modern History']),
        ('Language', 'LANG', ['French', 'Spanish', 'Mandarin', 'German']),
        ('Arts', 'ART', ['Visual Arts', 'Music', 'Drama', 'Photography']),
        ('Physical Education', 'PE', ['PE 9', 'PE 10', 'PE 11', 'PE 12']),
        ('Technology', 'TECH', ['Computer Science', 'Digital Media', 'Robotics', 'Web Design'])
    ]
    
    classes = []
    class_id_counter = 1
    
    for subject_area, code_prefix, course_names in subjects_and_codes:
        # Find teachers for this subject
        subject_teachers = [t for t in teachers if subject_area.lower() in t['subject'].lower()]
        if not subject_teachers:
            subject_teachers = teachers[:3]  # Fallback to first 3 teachers
        
        for grade in [9, 10, 11, 12]:
            course_name = random.choice(course_names)
            teacher = random.choice(subject_teachers)
            
            class_obj = {
                'name': f'{course_name} {grade}',
                'subject': subject_area,
                'class_code': f'{code_prefix}{grade}{str(class_id_counter).zfill(2)}',
                'grade': grade,
                'teacher_id': teacher['_id'] if '_id' in teacher else str(class_id_counter),
                'teacher_name': f"{teacher['first_name']} {teacher['last_name']}",
                'room': f'{random.randint(100, 399)}',
                'max_students': random.randint(20, 30),
                'schedule': {
                    random.choice(['monday', 'tuesday', 'wednesday', 'thursday', 'friday']): 
                        f"{random.randint(8, 15):02d}:{random.choice(['00', '30'])}-{random.randint(9, 16):02d}:{random.choice(['00', '30'])}"
                },
                'school_year': SCHOOL_YEAR,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            classes.append(class_obj)
            class_id_counter += 1
    
    return classes

def assign_students_to_classes(students, classes):
    """Assign students to classes based on their grade"""
    updated_students = []
    
    for student in students:
        grade = student['grade']
        # Find classes for this grade
        grade_classes = [c for c in classes if c['grade'] == grade]
        
        if grade_classes:
            # Assign student to a random class of their grade
            assigned_class = random.choice(grade_classes)
            student['class_id'] = assigned_class.get('_id', str(len(updated_students) % len(grade_classes)))
        
        updated_students.append(student)
    
    return updated_students

def generate_attendance_data(students, classes, days=DAYS_OF_DATA):
    """Generate realistic attendance data"""
    attendance_records = []
    
    # Start date (6 months ago)
    start_date = datetime.now() - timedelta(days=days)
    
    # Create a mapping of students to their assigned classes
    student_class_map = {}
    for student in students:
        if 'class_id' in student:
            student_class_map[student['student_id']] = student['class_id']
    
    # Generate attendance for each day
    current_date = start_date
    
    while current_date <= datetime.now():
        # Skip weekends
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue
        
        # Skip some holidays and breaks
        if is_holiday_or_break(current_date):
            current_date += timedelta(days=1)
            continue
        
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Generate attendance for each student
        for student in students:
            student_id = student['student_id']
            
            if student_id not in student_class_map:
                continue
            
            class_id = student_class_map[student_id]
            
            # Calculate attendance probability based on various factors
            base_probability = get_attendance_probability(student, current_date)
            
            # Determine status based on probability
            status = determine_attendance_status(base_probability, student['attendance_personality'])
            
            # Create attendance record
            record = {
                'student_id': student_id,
                'class_id': class_id,
                'date': date_str,
                'status': status,
                'notes': generate_attendance_notes(status, student['attendance_personality']),
                'marked_by': 'system',  # Will be updated with actual teacher IDs
                'marked_at': current_date.replace(
                    hour=random.randint(8, 10),
                    minute=random.randint(0, 59)
                ),
                'created_at': current_date,
                'updated_at': current_date
            }
            
            attendance_records.append(record)
        
        current_date += timedelta(days=1)
    
    return attendance_records

def is_holiday_or_break(date):
    """Check if date is a holiday or break"""
    holidays = [
        # Thanksgiving (October)
        (10, 14), (10, 15), (10, 16),
        # Christmas break (December)
        (12, 23), (12, 24), (12, 25), (12, 26), (12, 27), (12, 28), (12, 29), (12, 30), (12, 31),
        # New Year
        (1, 1), (1, 2), (1, 3),
        # Spring break (March)
        (3, 18), (3, 19), (3, 20), (3, 21), (3, 22),
        # Good Friday, Easter Monday
        (3, 29), (4, 1),
        # Victoria Day (May)
        (5, 20),
    ]
    
    return (date.month, date.day) in holidays

def get_attendance_probability(student, date):
    """Calculate attendance probability based on multiple factors"""
    # Base probability from day of week
    day_factor = DAY_PATTERNS.get(date.weekday(), 0.85)
    
    # Seasonal factor
    seasonal_factor = SEASONAL_FACTORS.get(date.month, 0.85)
    
    # Student personality factor
    personality_factors = {
        'excellent': 0.95,
        'good': 0.87,
        'average': 0.82,
        'concerning': 0.75,
        'poor': 0.65
    }
    
    personality_factor = personality_factors.get(student['attendance_personality'], 0.85)
    
    # Random variation
    random_factor = random.uniform(0.9, 1.1)
    
    # Combine factors
    probability = day_factor * seasonal_factor * personality_factor * random_factor
    
    return min(1.0, max(0.0, probability))

def determine_attendance_status(probability, personality):
    """Determine attendance status based on probability and personality"""
    if probability >= 0.9:
        return 'present'
    elif probability >= 0.85:
        return random.choices(['present', 'late'], weights=[0.85, 0.15])[0]
    elif probability >= 0.75:
        return random.choices(['present', 'late', 'absent'], weights=[0.7, 0.2, 0.1])[0]
    elif probability >= 0.6:
        return random.choices(['present', 'late', 'absent', 'excused'], weights=[0.6, 0.15, 0.2, 0.05])[0]
    else:
        return random.choices(['present', 'absent', 'excused'], weights=[0.4, 0.5, 0.1])[0]

def generate_attendance_notes(status, personality):
    """Generate realistic notes for attendance records"""
    notes_by_status = {
        'absent': [
            'Sick', 'Family emergency', 'Medical appointment', 'Unexcused absence', 
            'Parent called in sick', 'Flu symptoms', 'Doctor appointment'
        ],
        'late': [
            'Traffic', 'Overslept', 'Family issue', 'Bus was late', 
            'Medical appointment ran late', 'Car trouble'
        ],
        'excused': [
            'Medical appointment', 'Family emergency', 'Bereavement', 
            'Educational trip', 'Court appearance', 'Religious observance'
        ],
        'present': ['']  # Usually no notes for present
    }
    
    status_notes = notes_by_status.get(status, [''])
    
    # Add personality-based note frequency
    if personality in ['poor', 'concerning'] and status == 'absent':
        return random.choice(notes_by_status['absent'])
    elif status != 'present' and random.random() < 0.7:
        return random.choice(status_notes)
    else:
        return ''

def save_to_mongodb(students, teachers, admins, classes, attendance_records):
    """Save all data to MongoDB"""
    try:
        # Connect to MongoDB
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/attendance_db')
        client = MongoClient(mongodb_uri)
        db = client.get_database()
        
        print(f"Connected to MongoDB: {db.name}")
        
        # Clear existing data
        print("Clearing existing data...")
        db.students.delete_many({})
        db.users.delete_many({})
        db.classes.delete_many({})
        db.attendance.delete_many({})
        
        # Insert students
        print(f"Inserting {len(students)} students...")
        student_result = db.students.insert_many(students)
        
        # Update student IDs in the student data for class assignment
        for i, student_id in enumerate(student_result.inserted_ids):
            students[i]['_id'] = student_id
        
        # Insert teachers and admins as users
        all_users = teachers + admins
        print(f"Inserting {len(all_users)} users (teachers and admins)...")
        user_result = db.users.insert_many(all_users)
        
        # Update teacher IDs
        for i, user_id in enumerate(user_result.inserted_ids):
            if i < len(teachers):
                teachers[i]['_id'] = user_id
        
        # Insert classes with correct teacher IDs
        print(f"Inserting {len(classes)} classes...")
        # Update teacher IDs in classes
        teacher_map = {f"{t['first_name']} {t['last_name']}": t['_id'] for t in teachers}
        for class_obj in classes:
            teacher_name = class_obj['teacher_name']
            if teacher_name in teacher_map:
                class_obj['teacher_id'] = str(teacher_map[teacher_name])
        
        class_result = db.classes.insert_many(classes)
        
        # Update class IDs
        for i, class_id in enumerate(class_result.inserted_ids):
            classes[i]['_id'] = class_id
        
        # Update students with correct class IDs
        class_map = {c['class_code']: str(c['_id']) for c in classes}
        students_to_update = []
        
        for student in students:
            grade = student['grade']
            # Find a class for this grade
            grade_classes = [c for c in classes if c['grade'] == grade]
            if grade_classes:
                assigned_class = random.choice(grade_classes)
                student['class_id'] = str(assigned_class['_id'])
                students_to_update.append({
                    'filter': {'_id': student['_id']},
                    'update': {'$set': {'class_id': str(assigned_class['_id'])}}
                })
        
        # Bulk update students with class assignments
        print("Updating student class assignments...")
        for update_op in students_to_update:
            db.students.update_one(update_op['filter'], update_op['update'])
        
        # Update attendance records with correct IDs
        print("Preparing attendance records...")
        student_id_map = {s['student_id']: str(s['_id']) for s in students}
        valid_attendance_records = []
        
        for record in attendance_records:
            if record['student_id'] in student_id_map:
                # Update with MongoDB ObjectId
                record['student_id'] = student_id_map[record['student_id']]
                
                # Find corresponding class
                student_mongo_id = record['student_id']
                student_doc = db.students.find_one({'_id': student_result.inserted_ids[
                    list(student_id_map.values()).index(student_mongo_id)
                ]})
                
                if student_doc and student_doc.get('class_id'):
                    record['class_id'] = student_doc['class_id']
                    valid_attendance_records.append(record)
        
        # Insert attendance records in batches
        print(f"Inserting {len(valid_attendance_records)} attendance records...")
        batch_size = 1000
        for i in range(0, len(valid_attendance_records), batch_size):
            batch = valid_attendance_records[i:i + batch_size]
            db.attendance.insert_many(batch)
            print(f"Inserted batch {i // batch_size + 1}/{(len(valid_attendance_records) + batch_size - 1) // batch_size}")
        
        print("✅ Sample data generated successfully!")
        print(f"📊 Data Summary:")
        print(f"   - Students: {db.students.count_documents({})}")
        print(f"   - Users (Teachers/Admins): {db.users.count_documents({})}")
        print(f"   - Classes: {db.classes.count_documents({})}")
        print(f"   - Attendance Records: {db.attendance.count_documents({})}")
        
        # Generate some basic statistics
        print(f"\n📈 Attendance Statistics:")
        pipeline = [
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        
        stats = list(db.attendance.aggregate(pipeline))
        total_records = sum(stat['count'] for stat in stats)
        
        for stat in stats:
            percentage = (stat['count'] / total_records) * 100
            print(f"   - {stat['_id'].title()}: {stat['count']:,} ({percentage:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving to MongoDB: {e}")
        return False
    
    finally:
        client.close()

def save_to_csv(students, teachers, admins, classes, attendance_records):
    """Save data to CSV files for backup/analysis"""
    try:
        os.makedirs('data', exist_ok=True)
        
        # Save students
        df_students = pd.DataFrame(students)
        df_students.to_csv('data/students.csv', index=False)
        
        # Save users (teachers + admins)
        df_users = pd.DataFrame(teachers + admins)
        df_users.to_csv('data/users.csv', index=False)
        
        # Save classes
        df_classes = pd.DataFrame(classes)
        df_classes.to_csv('data/classes.csv', index=False)
        
        # Save attendance
        df_attendance = pd.DataFrame(attendance_records)
        df_attendance.to_csv('data/attendance_records.csv', index=False)
        
        print("✅ CSV files saved to 'data/' directory")
        
    except Exception as e:
        print(f"❌ Error saving CSV files: {e}")

def main():
    """Main function to generate all sample data"""
    print("🚀 Generating sample data for Alexander Academy Attendance System")
    print("=" * 60)
    
    # Generate data
    print("👥 Generating students...")
    students = generate_students()
    
    print("👨‍🏫 Generating teachers...")
    teachers = generate_teachers()
    
    print("👔 Generating admin users...")
    admins = generate_admin_users()
    
    print("📚 Generating classes...")
    classes = generate_classes(teachers)
    
    print("🎯 Assigning students to classes...")
    students = assign_students_to_classes(students, classes)
    
    print("📋 Generating attendance data...")
    attendance_records = generate_attendance_data(students, classes)
    
    # Save data
    print("\n💾 Saving data...")
    
    # Save to CSV files
    save_to_csv(students, teachers, admins, classes, attendance_records)
    
    # Save to MongoDB
    success = save_to_mongodb(students, teachers, admins, classes, attendance_records)
    
    if success:
        print("\n✨ Sample data generation completed successfully!")
        print("🔑 Default login credentials created:")
        print("   - Admin: admin@alexander.edu / admin123")
        print("   - Teacher: (any teacher email) / teacher123") 
        print("   - Example: sarah.johnson@alexander.edu / teacher123")
    else:
        print("\n⚠️ Sample data generation completed with errors. Check MongoDB connection.")

if __name__ == "__main__":
    main()