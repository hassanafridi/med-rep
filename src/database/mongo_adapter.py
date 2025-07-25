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
    MongoDB adapter that provides SQLite-compatible methods for existing code.
    Translates SQL queries to MongoDB operations where possible.
    """
    
    def __init__(self, mongo_db_instance=None, connection_string: str = None, database_name: str = "medtran_db"):
        """Initialize the MongoDB adapter"""
        if mongo_db_instance:
            self.mongo_db = mongo_db_instance
        else:
            from .mongo_db import MongoDB
            self.mongo_db = MongoDB(connection_string, database_name)
        
        self.connected = False
        self.cursor = self  # For SQLite compatibility
        self.conn = self    # For SQLite compatibility
        self._db_path = None # For SQLite compatibility
        self._lastrowid = None
        self._last_results = []  # Store results for fetchall/fetchone
        
        # Expose the database directly for UserAuth compatibility
        self.db = None
        
        self.collections = {
            'customers': 'customers',
            'products': 'products', 
            'entries': 'entries',
            'transactions': 'transactions',
            'users': 'users'
        }
        
        # Ensure connection and data availability
        self._ensure_data_available()
    
    @property
    def db_path(self):
        return self._db_path
    
    @db_path.setter 
    def db_path(self, value):
        self._db_path = value
    
    @property
    def lastrowid(self):
        return self._lastrowid
    
    def _ensure_data_available(self):
        """Ensure MongoDB connection and data availability"""
        try:
            # Connect to MongoDB
            if not self.connected:
                self.connect()
            
            # Check if we have basic data
            if not self.connected:
                logger.warning("MongoDB not connected, cannot ensure data availability")
                return False
                
            # Check if collections have data
            try:
                customer_count = self.mongo_db.db.customers.count_documents({})
                product_count = self.mongo_db.db.products.count_documents({})
                entry_count = self.mongo_db.db.entries.count_documents({})
                
                logger.info(f"Data availability check: {customer_count} customers, {product_count} products, {entry_count} entries")
                
                # If no data exists, try to add sample data
                if customer_count == 0 and product_count == 0 and entry_count == 0:
                    logger.info("No data found, attempting to insert sample data")
                    self.insert_sample_data()
                
                return True
            except Exception as e:
                logger.error(f"Error checking data availability: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error ensuring data availability: {e}")
            return False
    
    def connect(self) -> bool:
        """Connect to MongoDB"""
        if not self.connected:
            try:
                # Connect through mongo_db
                result = self.mongo_db.connect()
                self.connected = bool(result) if result is not None else False
                
                # Expose the database for UserAuth compatibility
                if self.connected:
                    # Ensure mongo_db has a valid db attribute - check for None explicitly
                    if hasattr(self.mongo_db, 'db') and self.mongo_db.db is not None:
                        self.db = self.mongo_db.db
                    else:
                        logging.error("MongoDB instance does not have valid db attribute")
                        self.connected = False
                        return False
                    
                return self.connected
            except Exception as e:
                logger.error(f"MongoDB connection error: {e}")
                return False
        return self.connected

    def close(self):
        """Close MongoDB connection (compatibility method)"""
        try:
            if self.mongo_db is not None:
                self.mongo_db.close()
        except Exception as e:
            logger.error(f"MongoDB close error: {e}")
    
    def init_db(self):
        """Initialize MongoDB collections and indexes (compatibility method)"""
        try:
            result = self.mongo_db.init_db()
            return bool(result) if result is not None else False
        except Exception as e:
            logger.error(f"MongoDB init_db error: {e}")
            return False
    
    def insert_sample_data(self):
        """Insert sample data (compatibility method)"""
        try:
            # Check if data already exists
            if (self.mongo_db.db.customers.count_documents({}) > 0 or 
                self.mongo_db.db.products.count_documents({}) > 0):
                logger.info("Sample data already exists, skipping insertion")
                return True
                
            # Insert sample customers with pharmaceutical business names
            sample_customers = [
                {"name": "Tariq Medical Store", "contact": "0333-99-11-514", "address": "Main Market, Faisalabad\nPunjab, Pakistan"},
                {"name": "Huzaifa Shopping Mall", "contact": "0300-12-34567", "address": "Johal Road, Addah\nPunjab, Pakistan"},
                {"name": "City Pharmacy", "contact": "042-12345678", "address": "Liberty Market, Lahore\nPunjab, Pakistan"},
                {"name": "Medicare Center", "contact": "051-87654321", "address": "F-7 Markaz, Islamabad\nICT, Pakistan"},
                {"name": "Health Plus Pharmacy", "contact": "021-11223344", "address": "Clifton Block 2, Karachi\nSindh, Pakistan"}
            ]
            
            customer_ids = []
            for customer in sample_customers:
                result = self.mongo_db.db.customers.insert_one(customer)
                customer_ids.append(result.inserted_id)
                logger.info(f"Inserted customer: {customer['name']}")
            
            # Insert sample pharmaceutical products with MRP
            sample_products = [
                {"name": "G+ cream", "description": "Topical antibiotic cream", "unit_price": 850, "mrp": 1020, "batch_number": "GP1K24", "expiry_date": "2025-12-31"},
                {"name": "B+ cream", "description": "Vitamin B complex cream", "unit_price": 850, "mrp": 1020, "batch_number": "BP2K24", "expiry_date": "2025-11-30"},
                {"name": "Folicare Shop", "description": "Folic acid supplement", "unit_price": 220, "mrp": 263.5, "batch_number": "FC3K24", "expiry_date": "2025-10-31"},
                {"name": "Scarheal", "description": "Scar healing ointment", "unit_price": 850, "mrp": 1020, "batch_number": "SH4K24", "expiry_date": "2025-09-30"},
                {"name": "Paracetamol 500mg", "description": "Pain reliever and fever reducer", "unit_price": 120, "mrp": 150, "batch_number": "PC5K24", "expiry_date": "2026-01-31"}
            ]
            
            product_ids = []
            for product in sample_products:
                result = self.mongo_db.db.products.insert_one(product)
                product_ids.append(result.inserted_id)
                logger.info(f"Inserted product: {product['name']}")
            
            # Insert sample entries (transactions)
            import random
            from datetime import datetime, timedelta
            
            sample_entries = []
            current_balance = 0
            
            # Generate entries for the last 90 days
            for i in range(36):  # Increased to 36 entries
                entry_date = (datetime.now() - timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d')
                customer_id = random.choice(customer_ids)
                product_id = random.choice(product_ids)
                
                # Get product info for pricing
                product_info = next((p for p in sample_products if str(product_ids[sample_products.index(p)]) == str(product_id)), sample_products[0])
                
                quantity = random.randint(1, 10)
                unit_price = product_info['unit_price']
                is_credit = random.choice([True, False])  # Mix of sales and purchases
                
                # Add some realistic notes
                notes_options = [
                    "Regular customer order",
                    "Bulk purchase discount applied",
                    "Emergency supply",
                    "Monthly stock replenishment",
                    "Special order for patient",
                    ""
                ]
                notes = random.choice(notes_options)
                
                entry = {
                    "date": entry_date,
                    "customer_id": customer_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "is_credit": is_credit,
                    "notes": notes,
                    "created_at": datetime.now()
                }
                
                sample_entries.append(entry)
                
                # Calculate running balance
                amount = quantity * unit_price
                if is_credit:
                    current_balance += amount
                else:
                    current_balance -= amount
            
            # Insert all entries
            if sample_entries:
                result = self.mongo_db.db.entries.insert_many(sample_entries)
                logger.info(f"Inserted {len(result.inserted_ids)} entries")
                
                # Create corresponding transactions
                transactions = []
                running_balance = 0
                
                for i, entry in enumerate(sample_entries):
                    amount = entry['quantity'] * entry['unit_price']
                    if entry['is_credit']:
                        running_balance += amount
                    else:
                        running_balance -= amount
                    
                    transaction = {
                        "entry_id": result.inserted_ids[i],
                        "amount": amount,
                        "balance": running_balance,
                        "created_at": datetime.now()
                    }
                    transactions.append(transaction)
                
                if transactions:
                    trans_result = self.mongo_db.db.transactions.insert_many(transactions)
                    logger.info(f"Inserted {len(trans_result.inserted_ids)} transactions")
            
            logger.info("Sample pharmaceutical data inserted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting sample data: {e}")
            return False
    
    # SQLite compatibility methods for cursor
    def fetchall(self):
        """SQLite compatibility method - return all results from last execute"""
        return self._last_results
    
    def fetchone(self):
        """SQLite compatibility method - return first result from last execute"""
        if self._last_results:
            return self._last_results[0]
        return None
    
    def commit(self):
        """SQLite compatibility method (no-op for MongoDB)"""
        pass
    
    def rollback(self):
        """SQLite compatibility method (no-op for MongoDB)"""
        pass
    
    def execute(self, query: str, params: tuple = None) -> List[List]:
        """
        Execute SQL-like queries and convert to MongoDB operations
        Returns data in SQL-like format for compatibility
        """
        try:
            if not self.connected:
                self.connect()
                
            query_original = query
            query = query.strip().upper()
            params = params or ()
            
            results = []
            
            # Handle different query types
            if query.startswith('SELECT * FROM CUSTOMERS'):
                results = self._handle_select_customers()
            elif query.startswith('SELECT * FROM PRODUCTS'):
                results = self._handle_select_products()
            elif query.startswith('SELECT * FROM ENTRIES'):
                results = self._handle_select_entries()
            elif query.startswith('SELECT * FROM TRANSACTIONS'):
                results = self._handle_select_transactions()
            elif "SUM(QUANTITY * UNIT_PRICE)" in query and "IS_CREDIT = 1" in query:
                results = self._handle_sales_query(query, params)
            elif "SUM(QUANTITY * UNIT_PRICE)" in query and "IS_CREDIT = 0" in query:
                results = self._handle_debits_query(query, params)
            elif "COUNT(*)" in query and "ENTRIES" in query:
                results = self._handle_count_query(query, params)
            elif "MAX(BALANCE)" in query:
                results = self._handle_balance_query()
            elif "SELECT P.NAME" in query and "GROUP BY P.NAME" in query:
                results = self._handle_product_distribution_query()
            elif "EXPIRED" in query or "EXPIRY_DATE" in query:
                results = self._handle_expiry_query(query)
            elif 'COUNT(' in query:
                results = self._handle_count(query_original, params)
            elif 'SUM(' in query:
                results = self._handle_sum(query_original, params)
            elif 'MAX(' in query:
                results = self._handle_max(query_original, params)
            elif query.startswith('INSERT'):
                results = self._handle_insert(query_original, params)
            elif query.startswith('SELECT'):
                results = self._handle_select(query_original, params)
            else:
                # Generic query handling
                results = self._handle_generic_query(query, params)
            
            # Store results for fetchall/fetchone compatibility
            self._last_results = results
            logger.debug(f"Query executed: {query_original[:50]}... -> {len(results)} results")
            return results
                
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            import traceback
            traceback.print_exc()
            self._last_results = []
            return []
    
    def _handle_select_customers(self) -> List[List]:
        """Handle SELECT * FROM customers"""
        try:
            customers = self.get_customers()
            results = []
            for customer in customers:
                results.append([
                    customer.get('id', ''),
                    customer.get('name', ''),
                    customer.get('contact', ''),
                    customer.get('address', '')
                ])
            logger.info(f"SELECT customers returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error in _handle_select_customers: {e}")
            return []
    
    def _handle_select_products(self) -> List[List]:
        """Handle SELECT * FROM products"""
        try:
            products = self.get_products()
            results = []
            for product in products:
                results.append([
                    product.get('id', ''),
                    product.get('name', ''),
                    product.get('description', ''),
                    float(product.get('unit_price', 0)),  # Wholesale price
                    float(product.get('mrp', 0)),  # Market retail price
                    product.get('batch_number', ''),
                    product.get('expiry_date', '')
                ])
            logger.info(f"SELECT products returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error in _handle_select_products: {e}")
            return []
    
    def _handle_select_entries(self) -> List[List]:
        """Handle SELECT * FROM entries"""
        try:
            entries = self.get_entries()
            results = []
            for entry in entries:
                results.append([
                    entry.get('id', ''),
                    entry.get('date', ''),
                    entry.get('customer_id', ''),
                    entry.get('product_id', ''),
                    float(entry.get('quantity', 0)),
                    float(entry.get('unit_price', 0)),
                    bool(entry.get('is_credit', False)),
                    entry.get('notes', '')
                ])
            logger.info(f"SELECT entries returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error in _handle_select_entries: {e}")
            return []
    
    def _handle_select_transactions(self) -> List[List]:
        """Handle SELECT * FROM transactions"""
        try:
            transactions = self.get_transactions()
            results = []
            for transaction in transactions:
                results.append([
                    transaction.get('id', ''),
                    transaction.get('entry_id', ''),
                    float(transaction.get('amount', 0)),
                    float(transaction.get('balance', 0))
                ])
            logger.info(f"SELECT transactions returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error in _handle_select_transactions: {e}")
            return []
    
    def get_customers(self):
        """Get all customers (compatibility method)"""
        try:
            # Get raw customers from MongoDB
            raw_customers = list(self.mongo_db.db.customers.find())
            logger.info(f"Retrieved {len(raw_customers)} customers directly from MongoDB")
            
            # Ensure proper data types for compatibility
            formatted_customers = []
            for customer in raw_customers:
                formatted_customer = {}
                # Handle ObjectId conversion properly
                formatted_customer['id'] = str(customer.get('_id', ''))
                formatted_customer['name'] = str(customer.get('name', ''))
                formatted_customer['contact'] = str(customer.get('contact', ''))
                formatted_customer['address'] = str(customer.get('address', ''))
                formatted_customers.append(formatted_customer)
            
            logger.info(f"Formatted {len(formatted_customers)} customers")
            return formatted_customers
        except Exception as e:
            logger.error(f"MongoDB get_customers error: {e}")
            return []
    
    def get_products(self):
        """Get all products (compatibility method)"""
        try:
            # Get raw products from MongoDB
            raw_products = list(self.mongo_db.db.products.find())
            logger.info(f"Retrieved {len(raw_products)} products directly from MongoDB")
            
            # Ensure proper data types for compatibility
            formatted_products = []
            for product in raw_products:
                formatted_product = {}
                try:
                    # Handle ObjectId conversion properly
                    formatted_product['id'] = str(product.get('_id', ''))
                    formatted_product['name'] = str(product.get('name', ''))
                    formatted_product['description'] = str(product.get('description', ''))
                    
                    # Ensure unit_price is float (wholesale price) with proper type checking
                    unit_price_raw = product.get('unit_price', 0)
                    formatted_product['unit_price'] = float(unit_price_raw) if unit_price_raw else 0.0
                    
                    # Enhanced MRP handling with validation and fallback calculation
                    mrp_raw = product.get('mrp', 0)
                    logger.debug(f"Product {formatted_product['name']}: Raw MRP from DB = {mrp_raw} (type: {type(mrp_raw)})")
                    
                    if mrp_raw is None:
                        # Calculate MRP as 120% of unit_price if completely missing
                        calculated_mrp = formatted_product['unit_price'] * 1.2
                        formatted_product['mrp'] = calculated_mrp
                        logger.warning(f"Product {formatted_product['name']}: MRP is None, calculated as {calculated_mrp:.2f}")
                    elif isinstance(mrp_raw, (int, float)) and mrp_raw > 0:
                        formatted_product['mrp'] = float(mrp_raw)
                        logger.debug(f"Product {formatted_product['name']}: MRP converted to {formatted_product['mrp']}")
                    elif isinstance(mrp_raw, str) and mrp_raw.strip():
                        try:
                            parsed_mrp = float(mrp_raw)
                            if parsed_mrp > 0:
                                formatted_product['mrp'] = parsed_mrp
                                logger.debug(f"Product {formatted_product['name']}: MRP converted from string to {formatted_product['mrp']}")
                            else:
                                # Calculate MRP if parsed value is 0 or negative
                                calculated_mrp = formatted_product['unit_price'] * 1.2
                                formatted_product['mrp'] = calculated_mrp
                                logger.warning(f"Product {formatted_product['name']}: MRP was {parsed_mrp}, calculated as {calculated_mrp:.2f}")
                        except ValueError:
                            # Calculate MRP if string can't be parsed
                            calculated_mrp = formatted_product['unit_price'] * 1.2
                            formatted_product['mrp'] = calculated_mrp
                            logger.warning(f"Product {formatted_product['name']}: Invalid MRP string '{mrp_raw}', calculated as {calculated_mrp:.2f}")
                    else:
                        # Calculate MRP for any other invalid cases
                        calculated_mrp = formatted_product['unit_price'] * 1.2
                        formatted_product['mrp'] = calculated_mrp
                        logger.warning(f"Product {formatted_product['name']}: Invalid MRP value '{mrp_raw}', calculated as {calculated_mrp:.2f}")
                    
                    formatted_product['batch_number'] = str(product.get('batch_number', ''))
                    formatted_product['expiry_date'] = str(product.get('expiry_date', ''))
                    
                    # Final validation to ensure MRP is never zero or negative
                    if formatted_product['mrp'] <= 0:
                        formatted_product['mrp'] = max(formatted_product['unit_price'] * 1.2, 1.0)
                        logger.warning(f"Product {formatted_product['name']}: MRP was <= 0, set to {formatted_product['mrp']:.2f}")
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Data type conversion error for product {product.get('_id', 'unknown')}: {e}")
                    # Use safe defaults
                    formatted_product['unit_price'] = 0.0
                    formatted_product['mrp'] = 1.0  # Default minimum MRP
                
                formatted_products.append(formatted_product)
            
            logger.info(f"Formatted {len(formatted_products)} products")
            return formatted_products
        except Exception as e:
            logger.error(f"MongoDB get_products error: {e}")
            return []

    def get_entries(self, customer_id=None, limit=None):
        """Get all entries (compatibility method)"""
        try:
            # Get raw entries from MongoDB with proper sorting
            query = {}
            if customer_id:
                from bson import ObjectId
                try:
                    query["customer_id"] = ObjectId(customer_id)
                except:
                    query["customer_id"] = customer_id  # Try as string
            
            # Sort by date descending, then by created_at descending to get most recent first
            cursor = self.mongo_db.db.entries.find(query).sort([("date", -1), ("created_at", -1)])
            if limit:
                cursor = cursor.limit(limit)
                
            raw_entries = list(cursor)
            logger.info(f"Retrieved {len(raw_entries)} entries directly from MongoDB (limit: {limit})")
            
            # Convert entries to match expected format for UI with proper data types
            formatted_entries = []
            for entry in raw_entries:
                formatted_entry = {}
                try:
                    # Handle ObjectId conversion properly
                    formatted_entry['id'] = str(entry.get('_id', ''))
                    
                    # Convert ObjectId references to strings
                    formatted_entry['customer_id'] = str(entry.get('customer_id', ''))
                    formatted_entry['product_id'] = str(entry.get('product_id', ''))
                    
                    # Ensure numeric values are properly typed
                    formatted_entry['quantity'] = float(entry.get('quantity', 0))
                    formatted_entry['unit_price'] = float(entry.get('unit_price', 0))
                    
                    # Ensure date is string for consistency and not None/empty
                    date_value = entry.get('date', '')
                    if not date_value:
                        # Use creation date as fallback
                        created_at = entry.get('created_at')
                        if created_at:
                            if hasattr(created_at, 'strftime'):
                                date_value = created_at.strftime('%Y-%m-%d')
                            else:
                                date_value = str(created_at)[:10]  # Take first 10 chars
                        else:
                            date_value = '2024-01-01'  # Default fallback
                    
                    formatted_entry['date'] = str(date_value)
                    formatted_entry['is_credit'] = bool(entry.get('is_credit', False))
                    formatted_entry['notes'] = str(entry.get('notes', ''))
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Data type conversion error for entry {entry.get('_id', 'unknown')}: {e}")
                    # Use defaults for problematic values
                    formatted_entry['quantity'] = 0.0
                    formatted_entry['unit_price'] = 0.0
                    formatted_entry['date'] = '2024-01-01'
                
                formatted_entries.append(formatted_entry)
            
            logger.info(f"Formatted {len(formatted_entries)} entries")
            return formatted_entries
        except Exception as e:
            logger.error(f"MongoDB get_entries error: {e}")
            return []
    
    def get_transactions(self):
        """Get all transactions (compatibility method)"""
        try:
            # Get raw transactions from MongoDB
            raw_transactions = list(self.mongo_db.db.transactions.find())
            logger.info(f"Retrieved {len(raw_transactions)} transactions directly from MongoDB")
            
            # Ensure proper data types
            formatted_transactions = []
            for transaction in raw_transactions:
                formatted_transaction = {}
                try:
                    # Handle ObjectId conversion properly
                    formatted_transaction['id'] = str(transaction.get('_id', ''))
                    formatted_transaction['entry_id'] = str(transaction.get('entry_id', ''))
                    formatted_transaction['amount'] = float(transaction.get('amount', 0))
                    formatted_transaction['balance'] = float(transaction.get('balance', 0))
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Data type conversion error for transaction {transaction.get('_id', 'unknown')}: {e}")
                    formatted_transaction['amount'] = 0.0
                    formatted_transaction['balance'] = 0.0
                    
                formatted_transactions.append(formatted_transaction)
            
            logger.info(f"Formatted {len(formatted_transactions)} transactions")
            return formatted_transactions
        except Exception as e:
            logger.error(f"MongoDB get_transactions error: {e}")
            return []

    # Add methods for UI compatibility
    def add_customer(self, name, contact="", address=""):
        """Add a new customer"""
        try:
            return self.mongo_db.add_customer(name, contact, address)
        except Exception as e:
            logger.error(f"Error adding customer: {e}")
            return None
    
    def add_product(self, name, description="", unit_price=0.0, batch_number="", expiry_date="", mrp=0.0):
        """Add a new product with MRP"""
        try:
            # Ensure unit_price and mrp are float
            unit_price = float(unit_price) if unit_price else 0.0
            mrp = float(mrp) if mrp else 0.0
            
            # Add product with MRP support
            result = self.mongo_db.add_product(name, description, unit_price, batch_number, expiry_date, mrp)
            
            if result:
                logger.info(f"Successfully added product: {name} with MRP: {mrp}")
            else:
                logger.error(f"Failed to add product: {name}")
            
            return result
                
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def add_entry(self, date, customer_id, product_id, quantity, unit_price, is_credit, notes=""):
        """Add a new entry"""
        try:
            # Ensure proper data types
            quantity = float(quantity) if quantity else 0.0
            unit_price = float(unit_price) if unit_price else 0.0
            return self.mongo_db.add_entry(date, customer_id, product_id, quantity, unit_price, is_credit, notes)
        except Exception as e:
            logger.error(f"Error adding entry: {e}")
            return None
    
    def add_transaction(self, entry_id, amount, balance):
        """Add a new transaction"""
        try:
            # Ensure proper data types
            amount = float(amount) if amount else 0.0
            balance = float(balance) if balance else 0.0
            
            # Convert entry_id to ObjectId if it's a string
            from bson import ObjectId
            if isinstance(entry_id, str):
                try:
                    entry_id = ObjectId(entry_id)
                except:
                    pass  # Keep as string if conversion fails
            
            return self.mongo_db.add_transaction(entry_id, amount, balance)
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return None

    def clear_all_collections(self):
        """Clear all collections (for restore functionality)"""
        try:
            collections = ['customers', 'products', 'entries', 'transactions']
            for collection_name in collections:
                self.mongo_db.db[collection_name].delete_many({})
            logger.info("All collections cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing collections: {e}")
            return False

    def restore_customers(self, customers_data):
        """Restore customers from backup data"""
        try:
            for customer in customers_data:
                self.add_customer(
                    customer.get('name', ''),
                    customer.get('contact', ''),
                    customer.get('address', '')
                )
            return True
        except Exception as e:
            logger.error(f"Error restoring customers: {e}")
            return False

    def restore_products(self, products_data):
        """Restore products from backup data"""
        try:
            for product in products_data:
                self.add_product(
                    product.get('name', ''),
                    product.get('description', ''),
                    product.get('unit_price', 0),
                    product.get('batch_number', ''),
                    product.get('expiry_date', '')
                )
            return True
        except Exception as e:
            logger.error(f"Error restoring products: {e}")
            return False

    def restore_entries(self, entries_data):
        """Restore entries from backup data"""
        try:
            for entry in entries_data:
                self.add_entry(
                    entry.get('date', ''),
                    entry.get('customer_id', ''),
                    entry.get('product_id', ''),
                    entry.get('quantity', 0),
                    entry.get('unit_price', 0),
                    entry.get('is_credit', True),
                    entry.get('notes', '')
                )
            return True
        except Exception as e:
            logger.error(f"Error restoring entries: {e}")
            return False

    def restore_transactions(self, transactions_data):
        """Restore transactions from backup data"""
        try:
            for transaction in transactions_data:
                self.add_transaction(
                    transaction.get('entry_id', ''),
                    transaction.get('amount', 0),
                    transaction.get('balance', 0)
                )
            return True
        except Exception as e:
            logger.error(f"Error restoring transactions: {e}")
            return False

    def update_entry_notes(self, entry_id, new_notes):
        """Update the notes field of an existing entry"""
        try:
            from bson import ObjectId
            
            # Convert entry_id to ObjectId if it's a string
            if isinstance(entry_id, str):
                try:
                    entry_id = ObjectId(entry_id)
                except:
                    pass  # Keep as string if conversion fails
            
            # Update the entry
            result = self.mongo_db.db.entries.update_one(
                {"_id": entry_id},
                {"$set": {"notes": new_notes}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated entry {entry_id} with new notes")
                return True
            else:
                logger.warning(f"No entry found with ID {entry_id} to update")
                return False
                
        except Exception as e:
            logger.error(f"Error updating entry notes: {e}")
            return False
    
    def get_entry_by_id(self, entry_id):
        """Get a specific entry by ID"""
        try:
            from bson import ObjectId
            
            # Convert entry_id to ObjectId if it's a string
            if isinstance(entry_id, str):
                try:
                    entry_id = ObjectId(entry_id)
                except:
                    pass  # Keep as string if conversion fails
            
            # Get the entry
            entry = self.mongo_db.db.entries.find_one({"_id": entry_id})
            
            if entry:
                # Format the entry similar to get_entries()
                formatted_entry = {
                    'id': str(entry.get('_id', '')),
                    'date': str(entry.get('date', '')),
                    'customer_id': str(entry.get('customer_id', '')),
                    'product_id': str(entry.get('product_id', '')),
                    'quantity': float(entry.get('quantity', 0)),
                    'unit_price': float(entry.get('unit_price', 0)),
                    'is_credit': bool(entry.get('is_credit', False)),
                    'notes': str(entry.get('notes', ''))
                }
                return formatted_entry
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting entry by ID: {e}")
            return None

    # ...existing code...
    
    def _handle_sales_query(self, query: str, params: tuple = None) -> List[List]:
        """Handle sales/revenue queries"""
        try:
            # Build MongoDB aggregation pipeline
            pipeline = [
                {"$match": {"is_credit": True}},
                {
                    "$addFields": {
                        "revenue": {
                            "$multiply": [
                                {"$toDouble": "$quantity"}, 
                                {"$toDouble": "$unit_price"}
                            ]
                        }
                    }
                }
            ]
            
            # Add date filtering if params provided
            if params and len(params) >= 1:
                if len(params) == 1:
                    # Single date - greater than or equal
                    pipeline[0]["$match"]["date"] = {"$gte": str(params[0])}
                elif len(params) == 2:
                    # Date range
                    pipeline[0]["$match"]["date"] = {"$gte": str(params[0]), "$lte": str(params[1])}
            
            # Add grouping
            pipeline.append({
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$revenue"}
                }
            })
            
            result = list(self.mongo_db.db.entries.aggregate(pipeline))
            if result:
                return [[float(result[0]["total"])]]
            return [[0.0]]
            
        except Exception as e:
            logger.error(f"Error in sales query: {e}")
            return [[0.0]]
    
    def _handle_debits_query(self, query: str, params: tuple = None) -> List[List]:
        """Handle debit/expense queries"""
        try:
            pipeline = [
                {"$match": {"is_credit": False}},
                {
                    "$addFields": {
                        "amount": {
                            "$multiply": [
                                {"$toDouble": "$quantity"}, 
                                {"$toDouble": "$unit_price"}
                            ]
                        }
                    }
                }
            ]
            
            if params and len(params) >= 1:
                if len(params) == 1:
                    pipeline[0]["$match"]["date"] = {"$gte": str(params[0])}
                elif len(params) == 2:
                    pipeline[0]["$match"]["date"] = {"$gte": str(params[0]), "$lte": str(params[1])}
            
            pipeline.append({
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$amount"}
                }
            })
            
            result = list(self.mongo_db.db.entries.aggregate(pipeline))
            if result:
                return [[float(result[0]["total"])]]
            return [[0.0]]
            
        except Exception as e:
            logger.error(f"Error in debits query: {e}")
            return [[0.0]]
    
    def _handle_count_query(self, query: str, params: tuple = None) -> List[List]:
        """Handle COUNT queries"""
        try:
            match_criteria = {}
            
            if "IS_CREDIT = 1" in query:
                match_criteria["is_credit"] = True
            elif "IS_CREDIT = 0" in query:
                match_criteria["is_credit"] = False
                
            if params and len(params) >= 1:
                if len(params) == 1:
                    match_criteria["date"] = {"$gte": str(params[0])}
                elif len(params) == 2:
                    match_criteria["date"] = {"$gte": str(params[0]), "$lte": str(params[1])}
            
            count = self.mongo_db.db.entries.count_documents(match_criteria)
            return [[int(count)]]
            
        except Exception as e:
            logger.error(f"Error in count query: {e}")
            return [[0]]
    
    def _handle_balance_query(self) -> List[List]:
        """Handle balance queries"""
        try:
            # Get the latest transaction's balance
            result = list(self.mongo_db.db.transactions.find(
                {}, {"balance": 1}
            ).sort("created_at", -1).limit(1))
            
            if result:
                balance = float(result[0].get("balance", 0))
                return [[balance]]
            return [[0.0]]
            
        except Exception as e:
            logger.error(f"Error in balance query: {e}")
            return [[0.0]]
    
    def _handle_product_distribution_query(self) -> List[List]:
        """Handle product distribution queries for charts"""
        try:
            pipeline = [
                {
                    "$lookup": {
                        "from": "products",
                        "localField": "product_id",
                        "foreignField": "_id",
                        "as": "product"
                    }
                },
                {"$unwind": "$product"},
                {"$match": {"is_credit": True}},
                {
                    "$addFields": {
                        "revenue": {
                            "$multiply": [
                                {"$toDouble": "$quantity"}, 
                                {"$toDouble": "$unit_price"}
                            ]
                        }
                    }
                },
                {
                    "$group": {
                        "_id": "$product.name",
                        "total_revenue": {"$sum": "$revenue"},
                        "batch_count": {"$addToSet": "$product.batch_number"}
                    }
                },
                {
                    "$addFields": {
                        "batch_count": {"$size": "$batch_count"}
                    }
                },
                {"$sort": {"total_revenue": -1}},
                {"$limit": 5}
            ]
            
            results = list(self.mongo_db.db.entries.aggregate(pipeline))
            
            # Convert to SQL-like format: [name, total_revenue, batch_count]
            formatted_results = []
            for result in results:
                formatted_results.append([
                    result["_id"],  # product name
                    float(result["total_revenue"]),
                    int(result["batch_count"])
                ])
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in product distribution query: {e}")
            return []
    
    def _handle_expiry_query(self, query: str) -> List[List]:
        """Handle expiry-related queries"""
        try:
            from datetime import datetime, date
            
            today = date.today().strftime("%Y-%m-%d")
            
            # Get products with their sales data
            pipeline = [
                {
                    "$lookup": {
                        "from": "entries",
                        "localField": "_id",
                        "foreignField": "product_id",
                        "as": "sales"
                    }
                },
                {"$match": {"sales": {"$ne": []}}},  # Only products with sales
                {
                    "$addFields": {
                        "sales_total": {
                            "$sum": {
                                "$map": {
                                    "input": {"$filter": {"input": "$sales", "cond": {"$eq": ["$$this.is_credit", True]}}},
                                    "as": "sale",
                                    "in": {"$multiply": ["$$sale.quantity", "$$sale.unit_price"]}
                                }
                            }
                        }
                    }
                },
                {"$match": {"sales_total": {"$gt": 0}}}  # Only products with actual sales
            ]
            
            # Add expiry date filter based on query
            if "WHERE P.EXPIRY_DATE <" in query.upper():
                # Expired products
                pipeline.append({"$match": {"expiry_date": {"$lt": today}}})
            elif "WHERE P.EXPIRY_DATE >=" in query.upper():
                # Products expiring soon (within next 30 days)
                from datetime import timedelta
                future_date = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
                pipeline.append({
                    "$match": {
                        "expiry_date": {"$gte": today, "$lte": future_date}
                    }
                })
            
            results = list(self.mongo_db.db.products.aggregate(pipeline))
            
            # Convert to expected format: [name, batch_number, expiry_date, sales_total]
            formatted_results = []
            for result in results:
                formatted_results.append([
                    result.get("name", ""),
                    result.get("batch_number", ""),
                    result.get("expiry_date", ""),
                    float(result.get("sales_total", 0))
                ])
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in expiry query: {e}")
            return []
    
    def _handle_generic_query(self, query: str, params: tuple = None) -> List[List]:
        """Handle other generic queries"""
        try:
            logger.warning(f"Generic query handler called for: {query}")
            return []
        except Exception as e:
            logger.error(f"Error in generic query: {e}")
            return []
    
    def _handle_select(self, query: str, params: tuple) -> List[Tuple]:
        """Handle SELECT queries"""
        try:
            query_upper = query.upper()
            
            # Handle joined queries for dashboard/UI
            if 'JOIN CUSTOMERS C' in query_upper and 'JOIN PRODUCTS P' in query_upper:
                return self._get_transactions_data(query, params)
            
            # Handle product alerts queries
            elif 'FROM PRODUCTS P' in query_upper and 'EXPIRY_DATE' in query_upper:
                return self._get_product_alerts(query, params)
            
            # Handle sales/entries queries
            elif 'FROM ENTRIES' in query_upper:
                return self._get_entries_data(query, params)
            
            # Default empty result
            return []
            
        except Exception as e:
            logger.error(f"Error in SELECT handler: {e}")
            return []
    
    def _handle_count(self, query: str, params: tuple) -> List[Tuple]:
        """Handle COUNT queries"""
        try:
            query_upper = query.upper()
            
            if 'FROM PRODUCTS' in query_upper:
                count = self.mongo_db.db.products.count_documents({})
                return [(count,)]
            elif 'FROM ENTRIES' in query_upper:
                count = self.mongo_db.db.entries.count_documents({})
                return [(count,)]
            elif 'FROM CUSTOMERS' in query_upper:
                count = self.mongo_db.db.customers.count_documents({})
                return [(count,)]
            
            return [(0,)]
            
        except Exception as e:
            logger.error(f"Error in COUNT handler: {e}")
            return [(0,)]
    
    def _handle_sum(self, query: str, params: tuple) -> List[Tuple]:
        """Handle SUM queries"""
        try:
            query_upper = query.upper()
            
            if 'FROM ENTRIES' in query_upper and 'QUANTITY * UNIT_PRICE' in query_upper:
                # Use MongoDB aggregation for better performance
                pipeline = []
                
                # Add match conditions based on query
                match_conditions = {}
                
                if 'IS_CREDIT = 1' in query_upper:
                    match_conditions["is_credit"] = True
                elif 'IS_CREDIT = 0' in query_upper:
                    match_conditions["is_credit"] = False
                
                if match_conditions:
                    pipeline.append({"$match": match_conditions})
                
                # Calculate sum of quantity * unit_price
                pipeline.extend([
                    {
                        "$group": {
                            "_id": None,
                            "total": {
                                "$sum": {
                                    "$multiply": ["$quantity", "$unit_price"]
                                }
                            }
                        }
                    }
                ])
                
                result = list(self.mongo_db.db.entries.aggregate(pipeline))
                total = float(result[0]["total"]) if result else 0.0
                return [(total,)]
            
            return [(0.0,)]
            
        except Exception as e:
            logger.error(f"Error in SUM handler: {e}")
            return [(0.0,)]
    
    def _handle_max(self, query: str, params: tuple) -> List[Tuple]:
        """Handle MAX queries"""
        try:
            if 'FROM TRANSACTIONS' in query.upper():
                # Use MongoDB aggregation to get max balance
                pipeline = [
                    {
                        "$group": {
                            "_id": None,
                            "max_balance": {"$max": "$balance"}
                        }
                    }
                ]
                
                result = list(self.mongo_db.db.transactions.aggregate(pipeline))
                max_balance = float(result[0]["max_balance"]) if result else 0.0
                return [(max_balance,)]
            
            return [(0.0,)]
            
        except Exception as e:
            logger.error(f"Error in MAX handler: {e}")
            return [(0.0,)]
    
    def _handle_insert(self, query: str, params: tuple) -> List[Tuple]:
        """Handle INSERT queries"""
        try:
            query_upper = query.upper()
            
            if 'INTO CUSTOMERS' in query_upper:
                if len(params) >= 3:
                    result = self.mongo_db.add_customer(params[0], params[1], params[2])
                    return [(result,)] if result else []
            
            elif 'INTO PRODUCTS' in query_upper:
                if len(params) >= 5:
                    result = self.mongo_db.add_product(
                        params[0], params[1], params[2], params[3], params[4]
                    )
                    return [(result,)] if result else []
            
            elif 'INTO ENTRIES' in query_upper:
                if len(params) >= 7:
                    result = self.mongo_db.add_entry(
                        params[0], params[1], params[2], params[3], 
                        params[4], params[5], params[6]
                    )
                    return [(result,)] if result else []
            
            return []
            
        except Exception as e:
            logger.error(f"Error in INSERT handler: {e}")
            return []
    
    def _get_product_alerts(self, query: str, params: tuple) -> List[Tuple]:
        """Get product alerts for expired/expiring products"""
        try:
            products = self.get_products()
            entries = self.get_entries()
            
            # Create a mapping of product sales
            product_sales = {}
            for entry in entries:
                if entry.get('is_credit'):
                    product_id = entry.get('product_id')
                    if product_id:
                        total = entry.get('quantity', 0) * entry.get('unit_price', 0)
                        product_sales[product_id] = product_sales.get(product_id, 0) + total
            
            results = []
            target_date = params[0] if params else ""
            
            for product in products:
                product_id = str(product.get('id', ''))
                expiry_date = product.get('expiry_date', '')
                
                # Check if product has sales and meets date criteria
                if product_id in product_sales and product_sales[product_id] > 0:
                    if 'WHERE P.EXPIRY_DATE <' in query.upper():
                        if expiry_date < target_date:
                            results.append((
                                product.get('name', ''),
                                product.get('batch_number', ''),
                                expiry_date,
                                product_sales[product_id]
                            ))
                    elif 'WHERE P.EXPIRY_DATE >=' in query.upper() and len(params) >= 2:
                        if target_date <= expiry_date <= params[1]:
                            results.append((
                                product.get('name', ''),
                                product.get('batch_number', ''),
                                expiry_date,
                                product_sales[product_id]
                            ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting product alerts: {e}")
            return []
    
    def _get_entries_data(self, query: str, params: tuple) -> List[Tuple]:
        """Get entries data based on query"""
        try:
            entries = self.get_entries()
            results = []
            
            for entry in entries:
                if self._entry_matches_filters(entry, query, params):
                    # Return entry data in expected format
                    quantity = entry.get('quantity', 0)
                    unit_price = entry.get('unit_price', 0)
                    total = quantity * unit_price
                    
                    results.append((
                        entry.get('date', ''),
                        entry.get('customer_id', ''),
                        entry.get('product_id', ''),
                        entry.get('is_credit', False),
                        total,
                        quantity
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting entries data: {e}")
            return []
    
    def _get_transactions_data(self, query: str, params: tuple) -> List[Tuple]:
        """Get transaction data with joins"""
        try:
            # Use MongoDB aggregation for proper joins
            pipeline = [
                {
                    "$lookup": {
                        "from": "customers",
                        "localField": "customer_id",
                        "foreignField": "_id",
                        "as": "customer"
                    }
                },
                {
                    "$lookup": {
                        "from": "products",
                        "localField": "product_id",
                        "foreignField": "_id",
                        "as": "product"
                    }
                },
                {"$unwind": "$customer"},
                {"$unwind": "$product"},
                {"$sort": {"date": -1}},
                {"$limit": 5},
                {
                    "$project": {
                        "date": 1,
                        "customer_name": "$customer.name",
                        "product_name": "$product.name",
                        "is_credit": 1,
                        "quantity": 1,
                        "unit_price": 1,
                        "total": {"$multiply": ["$quantity", "$unit_price"]},
                        "batch_number": "$product.batch_number",
                        "expiry_date": "$product.expiry_date"
                    }
                }
            ]
            
            result = list(self.mongo_db.db.entries.aggregate(pipeline))
            
            formatted_results = []
            for entry in result:
                try:
                    formatted_results.append((
                        str(entry.get('date', '')),
                        str(entry.get('customer_name', '')),
                        str(entry.get('product_name', '')),
                        bool(entry.get('is_credit', False)),
                        float(entry.get('total', 0)),
                        float(entry.get('quantity', 0)),
                        str(entry.get('batch_number', '')),
                        str(entry.get('expiry_date', ''))
                    ))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping transaction due to data type error: {e}")
                    continue
            
            logger.info(f"Generated {len(formatted_results)} transaction results using aggregation")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error getting transactions data: {e}")
            return []

    def _entry_matches_filters(self, entry: dict, query: str, params: tuple) -> bool:
        """Check if entry matches query filters"""
        try:
            query_upper = query.upper()
            
            # Check is_credit filter
            if 'IS_CREDIT = 1' in query_upper and not entry.get('is_credit'):
                return False
            elif 'IS_CREDIT = 0' in query_upper and entry.get('is_credit'):
                return False
            
            # Check date filters with proper string comparison
            entry_date = str(entry.get('date', ''))
            if params:
                if 'DATE >=' in query_upper:
                    if len(params) >= 1 and entry_date < str(params[0]):
                        return False
                if 'DATE <=' in query_upper:
                    if len(params) >= 2 and entry_date > str(params[1]):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking entry filters: {e}")
            return False

    def test_data_retrieval(self):
        """Test method to verify data retrieval"""
        try:
            logger.info("=== Testing MongoDB Data Retrieval ===")
            
            # Test customers
            customers = self.get_customers()
            logger.info(f"Customers found: {len(customers)}")
            if customers:
                logger.info(f"Sample customer: {customers[0]}")
            
            # Test products
            products = self.get_products()
            logger.info(f"Products found: {len(products)}")
            if products:
                logger.info(f"Sample product: {products[0]}")
            
            # Test entries
            entries = self.get_entries()
            logger.info(f"Entries found: {len(entries)}")
            if entries:
                logger.info(f"Sample entry: {entries[0]}")
            
            # Test transactions
            transactions = self.get_transactions()
            logger.info(f"Transactions found: {len(transactions)}")
            if transactions:
                logger.info(f"Sample transaction: {transactions[0]}")
            
            logger.info("=== End Data Retrieval Test ===")
            
            return {
                'customers': len(customers),
                'products': len(products),
                'entries': len(entries),
                'transactions': len(transactions)
            }
            
        except Exception as e:
            logger.error(f"Error in test_data_retrieval: {e}")
            return {'error': str(e)}

    def get_customer_balance(self, customer_id):
        """Calculate balance for a specific customer (Credit - Debit), return 0 if negative"""
        try:
            entries = self.get_entries()
            balance = 0
            
            for entry in entries:
                if str(entry.get('customer_id')) == str(customer_id):
                    amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                    if entry.get('is_credit', False):
                        balance += amount  # Credit increases balance
                    else:
                        balance -= amount  # Debit decreases balance
            
            # Return 0 if balance is negative
            return max(0, balance)
        except Exception as e:
            print(f"Error calculating customer balance: {e}")
            return 0
    
    def get_all_customer_balances(self):
        """Get balances for all customers"""
        try:
            customers = self.get_customers()
            entries = self.get_entries()
            
            # Create customer lookup
            customer_lookup = {}
            for customer in customers:
                customer_id = str(customer.get('id'))
                customer_lookup[customer_id] = {
                    'id': customer_id,
                    'name': customer.get('name', ''),
                    'contact': customer.get('contact', ''),
                    'address': customer.get('address', ''),
                    'credit_total': 0,
                    'debit_total': 0,
                    'raw_balance': 0,
                    'balance': 0
                }
            
            # Calculate totals for each customer
            for entry in entries:
                customer_id = str(entry.get('customer_id'))
                if customer_id in customer_lookup:
                    amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                    
                    if entry.get('is_credit', False):
                        customer_lookup[customer_id]['credit_total'] += amount
                    else:
                        customer_lookup[customer_id]['debit_total'] += amount
            
            # Calculate final balances (Credit - Debit, but show 0 if negative)
            for customer_data in customer_lookup.values():
                raw_balance = customer_data['credit_total'] - customer_data['debit_total']
                customer_data['raw_balance'] = raw_balance
                customer_data['balance'] = max(0, raw_balance)  # Show 0 if negative
        
            return list(customer_lookup.values())
            
        except Exception as e:
            print(f"Error getting customer balances: {e}")
            return []

    def get_entries_with_balance(self, filters=None, limit=None):
        """Get entries with running balance calculation"""
        try:
            # Get ALL entries first, then apply filters
            all_entries = self.get_entries()
            customers = self.get_customers()
            products = self.get_products()
            
            # Debug: Check how many entries we retrieved
            logger.info(f"DEBUG: Retrieved {len(all_entries)} total entries from MongoDB")
            
            # Create lookups
            customer_lookup = {str(c.get('id')): c for c in customers}
            product_lookup = {str(p.get('id')): p for p in products}
            
            # Apply filters if provided
            filtered_entries = []
            
            if filters:
                print(f"DEBUG: Applying filters: {filters}")
                
                for entry in all_entries:
                    include_entry = True
                    
                    # Date range filter - apply if both dates are provided
                    if filters.get('from_date') and filters.get('to_date'):
                        entry_date = entry.get('date', '')
                        from_date = filters['from_date']
                        to_date = filters['to_date']
                        
                        # Use string comparison for dates in YYYY-MM-DD format
                        if not (from_date <= entry_date <= to_date):
                            include_entry = False
                            print(f"DEBUG: Date filter - excluded entry {entry_date} (not in {from_date} to {to_date})")
                    
                    # Customer filter
                    if filters.get('customer_id'):
                        if str(entry.get('customer_id')) != str(filters['customer_id']):
                            include_entry = False
                            print(f"DEBUG: Customer filter - excluded entry for customer {entry.get('customer_id')}")
                    
                    # Entry type filter
                    if filters.get('entry_type'):
                        if filters['entry_type'] == 'credit' and not entry.get('is_credit'):
                            include_entry = False
                            print(f"DEBUG: Type filter - excluded debit entry")
                        elif filters['entry_type'] == 'debit' and entry.get('is_credit'):
                            include_entry = False
                            print(f"DEBUG: Type filter - excluded credit entry")
                    
                    # Notes search
                    if filters.get('notes_search'):
                        notes = entry.get('notes', '').lower()
                        search_term = filters['notes_search'].lower()
                        if search_term not in notes:
                            include_entry = False
                            print(f"DEBUG: Notes filter - excluded entry ('{search_term}' not in notes)")
                    
                    if include_entry:
                        filtered_entries.append(entry)
                
                print(f"DEBUG: After filtering: {len(filtered_entries)} entries remain")
            else:
                # No filters - use all entries
                filtered_entries = all_entries
            
            # For balance calculation, we need to process ALL entries chronologically
            # But we only show the filtered ones at the end
            all_entries_sorted = sorted(all_entries, key=lambda x: (x.get('date', ''), x.get('id', '')))
            
            # Calculate running balance for ALL entries to get accurate balance
            running_balance = 0
            entry_balances = {}
            
            for entry in all_entries_sorted:
                amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                
                # Update running balance
                if entry.get('is_credit'):
                    running_balance += amount
                else:
                    running_balance -= amount
                
                # Store balance for this entry
                entry_balances[entry.get('id')] = max(0, running_balance)
            
            # Now create enriched entries only for filtered entries
            enriched_entries = []
            
            for entry in filtered_entries:
                customer_id = str(entry.get('customer_id'))
                product_id = str(entry.get('product_id'))
                
                customer_info = customer_lookup.get(customer_id, {})
                product_info = product_lookup.get(product_id, {})
                
                amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                
                enriched_entry = {
                    'id': entry.get('id'),
                    'date': entry.get('date'),
                    'customer_id': customer_id,
                    'customer_name': customer_info.get('name', 'Unknown'),
                    'product_id': product_id,
                    'product_name': product_info.get('name', 'Unknown'),
                    'quantity': entry.get('quantity'),
                    'unit_price': entry.get('unit_price'),
                    'amount': amount,
                    'is_credit': entry.get('is_credit'),
                    'type': 'Credit' if entry.get('is_credit') else 'Debit',
                    'notes': entry.get('notes', ''),
                    'running_balance': entry_balances.get(entry.get('id'), 0)
                }
                
                enriched_entries.append(enriched_entry)
            
            # Sort by date DESCENDING to show most recent first for display
            enriched_entries.sort(key=lambda x: (x.get('date', ''), x.get('id', '')), reverse=True)
            
            # Apply limit after processing and sorting if specified
            if limit and len(enriched_entries) > limit:
                print(f"DEBUG: Applying limit {limit} to {len(enriched_entries)} entries")
                enriched_entries = enriched_entries[:limit]
                logger.info(f"Limited results to {limit} entries")
            
            logger.info(f"Returning {len(enriched_entries)} enriched entries")
            print(f"DEBUG: Final result count: {len(enriched_entries)} entries")
            if enriched_entries:
                print(f"DEBUG: First entry date (newest): {enriched_entries[0]['date']}")
                print(f"DEBUG: Last entry date (oldest): {enriched_entries[-1]['date']}")
            
            return enriched_entries
            
        except Exception as e:
            print(f"Error getting entries with balance: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def update_products_with_mrp(self):
        """Update existing products that have missing or zero MRP values"""
        try:
            # Get all products
            products = list(self.mongo_db.db.products.find())
            updated_count = 0
            
            for product in products:
                current_mrp = product.get('mrp', 0)
                unit_price = product.get('unit_price', 0)
                
                # If MRP is missing or zero, calculate a reasonable MRP
                if not current_mrp or current_mrp == 0:
                    # Calculate MRP as 20% higher than unit_price
                    new_mrp = float(unit_price) * 1.2
                    
                    # Update the product
                    result = self.mongo_db.db.products.update_one(
                        {"_id": product["_id"]},
                        {"$set": {"mrp": new_mrp}}
                    )
                    
                    if result.modified_count > 0:
                        updated_count += 1
                        logger.info(f"Updated MRP for {product.get('name', 'Unknown')}: {unit_price} -> {new_mrp}")
            
            logger.info(f"Updated MRP for {updated_count} products")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating products with MRP: {e}")
            return 0
    
    def get_expired_products(self):
        """Get all expired products for debugging"""
        try:
            from datetime import datetime
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Get all products with expiry dates
            products = list(self.mongo_db.db.products.find({
                "expiry_date": {"$exists": True, "$ne": ""}
            }))
            
            expired_products = []
            for product in products:
                expiry_date = product.get('expiry_date', '')
                if expiry_date and expiry_date < current_date:
                    product_info = {
                        'id': str(product.get('_id', '')),
                        'name': product.get('name', ''),
                        'batch_number': product.get('batch_number', ''),
                        'expiry_date': expiry_date,
                        'unit_price': product.get('unit_price', 0),
                        'mrp': product.get('mrp', 0)
                    }
                    expired_products.append(product_info)
            
            logger.info(f"Found {len(expired_products)} expired products")
            return expired_products
            
        except Exception as e:
            logger.error(f"Error getting expired products: {e}")
            return []

    def debug_product_data(self):
        """Debug method to check product data quality"""
        try:
            products = list(self.mongo_db.db.products.find())
            
            print(f"\n=== PRODUCT DATA DEBUG ===")
            print(f"Total products: {len(products)}")
            
            products_with_expiry = 0
            expired_count = 0
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            for i, product in enumerate(products):
                print(f"\nProduct {i+1}:")
                print(f"  ID: {product.get('_id')}")
                print(f"  Name: {product.get('name', 'NO NAME')}")
                print(f"  Batch: {product.get('batch_number', 'NO BATCH')}")
                print(f"  Expiry: {product.get('expiry_date', 'NO EXPIRY')}")
                print(f"  Unit Price: {product.get('unit_price', 'NO PRICE')}")
                print(f"  MRP: {product.get('mrp', 'NO MRP')}")
                
                expiry_date = product.get('expiry_date', '')
                if expiry_date:
                    products_with_expiry += 1
                    if expiry_date < current_date:
                        expired_count += 1
                        print(f"  >>> EXPIRED! ({expiry_date} < {current_date})")
            
            print(f"\nSummary:")
            print(f"  Products with expiry dates: {products_with_expiry}")
            print(f"  Expired products: {expired_count}")
            print(f"=== END DEBUG ===\n")
            
            return {
                'total': len(products),
                'with_expiry': products_with_expiry,
                'expired': expired_count
            }
            
        except Exception as e:
            logger.error(f"Error in debug_product_data: {e}")
            return {}

    def delete_entry(self, entry_id):
        """Delete an entry by ID"""
        try:
            return self.mongo_db.delete_entry(entry_id)
        except Exception as e:
            logger.error(f"Error deleting entry: {e}")
            return False
    
    def delete_transaction(self, transaction_id):
        """Delete a transaction by ID"""
        try:
            return self.mongo_db.delete_transaction(transaction_id)
        except Exception as e:
            logger.error(f"Error deleting transaction: {e}")
            return False

# Compatibility alias for easy replacement
Database = MongoAdapter