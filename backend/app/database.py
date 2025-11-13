"""
MongoDB Database Configuration (Simplified SSL Version for Render)
"""
import os
import logging
import certifi
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


class MongoDB:
    def __init__(self):
        """Initialize MongoDB connection (lazy)"""
        # Suppress pymongo debug logs
        logging.getLogger('pymongo').setLevel(logging.WARNING)
        logging.getLogger('pymongo').disabled = True
        
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

    def _connect_with_retry(self):
        """Attempt to connect with or without TLS depending on environment"""
        try:
            server_timeout = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", 20000))
            insecure = os.getenv("MONGO_INSECURE", "true").lower() in ("1", "true", "yes")

            # Determine whether TLS should be used
            use_tls = self.mongo_url.startswith("mongodb+srv://") or os.getenv("MONGO_TLS", "false").lower() in ("1", "true", "yes")

            client_kwargs = {
                "serverSelectionTimeoutMS": server_timeout,
                "tls": use_tls,
            }

            if use_tls:
                if insecure:
                    client_kwargs.update({
                        "tlsAllowInvalidCertificates": True,
                        "tlsAllowInvalidHostnames": True,
                    })
                else:
                    client_kwargs.update({
                        "tlsCAFile": certifi.where(),
                    })

            self.client = MongoClient(self.mongo_url, **client_kwargs)
            self.db = self.client[self.db_name]
            self.client.admin.command("ping")
            print("✅ Connected to MongoDB!")
            return

        except ServerSelectionTimeoutError as e:
            print(f"❌ MongoDB connection timeout: {e}")
        except Exception as e:
            nested = getattr(e, '__cause__', None) or getattr(e, '__context__', None)
            print(f"❌ Failed to connect to MongoDB: {e}")
            if nested:
                print(f"ℹ️ Nested error: {nested}")

        print("❌ Could not connect to MongoDB.")
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
            return

        try:
            self.users.create_index("email", unique=True)
            self.students.create_index("student_id", unique=True)
            self.students.create_index("email", unique=True)
            self._migrate_attendance_indexes()
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
        except Exception as e:
            if "already exists" not in str(e):
                print(f"⚠️ Could not create attendance indexes: {e}")

    # ---------------------------------------------------------------------

    def check_and_seed_data(self):
        """Check if data exists in database, if not seed it with demo data"""
        if self.db is None:
            return False

        try:
            user_count = self.users.count_documents({})
            if user_count > 0:
                return False

            from app.utils.demo_data import initialize_demo_data

            initialize_demo_data(self.db)
            return True
        except Exception as e:
            print(f"❌ Error checking/seeding data: {e}")
            return False

    # ---------------------------------------------------------------------

    def close_connection(self):
        """Close MongoDB connection"""
        if self.client is not None:
            self.client.close()
