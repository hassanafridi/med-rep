import hashlib
import os
import sqlite3
import logging
import secrets
import string

class UserAuth:
    """User authentication and management"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_user_table()
    
    def init_user_table(self):
        """Initialize the user table if it doesn't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
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
            ''')
            
            # Check if admin user exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            count = cursor.fetchone()[0]
            
            # Create default admin user if needed
            if count == 0:
                # Generate random salt
                salt = self.generate_salt()
                
                # Default password is 'admin'
                password_hash = self.hash_password('admin', salt)
                
                cursor.execute(
                    "INSERT INTO users (username, password_hash, salt, full_name, role) VALUES (?, ?, ?, ?, ?)",
                    ('admin', password_hash, salt, 'Administrator', 'admin')
                )
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize user table: {e}")
            return False
    
    def generate_salt(self, length=16):
        """Generate a random salt for password hashing"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def hash_password(self, password, salt):
        """Hash a password with salt using SHA-256"""
        salted_password = password + salt
        return hashlib.sha256(salted_password.encode()).hexdigest()
    
    def authenticate(self, username, password):
        """Authenticate a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user information
            cursor.execute(
                "SELECT id, password_hash, salt, role FROM users WHERE username = ?",
                (username,)
            )
            
            user = cursor.fetchone()
            
            if not user:
                return False, "Invalid username or password"
            
            user_id, stored_hash, salt, role = user
            
            # Hash the provided password with the stored salt
            password_hash = self.hash_password(password, salt)
            
            # Check if password matches
            if password_hash != stored_hash:
                return False, "Invalid username or password"
            
            # Update last login time
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            
            conn.commit()
            conn.close()
            
            return True, {
                'user_id': user_id,
                'username': username,
                'role': role
            }
            
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return False, str(e)
    
    def add_user(self, username, password, full_name, role='user'):
        """Add a new user"""
        try:
            # Generate salt
            salt = self.generate_salt()
            
            # Hash password
            password_hash = self.hash_password(password, salt)
            
            # Add user to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt, full_name, role) VALUES (?, ?, ?, ?, ?)",
                (username, password_hash, salt, full_name, role)
            )
            
            conn.commit()
            conn.close()
            
            return True, "User added successfully"
            
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        except Exception as e:
            logging.error(f"Add user error: {e}")
            return False, str(e)
    
    def change_password(self, user_id, current_password, new_password):
        """Change a user's password"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current password hash and salt
            cursor.execute(
                "SELECT password_hash, salt FROM users WHERE id = ?",
                (user_id,)
            )
            
            result = cursor.fetchone()
            
            if not result:
                return False, "User not found"
            
            stored_hash, salt = result
            
            # Verify current password
            current_hash = self.hash_password(current_password, salt)
            if current_hash != stored_hash:
                return False, "Current password is incorrect"
            
            # Generate new salt and hash
            new_salt = self.generate_salt()
            new_hash = self.hash_password(new_password, new_salt)
            
            # Update password
            cursor.execute(
                "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                (new_hash, new_salt, user_id)
            )
            
            conn.commit()
            conn.close()
            
            return True, "Password changed successfully"
            
        except Exception as e:
            logging.error(f"Change password error: {e}")
            return False, str(e)
    
    def get_users(self):
        """Get all users"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, username, full_name, role, created_at, last_login FROM users"
            )
            
            users = cursor.fetchall()
            
            conn.close()
            
            return users
            
        except Exception as e:
            logging.error(f"Get users error: {e}")
            return []
    
    def delete_user(self, user_id):
        """Delete a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user is admin
            cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
            role = cursor.fetchone()[0]
            
            if role == 'admin':
                # Check if this is the last admin
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
                admin_count = cursor.fetchone()[0]
                
                if admin_count == 1:
                    return False, "Cannot delete the last admin user"
            
            # Delete user
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            conn.commit()
            conn.close()
            
            return True, "User deleted successfully"
            
        except Exception as e:
            logging.error(f"Delete user error: {e}")
            return False, str(e)