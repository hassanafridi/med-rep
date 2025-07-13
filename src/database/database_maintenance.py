import os
import logging
import shutil
import datetime
import time
from src.database.mongo_adapter import MongoAdapter
from src.config import Config

class DatabaseMaintenance:
    """Database maintenance and integrity check utilities for MongoDB"""
    
    def __init__(self, db_path=None):
        # For MongoDB, db_path is not used but kept for compatibility
        self.db_path = db_path
        self.config = Config()
        
        # Initialize MongoDB connection
        try:
            self.db = MongoAdapter()
            if not self.db.connect():
                logging.error("Failed to connect to MongoDB for maintenance")
                self.db = None
        except Exception as e:
            logging.error(f"MongoDB maintenance initialization error: {e}")
            self.db = None
        
    def check_integrity(self):
        """Check database integrity for MongoDB"""
        try:
            if not self.db:
                return False, "No database connection"
            
            # Test basic operations
            test_result = self.db.mongo_db.db.command("ping")
            if test_result.get('ok') != 1:
                return False, "MongoDB ping failed"
            
            # Check collections exist
            expected_collections = ['customers', 'products', 'entries', 'transactions', 'users']
            existing_collections = self.db.mongo_db.db.list_collection_names()
            
            missing_collections = [col for col in expected_collections if col not in existing_collections]
            if missing_collections:
                return False, f"Missing collections: {', '.join(missing_collections)}"
            
            logging.info("MongoDB integrity check passed")
            return True, "Database integrity check passed"
            
        except Exception as e:
            logging.error(f"MongoDB integrity check error: {e}")
            return False, str(e)
    
    def vacuum_database(self):
        """Equivalent to vacuum for MongoDB - compact collections"""
        try:
            if not self.db:
                return False, "No database connection"
            
            collections = ['customers', 'products', 'entries', 'transactions', 'users']
            compacted = []
            
            for collection_name in collections:
                try:
                    result = self.db.mongo_db.db.command("compact", collection_name)
                    if result.get('ok') == 1:
                        compacted.append(collection_name)
                except Exception as e:
                    logging.warning(f"Could not compact {collection_name}: {e}")
            
            message = f"Compacted collections: {', '.join(compacted)}" if compacted else "No collections compacted"
            logging.info(f"MongoDB compact completed: {message}")
            return True, f"Database compaction completed. {message}"
            
        except Exception as e:
            logging.error(f"MongoDB compact error: {e}")
            return False, str(e)
    
    def analyze_database(self):
        """Equivalent to analyze for MongoDB - rebuild indexes"""
        try:
            if not self.db:
                return False, "No database connection"
            
            collections = ['customers', 'products', 'entries', 'transactions', 'users']
            reindexed = []
            
            for collection_name in collections:
                try:
                    collection = self.db.mongo_db.db[collection_name]
                    collection.reindex()
                    reindexed.append(collection_name)
                except Exception as e:
                    logging.warning(f"Could not reindex {collection_name}: {e}")
            
            message = f"Reindexed collections: {', '.join(reindexed)}" if reindexed else "No collections reindexed"
            logging.info(f"MongoDB reindex completed: {message}")
            return True, f"Database analysis completed. {message}"
            
        except Exception as e:
            logging.error(f"MongoDB analysis error: {e}")
            return False, str(e)
    
    def repair_database(self):
        """Attempt to repair MongoDB connection issues"""
        try:
            # For MongoDB, repair usually means reconnecting and rebuilding indexes
            if self.db:
                self.db.close()
            
            # Reinitialize connection
            self.db = MongoAdapter()
            if not self.db.connect():
                return False, "Failed to reconnect to MongoDB"
            
            # Rebuild indexes
            success, message = self.analyze_database()
            if not success:
                return False, f"Repair failed during index rebuild: {message}"
            
            logging.info("MongoDB repair completed successfully")
            return True, "Database repair completed successfully"
            
        except Exception as e:
            logging.error(f"MongoDB repair error: {e}")
            return False, str(e)
    
    def get_database_info(self):
        """Get information about the MongoDB database"""
        try:
            if not self.db:
                return None
            
            info = {}
            
            # Database stats
            db_stats = self.db.mongo_db.db.command("dbStats")
            info['file_size'] = db_stats.get('dataSize', 0) / (1024 * 1024)  # Size in MB
            info['last_modified'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Collection information
            collections = ['customers', 'products', 'entries', 'transactions', 'users']
            info['tables'] = []
            total_rows = 0
            
            for collection_name in collections:
                try:
                    collection = self.db.mongo_db.db[collection_name]
                    row_count = collection.count_documents({})
                    
                    info['tables'].append({
                        'name': collection_name,
                        'rows': row_count
                    })
                    
                    total_rows += row_count
                except Exception as e:
                    logging.warning(f"Could not get stats for {collection_name}: {e}")
            
            info['total_rows'] = total_rows
            
            # Index information
            all_indexes = []
            for collection_name in collections:
                try:
                    collection = self.db.mongo_db.db[collection_name]
                    indexes = collection.list_indexes()
                    for index in indexes:
                        if index['name'] != '_id_':  # Skip default _id index
                            all_indexes.append(f"{collection_name}.{index['name']}")
                except Exception as e:
                    logging.warning(f"Could not get indexes for {collection_name}: {e}")
            
            info['indexes'] = all_indexes
            
            # MongoDB doesn't have schema version like SQLite
            info['schema_version'] = "MongoDB"
            
            return info
            
        except Exception as e:
            logging.error(f"Error getting MongoDB database info: {e}")
            return None
    
    def optimize_database(self):
        """Fully optimize the MongoDB database"""
        try:
            # Check integrity first
            integrity_ok, message = self.check_integrity()
            if not integrity_ok:
                return False, f"Integrity check failed: {message}"
            
            # Run optimization steps
            steps_completed = []
            
            # Compact collections
            compact_ok, compact_msg = self.vacuum_database()
            if compact_ok:
                steps_completed.append("Compaction")
            
            # Rebuild indexes
            analyze_ok, analyze_msg = self.analyze_database()
            if analyze_ok:
                steps_completed.append("Index rebuild")
            
            if steps_completed:
                message = f"Database optimization completed: {', '.join(steps_completed)}"
                logging.info(message)
                return True, message
            else:
                return False, "No optimization steps completed successfully"
            
        except Exception as e:
            logging.error(f"MongoDB optimization error: {e}")
            return False, str(e)