import hashlib
import logging
import secrets
import string
import sqlite3
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError

class UserAuth:
    """User authentication and management, backed by SQLite OR MongoDB"""

    def __init__(self, db_source):
        """
        db_source: either
          - a string path to your SQLite file
          - a MongoDB instance (your MongoDB class)
        """
        # Detect mode
        self.use_sqlite = isinstance(db_source, str)

        if self.use_sqlite:
            # SQLITE MODE
            self.db_path = db_source
            self._init_sqlite()
        else:
            # MONGO MODE
            self.mongo_db = db_source
            self._init_mongo()

    #
    # --- Initialization branches ---
    #
    def _init_sqlite(self):
        """Create the users table if it doesn’t exist, and seed admin."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  salt TEXT NOT NULL,
                  full_name TEXT,
                  role TEXT NOT NULL DEFAULT 'user',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_login TIMESTAMP
                )
            """)
            # seed admin
            c.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
            if c.fetchone()[0] == 0:
                salt = self._generate_salt()
                pw_hash = self._hash_password('admin', salt)
                c.execute(
                  "INSERT INTO users (username, password_hash, salt, full_name, role) VALUES (?, ?, ?, ?, 'admin')",
                  ('admin', pw_hash, salt, 'Administrator')
                )
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"SQLite user-init error: {e}")

    def _init_mongo(self):
        """Create the users collection with unique username index."""
        try:
            coll = self.mongo_db.db.users
            # ensure unique index on username
            coll.create_index("username", unique=True)
            # seed admin if missing
            if coll.count_documents({"username": "admin"}) == 0:
                salt = self._generate_salt()
                pw_hash = self._hash_password('admin', salt)
                coll.insert_one({
                    "username":      "admin",
                    "password_hash": pw_hash,
                    "salt":          salt,
                    "full_name":     "Administrator",
                    "role":          "admin",
                    "created_at":    datetime.now(timezone.utc),
                    "last_login":    None
                })
        except Exception as e:
            logging.error(f"Mongo user-init error: {e}")

    #
    # --- Common utilities ---
    #
    def _generate_salt(self, length=16):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def _hash_password(self, password, salt):
        return hashlib.sha256((password + salt).encode()).hexdigest()

    #
    # --- Public interface ---
    #
    def authenticate(self, username, password):
        """Return (True, user_info) or (False, error_msg)."""
        if self.use_sqlite:
            return self._auth_sqlite(username, password)
        else:
            return self._auth_mongo(username, password)

    def add_user(self, username, password, full_name, role='user'):
        if self.use_sqlite:
            return self._add_sqlite(username, password, full_name, role)
        else:
            return self._add_mongo(username, password, full_name, role)

    def change_password(self, user_id, current_password, new_password):
        if self.use_sqlite:
            return self._chg_sqlite(user_id, current_password, new_password)
        else:
            return self._chg_mongo(user_id, current_password, new_password)

    def get_users(self):
        if self.use_sqlite:
            return self._get_sqlite()
        else:
            return self._get_mongo()

    def delete_user(self, user_id):
        if self.use_sqlite:
            return self._del_sqlite(user_id)
        else:
            return self._del_mongo(user_id)

    #
    # --- SQLite implementations ---
    #
    def _auth_sqlite(self, username, password):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT id,password_hash,salt,role FROM users WHERE username=?", (username,))
            row = c.fetchone()
            if not row:
                return False, "Invalid username or password"
            uid, stored, salt, role = row
            if self._hash_password(password, salt) != stored:
                return False, "Invalid username or password"
            c.execute("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?", (uid,))
            conn.commit()
            conn.close()
            return True, {"user_id": uid, "username": username, "role": role}
        except Exception as e:
            logging.error(f"SQLite auth error: {e}")
            return False, str(e)

    def _add_sqlite(self, username, password, full_name, role):
        try:
            salt = self._generate_salt()
            pw_hash = self._hash_password(password, salt)
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                "INSERT INTO users (username,password_hash,salt,full_name,role) VALUES (?,?,?,?,?)",
                (username, pw_hash, salt, full_name, role)
            )
            conn.commit()
            conn.close()
            return True, "User added successfully"
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        except Exception as e:
            logging.error(f"SQLite add_user error: {e}")
            return False, str(e)

    def _chg_sqlite(self, user_id, current, new):
        # same as your existing logic under change_password()
        # …

        # For brevity, you’d just copy/paste your existing method here.
        pass

    def _get_sqlite(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id,username,full_name,role,created_at,last_login FROM users")
        rows = c.fetchall()
        conn.close()
        return rows

    def _del_sqlite(self, user_id):
        # your delete_user() logic here…
        pass

    #
    # --- Mongo implementations ---
    #
    def _auth_mongo(self, username, password):
        try:
            coll = self.mongo_db.db.users
            doc = coll.find_one({"username": username})
            if not doc:
                return False, "Invalid username or password"
            if self._hash_password(password, doc["salt"]) != doc["password_hash"]:
                return False, "Invalid username or password"
            coll.update_one(
                {"_id": doc["_id"]},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )
            return True, {
                "user_id": str(doc["_id"]),
                "username": doc["username"],
                "role":     doc["role"]
            }
        except Exception as e:
            logging.error(f"Mongo auth error: {e}")
            return False, str(e)

    def _add_mongo(self, username, password, full_name, role):
        try:
            coll = self.mongo_db.db.users
            salt = self._generate_salt()
            pw_hash = self._hash_password(password, salt)
            coll.insert_one({
                "username":      username,
                "password_hash": pw_hash,
                "salt":          salt,
                "full_name":     full_name,
                "role":          role,
                "created_at":    datetime.now(timezone.utc),
                "last_login":    None
            })
            return True, "User added successfully"
        except DuplicateKeyError:
            return False, "Username already exists"
        except Exception as e:
            logging.error(f"Mongo add_user error: {e}")
            return False, str(e)

    def _chg_mongo(self, user_id, current, new):
        # implement the same flow as your sqlite version, but using find_one/​update_one
        pass

    def _get_mongo(self):
        coll = self.mongo_db.db.users
        docs = list(coll.find({}, {
            "username":1,"full_name":1,"role":1,"created_at":1,"last_login":1
        }))
        # convert ObjectId→str
        for d in docs:
            d["id"] = str(d.pop("_id"))
        return docs

    def _del_mongo(self, user_id):
        # same guard logic against last-admin, but via count_documents + delete_one
        pass
