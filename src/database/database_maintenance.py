import os
import sqlite3
import logging
import shutil
import datetime
import time

class DatabaseMaintenance:
    """Database maintenance and integrity check utilities"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        
    def check_integrity(self):
        """Check database integrity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Run SQLite integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            
            conn.close()
            
            if result != "ok":
                logging.error(f"Database integrity check failed: {result}")
                return False, result
            
            return True, "Database integrity check passed"
            
        except Exception as e:
            logging.error(f"Database integrity check error: {e}")
            return False, str(e)
    
    def vacuum_database(self):
        """Vacuum the database to optimize storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Run VACUUM command
            conn.execute("VACUUM")
            
            conn.close()
            
            logging.info("Database vacuum completed successfully")
            return True, "Database vacuum completed successfully"
            
        except Exception as e:
            logging.error(f"Database vacuum error: {e}")
            return False, str(e)
    
    def analyze_database(self):
        """Run ANALYZE to update statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Run ANALYZE command
            conn.execute("ANALYZE")
            
            conn.close()
            
            logging.info("Database analysis completed successfully")
            return True, "Database analysis completed successfully"
            
        except Exception as e:
            logging.error(f"Database analysis error: {e}")
            return False, str(e)
    
    def repair_database(self):
        """Attempt to repair a corrupted database"""
        try:
            # Create backup before repair
            backup_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.db_path}.repair_backup_{backup_time}"
            shutil.copy2(self.db_path, backup_path)
            
            # Create a new connection
            conn = sqlite3.connect(self.db_path)
            
            # Dump all data
            with conn:
                dump = "".join(conn.iterdump())
            
            conn.close()
            
            # Delete the original database file
            os.remove(self.db_path)
            
            # Create a new database file
            new_conn = sqlite3.connect(self.db_path)
            
            # Restore data from dump
            new_conn.executescript(dump)
            new_conn.close()
            
            logging.info(f"Database repair completed successfully. Backup at {backup_path}")
            return True, f"Database repair completed successfully. Backup at {backup_path}"
            
        except Exception as e:
            logging.error(f"Database repair error: {e}")
            return False, str(e)
    
    def get_database_info(self):
        """Get information about the database"""
        try:
            info = {}
            
            # File info
            info['file_size'] = os.path.getsize(self.db_path) / (1024 * 1024)  # Size in MB
            info['last_modified'] = datetime.datetime.fromtimestamp(
                os.path.getmtime(self.db_path)
            ).strftime("%Y-%m-%d %H:%M:%S")
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            info['tables'] = []
            total_rows = 0
            
            for table in tables:
                table_name = table[0]
                if table_name.startswith('sqlite_'):
                    continue
                
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
                info['tables'].append({
                    'name': table_name,
                    'rows': row_count
                })
                
                total_rows += row_count
            
            info['total_rows'] = total_rows
            
            # Get index information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = cursor.fetchall()
            info['indexes'] = [index[0] for index in indexes if not index[0].startswith('sqlite_')]
            
            # Get schema version
            cursor.execute("PRAGMA schema_version")
            info['schema_version'] = cursor.fetchone()[0]
            
            conn.close()
            
            return info
            
        except Exception as e:
            logging.error(f"Error getting database info: {e}")
            return None
    
    def optimize_database(self):
        """Fully optimize the database"""
        try:
            # Check integrity first
            integrity_ok, message = self.check_integrity()
            if not integrity_ok:
                return False, f"Integrity check failed: {message}"
            
            # Create backup before optimization
            backup_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.db_path}.optimize_backup_{backup_time}"
            shutil.copy2(self.db_path, backup_path)
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            
            # Run optimization steps
            with conn:
                # Reindex
                conn.execute("REINDEX")
                
                # Analyze
                conn.execute("ANALYZE")
                
                # Vacuum
                conn.execute("VACUUM")
            
            conn.close()
            
            logging.info("Database optimization completed successfully")
            return True, "Database optimization completed successfully"
            
        except Exception as e:
            logging.error(f"Database optimization error: {e}")
            return False, str(e)