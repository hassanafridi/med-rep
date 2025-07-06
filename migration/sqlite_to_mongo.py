# migration/sqlite_to_mongo_atlas.py

import sqlite3
import sys
import os
from datetime import datetime, timezone
import logging
from pymongo.errors import DuplicateKeyError

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.mongo_db import MongoDB

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SQLiteToMongoMigrator:
    def __init__(self, sqlite_path: str):
        """
        Initialize the migrator with your Atlas connection
        
        Args:
            sqlite_path: Path to SQLite database file
        """
        self.sqlite_path = sqlite_path
        # Use the same connection as in your mongo_db.py
        self.mongo_db = MongoDB()  # This will use your Atlas connection
        self.sqlite_conn = None
        
    def connect_sqlite(self) -> bool:
        """Connect to SQLite database"""
        try:
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row  # Enable column access by name
            logger.info(f"Connected to SQLite database: {self.sqlite_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"SQLite connection error: {e}")
            return False
    
    def migrate_customers(self) -> bool:
        """Migrate customers from SQLite to MongoDB"""
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("SELECT * FROM customers")
            customers = cursor.fetchall()
            
            logger.info(f"Migrating {len(customers)} customers...")
            
            for customer in customers:
                customer_doc = {
                    "name": customer["name"],
                    "contact": customer["contact"] or "",
                    "address": customer["address"] or "",
                    "created_at": self._parse_timestamp(customer["created_at"]),
                    "legacy_id": customer["id"]  # Keep original ID for reference
                }
                
                try:
                    result = self.mongo_db.db.customers.insert_one(customer_doc)
                    logger.debug(f"Migrated customer: {customer['name']} -> {result.inserted_id}")
                except DuplicateKeyError:
                    logger.warning(f"Skipping duplicate customer id={customer['id']} name={customer['name']}")
                    continue
            
            logger.info(f"Successfully migrated {len(customers)} customers")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating customers: {e}")
            return False
    
    def migrate_products(self) -> bool:
        """Migrate products from SQLite to MongoDB"""
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("SELECT * FROM products")
            products = cursor.fetchall()
            
            logger.info(f"Migrating {len(products)} products...")
            
            for product in products:
                product_doc = {
                    "name": product["name"],
                    "description": product["description"] or "",
                    "unit_price": float(product["unit_price"]) if product["unit_price"] else 0.0,
                    "batch_number": product["batch_number"] or "",
                    "expiry_date": product["expiry_date"] or "",
                    "created_at": self._parse_timestamp(product["created_at"]),
                    "legacy_id": product["id"]  # Keep original ID for reference
                }
                
                try:
                    result = self.mongo_db.db.products.insert_one(product_doc)
                    logger.debug(f"Migrated product: {product['name']} -> {result.inserted_id}")
                except DuplicateKeyError:
                    logger.warning(f"Skipping duplicate product id={product['id']} name={product['name']}")
                    continue
            
            logger.info(f"Successfully migrated {len(products)} products")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating products: {e}")
            return False
    
    def migrate_entries(self) -> bool:
        """Migrate entries from SQLite to MongoDB"""
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("SELECT * FROM entries")
            entries = cursor.fetchall()
            
            logger.info(f"Migrating {len(entries)} entries...")
            
            # Create lookup maps for customer and product IDs
            customer_map = self._create_legacy_id_map("customers")
            product_map = self._create_legacy_id_map("products")
            
            for entry in entries:
                # Get MongoDB ObjectIds for customer and product
                customer_oid = customer_map.get(entry["customer_id"])
                product_oid = product_map.get(entry["product_id"])
                
                if not customer_oid or not product_oid:
                    logger.warning(f"Skipping entry {entry['id']} - missing customer or product reference")
                    continue
                
                entry_doc = {
                    "date": entry["date"],
                    "customer_id": customer_oid,
                    "product_id": product_oid,
                    "quantity": int(entry["quantity"]) if entry["quantity"] else 0,
                    "unit_price": float(entry["unit_price"]) if entry["unit_price"] else 0.0,
                    "is_credit": bool(entry["is_credit"]),
                    "notes": entry["notes"] or "",
                    "created_at": self._parse_timestamp(entry["created_at"]),
                    "legacy_id": entry["id"]  # Keep original ID for reference
                }
                
                try:
                    result = self.mongo_db.db.entries.insert_one(entry_doc)
                    logger.debug(f"Migrated entry: {entry['id']} -> {result.inserted_id}")
                except DuplicateKeyError:
                    logger.warning(f"Skipping duplicate entry id={entry['id']}")
                    continue
            
            logger.info(f"Successfully migrated entries")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating entries: {e}")
            return False
    
    def migrate_transactions(self) -> bool:
        """Migrate transactions from SQLite to MongoDB"""
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("SELECT * FROM transactions")
            transactions = cursor.fetchall()
            
            logger.info(f"Migrating {len(transactions)} transactions...")
            
            # Create lookup map for entry IDs
            entry_map = self._create_legacy_id_map("entries")
            
            for transaction in transactions:
                # Get MongoDB ObjectId for entry
                entry_oid = entry_map.get(transaction["entry_id"])
                
                if not entry_oid:
                    logger.warning(f"Skipping transaction {transaction['id']} - missing entry reference")
                    continue
                
                transaction_doc = {
                    "entry_id": entry_oid,
                    "amount": float(transaction["amount"]) if transaction["amount"] else 0.0,
                    "balance": float(transaction["balance"]) if transaction["balance"] else 0.0,
                    "created_at": self._parse_timestamp(transaction["created_at"]),
                    "legacy_id": transaction["id"]  # Keep original ID for reference
                }
                
                try:
                    result = self.mongo_db.db.transactions.insert_one(transaction_doc)
                    logger.debug(f"Migrated transaction: {transaction['id']} -> {result.inserted_id}")
                except DuplicateKeyError:
                    logger.warning(f"Skipping duplicate transaction id={transaction['id']}")
                    continue
            
            logger.info(f"Successfully migrated transactions")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating transactions: {e}")
            return False
    
    def migrate_users(self) -> bool:
        """Migrate users if they exist in SQLite"""
        try:
            cursor = self.sqlite_conn.cursor()
            
            # Check if users table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if not cursor.fetchone():
                logger.info("Users table not found in SQLite - skipping user migration")
                return True
            
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            
            logger.info(f"Migrating {len(users)} users...")
            
            for user in users:
                user_doc = {
                    "username": user["username"],
                    "password_hash": user["password_hash"],
                    "salt": user["salt"],          # ← carry the salt across
                    "role": user["role"] or "user",
                    "created_at": self._parse_timestamp(user["created_at"]),
                    "last_login": self._parse_timestamp(user["last_login"]) if user["last_login"] else None,
                    "legacy_id": user["id"]  # Keep original ID for reference
                }
                
                # upsert will create the doc if missing, or update the existing one
                self.mongo_db.db.users.update_one(
                    {"username": user["username"]},
                    {"$set": user_doc},
                    upsert=True
                )
                logger.debug(f"Upserted user: {user['username']}")
            
            logger.info(f"Successfully migrated users")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating users: {e}")
            return False
    
    def _create_legacy_id_map(self, collection_name: str) -> dict:
        """Create a mapping from legacy SQLite IDs to MongoDB ObjectIds"""
        try:
            documents = self.mongo_db.db[collection_name].find({}, {"_id": 1, "legacy_id": 1})
            return {doc["legacy_id"]: doc["_id"] for doc in documents if "legacy_id" in doc}
        except Exception as e:
            logger.error(f"Error creating legacy ID map for {collection_name}: {e}")
            return {}
    
    def _parse_timestamp(self, timestamp_str):
        """Parse timestamp string to datetime object"""
        if not timestamp_str:
            return datetime.now(timezone.utc)
        
        try:
            # Try different timestamp formats
            formats = [
                "%Y-%m-%d %H:%M:%S.%f",  # SQLite default with microseconds
                "%Y-%m-%d %H:%M:%S",     # SQLite default without microseconds
                "%Y-%m-%d",              # Date only
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(timestamp_str, fmt)
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            
            # If all formats fail, return current time
            logger.warning(f"Could not parse timestamp: {timestamp_str}")
            return datetime.now(timezone.utc)
            
        except Exception as e:
            logger.warning(f"Error parsing timestamp {timestamp_str}: {e}")
            return datetime.now(timezone.utc)
    
    def verify_migration(self) -> bool:
        """Verify that migration completed successfully"""
        try:
            logger.info("Verifying migration...")
            
            # Count records in SQLite
            sqlite_counts = {}
            cursor = self.sqlite_conn.cursor()
            
            tables = ["customers", "products", "entries", "transactions"]
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    sqlite_counts[table] = cursor.fetchone()[0]
                except sqlite3.Error:
                    sqlite_counts[table] = 0
            
            # Count documents in MongoDB
            mongo_counts = {}
            for collection in ["customers", "products", "entries", "transactions"]:
                mongo_counts[collection] = self.mongo_db.db[collection].count_documents({})
            
            # Compare counts
            success = True
            for table in tables:
                sqlite_count = sqlite_counts.get(table, 0)
                mongo_count = mongo_counts.get(table, 0)
                
                if sqlite_count == mongo_count:
                    logger.info(f"[OK] {table}: {sqlite_count} records migrated successfully")
                else:
                    logger.error(f"[MISMATCH] {table}: SQLite={sqlite_count}, MongoDB={mongo_count}")
                    success = False
            
            if success:
                logger.info("Migration verification completed successfully!")
            else:
                logger.error("Migration verification failed - some records may be missing")
            
            return success
            
        except Exception as e:
            logger.error(f"Error during migration verification: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Run the complete migration process"""
        try:
            logger.info("Starting SQLite to MongoDB Atlas migration...")
            
            # Connect to databases
            if not self.connect_sqlite():
                return False
            
            if not self.mongo_db.connect():
                return False
            
            # Initialize MongoDB collections and indexes
            if not self.mongo_db.init_db():
                return False
            
            # Run migrations in order (customers and products first, then entries, then transactions)
            migration_steps = [
                ("customers", self.migrate_customers),
                ("products", self.migrate_products), 
                ("entries", self.migrate_entries),
                ("transactions", self.migrate_transactions),
                ("users", self.migrate_users)
            ]
            
            for step_name, migration_func in migration_steps:
                logger.info(f"Starting {step_name} migration...")
                if not migration_func():
                    logger.error(f"Failed to migrate {step_name}")
                    return False
                logger.info(f"Completed {step_name} migration")
            
            # Verify migration
            if not self.verify_migration():
                logger.warning("Migration verification failed, but migration may still be usable")
            
            logger.info("Migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
        finally:
            # Clean up connections
            if self.sqlite_conn:
                self.sqlite_conn.close()
            self.mongo_db.close()
    
    def create_backup(self, backup_path: str) -> bool:
        """Create a backup of the SQLite database before migration"""
        try:
            import shutil
            shutil.copy2(self.sqlite_path, backup_path)
            logger.info(f"SQLite backup created: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False


def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate data from SQLite to MongoDB Atlas")
    parser.add_argument("--sqlite-path", required=True, help="Path to SQLite database file")
    parser.add_argument("--create-backup", action="store_true", 
                       help="Create backup of SQLite database before migration")
    parser.add_argument("--backup-path", help="Path for SQLite backup file")
    
    args = parser.parse_args()
    
    # Validate SQLite database exists
    if not os.path.exists(args.sqlite_path):
        logger.error(f"SQLite database not found: {args.sqlite_path}")
        return False
    
    # Create migrator
    migrator = SQLiteToMongoMigrator(sqlite_path=args.sqlite_path)
    
    # Create backup if requested
    if args.create_backup:
        backup_path = args.backup_path or f"{args.sqlite_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if not migrator.create_backup(backup_path):
            logger.error("Failed to create backup")
            return False
    
    # Run migration
    success = migrator.run_migration()
    
    if success:
        print("\n" + "="*50)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("Your data has been successfully migrated from SQLite to MongoDB Atlas.")
        print("You can now update your application to use the MongoDB database.")
        print("\nNext steps:")
        print("1. Update your application code to use MongoDB")
        print("2. Test the application with the new database")
        print("3. Keep the SQLite backup for safety")
        print(f"4. Your data is now available in MongoDB Atlas database: medrep")
    else:
        print("\n" + "="*50)
        print("MIGRATION FAILED!")
        print("="*50)
        print("Please check the migration.log file for detailed error information.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)