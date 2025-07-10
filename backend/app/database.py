"""
MongoDB Database Configuration (Render + MongoDB Atlas Safe Version)
"""
import os
import time
import certifi
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


class MongoDB:
    def __init__(self):
        """Initialize MongoDB connection (lazy)"""
        self.mongo_url = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.db_name = os.getenv("DB_NAME", "alexander_academy_db")
        self.client = None
        self.db = None

        # Don’t immediately connect — lazy init
        self._connect_with_retry()

        # Initialize collections (safe to reference later)
        if self.db is not None:
            self._init_collections()
            self._create_indexes()

    # ---------------------------------------------------------------------

    def _connect_with_retry(self, retries: int = 5, delay: int = 3):
        """Attempt to connect with retries and SSL fix"""
        for attempt in range(1, retries + 1):
            try:
                # Explicit TLS and CA bundle to prevent SSL handshake errors
                self.client = MongoClient(
                    self.mongo_url,
                    tls=True,
                    tlsCAFile=certifi.where(),
                    serverSelectionTimeoutMS=20000,
                )

                self.db = self.client[self.db_name]
                # Quick ping test
                self.client.admin.command("ping")
                print(f"✅ Connected to MongoDB: {self.db_name}")
                return

            except ServerSelectionTimeoutError as e:
                print(f"⚠️ MongoDB connection timeout (attempt {attempt}/{retries}): {e}")
            except Exception as e:
                print(f"❌ Failed to connect to MongoDB (attempt {attempt}/{retries}): {e}")

            time.sleep(delay)

        print("❌ Could not connect to MongoDB after several attempts.")
        self.client = None
        self.db = None

    # ---------------------------------------------------------------------

    def _init_collections(self):
        """Initialize commonly used collections"""
        self.users = self.db.users
        self.students = self.db.students
        self.classes = self.db.classes
        self.attendance = self.db.attendance
        self.alerts = self.db.alerts
        self.predictions = self.db.predictions
        self.reports = self.db.reports

    # ---------------------------------------------------------------------

    def _create_indexes(self):
        """Create database indexes for better performance"""
        if self.db is None:
            print("⚠️ Skipping index creation: No DB connection.")
            return

        try:
            self.users.create_index("email", unique=True)
            self.students.create_index("student_id", unique=True)
            self.students.create_index("email", unique=True)
            self._migrate_attendance_indexes()
            print("✅ Database indexes created")
        except Exception as e:
            print(f"⚠️ Warning: Could not create indexes: {e}")

    def _migrate_attendance_indexes(self):
        """Create optimized attendance indexes"""
        try:
            self.attendance.create_index(
                [("student_id", 1), ("date", 1)],
                unique=False,
                name="student_date_idx",
                background=True,
            )
            self.attendance.create_index("class_id", background=True)
            print("✅ Attendance indexes created/updated")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"⚠️ Could not create attendance indexes: {e}")

    # ---------------------------------------------------------------------

    def check_and_seed_data(self):
        """Check if data exists in database, if not seed it with demo data"""
        if self.db is None:
            print("⚠️ Cannot seed data: No DB connection.")
            return False

        try:
            user_count = self.users.count_documents({})
            if user_count > 0:
                print("ℹ️ Database already contains data - skipping seed")
                return False

            print("📊 Database is empty - seeding with initial data...")
            from app.utils.demo_data import initialize_demo_data

            initialize_demo_data(self.db)
            print("✅ Database seeded successfully with demo data")
            print("📧 Demo Accounts:")
            print("   Teacher: teacher@alexander.academy / teacher123")
            print("   Admin:   admin@alexander.academy / admin123")
            print("   Parent:  parent@alexander.academy / parent123")
            return True
        except Exception as e:
            print(f"❌ Error checking/seeding data: {e}")
            return False

    # ---------------------------------------------------------------------

    def close_connection(self):
        """Close MongoDB connection"""
        if self.client is not None:
            self.client.close()
            print("🔒 MongoDB connection closed.")
