"""
WSGI entry point for production deployment
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import the Flask app
from main import app

if __name__ == "__main__":
    app.run()
