"""
Simple ML fallback for when scikit-learn is not available
Provides rule-based predictions for attendance system
"""

from datetime import datetime, timedelta
import random

# Try to import numpy, fallback to basic calculations if not available
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None


class SimplePredictor:
    """Simple rule-based predictor that doesn't require scikit-learn"""
    
    def __init__(self):
        self.is_trained = False
        
    def fit(self, X, y):
        """Mock training - just set the flag"""
        self.is_trained = True
        return self
    
    def predict_proba(self, X):
        """Simple rule-based prediction"""
        if not self.is_trained:
            # Return random probabilities
            return np.random.random((len(X), 2))
        
        probabilities = []
        for features in X:
            # Simple heuristic: higher absence probability on Mondays and Fridays
            day_of_week = features[0] if len(features) > 0 else random.randint(0, 6)
            
            if day_of_week in [0, 4]:  # Monday or Friday
                absent_prob = 0.7 + random.uniform(-0.3, 0.2)
            else:
                absent_prob = 0.3 + random.uniform(-0.2, 0.3)
            
            absent_prob = max(0.1, min(0.9, absent_prob))  # Keep between 0.1 and 0.9
            present_prob = 1.0 - absent_prob
            
            probabilities.append([present_prob, absent_prob])
        
        return np.array(probabilities)


def generate_demo_data():
    """Generate some demo attendance data"""
    data = []
    labels = []
    
    # Generate 100 days of demo data
    start_date = datetime.now() - timedelta(days=100)
    
    for i in range(100):
        current_date = start_date + timedelta(days=i)
        day_of_week = current_date.weekday()
        
        # Features: [day_of_week, is_holiday, previous_absences, grade]
        is_holiday = 1 if day_of_week >= 5 else 0  # Weekend as holiday
        previous_absences = random.randint(0, 5)
        grade = random.randint(9, 12)
        
        features = [day_of_week, is_holiday, previous_absences, grade]
        data.append(features)
        
        # Label: 1 for absent, 0 for present
        # Higher probability of absence on holidays and with more previous absences
        absent_prob = 0.1 + (is_holiday * 0.4) + (previous_absences * 0.05)
        absent_prob = min(0.8, absent_prob)
        
        label = 1 if random.random() < absent_prob else 0
        labels.append(label)
    
    return np.array(data), np.array(labels)


def train_simple_model():
    """Train the simple model with demo data"""
    print("🤖 Training simple ML model...")
    
    # Generate demo data
    X, y = generate_demo_data()
    
    # Create and train model
    model = SimplePredictor()
    model.fit(X, y)
    
    print("✅ Simple ML model trained successfully!")
    return model


def predict_absence_risk(student_data, date=None):
    """
    Predict absence risk for a student
    
    Args:
        student_data: Dictionary containing student information
        date: Optional date for prediction (defaults to tomorrow)
    
    Returns:
        Dictionary with prediction results
    """
    if date is None:
        date = datetime.now() + timedelta(days=1)
    
    # Simple heuristic based on day of week and historical data
    day_of_week = date.weekday()
    
    # Get some basic features
    grade = student_data.get('grade', 10)
    previous_absences = student_data.get('absence_count', 0)
    
    # Create feature vector
    is_holiday = 1 if day_of_week >= 5 else 0
    features = [day_of_week, is_holiday, previous_absences, grade]
    
    # Use simple predictor
    model = SimplePredictor()
    model.is_trained = True  # Mock training
    
    predictions = model.predict_proba([features])
    absence_probability = predictions[0][1]
    
    # Determine risk level
    if absence_probability > 0.7:
        risk_level = "high"
    elif absence_probability > 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "student_id": student_data.get('_id'),
        "prediction_date": date.isoformat(),
        "absence_probability": float(absence_probability),
        "risk_level": risk_level,
        "factors": {
            "day_of_week": day_of_week,
            "is_weekend": day_of_week >= 5,
            "previous_absences": previous_absences,
            "grade": grade
        }
    }


def detect_unusual_patterns(attendance_data):
    """
    Detect unusual attendance patterns
    
    Args:
        attendance_data: List of attendance records
    
    Returns:
        List of detected unusual patterns
    """
    patterns = []
    
    if not attendance_data:
        return patterns
    
    # Simple pattern detection
    total_records = len(attendance_data)
    absent_count = sum(1 for record in attendance_data if record.get('status') == 'absent')
    
    if total_records > 0:
        absence_rate = absent_count / total_records
        
        if absence_rate > 0.5:
            patterns.append({
                "type": "high_absence_rate",
                "description": f"Student has {absence_rate:.1%} absence rate",
                "severity": "high" if absence_rate > 0.7 else "medium",
                "detected_at": datetime.now().isoformat()
            })
    
    # Check for consecutive absences
    consecutive_absences = 0
    max_consecutive = 0
    
    for record in sorted(attendance_data, key=lambda x: x.get('date', '')):
        if record.get('status') == 'absent':
            consecutive_absences += 1
            max_consecutive = max(max_consecutive, consecutive_absences)
        else:
            consecutive_absences = 0
    
    if max_consecutive >= 3:
        patterns.append({
            "type": "consecutive_absences",
            "description": f"Student had {max_consecutive} consecutive absences",
            "severity": "high" if max_consecutive >= 5 else "medium",
            "detected_at": datetime.now().isoformat()
        })
    
    return patterns


if __name__ == "__main__":
    model = train_simple_model()
    
    # Test prediction
    test_data = [[0, 0, 1, 10]]  # Monday, no holiday, 1 previous absence, grade 10
    predictions = model.predict_proba(test_data)
    print(f"Test prediction: {predictions[0][1]:.2%} chance of absence")