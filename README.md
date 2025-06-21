# 🎓 Smart Digital Register

An intelligent attendance management system for Alexander Academy with ML-powered predictions and automated alerts.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- MongoDB (optional - uses in-memory DB by default)

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm start
```

### 3. Default Login

- **Admin**: admin@alexander.academy / admin123
- **Teacher**: Any teacher email / teacher123
- **Parent**: Any parent email / parent123

## 📁 Project Structure

```
├── backend/          # Flask API server
├── frontend/         # React web application
├── ml/              # Machine learning models & training
├── scripts/         # Utility scripts
└── README.md
```

## ⚙️ Configuration

Create `.env` files:

**Backend** (.env):

```env
JWT_SECRET_KEY=your-secret-key-here
MONGODB_URI=mongodb://localhost:27017/attendance_db
FLASK_ENV=development
PORT=5000
```

**Frontend** (.env):

```env
REACT_APP_API_URL=http://localhost:5000/api
```

## 🔧 Scripts

- `scripts/fix_data_consistency.py` - Fix database inconsistencies
- `ml/train_model.py` - Train ML prediction models
- `ml/generate_sample_data.py` - Generate demo data
