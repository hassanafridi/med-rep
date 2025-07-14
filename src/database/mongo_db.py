# src/database/mongo_db.py

import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from datetime import datetime, timezone
import os
from typing import Optional, Dict, List, Any
from bson import ObjectId

# Setup logging
logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self, connection_string: str = None, database_name: str = "medtran_db"):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection string (defaults to local MongoDB)
            database_name: Name of the database to use
        """
        self.connection_string = connection_string or "mongodb+srv://medrep:Dk9Glbs2B2E0Dxof@cluster0.tgwmarr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        self.database_name = 'medrep'
        self.client: Optional[MongoClient] = None
        self.db = None
        
    def connect(self) -> bool:
        """Connect to MongoDB"""
        try:
            if self.client is None:
                self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            
            # Test the connection
            self.client.admin.command('ping')
            
            # Set the database reference
            self.db = self.client[self.database_name]
            
            logger.info(f"Connected to MongoDB database: {self.database_name}")
            return True
            
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {e}")
            self.db = None
            return False
        except Exception as e:
            logger.error(f"MongoDB connection error: {e}")
            self.db = None
            return False
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def init_db(self) -> bool:
        """Initialize collections and indexes"""
        try:
            if not self.connect():
                return False
                
            # Create indexes for better performance
            
            # Customers collection indexes
            self.db.customers.create_index("name")
            self.db.customers.create_index("contact")
            
            # Products collection indexes
            self.db.products.create_index("name")
            self.db.products.create_index("batch_number")
            self.db.products.create_index("expiry_date")
            
            # Entries collection indexes
            self.db.entries.create_index("date")
            self.db.entries.create_index("customer_id")
            self.db.entries.create_index("product_id")
            self.db.entries.create_index([("date", -1), ("customer_id", 1)])
            
            # Transactions collection indexes
            self.db.transactions.create_index("entry_id")
            self.db.transactions.create_index("created_at")
            
            # Users collection indexes (for authentication)
            self.db.users.create_index("username", unique=True)
            
            # Audit trail collection indexes
            self.db.audit_trail.create_index("timestamp")
            self.db.audit_trail.create_index("username")
            self.db.audit_trail.create_index("action")
            
            logger.info("MongoDB collections and indexes initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"MongoDB initialization error: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if MongoDB connection is active"""
        try:
            if self.client:
                self.client.admin.command('ping')
                return True
            return False
        except Exception:
            return False

    def insert_sample_data(self) -> bool:
        """Insert sample data for testing"""
        try:
            if not self.db:
                if not self.connect():
                    return False
                
            # Sample customers
            customers = [
                {
                    "name": "John Doe",
                    "contact": "555-1234",
                    "address": "123 Main St",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Jane Smith", 
                    "contact": "555-5678",
                    "address": "456 Oak Ave",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Medical Center A",
                    "contact": "555-9101", 
                    "address": "789 Hospital Blvd",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "City Pharmacy",
                    "contact": "555-2468",
                    "address": "321 Commerce St",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "Health Clinic B",
                    "contact": "555-1357",
                    "address": "654 Medical Plaza",
                    "created_at": datetime.now(timezone.utc)
                }
            ]
            
            # Insert customers if collection is empty
            if self.db.customers.count_documents({}) == 0:
                result = self.db.customers.insert_many(customers)
                logger.info(f"Inserted {len(result.inserted_ids)} sample customers")
            
            # Sample products with more variety
            products = [
                {
                    "name": "MediCure",
                    "description": "General antibiotic",
                    "unit_price": 25.50,
                    "mrp": 30.60,  # 20% higher than unit_price
                    "batch_number": "MCR-2024-001",
                    "expiry_date": "2025-12-31",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "MediCure",
                    "description": "General antibiotic", 
                    "unit_price": 25.50,
                    "mrp": 30.60,
                    "batch_number": "MCR-2024-002",
                    "expiry_date": "2026-06-30",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "PainAway",
                    "description": "Pain reliever",
                    "unit_price": 12.75,
                    "mrp": 15.30,
                    "batch_number": "PA-2024-101", 
                    "expiry_date": "2025-08-15",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "PainAway",
                    "description": "Pain reliever",
                    "unit_price": 12.75,
                    "mrp": 15.30,
                    "batch_number": "PA-2024-102",
                    "expiry_date": "2025-11-30", 
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "HealthBoost",
                    "description": "Vitamin supplement",
                    "unit_price": 35.00,
                    "mrp": 42.00,
                    "batch_number": "HB-2024-001",
                    "expiry_date": "2027-03-20",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "HealthBoost", 
                    "description": "Vitamin supplement",
                    "unit_price": 35.00,
                    "mrp": 42.00,
                    "batch_number": "HB-2024-002",
                    "expiry_date": "2026-09-10",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "ColdRelief",
                    "description": "Cold and flu medicine",
                    "unit_price": 18.25,
                    "mrp": 21.90,
                    "batch_number": "CR-2024-001",
                    "expiry_date": "2025-10-15",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "HeartCare",
                    "description": "Cardiovascular support",
                    "unit_price": 45.00,
                    "mrp": 54.00,
                    "batch_number": "HC-2024-001",
                    "expiry_date": "2026-12-31",
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "TYes",
                    "description": "Pharmaceutical product",
                    "unit_price": 15.0,
                    "mrp": 19.0,  # Add proper MRP for TYes
                    "batch_number": "2342",
                    "expiry_date": "2025-12-31",
                    "created_at": datetime.now(timezone.utc)
                }
            ]
            
            # Insert products if collection is empty
            if self.db.products.count_documents({}) == 0:
                result = self.db.products.insert_many(products)
                logger.info(f"Inserted {len(result.inserted_ids)} sample products")
            
            # Create a default admin user if users collection is empty
            if self.db.users.count_documents({}) == 0:
                import hashlib
                default_password = "admin123"
                password_hash = hashlib.sha256(default_password.encode()).hexdigest()
                
                admin_user = {
                    "username": "admin",
                    "password_hash": password_hash,
                    "role": "admin",
                    "created_at": datetime.now(timezone.utc),
                    "last_login": None
                }
                result = self.db.users.insert_one(admin_user)
                logger.info(f"Created default admin user (password: {default_password})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error inserting sample data: {e}")
            return False
    
    # Customer operations
    def get_customers(self) -> List[Dict]:
        """Get all customers"""
        try:
            customers = list(self.db.customers.find({}, {"_id": 1, "name": 1, "contact": 1, "address": 1}))
            # Convert ObjectId to string for compatibility
            for customer in customers:
                customer["id"] = str(customer["_id"])
                del customer["_id"]
            return customers
        except Exception as e:
            logger.error(f"Error getting customers: {e}")
            return []
    
    def add_customer(self, name: str, contact: str = "", address: str = "") -> str:
        """Add a new customer"""
        try:
            customer = {
                "name": name,
                "contact": contact, 
                "address": address,
                "created_at": datetime.now(timezone.utc)
            }
            result = self.db.customers.insert_one(customer)
            logger.info(f"Added customer: {name}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error adding customer: {e}")
            return None
    
    def update_customer(self, customer_id: str, name: str, contact: str = "", address: str = "") -> bool:
        """Update a customer"""
        try:
            result = self.db.customers.update_one(
                {"_id": ObjectId(customer_id)},
                {"$set": {
                    "name": name,
                    "contact": contact,
                    "address": address,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating customer: {e}")
            return False
    
    def delete_customer(self, customer_id: str) -> bool:
        """Delete a customer"""
        try:
            result = self.db.customers.delete_one({"_id": ObjectId(customer_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting customer: {e}")
            return False
    
    # Product operations
    def get_products(self) -> List[Dict]:
        """Get all products"""
        try:
            products = list(self.db.products.find().sort("name", 1))
            # Convert ObjectId to string for compatibility
            for product in products:
                product["id"] = str(product["_id"])
                del product["_id"]
            return products
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return []
    
    def add_product(self, name: str, description: str = "", unit_price: float = 0.0, 
                   batch_number: str = "", expiry_date: str = "", mrp: float = 0.0) -> str:
        """Add a new product with MRP support"""
        try:
            product = {
                "name": name,
                "description": description,
                "unit_price": unit_price,
                "mrp": mrp,  # Market Retail Price
                "batch_number": batch_number,
                "expiry_date": expiry_date,
                "created_at": datetime.now(timezone.utc)
            }
            result = self.db.products.insert_one(product)
            logger.info(f"Added product: {name} with MRP: {mrp}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            return None
    
    def update_product(self, product_id: str, name: str, description: str = "", 
                      unit_price: float = 0.0, batch_number: str = "", expiry_date: str = "", 
                      mrp: float = 0.0) -> bool:
        """Update a product with MRP support"""
        try:
            result = self.db.products.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": {
                    "name": name,
                    "description": description,
                    "unit_price": unit_price,
                    "mrp": mrp,  # Market Retail Price
                    "batch_number": batch_number,
                    "expiry_date": expiry_date,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            return False
    
    def delete_product(self, product_id: str) -> bool:
        """Delete a product"""
        try:
            result = self.db.products.delete_one({"_id": ObjectId(product_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            return False
    
    # Entry operations
    def add_entry(self, date: str, customer_id: str, product_id: str, quantity: int,
                 unit_price: float, is_credit: bool, notes: str = "") -> str:
        """Add a new entry"""
        try:
            entry = {
                "date": date,
                "customer_id": ObjectId(customer_id),
                "product_id": ObjectId(product_id),
                "quantity": quantity,
                "unit_price": unit_price,
                "is_credit": is_credit,
                "notes": notes,
                "created_at": datetime.now(timezone.utc)
            }
            result = self.db.entries.insert_one(entry)
            logger.info(f"Added entry for customer: {customer_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error adding entry: {e}")
            return None
    
    def get_entries(self, customer_id: str = None, limit: int = None) -> List[Dict]:
        """Get entries, optionally filtered by customer"""
        try:
            query = {}
            if customer_id:
                query["customer_id"] = ObjectId(customer_id)
            
            cursor = self.db.entries.find(query).sort("date", -1)
            if limit:
                cursor = cursor.limit(limit)
                
            entries = list(cursor)
            
            # Convert ObjectIds to strings and populate customer/product info
            for entry in entries:
                entry["id"] = str(entry["_id"])
                del entry["_id"]
                entry["customer_id"] = str(entry["customer_id"])
                entry["product_id"] = str(entry["product_id"])
                
            return entries
        except Exception as e:
            logger.error(f"Error getting entries: {e}")
            return []
    
    # Transaction operations
    def add_transaction(self, entry_id: str, amount: float, balance: float) -> str:
        """Add a transaction"""
        try:
            transaction = {
                "entry_id": ObjectId(entry_id),
                "amount": amount,
                "balance": balance,
                "created_at": datetime.now(timezone.utc)
            }
            result = self.db.transactions.insert_one(transaction)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return None
    
    def get_transactions(self, entry_id: str = None) -> List[Dict]:
        """Get transactions, optionally filtered by entry"""
        try:
            query = {}
            if entry_id:
                query["entry_id"] = ObjectId(entry_id)
                
            transactions = list(self.db.transactions.find(query).sort("created_at", -1))
            
            # Convert ObjectIds to strings
            for transaction in transactions:
                transaction["id"] = str(transaction["_id"])
                del transaction["_id"]
                transaction["entry_id"] = str(transaction["entry_id"])
                
            return transactions
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            return []
    
    # User authentication operations
    def add_user(self, username: str, password_hash: str, role: str = "user") -> str:
        """Add a new user"""
        try:
            user = {
                "username": username,
                "password_hash": password_hash,
                "role": role,
                "created_at": datetime.now(timezone.utc),
                "last_login": None
            }
            result = self.db.users.insert_one(user)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Dict:
        """Get user by username"""
        try:
            user = self.db.users.find_one({"username": username})
            if user:
                user["id"] = str(user["_id"])
                del user["_id"]
            return user
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def update_user_login(self, username: str) -> bool:
        """Update user's last login time"""
        try:
            result = self.db.users.update_one(
                {"username": username},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user login: {e}")
            return False
    
    # Audit trail operations
    def add_audit_entry(self, username: str, action: str, table_name: str = None, 
                       record_id: str = None, details: str = None) -> str:
        """Add an audit trail entry"""
        try:
            audit_entry = {
                "username": username,
                "action": action,
                "table_name": table_name,
                "record_id": record_id,
                "details": details,
                "timestamp": datetime.now(timezone.utc)
            }
            result = self.db.audit_trail.insert_one(audit_entry)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error adding audit entry: {e}")
            return None
    
    def get_audit_trail(self, username: str = None, action: str = None, 
                       table_name: str = None, limit: int = 100) -> List[Dict]:
        """Get audit trail entries"""
        try:
            query = {}
            if username:
                query["username"] = username
            if action:
                query["action"] = action
            if table_name:
                query["table_name"] = table_name
                
            audit_entries = list(
                self.db.audit_trail.find(query)
                .sort("timestamp", -1)
                .limit(limit)
            )
            
            # Convert ObjectIds to strings
            for entry in audit_entries:
                entry["id"] = str(entry["_id"])
                del entry["_id"]
                
            return audit_entries
        except Exception as e:
            logger.error(f"Error getting audit trail: {e}")
            return []
    
    # Utility methods
    def get_database_info(self) -> Dict:
        """Get database information"""
        try:
            info = {
                "database_name": self.database_name,
                "connection_string": self.connection_string,
                "collections": {},
                "total_documents": 0
            }
            
            for collection_name in self.db.list_collection_names():
                count = self.db[collection_name].count_documents({})
                info["collections"][collection_name] = count
                info["total_documents"] += count
                
            return info
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {}
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a simple JSON backup of the database"""
        try:
            import json
            
            backup_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "database_name": self.database_name,
                "collections": {}
            }
            
            for collection_name in self.db.list_collection_names():
                documents = list(self.db[collection_name].find())
                # Convert ObjectIds and datetime objects to strings
                for doc in documents:
                    self._convert_bson_types(doc)
                backup_data["collections"][collection_name] = documents
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, default=str)
                
            logger.info(f"Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
    
    def _convert_bson_types(self, obj):
        """Convert BSON types to JSON-serializable types"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, ObjectId):
                    obj[key] = str(value)
                elif isinstance(value, datetime):
                    obj[key] = value.isoformat()
                elif isinstance(value, (dict, list)):
                    self._convert_bson_types(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, ObjectId):
                    obj[i] = str(item)
                elif isinstance(item, datetime):
                    obj[i] = item.isoformat()
                elif isinstance(item, (dict, list)):
                    self._convert_bson_types(item)
    
    def clear_all_data(self) -> bool:
        """Clear all data from the database (use with caution)"""
        try:
            collections = ['customers', 'products', 'entries', 'transactions', 'users', 'audit_trail']
            for collection_name in collections:
                result = self.db[collection_name].delete_many({})
                logger.info(f"Cleared {result.deleted_count} documents from {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            return False