# Smart Digital Register

Attendance management system.

## Structure

- `backend/` - Flask API
- `frontend/` - React app
- `ml/` - ML models

## Setup & Run

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## Environment Variables

### Backend (.env)

```env
JWT_SECRET_KEY=your-secret-key-here
MONGODB_URI=memory://demo
FLASK_ENV=development
PORT=5000
```

### Frontend (.env)

```env
REACT_APP_API_URL=http://localhost:5000/api
```
