import unittest
import sys
import os
import sqlite3
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.db import Database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        """Set up test database"""
        self.db = Database(db_path=':memory:')  # Use in-memory database for testing
        self.db.init_db()
        self.db.connect()
    
    def tearDown(self):
        """Clean up after test"""
        self.db.close()
    
    def test_init_db(self):
        """Test database initialization"""
        # Check if tables were created
        tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
        self.db.cursor.execute(tables_query)
        tables = [row[0] for row in self.db.cursor.fetchall()]
        
        expected_tables = ['customers', 'products', 'entries', 'transactions']
        for table in expected_tables:
            self.assertIn(table, tables)
    
    def test_insert_sample_data(self):
        """Test inserting sample data"""
        self.db.insert_sample_data()
        
        # Check customers
        self.db.cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = self.db.cursor.fetchone()[0]
        self.assertGreater(customer_count, 0)
        
        # Check products
        self.db.cursor.execute("SELECT COUNT(*) FROM products")
        product_count = self.db.cursor.fetchone()[0]
        self.assertGreater(product_count, 0)
    
    def test_entry_transaction(self):
        """Test adding an entry and corresponding transaction"""
        # Add customer and product first
        self.db.cursor.execute(
            "INSERT INTO customers (name, contact, address) VALUES (?, ?, ?)",
            ("Test Customer", "123-456-7890", "123 Test St")
        )
        customer_id = self.db.cursor.lastrowid
        
        self.db.cursor.execute(
            "INSERT INTO products (name, description, unit_price) VALUES (?, ?, ?)",
            ("Test Product", "Test Description", 10.0)
        )
        product_id = self.db.cursor.lastrowid
        
        # Add entry
        today = datetime.now().strftime('%Y-%m-%d')
        self.db.cursor.execute(
            "INSERT INTO entries (date, customer_id, product_id, quantity, unit_price, is_credit, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (today, customer_id, product_id, 2, 10.0, True, "Test entry")
        )
        entry_id = self.db.cursor.lastrowid
        
        # Add transaction
        self.db.cursor.execute(
            "INSERT INTO transactions (entry_id, amount, balance) VALUES (?, ?, ?)",
            (entry_id, 20.0, 20.0)
        )
        
        # Check if entry was added
        self.db.cursor.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
        entry = self.db.cursor.fetchone()
        self.assertIsNotNone(entry)
        
        # Check if transaction was added
        self.db.cursor.execute("SELECT * FROM transactions WHERE entry_id = ?", (entry_id,))
        transaction = self.db.cursor.fetchone()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction[2], 20.0)  # amount
        self.assertEqual(transaction[3], 20.0)  # balance

if __name__ == '__main__':
    unittest.main()