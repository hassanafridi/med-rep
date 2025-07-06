# src/database/mongo_adapter.py

"""
MongoDB adapter that provides a SQLite-compatible interface for existing code.
This allows gradual migration of your existing codebase to MongoDB.
"""

import logging
from typing import List, Tuple, Any, Optional
from datetime import datetime, timezone
from bson import ObjectId
from .mongo_db import MongoDB

logger = logging.getLogger(__name__)

class MongoAdapter:
    """
    Adapter class that provides a SQLite-like interface for MongoDB operations.
    This allows existing code to work with minimal changes.
    """
    
    def __init__(self, connection_string: str = None, database_name: str = "medtran_db"):
        self.mongo_db = MongoDB(connection_string, database_name)
        self.connected = False
        
        # Simulate cursor for compatibility
        self.cursor = self
        self.lastrowid = None
        
    def connect(self) -> bool:
        """Connect to MongoDB"""
        self.connected = self.mongo_db.connect()
        return self.connected
    
    def close(self):
        """Close MongoDB connection"""
        if self.connected:
            self.mongo_db.close()
            self.connected = False
    
    def init_db(self) -> bool:
        """Initialize database"""
        return self.mongo_db.init_db()
    
    def insert_sample_data(self) -> bool:
        """Insert sample data"""
        return self.mongo_db.insert_sample_data()
    
    def execute(self, query: str, params: tuple = None) -> bool:
        """
        Execute a query - converts SQL-like operations to MongoDB operations.
        This is a simplified implementation for common operations.
        """
        try:
            query = query.strip().upper()
            
            if query.startswith("INSERT INTO customers"):
                return self._handle_customer_insert(params)
            elif query.startswith("INSERT INTO products"):
                return self._handle_product_insert(params)
            elif query.startswith("INSERT INTO entries"):
                return self._handle_entry_insert(params)
            elif query.startswith("INSERT INTO transactions"):
                return self._handle_transaction_insert(params)
            elif query.startswith("UPDATE customers"):
                return self._handle_customer_update(query, params)
            elif query.startswith("UPDATE products"):
                return self._handle_product_update(query, params)
            elif query.startswith("DELETE FROM customers"):
                return self._handle_customer_delete(query, params)
            elif query.startswith("DELETE FROM products"):
                return self._handle_product_delete(query, params)
            else:
                logger.warning(f"Unsupported query: {query}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return False
    
    def executemany(self, query: str, params_list: List[tuple]) -> bool:
        """Execute multiple queries"""
        try:
            for params in params_list:
                if not self.execute(query, params):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error executing multiple queries: {e}")
            return False
    
    def fetchall(self) -> List[tuple]:
        """Fetch all results from the last query"""
        # This should be called after a SELECT query
        # For now, return empty list - implement based on your specific needs
        return []
    
    def fetchone(self) -> tuple:
        """Fetch one result from the last query"""
        # This should be called after a SELECT query
        # For now, return None - implement based on your specific needs
        return None
    
    def commit(self):
        """Commit transaction (MongoDB auto-commits, so this is a no-op)"""
        pass
    
    def rollback(self):
        """Rollback transaction (limited support in MongoDB)"""
        pass
    
    # Helper methods for handling specific operations
    
    def _handle_customer_insert(self, params: tuple) -> bool:
        """Handle customer insert"""
        try:
            if len(params) == 3:
                name, contact, address = params
                result_id = self.mongo_db.add_customer(name, contact or "", address or "")
                if result_id:
                    # Convert ObjectId to integer-like value for compatibility
                    self.lastrowid = hash(result_id) % (10**9)
                    return True
            return False
        except Exception as e:
            logger.error(f"Error inserting customer: {e}")
            return False
    
    def _handle_product_insert(self, params: tuple) -> bool:
        """Handle product insert"""
        try:
            if len(params) >= 3:
                name, description, unit_price = params[:3]
                batch_number = params[3] if len(params) > 3 else ""
                expiry_date = params[4] if len(params) > 4 else ""
                
                result_id = self.mongo_db.add_product(
                    name, description or "", float(unit_price) if unit_price else 0.0,
                    batch_number, expiry_date
                )
                if result_id:
                    self.lastrowid = hash(result_id) % (10**9)
                    return True
            return False
        except Exception as e:
            logger.error(f"Error inserting product: {e}")
            return False
    
    def _handle_entry_insert(self, params: tuple) -> bool:
        """Handle entry insert"""
        try:
            if len(params) >= 6:
                date, customer_id, product_id, quantity, unit_price, is_credit = params[:6]
                notes = params[6] if len(params) > 6 else ""
                
                # Convert customer_id and product_id from integer to ObjectId
                customer_oid = self._find_objectid_by_legacy_id("customers", customer_id)
                product_oid = self._find_objectid_by_legacy_id("products", product_id)
                
                if customer_oid and product_oid:
                    result_id = self.mongo_db.add_entry(
                        date, str(customer_oid), str(product_oid),
                        int(quantity) if quantity else 0,
                        float(unit_price) if unit_price else 0.0,
                        bool(is_credit), notes or ""
                    )
                    if result_id:
                        self.lastrowid = hash(result_id) % (10**9)
                        return True
            return False
        except Exception as e:
            logger.error(f"Error inserting entry: {e}")
            return False
    
    def _handle_transaction_insert(self, params: tuple) -> bool:
        """Handle transaction insert"""
        try:
            if len(params) >= 3:
                entry_id, amount, balance = params[:3]
                
                # Convert entry_id from integer to ObjectId
                entry_oid = self._find_objectid_by_legacy_id("entries", entry_id)
                
                if entry_oid:
                    result_id = self.mongo_db.add_transaction(
                        str(entry_oid),
                        float(amount) if amount else 0.0,
                        float(balance) if balance else 0.0
                    )
                    if result_id:
                        self.lastrowid = hash(result_id) % (10**9)
                        return True
            return False
        except Exception as e:
            logger.error(f"Error inserting transaction: {e}")
            return False
    
    def _handle_customer_update(self, query: str, params: tuple) -> bool:
        """Handle customer update"""
        # Simplified - you may need to parse the WHERE clause
        logger.warning("Customer update not fully implemented")
        return False
    
    def _handle_product_update(self, query: str, params: tuple) -> bool:
        """Handle product update"""
        # Simplified - you may need to parse the WHERE clause
        logger.warning("Product update not fully implemented")
        return False
    
    def _handle_customer_delete(self, query: str, params: tuple) -> bool:
        """Handle customer delete"""
        # Simplified - you may need to parse the WHERE clause
        logger.warning("Customer delete not fully implemented")
        return False
    
    def _handle_product_delete(self, query: str, params: tuple) -> bool:
        """Handle product delete"""
        # Simplified - you may need to parse the WHERE clause
        logger.warning("Product delete not fully implemented")
        return False
    
    def _find_objectid_by_legacy_id(self, collection: str, legacy_id: int) -> Optional[ObjectId]:
        """Find MongoDB ObjectId by legacy SQLite ID"""
        try:
            doc = self.mongo_db.db[collection].find_one({"legacy_id": legacy_id})
            return doc["_id"] if doc else None
        except Exception as e:
            logger.error(f"Error finding ObjectId for legacy_id {legacy_id}: {e}")
            return None
    
    # Methods that provide direct access to MongoDB operations for new code
    
    def get_customers_mongo(self) -> List[dict]:
        """Get customers using MongoDB native operations"""
        return self.mongo_db.get_customers()
    
    def get_products_mongo(self) -> List[dict]:
        """Get products using MongoDB native operations"""
        return self.mongo_db.get_products()
    
    def get_entries_mongo(self, customer_id: str = None, limit: int = None) -> List[dict]:
        """Get entries using MongoDB native operations"""
        return self.mongo_db.get_entries(customer_id, limit)
    
    def get_transactions_mongo(self, entry_id: str = None) -> List[dict]:
        """Get transactions using MongoDB native operations"""
        return self.mongo_db.get_transactions(entry_id)
    
    def add_customer_mongo(self, name: str, contact: str = "", address: str = "") -> str:
        """Add customer using MongoDB native operations"""
        return self.mongo_db.add_customer(name, contact, address)
    
    def add_product_mongo(self, name: str, description: str = "", unit_price: float = 0.0,
                         batch_number: str = "", expiry_date: str = "") -> str:
        """Add product using MongoDB native operations"""
        return self.mongo_db.add_product(name, description, unit_price, batch_number, expiry_date)
    
    def update_customer_mongo(self, customer_id: str, name: str, contact: str = "", address: str = "") -> bool:
        """Update customer using MongoDB native operations"""
        return self.mongo_db.update_customer(customer_id, name, contact, address)
    
    def update_product_mongo(self, product_id: str, name: str, description: str = "",
                           unit_price: float = 0.0, batch_number: str = "", expiry_date: str = "") -> bool:
        """Update product using MongoDB native operations"""
        return self.mongo_db.update_product(product_id, name, description, unit_price, batch_number, expiry_date)
    
    def delete_customer_mongo(self, customer_id: str) -> bool:
        """Delete customer using MongoDB native operations"""
        return self.mongo_db.delete_customer(customer_id)
    
    def delete_product_mongo(self, product_id: str) -> bool:
        """Delete product using MongoDB native operations"""
        return self.mongo_db.delete_product(product_id)
    
    def get_database_info(self) -> dict:
        """Get database information"""
        return self.mongo_db.get_database_info()
    
    def backup_database(self, backup_path: str) -> bool:
        """Create database backup"""
        return self.mongo_db.backup_database(backup_path)


# Compatibility alias for easy replacement
Database = MongoAdapter