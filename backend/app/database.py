"""
MongoDB Database Configuration (Render + MongoDB Atlas Safe Version)
"""
import os
import time
import ssl
import certifi
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError
import logging
import traceback


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
                # TLS/SSL diagnostic info
                try:
                    openssl = ssl.OPENSSL_VERSION
                except Exception:
                    openssl = "<unknown OpenSSL version>"

                print(f"ℹ️ TLS/SSL Diagnostics: OpenSSL={openssl}")

                # Build client kwargs
                client_kwargs = {
                    "serverSelectionTimeoutMS": int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", 20000)),
                }

                # Use certifi bundle to create a proper SSLContext to avoid CA/hostname issues
                try:
                    ca_file = certifi.where()
                    # Build a secure SSLContext
                    context = ssl.create_default_context(cafile=ca_file)
                    # Ensure minimum TLS v1.2
                    try:
                        context.minimum_version = ssl.TLSVersion.TLSv1_2
                    except Exception:
                        # Older Python may not have TLSVersion; ignore
                        pass

                    # Allow developer to bypass certificate verification for local testing only
                    if os.getenv("MONGO_TLS_INSECURE", "false").lower() in ("1", "true", "yes"):
                        print("⚠️ WARNING: MONGO_TLS_INSECURE enabled - certificate verification will be skipped. Do NOT use in production.")
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE

                    # Pass both modern tls flags and the ssl_context for maximum compatibility
                    client_kwargs.update({
                        "tls": True,
                        "tlsCAFile": ca_file,
                        "ssl": True,
                        "ssl_context": context,
                    })
                except Exception as ex:
                    # If certifi/ssl context creation fails, fallback to simple tls flags
                    print(f"⚠️ Could not create SSLContext with certifi: {ex}")
                    client_kwargs.update({"tls": True, "ssl": True})

                # If MONGO_TLS_INSECURE set but context creation failed above, set allow invalid certificates
                if os.getenv("MONGO_TLS_INSECURE", "false").lower() in ("1", "true", "yes"):
                    client_kwargs["tlsAllowInvalidCertificates"] = True
                    try:
                        client_kwargs["ssl_cert_reqs"] = ssl.CERT_NONE
                    except Exception:
                        pass

                # Enable verbose pymongo logging to help diagnose TLS handshakes in deploy logs
                try:
                    logging.getLogger('pymongo').setLevel(logging.DEBUG)
                    logging.getLogger('pymongo').addHandler(logging.StreamHandler())
                except Exception:
                    pass

                # Print safe diagnostic (don't print the full URI which may contain credentials)
                safe_host = self.mongo_url.split('@')[-1] if '@' in self.mongo_url else self.mongo_url
                print(f"ℹ️ Attempting MongoClient connection to: {safe_host}")

                # Try creating MongoClient; if the installed pymongo doesn't accept ssl_context
                # fallback by removing it and retrying once.
                try:
                    self.client = MongoClient(self.mongo_url, **client_kwargs)
                except ConfigurationError as ce:
                    msg = str(ce)
                    print(f"⚠️ ConfigurationError when creating MongoClient: {msg}")
                    # If ssl_context was the problem, remove it and retry
                    if 'ssl_context' in client_kwargs:
                        print("ℹ️ Retrying MongoClient without 'ssl_context' for compatibility with this pymongo version")
                        client_kwargs.pop('ssl_context', None)
                        try:
                            self.client = MongoClient(self.mongo_url, **client_kwargs)
                        except Exception:
                            print("❌ Retry without ssl_context failed:")
                            traceback.print_exc()
                            raise
                    else:
                        # Not caused by ssl_context — re-raise for outer handler
                        raise
                except Exception as ce:
                    # Print traceback to logs for better debugging of TLS errors
                    print("❌ Exception creating MongoClient:")
                    traceback.print_exc()
                    raise
                self.db = self.client[self.db_name]

                # Quick ping test
                self.client.admin.command("ping")
                print(f"✅ Connected to MongoDB: {self.db_name}")
                return

            except ServerSelectionTimeoutError as e:
                # Common for Atlas TLS issues
                print(f"⚠️ MongoDB connection timeout (attempt {attempt}/{retries}): {e}")
                print("ℹ️ Tip: If this is an SSL/TLS handshake error, try setting MONGO_TLS_INSECURE=true for a temporary non-production workaround or update your Python/OpenSSL installation.")
            except Exception as e:
                nested = getattr(e, '__cause__', None) or getattr(e, '__context__', None)
                print(f"❌ Failed to connect to MongoDB (attempt {attempt}/{retries}): {e}")
                if nested:
                    print(f"ℹ️ Nested error: {nested}")

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
