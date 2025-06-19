"""
ML Model Training for Attendance Prediction
Trains a Random Forest model to predict student absence probability
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import joblib
from pymongo import MongoClient
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set random seed
np.random.seed(42)

class AttendancePredictionModel:
    def __init__(self, mongodb_uri=None):
        """Initialize the model with database connection"""
        self.mongodb_uri = mongodb_uri or os.getenv('MONGODB_URI', 'mongodb://localhost:27017/attendance_db')
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        
    def connect_to_database(self):
        """Connect to MongoDB and return database object"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client.get_database()
            print(f"✅ Connected to MongoDB: {self.db.name}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
    
    def extract_features_from_data(self):
        """Extract and prepare features from the database"""
        try:
            print("📊 Extracting features from attendance data...")
            
            # Get all attendance records
            attendance_records = list(self.db.attendance.find())
            if not attendance_records:
                print("❌ No attendance records found in database")
                return None, None
            
            # Get all students
            students = list(self.db.students.find())
            student_map = {str(student['_id']): student for student in students}
            
            print(f"Found {len(attendance_records)} attendance records for {len(students)} students")
            
            # Convert to DataFrame
            df = pd.DataFrame(attendance_records)
            df['date'] = pd.to_datetime(df['date'])
            df['student_id'] = df['student_id'].astype(str)
            
            # Sort by student and date
            df = df.sort_values(['student_id', 'date'])
            
            # Create binary target (1 = absent, 0 = present/late/excused)
            df['is_absent'] = (df['status'] == 'absent').astype(int)
            
            # Feature engineering
            features_list = []
            
            # Process each student's data
            for student_id, student_data in df.groupby('student_id'):
                if student_id not in student_map:
                    continue
                
                student_info = student_map[student_id]
                student_records = student_data.sort_values('date').reset_index(drop=True)
                
                # Create features for each record (except the first few)
                for i in range(7, len(student_records)):  # Need at least 7 days of history
                    current_record = student_records.iloc[i]
                    history = student_records.iloc[:i]  # All previous records
                    recent_history = student_records.iloc[max(0, i-30):i]  # Last 30 days
                    very_recent = student_records.iloc[max(0, i-7):i]  # Last 7 days
                    
                    # Basic student features
                    features = {
                        'student_id': student_id,
                        'date': current_record['date'],
                        'grade': student_info.get('grade', 10),
                        'day_of_week': current_record['date'].weekday(),
                        'month': current_record['date'].month,
                        'day_of_month': current_record['date'].day,
                        'is_weekend': 1 if current_record['date'].weekday() >= 5 else 0,
                        'is_monday': 1 if current_record['date'].weekday() == 0 else 0,
                        'is_friday': 1 if current_record['date'].weekday() == 4 else 0,
                        
                        # Seasonal features
                        'is_winter': 1 if current_record['date'].month in [12, 1, 2] else 0,
                        'is_spring': 1 if current_record['date'].month in [3, 4, 5] else 0,
                        'is_fall': 1 if current_record['date'].month in [9, 10, 11] else 0,
                    }
                    
                    # Historical attendance features
                    if len(history) > 0:
                        total_history = len(history)
                        present_count = len(history[history['status'] == 'present'])
                        absent_count = len(history[history['status'] == 'absent'])
                        late_count = len(history[history['status'] == 'late'])
                        
                        features.update({
                            'total_history_days': total_history,
                            'historical_attendance_rate': present_count / total_history,
                            'historical_absence_rate': absent_count / total_history,
                            'historical_tardiness_rate': late_count / total_history,
                        })
                    else:
                        features.update({
                            'total_history_days': 0,
                            'historical_attendance_rate': 1.0,
                            'historical_absence_rate': 0.0,
                            'historical_tardiness_rate': 0.0,
                        })
                    
                    # Recent history features (last 30 days)
                    if len(recent_history) > 0:
                        recent_total = len(recent_history)
                        recent_present = len(recent_history[recent_history['status'] == 'present'])
                        recent_absent = len(recent_history[recent_history['status'] == 'absent'])
                        recent_late = len(recent_history[recent_history['status'] == 'late'])
                        
                        features.update({
                            'recent_30d_attendance_rate': recent_present / recent_total,
                            'recent_30d_absence_rate': recent_absent / recent_total,
                            'recent_30d_tardiness_rate': recent_late / recent_total,
                        })
                    else:
                        features.update({
                            'recent_30d_attendance_rate': 1.0,
                            'recent_30d_absence_rate': 0.0,
                            'recent_30d_tardiness_rate': 0.0,
                        })
                    
                    # Very recent features (last 7 days)
                    if len(very_recent) > 0:
                        very_recent_absent = len(very_recent[very_recent['status'] == 'absent'])
                        very_recent_late = len(very_recent[very_recent['status'] == 'late'])
                        
                        # Consecutive absence pattern
                        consecutive_absences = 0
                        for j in range(len(very_recent) - 1, -1, -1):
                            if very_recent.iloc[j]['status'] == 'absent':
                                consecutive_absences += 1
                            else:
                                break
                        
                        features.update({
                            'recent_7d_absence_count': very_recent_absent,
                            'recent_7d_late_count': very_recent_late,
                            'consecutive_absences': consecutive_absences,
                            'recent_7d_absence_rate': very_recent_absent / len(very_recent),
                        })
                    else:
                        features.update({
                            'recent_7d_absence_count': 0,
                            'recent_7d_late_count': 0,
                            'consecutive_absences': 0,
                            'recent_7d_absence_rate': 0.0,
                        })
                    
                    # Target variable
                    features['target'] = current_record['is_absent']
                    
                    features_list.append(features)
            
            # Create final DataFrame
            features_df = pd.DataFrame(features_list)
            
            print(f"✅ Created {len(features_df)} feature records")
            print(f"📈 Target distribution: {features_df['target'].value_counts().to_dict()}")
            
            return features_df
            
        except Exception as e:
            print(f"❌ Error extracting features: {e}")
            return None
    
    def train_model(self, features_df, test_size=0.2, validation_size=0.1):
        """Train the Random Forest model"""
        try:
            print("🤖 Training absence prediction model...")
            
            # Prepare features and target
            feature_columns = [col for col in features_df.columns 
                             if col not in ['student_id', 'date', 'target']]
            
            X = features_df[feature_columns]
            y = features_df['target']
            
            self.feature_names = feature_columns
            print(f"📋 Using {len(feature_columns)} features: {feature_columns}")
            
            # Handle missing values
            imputer = SimpleImputer(strategy='mean')
            X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)
            
            # Split data - ensure temporal ordering
            # Sort by date to maintain temporal consistency
            features_df_sorted = features_df.sort_values('date')
            
            # Use time-based split instead of random split
            total_samples = len(features_df_sorted)
            train_end = int(total_samples * (1 - test_size - validation_size))
            val_end = int(total_samples * (1 - test_size))
            
            train_indices = range(train_end)
            val_indices = range(train_end, val_end)
            test_indices = range(val_end, total_samples)
            
            X_train = X.iloc[train_indices]
            X_val = X.iloc[val_indices]
            X_test = X.iloc[test_indices]
            
            y_train = y.iloc[train_indices]
            y_val = y.iloc[val_indices]
            y_test = y.iloc[test_indices]
            
            print(f"📊 Data split: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")
            print(f"📊 Class distribution in training: {y_train.value_counts().to_dict()}")
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_val_scaled = self.scaler.transform(X_val)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Define model with hyperparameters
            model_params = {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 5,
                'min_samples_leaf': 2,
                'random_state': 42,
                'class_weight': 'balanced',  # Handle class imbalance
                'n_jobs': -1
            }
            
            # Train Random Forest
            self.model = RandomForestClassifier(**model_params)
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate on validation set
            val_pred = self.model.predict(X_val_scaled)
            val_pred_proba = self.model.predict_proba(X_val_scaled)[:, 1]
            
            print("\\n📊 Validation Set Performance:")
            print(classification_report(y_val, val_pred))
            
            # Calculate AUC if we have both classes
            if len(np.unique(y_val)) > 1:
                val_auc = roc_auc_score(y_val, val_pred_proba)
                print(f"🎯 Validation AUC: {val_auc:.4f}")
            
            # Test set evaluation
            test_pred = self.model.predict(X_test_scaled)
            test_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
            
            print("\\n📊 Test Set Performance:")
            print(classification_report(y_test, test_pred))
            
            if len(np.unique(y_test)) > 1:
                test_auc = roc_auc_score(y_test, test_pred_proba)
                print(f"🎯 Test AUC: {test_auc:.4f}")
            
            # Feature importance
            feature_importance = pd.DataFrame({
                'feature': feature_columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print("\\n🔍 Top 10 Most Important Features:")
            print(feature_importance.head(10).to_string(index=False))
            
            # Cross-validation
            cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5, scoring='roc_auc')
            print(f"\\n🔄 Cross-validation AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
            
            # Save feature importance plot
            self.plot_feature_importance(feature_importance)
            
            return {
                'train_score': self.model.score(X_train_scaled, y_train),
                'val_score': self.model.score(X_val_scaled, y_val),
                'test_score': self.model.score(X_test_scaled, y_test),
                'val_auc': val_auc if len(np.unique(y_val)) > 1 else None,
                'test_auc': test_auc if len(np.unique(y_test)) > 1 else None,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'feature_importance': feature_importance
            }
            
        except Exception as e:
            print(f"❌ Error training model: {e}")
            return None
    
    def plot_feature_importance(self, feature_importance, top_n=15):
        """Plot feature importance"""
        try:
            plt.figure(figsize=(12, 8))
            top_features = feature_importance.head(top_n)
            
            sns.barplot(data=top_features, y='feature', x='importance')
            plt.title(f'Top {top_n} Feature Importances - Absence Prediction Model')
            plt.xlabel('Importance')
            plt.ylabel('Features')
            plt.tight_layout()
            
            # Save plot
            os.makedirs('models', exist_ok=True)
            plt.savefig('models/feature_importance.png', dpi=300, bbox_inches='tight')
            print("💾 Feature importance plot saved to models/feature_importance.png")
            
            plt.close()
            
        except Exception as e:
            print(f"⚠️ Could not save feature importance plot: {e}")
    
    def save_model(self, model_path='models/absence_predictor.pkl'):
        """Save the trained model and scaler"""
        try:
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            model_package = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'trained_at': datetime.now().isoformat(),
                'model_type': 'RandomForestClassifier'
            }
            
            joblib.dump(model_package, model_path)
            print(f"💾 Model saved to {model_path}")
            
            # Save metadata
            metadata_path = model_path.replace('.pkl', '_metadata.json')
            metadata = {
                'trained_at': datetime.now().isoformat(),
                'model_type': 'RandomForestClassifier',
                'features': self.feature_names,
                'feature_count': len(self.feature_names) if self.feature_names else 0
            }
            
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"📋 Model metadata saved to {metadata_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving model: {e}")
            return False
    
    def load_model(self, model_path='models/absence_predictor.pkl'):
        """Load a trained model"""
        try:
            if not os.path.exists(model_path):
                print(f"❌ Model file not found: {model_path}")
                return False
            
            model_package = joblib.load(model_path)
            self.model = model_package['model']
            self.scaler = model_package['scaler']
            self.feature_names = model_package['feature_names']
            
            print(f"✅ Model loaded from {model_path}")
            print(f"📋 Model trained at: {model_package.get('trained_at', 'Unknown')}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def predict_absence_probability(self, student_features):
        """Predict absence probability for a student"""
        try:
            if self.model is None:
                raise ValueError("Model not trained or loaded")
            
            # Prepare features in the correct order
            feature_vector = []
            for feature_name in self.feature_names:
                feature_vector.append(student_features.get(feature_name, 0))
            
            # Scale features
            feature_vector = np.array(feature_vector).reshape(1, -1)
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # Get probability
            probability = self.model.predict_proba(feature_vector_scaled)[0][1]
            
            return float(probability)
            
        except Exception as e:
            print(f"❌ Error predicting: {e}")
            return None

def main():
    """Main training function"""
    print("🚀 Starting ML Model Training for Attendance Prediction")
    print("=" * 60)
    
    # Initialize model trainer
    trainer = AttendancePredictionModel()
    
    # Connect to database
    if not trainer.connect_to_database():
        print("❌ Cannot proceed without database connection")
        return
    
    # Extract features
    features_df = trainer.extract_features_from_data()
    if features_df is None:
        print("❌ Failed to extract features")
        return
    
    # Check if we have enough data
    if len(features_df) < 100:
        print(f"⚠️ Limited data available ({len(features_df)} records). Consider generating more sample data.")
        print("💡 Run: python generate_sample_data.py")
        
    # Train model
    results = trainer.train_model(features_df)
    if results is None:
        print("❌ Model training failed")
        return
    
    # Save model
    if trainer.save_model():
        print("✅ Model training completed successfully!")
        
        print(f"\\n📊 Model Performance Summary:")
        print(f"   - Training Accuracy: {results['train_score']:.4f}")
        print(f"   - Validation Accuracy: {results['val_score']:.4f}")
        print(f"   - Test Accuracy: {results['test_score']:.4f}")
        
        if results['test_auc']:
            print(f"   - Test AUC: {results['test_auc']:.4f}")
        
        print(f"   - Cross-validation AUC: {results['cv_mean']:.4f} (+/- {results['cv_std']*2:.4f})")
        
        print(f"\\n🎯 Model is ready for deployment!")
        print(f"📁 Model files saved in 'models/' directory")
        
    else:
        print("❌ Failed to save model")
    
    # Close database connection
    trainer.client.close()

if __name__ == "__main__":
    main()