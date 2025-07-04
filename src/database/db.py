import shutil
import sqlite3
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='data/medtran.db'):
        """Initialize database connection"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to the SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            return False
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def init_db(self):
        """Create tables if they don't exist"""
        try:
            self.connect()
            
            # Create Customers table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    contact TEXT,
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create Products table with batch number and expiry date
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    unit_price REAL,
                    batch_number TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create Entries table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    customer_id INTEGER,
                    product_id INTEGER,
                    quantity INTEGER,
                    unit_price REAL,
                    is_credit BOOLEAN,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Create Transactions table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_id INTEGER,
                    amount REAL NOT NULL,
                    balance REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (entry_id) REFERENCES entries (id)
                )
            ''')
            
            self.conn.commit()
            
            # Check if we need to migrate existing products table
            self._migrate_products_table()
            
            logger.info("Database initialized successfully")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            return False
        finally:
            self.close()
    
    def _migrate_products_table(self):
        """Migrate existing products table to include batch_number and expiry_date"""
        try:
            # Check if batch_number column exists
            self.cursor.execute("PRAGMA table_info(products)")
            columns = [column[1] for column in self.cursor.fetchall()]
            
            if 'batch_number' not in columns or 'expiry_date' not in columns:
                logger.info("Migrating products table to include batch_number and expiry_date")
                
                # Get existing data
                self.cursor.execute("SELECT id, name, description, unit_price, created_at FROM products")
                existing_products = self.cursor.fetchall()
                
                # Drop the old table
                self.cursor.execute("DROP TABLE products")
                
                # Create new table with updated schema
                self.cursor.execute('''
                    CREATE TABLE products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        unit_price REAL,
                        batch_number TEXT NOT NULL,
                        expiry_date TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Migrate existing data with default values
                for product in existing_products:
                    product_id, name, description, unit_price, created_at = product
                    self.cursor.execute('''
                        INSERT INTO products (id, name, description, unit_price, batch_number, expiry_date, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (product_id, name, description, unit_price, 'LEGACY-001', '2025-12-31', created_at))
                
                self.conn.commit()
                logger.info("Products table migration completed successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Migration error: {e}")
            raise
    
    def insert_sample_data(self):
        """Insert sample data for testing"""
        try:
            self.connect()
            
            # Sample customers
            customers = [
                ('John Doe', '555-1234', '123 Main St'),
                ('Jane Smith', '555-5678', '456 Oak Ave'),
                ('Medical Center A', '555-9101', '789 Hospital Blvd')
            ]
            
            self.cursor.executemany(
                'INSERT INTO customers (name, contact, address) VALUES (?, ?, ?)',
                customers
            )
            
            # Sample products with batch numbers and expiry dates
            products = [
                ('MediCure', 'General antibiotic', 25.50, 'MCR-2024-001', '2025-12-31'),
                ('MediCure', 'General antibiotic', 25.50, 'MCR-2024-002', '2026-06-30'),
                ('PainAway', 'Pain reliever', 12.75, 'PA-2024-101', '2025-08-15'),
                ('PainAway', 'Pain reliever', 12.75, 'PA-2024-102', '2025-11-30'),
                ('HealthBoost', 'Vitamin supplement', 35.00, 'HB-2024-001', '2027-03-20'),
                ('HealthBoost', 'Vitamin supplement', 35.00, 'HB-2024-002', '2026-09-10')
            ]
            
            self.cursor.executemany(
                'INSERT INTO products (name, description, unit_price, batch_number, expiry_date) VALUES (?, ?, ?, ?, ?)',
                products
            )
            
            self.conn.commit()
            logger.info("Sample data inserted successfully")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error inserting sample data: {e}")
            return False
        finally:
            self.close()
    
    def execute_query(self, query, params=None):
        """Execute a query with parameters safely"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return True
        except sqlite3.Error as e:
            logging.error(f"Query execution error: {e}")
            return False
        
    def repair_database(self):
        """Attempt to repair a corrupted database"""
        try:
            # Create a backup first
            backup_path = f"{self.db_path}.bak"
            shutil.copy2(self.db_path, backup_path)
            
            # Create a new connection and dump/reload the schema
            temp_conn = sqlite3.connect(self.db_path)
            dump = "".join(temp_conn.iterdump())
            temp_conn.close()
            
            # Recreate the database
            os.remove(self.db_path)
            new_conn = sqlite3.connect(self.db_path)
            new_conn.executescript(dump)
            new_conn.close()
            
            logging.info(f"Database repaired. Backup saved at {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Database repair failed: {e}")
            return False
        
    def create_indexes(self):
        """Create indexes for better performance"""
        try:
            self.connect()
            
            # Index for date lookups
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_date ON entries(date)")
            
            # Index for customer lookups
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_customer ON entries(customer_id)")
            
            # Index for product lookups
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_product ON entries(product_id)")
            
            # Index for entry_id in transactions
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_entry ON transactions(entry_id)")
            
            # Index for product batch lookups
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_batch ON products(batch_number)")
            
            # Index for product expiry lookups
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_expiry ON products(expiry_date)")
            
            # Composite index for product name and batch
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_name_batch ON products(name, batch_number)")
            
            self.conn.commit()
            logging.info("Indexes created successfully")
            return True
        except sqlite3.Error as e:
            logging.error(f"Failed to create indexes: {e}")
            return False
        finally:
            self.close()
            
    def get_products_by_name(self, product_name):
        """Get all products with the same name but different batches"""
        try:
            self.connect()
            self.cursor.execute(
                'SELECT id, name, description, unit_price, batch_number, expiry_date FROM products WHERE name = ? ORDER BY expiry_date DESC',
                (product_name,)
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error getting products by name: {e}")
            return []
        finally:
            self.close()
            
    def get_expired_products(self, current_date):
        """Get products that are expired or expiring soon"""
        try:
            self.connect()
            self.cursor.execute(
                'SELECT id, name, batch_number, expiry_date FROM products WHERE expiry_date <= ? ORDER BY expiry_date',
                (current_date,)
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error getting expired products: {e}")
            return []
        finally:
            self.close()