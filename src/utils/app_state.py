"""
Centralized Application State Management with Caching
Prevents redundant database calls and provides automatic UI updates
"""

from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading


class AppState(QObject):
    """
    Singleton class for managing application state with caching
    Emits signals when data changes to update all UI components
    """

    # Signals for data changes
    customers_changed = pyqtSignal()
    products_changed = pyqtSignal()
    entries_changed = pyqtSignal()

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(AppState, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        super().__init__()
        self._initialized = True

        # Cache storage
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

        # Cache expiration times (in seconds)
        self._cache_ttl = {
            'customers': 300,      # 5 minutes
            'products': 300,       # 5 minutes
            'entries': 60,         # 1 minute (more frequent updates)
            'customer_names': 300,
            'product_names': 300,
        }

        # Database adapter (will be set by main app)
        self._db = None

        print("AppState initialized")

    def set_database(self, db):
        """Set the database adapter"""
        self._db = db
        print("Database adapter set in AppState")

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache_timestamps:
            return False

        age = datetime.now() - self._cache_timestamps[key]
        ttl = self._cache_ttl.get(key, 60)

        is_valid = age.total_seconds() < ttl
        if not is_valid:
            print(f"Cache expired for '{key}' (age: {age.total_seconds():.1f}s, TTL: {ttl}s)")

        return is_valid

    def _set_cache(self, key: str, value: Any):
        """Store data in cache with timestamp"""
        self._cache[key] = value
        self._cache_timestamps[key] = datetime.now()
        print(f"Cache updated for '{key}' with {len(value) if isinstance(value, list) else 'data'} items")

    def _get_cache(self, key: str) -> Optional[Any]:
        """Get cached data if valid"""
        if self._is_cache_valid(key):
            print(f"Cache hit for '{key}'")
            return self._cache[key]

        print(f"Cache miss for '{key}'")
        return None

    def invalidate_cache(self, key: str = None):
        """Invalidate cache for specific key or all cache"""
        if key:
            if key in self._cache:
                del self._cache[key]
            if key in self._cache_timestamps:
                del self._cache_timestamps[key]
            print(f"Cache invalidated for '{key}'")
        else:
            self._cache.clear()
            self._cache_timestamps.clear()
            print("All cache invalidated")

    # Customer data management
    def get_customers(self, force_refresh: bool = False) -> List[Dict]:
        """Get customers with caching"""
        if not force_refresh:
            cached = self._get_cache('customers')
            if cached is not None:
                return cached

        if not self._db:
            print("Warning: Database not set in AppState")
            return []

        print("Fetching customers from database...")
        customers = self._db.get_customers()
        self._set_cache('customers', customers)
        return customers

    def get_customer_names(self, force_refresh: bool = False) -> Dict[str, str]:
        """Get customer name mapping with caching"""
        if not force_refresh:
            cached = self._get_cache('customer_names')
            if cached is not None:
                return cached

        customers = self.get_customers(force_refresh)
        customer_names = {
            f"{c.get('name', '')} - {c.get('address', '').split(chr(10))[0] if c.get('address') else ''}": str(c.get('id', ''))
            for c in customers
        }

        self._set_cache('customer_names', customer_names)
        return customer_names

    def add_customer(self, name: str, address: str, contact: str) -> bool:
        """Add customer and invalidate cache"""
        if not self._db:
            return False

        success = self._db.add_customer(name, address, contact)
        if success:
            print("Customer added, invalidating cache...")
            self.invalidate_cache('customers')
            self.invalidate_cache('customer_names')
            self.customers_changed.emit()

        return success

    def update_customer(self, customer_id: str, name: str, address: str, contact: str) -> bool:
        """Update customer and invalidate cache"""
        if not self._db:
            return False

        success = self._db.update_customer(customer_id, name, address, contact)
        if success:
            print("Customer updated, invalidating cache...")
            self.invalidate_cache('customers')
            self.invalidate_cache('customer_names')
            self.customers_changed.emit()

        return success

    def delete_customer(self, customer_id: str) -> bool:
        """Delete customer and invalidate cache"""
        if not self._db:
            return False

        success = self._db.mongo_db.delete_customer(customer_id)
        if success:
            print("Customer deleted, invalidating cache...")
            self.invalidate_cache('customers')
            self.invalidate_cache('customer_names')
            self.customers_changed.emit()

        return success

    # Product data management
    def get_products(self, force_refresh: bool = False) -> List[Dict]:
        """Get products with caching"""
        if not force_refresh:
            cached = self._get_cache('products')
            if cached is not None:
                return cached

        if not self._db:
            print("Warning: Database not set in AppState")
            return []

        print("Fetching products from database...")
        products = self._db.get_products()
        self._set_cache('products', products)
        return products

    def get_product_names(self, force_refresh: bool = False) -> Dict[str, str]:
        """Get product name mapping with caching"""
        if not force_refresh:
            cached = self._get_cache('product_names')
            if cached is not None:
                return cached

        products = self.get_products(force_refresh)
        product_names = {
            p.get('name', ''): str(p.get('id', ''))
            for p in products
        }

        self._set_cache('product_names', product_names)
        return product_names

    def add_product(self, name: str, description: str = '', unit_price: float = 0.0,
                    batch_number: str = '', expiry_date: str = '', mrp: float = 0.0) -> bool:
        """Add product and invalidate cache"""
        if not self._db:
            return False

        success = self._db.add_product(name, description, unit_price, batch_number, expiry_date, mrp)
        if success:
            print("Product added, invalidating cache...")
            self.invalidate_cache('products')
            self.invalidate_cache('product_names')
            self.products_changed.emit()

        return success

    def update_product(self, product_id: str, name: str, description: str = '',
                       unit_price: float = 0.0, batch_number: str = '',
                       expiry_date: str = '', mrp: float = 0.0) -> bool:
        """Update product and invalidate cache"""
        if not self._db:
            return False

        success = self._db.mongo_db.update_product(product_id, name, description, unit_price,
                                                   batch_number, expiry_date, mrp)
        if success:
            print("Product updated, invalidating cache...")
            self.invalidate_cache('products')
            self.invalidate_cache('product_names')
            self.products_changed.emit()

        return success

    def delete_product(self, product_id: str) -> bool:
        """Delete product and invalidate cache"""
        if not self._db:
            return False

        success = self._db.delete_product(product_id)
        if success:
            print("Product deleted, invalidating cache...")
            self.invalidate_cache('products')
            self.invalidate_cache('product_names')
            self.products_changed.emit()

        return success

    # Entry data management
    def get_entries(self, force_refresh: bool = False) -> List[Dict]:
        """Get entries with caching"""
        if not force_refresh:
            cached = self._get_cache('entries')
            if cached is not None:
                return cached

        if not self._db:
            print("Warning: Database not set in AppState")
            return []

        print("Fetching entries from database...")
        entries = self._db.get_entries()
        self._set_cache('entries', entries)
        return entries

    def add_entry(self, date: str, customer_id: str, product_id: str,
                  quantity: int, unit_price: float, is_credit: bool = False,
                  notes: str = '') -> bool:
        """Add entry and invalidate cache"""
        if not self._db:
            return False

        success = self._db.add_entry(date, customer_id, product_id, quantity,
                                     unit_price, is_credit, notes)
        if success:
            print("Entry added, invalidating cache...")
            self.invalidate_cache('entries')
            self.entries_changed.emit()

        return success

    def update_entry(self, entry_id: str, date: str, customer_id: str,
                     product_id: str, quantity: int, unit_price: float,
                     is_credit: bool = False, notes: str = '') -> bool:
        """Update entry and invalidate cache"""
        if not self._db:
            return False

        success = self._db.update_entry(entry_id, date, customer_id, product_id,
                                       quantity, unit_price, is_credit, notes)
        if success:
            print("Entry updated, invalidating cache...")
            self.invalidate_cache('entries')
            self.entries_changed.emit()

        return success

    def delete_entry(self, entry_id: str) -> bool:
        """Delete entry and invalidate cache"""
        if not self._db:
            return False

        success = self._db.delete_entry(entry_id)
        if success:
            print("Entry deleted, invalidating cache...")
            self.invalidate_cache('entries')
            self.entries_changed.emit()

        return success

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for debugging"""
        stats = {
            'cached_keys': list(self._cache.keys()),
            'cache_ages': {}
        }

        for key, timestamp in self._cache_timestamps.items():
            age = (datetime.now() - timestamp).total_seconds()
            ttl = self._cache_ttl.get(key, 60)
            stats['cache_ages'][key] = {
                'age_seconds': age,
                'ttl_seconds': ttl,
                'valid': age < ttl,
                'items': len(self._cache[key]) if isinstance(self._cache[key], list) else 'N/A'
            }

        return stats


# Global singleton instance
app_state = AppState()
