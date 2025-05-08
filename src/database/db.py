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
            
            # Create Products table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    unit_price REAL,
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
            logger.info("Database initialized successfully")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            return False
        finally:
            self.close()
    
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
            
            # Sample products
            products = [
                ('MediCure', 'General antibiotic', 25.50),
                ('PainAway', 'Pain reliever', 12.75),
                ('HealthBoost', 'Vitamin supplement', 35.00)
            ]
            
            self.cursor.executemany(
                'INSERT INTO products (name, description, unit_price) VALUES (?, ?, ?)',
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