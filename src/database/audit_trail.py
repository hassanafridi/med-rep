import sqlite3
import logging
import json
import datetime

class AuditTrail:
    """Track user actions and changes in the database"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_audit_table()
    
    def init_audit_table(self):
        """Initialize the audit trail table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create audit trail table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER,
                    username TEXT,
                    action_type TEXT NOT NULL,
                    table_name TEXT,
                    record_id INTEGER,
                    old_values TEXT,
                    new_values TEXT,
                    details TEXT
                )
            ''')
            
            # Create index for faster querying
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_trail(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_trail(user_id)')
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize audit trail: {e}")
            return False
    
    def log_action(self, user_id, username, action_type, table_name=None, record_id=None, 
                  old_values=None, new_values=None, details=None):
        """Log an action to the audit trail"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert dict values to JSON if provided
            old_values_json = json.dumps(old_values) if old_values else None
            new_values_json = json.dumps(new_values) if new_values else None
            
            # Insert into audit trail
            cursor.execute(
                '''
                INSERT INTO audit_trail 
                (user_id, username, action_type, table_name, record_id, old_values, new_values, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (user_id, username, action_type, table_name, record_id, 
                 old_values_json, new_values_json, details)
            )
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to log audit action: {e}")
            return False
    
    def log_login(self, user_id, username, success, details=None):
        """Log a login attempt"""
        action_type = "LOGIN_SUCCESS" if success else "LOGIN_FAILURE"
        return self.log_action(
            user_id=user_id,
            username=username,
            action_type=action_type,
            details=details
        )
    
    def log_data_change(self, user_id, username, operation, table_name, record_id, old_values=None, new_values=None):
        """Log a data change operation (INSERT, UPDATE, DELETE)"""
        if operation not in ["INSERT", "UPDATE", "DELETE"]:
            raise ValueError(f"Invalid operation: {operation}")
            
        return self.log_action(
            user_id=user_id,
            username=username,
            action_type=f"DATA_{operation}",
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values
        )
    
    def get_audit_trail(self, filters=None, limit=100, offset=0):
        """Get audit trail entries with optional filtering"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT * FROM audit_trail"
            params = []
            
            # Apply filters if provided
            if filters:
                where_clauses = []
                
                if 'user_id' in filters:
                    where_clauses.append("user_id = ?")
                    params.append(filters['user_id'])
                
                if 'username' in filters:
                    where_clauses.append("username LIKE ?")
                    params.append(f"%{filters['username']}%")
                
                if 'action_type' in filters:
                    where_clauses.append("action_type = ?")
                    params.append(filters['action_type'])
                
                if 'table_name' in filters:
                    where_clauses.append("table_name = ?")
                    params.append(filters['table_name'])
                
                if 'from_date' in filters:
                    where_clauses.append("timestamp >= ?")
                    params.append(filters['from_date'])
                
                if 'to_date' in filters:
                    where_clauses.append("timestamp <= ?")
                    params.append(filters['to_date'])
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
            
            # Add order by and limit
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            # Execute query
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            result = []
            for row in rows:
                row_dict = dict(row)
                
                # Parse JSON fields
                if row_dict['old_values']:
                    try:
                        row_dict['old_values'] = json.loads(row_dict['old_values'])
                    except:
                        pass
                        
                if row_dict['new_values']:
                    try:
                        row_dict['new_values'] = json.loads(row_dict['new_values'])
                    except:
                        pass
                
                result.append(row_dict)
            
            conn.close()
            return result
            
        except Exception as e:
            logging.error(f"Failed to get audit trail: {e}")
            return []
    
    def get_audit_count(self, filters=None):
        """Get count of audit trail entries with optional filtering"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT COUNT(*) FROM audit_trail"
            params = []
            
            # Apply filters if provided
            if filters:
                where_clauses = []
                
                if 'user_id' in filters:
                    where_clauses.append("user_id = ?")
                    params.append(filters['user_id'])
                
                if 'username' in filters:
                    where_clauses.append("username LIKE ?")
                    params.append(f"%{filters['username']}%")
                
                if 'action_type' in filters:
                    where_clauses.append("action_type = ?")
                    params.append(filters['action_type'])
                
                if 'table_name' in filters:
                    where_clauses.append("table_name = ?")
                    params.append(filters['table_name'])
                
                if 'from_date' in filters:
                    where_clauses.append("timestamp >= ?")
                    params.append(filters['from_date'])
                
                if 'to_date' in filters:
                    where_clauses.append("timestamp <= ?")
                    params.append(filters['to_date'])
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
            
            # Execute query
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            logging.error(f"Failed to get audit count: {e}")
            return 0