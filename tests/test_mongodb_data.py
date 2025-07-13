# test_mongodb_data.py
# Run this script to test your MongoDB connection and data

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.mongo_adapter import MongoAdapter
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mongodb_connection_and_data():
    """Test MongoDB connection and data retrieval"""
    print("=" * 60)
    print("TESTING MONGODB CONNECTION AND DATA")
    print("=" * 60)
    
    try:
        # Create MongoDB adapter
        print("1. Creating MongoDB adapter...")
        adapter = MongoAdapter()
        
        # Test connection
        print("2. Testing connection...")
        if adapter.connect():
            print("✅ MongoDB connection successful!")
        else:
            print("❌ MongoDB connection failed!")
            return False
        
        # Test data retrieval
        print("3. Testing data retrieval...")
        test_results = adapter.test_data_retrieval()
        
        print("\n📊 DATA SUMMARY:")
        print(f"   Customers: {test_results.get('customers', 0)}")
        print(f"   Products: {test_results.get('products', 0)}")
        print(f"   Entries: {test_results.get('entries', 0)}")
        print(f"   Transactions: {test_results.get('transactions', 0)}")
        
        # Test SQL compatibility
        print("\n4. Testing SQL compatibility...")
        
        # Test customer query
        print("   Testing customer query...")
        customer_results = adapter.execute("SELECT * FROM customers")
        print(f"   Customer query returned {len(customer_results)} results")
        
        # Test product query
        print("   Testing product query...")
        product_results = adapter.execute("SELECT * FROM products")
        print(f"   Product query returned {len(product_results)} results")
        
        # Test sales query
        print("   Testing sales query...")
        sales_results = adapter.execute("SELECT SUM(quantity * unit_price) FROM entries WHERE is_credit = 1")
        print(f"   Sales query returned: {sales_results}")
        
        # Test count query
        print("   Testing count query...")
        count_results = adapter.execute("SELECT COUNT(*) FROM entries")
        print(f"   Count query returned: {count_results}")
        
        print("\n✅ All tests completed successfully!")
        
        # Check if data exists
        total_records = sum([
            test_results.get('customers', 0),
            test_results.get('products', 0),
            test_results.get('entries', 0),
            test_results.get('transactions', 0)
        ])
        
        if total_records == 0:
            print("\n⚠️  WARNING: No data found in MongoDB!")
            print("   This might be why your UI shows no data.")
            print("   Consider running the migration script again:")
            print("   python migration/sqlite_to_mongo.py --sqlite-path data/medtran.db")
        else:
            print(f"\n🎉 Found {total_records} total records in MongoDB!")
            print("   Your data should be visible in the UI.")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_ui_queries():
    """Test the specific queries that UI components use"""
    print("\n" + "=" * 60)
    print("TESTING UI-SPECIFIC QUERIES")
    print("=" * 60)
    
    try:
        adapter = MongoAdapter()
        adapter.connect()
        
        # Test dashboard KPI queries
        print("Testing dashboard KPI queries...")
        
        # Current month sales
        from datetime import date
        current_month_start = date.today().replace(day=1).strftime("%Y-%m-%d")
        
        sales_query = f"""
            SELECT SUM(quantity * unit_price) 
            FROM entries 
            WHERE is_credit = 1 AND date >= '{current_month_start}'
        """
        
        sales_result = adapter.execute(sales_query)
        print(f"   Current month sales: {sales_result}")
        
        # Transaction count
        count_query = f"""
            SELECT COUNT(*) 
            FROM entries 
            WHERE date >= '{current_month_start}'
        """
        
        count_result = adapter.execute(count_query)
        print(f"   Current month transactions: {count_result}")
        
        # Balance query
        balance_query = "SELECT MAX(balance) FROM transactions"
        balance_result = adapter.execute(balance_query)
        print(f"   Current balance: {balance_result}")
        
        # Product distribution query
        product_query = """
            SELECT p.name, SUM(e.quantity * e.unit_price) as total,
                   COUNT(DISTINCT p.batch_number) as batch_count
            FROM entries e
            JOIN products p ON e.product_id = p.id
            WHERE e.is_credit = 1
            GROUP BY p.name
            ORDER BY total DESC
            LIMIT 5
        """
        
        product_result = adapter.execute(product_query)
        print(f"   Product distribution: {len(product_result)} products found")
        
        return True
        
    except Exception as e:
        print(f"❌ UI query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_mongodb_connection_and_data()
    success2 = test_specific_ui_queries()
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your MongoDB adapter should work with the UI.")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Please check the errors above and fix them.")