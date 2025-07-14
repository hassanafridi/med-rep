import hashlib
import logging
import secrets
import string
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError

class UserAuth:
    """User authentication and management, backed by MongoDB only"""

    def __init__(self, db_source):
        """
        db_source: either
          - a MongoDB instance (your MongoDB class)
          - a MongoAdapter instance
        """
        # Determine the type of db_source and set up accordingly
        if hasattr(db_source, 'mongo_db'):
            # MONGO ADAPTER MODE
            self.mongo_adapter = db_source
            self.db_source_type = 'adapter'
        else:
            # DIRECT MONGO MODE  
            self.mongo_db = db_source
            self.db_source_type = 'direct'
        
        self._init_mongo()

    def _init_mongo(self):
        """Create the users collection with unique username index."""
        try:
            # Get the collection based on source type
            if self.db_source_type == 'adapter':
                # Ensure adapter is connected
                if not self.mongo_adapter.connect():
                    logging.error("Failed to connect MongoAdapter")
                    return False
                
                # Check if db attribute exists after connection
                if not hasattr(self.mongo_adapter, 'db') or self.mongo_adapter.db is None:
                    logging.error("MongoAdapter.db is not available after connection")
                    return False
                    
                coll = self.mongo_adapter.db.users
            else:
                # Direct MongoDB instance
                if not self.mongo_db.connect():
                    logging.error("Failed to connect MongoDB directly")
                    return False
                    
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
                logging.info("Created default admin user")
                
            return True
            
        except Exception as e:
            logging.error(f"Mongo user-init error: {e}")
            return False

    def _generate_salt(self, length=16):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def _hash_password(self, password, salt):
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def authenticate(self, username, password, validate_only=False):
        """Authenticate user with username and password
        
        Args:
            username: The username
            password: The password (can be None if validate_only=True)
            validate_only: If True, only check if user exists without password verification
        
        Returns:
            tuple: (success: bool, result: dict or error message)
        """
        if not username:
            return False, "Username is required"
        
        if not validate_only and not password:
            return False, "Password is required"
        
        try:
            return self._auth_mongodb(username, password, validate_only)
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return False, str(e)
    
    def add_user(self, username, password, full_name, role='user'):
        return self._add_mongo(username, password, full_name, role)

    def get_users(self):
        return self._get_mongo()

    def delete_user(self, user_id):
        return self._del_mongo(user_id)

    def _auth_mongodb(self, username, password, validate_only=False):
        """Authenticate against MongoDB"""
        try:
            # Get the collection based on source type
            if self.db_source_type == 'adapter':
                if not hasattr(self.mongo_adapter, 'db') or self.mongo_adapter.db is None:
                    return False, "Database not available"
                coll = self.mongo_adapter.db.users
            else:
                if not hasattr(self.mongo_db, 'db') or self.mongo_db.db is None:
                    return False, "Database not available"
                coll = self.mongo_db.db.users
            
            user = coll.find_one({"username": username})
            if not user:
                return False, "Invalid username or password"
            
            if validate_only:
                # Just return user info without password verification
                return True, {
                    "user_id": str(user.get("_id")),
                    "username": user.get("username"),
                    "role": user.get("role", "user")
                }
            
            stored_hash = user.get("password_hash")
            salt = user.get("salt")
            
            if not stored_hash or not salt:
                return False, "Invalid user data"
            
            if self._hash_password(password, salt) != stored_hash:
                return False, "Invalid username or password"
            
            # Update last login
            coll.update_one(
                {"username": username},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )
            
            return True, {
                "user_id": str(user.get("_id")),
                "username": user.get("username"),
                "role": user.get("role", "user")
            }
            
        except Exception as e:
            logging.error(f"MongoDB auth error: {e}")
            return False, str(e)

    def _add_mongo(self, username, password, full_name, role):
        try:
            # Get the collection based on source type
            if self.db_source_type == 'adapter':
                coll = self.mongo_adapter.db.users
            else:
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

    def _get_mongo(self):
        try:
            # Get the collection based on source type
            if self.db_source_type == 'adapter':
                coll = self.mongo_adapter.db.users
            else:
                coll = self.mongo_db.db.users
                
            docs = list(coll.find({}, {
                "username":1,"full_name":1,"role":1,"created_at":1,"last_login":1
            }))
            # convert ObjectId→str
            for d in docs:
                d["id"] = str(d.pop("_id"))
            return docs
        except Exception as e:
            logging.error(f"Error getting users: {e}")
            return []

    def _del_mongo(self, user_id):
        try:
            # Get the collection based on source type
            if self.db_source_type == 'adapter':
                coll = self.mongo_adapter.db.users
            else:
                coll = self.mongo_db.db.users
                
            # Prevent deletion of last admin
            admin_count = coll.count_documents({"role": "admin"})
            user = coll.find_one({"_id": user_id})
            
            if user and user.get("role") == "admin" and admin_count <= 1:
                return False, "Cannot delete the last admin user"
            
            result = coll.delete_one({"_id": user_id})
            if result.deleted_count > 0:
                return True, "User deleted successfully"
            else:
                return False, "User not found"
        except Exception as e:
            logging.error(f"Error deleting user: {e}")
            return False, str(e)

    def test_connection(self):
        """Test the MongoDB connection"""
        try:
            if self.db_source_type == 'adapter':
                # Test adapter connection
                if not self.mongo_adapter.connect():
                    return False
                
                if not hasattr(self.mongo_adapter, 'db') or self.mongo_adapter.db is None:
                    return False
                    
                # Test by trying to access the database
                self.mongo_adapter.db.users.find_one()
                return True
            else:
                # Test direct MongoDB
                if not self.mongo_db.connect():
                    return False
                    
                # Test by trying to access the database
                self.mongo_db.db.users.find_one()
                return True
                
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return False
