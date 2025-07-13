# Enhanced test_ui_data.py - Complete UI data flow testing

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.mongo_adapter import MongoAdapter
import logging

# Setup detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mongodb_connection():
    """Test basic MongoDB connectivity"""
    print("=" * 70)
    print("STEP 1: TESTING MONGODB CONNECTION")
    print("=" * 70)
    
    try:
        adapter = MongoAdapter()
        
        print("🔍 Testing MongoDB connection...")
        if adapter.connect():
            print("✅ MongoDB connection successful!")
            
            # Test direct MongoDB queries
            customer_count = adapter.mongo_db.db.customers.count_documents({})
            product_count = adapter.mongo_db.db.products.count_documents({})
            entry_count = adapter.mongo_db.db.entries.count_documents({})
            transaction_count = adapter.mongo_db.db.transactions.count_documents({})
            
            print(f"📊 Direct MongoDB counts:")
            print(f"   - Customers: {customer_count}")
            print(f"   - Products: {product_count}")
            print(f"   - Entries: {entry_count}")
            print(f"   - Transactions: {transaction_count}")
            
            return adapter, True
        else:
            print("❌ MongoDB connection failed!")
            return None, False
            
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        import traceback
        traceback.print_exc()
        return None, False

def test_adapter_methods(adapter):
    """Test MongoAdapter data retrieval methods"""
    print("\n" + "=" * 70)
    print("STEP 2: TESTING MONGOADAPTER DATA METHODS")
    print("=" * 70)
    
    try:
        print("🔍 Testing get_customers()...")
        customers = adapter.get_customers()
        print(f"   Result: {len(customers)} customers found")
        if customers:
            print(f"   Sample customer: {customers[0]}")
            # Check data structure
            sample = customers[0]
            required_keys = ['id', 'name', 'contact', 'address']
            missing_keys = [key for key in required_keys if key not in sample]
            if missing_keys:
                print(f"   ⚠️  Missing keys in customer data: {missing_keys}")
            else:
                print("   ✅ Customer data structure is correct")
        else:
            print("   ❌ No customers returned!")
            return False
        
        print("\n🔍 Testing get_products()...")
        products = adapter.get_products()
        print(f"   Result: {len(products)} products found")
        if products:
            print(f"   Sample product: {products[0]}")
            # Check data structure
            sample = products[0]
            required_keys = ['id', 'name', 'description', 'unit_price', 'batch_number', 'expiry_date']
            missing_keys = [key for key in required_keys if key not in sample]
            if missing_keys:
                print(f"   ⚠️  Missing keys in product data: {missing_keys}")
            else:
                print("   ✅ Product data structure is correct")
        else:
            print("   ❌ No products returned!")
            return False
        
        print("\n🔍 Testing get_entries()...")
        entries = adapter.get_entries()
        print(f"   Result: {len(entries)} entries found")
        if entries:
            print(f"   Sample entry: {entries[0]}")
        
        print("\n🔍 Testing get_transactions()...")
        transactions = adapter.get_transactions()
        print(f"   Result: {len(transactions)} transactions found")
        if transactions:
            print(f"   Sample transaction: {transactions[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Adapter methods test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sql_queries(adapter):
    """Test SQL-style queries used by UI"""
    print("\n" + "=" * 70)
    print("STEP 3: TESTING SQL-STYLE QUERIES")
    print("=" * 70)
    
    test_queries = [
        "SELECT * FROM customers",
        "SELECT * FROM products", 
        "SELECT * FROM entries",
        "SELECT * FROM transactions",
        "SELECT COUNT(*) FROM customers",
        "SELECT COUNT(*) FROM products",
        "SELECT COUNT(*) FROM entries",
        "SELECT SUM(quantity * unit_price) FROM entries WHERE is_credit = 1",
        "SELECT SUM(quantity * unit_price) FROM entries WHERE is_credit = 0",
        "SELECT MAX(balance) FROM transactions"
    ]
    
    all_passed = True
    
    for query in test_queries:
        try:
            print(f"\n🔍 Testing: {query}")
            result = adapter.execute(query)
            print(f"   ✅ Result: {len(result) if isinstance(result, list) else 'N/A'} rows")
            if result and len(result) > 0:
                print(f"   Sample: {result[0] if len(result[0]) <= 5 else str(result[0])[:100] + '...'}")
            else:
                print("   ⚠️  No results returned")
                if "SELECT *" in query:
                    print("   ❌ This is a problem - UI components need this data!")
                    all_passed = False
                    
        except Exception as e:
            print(f"   ❌ Query failed: {e}")
            all_passed = False
    
    return all_passed

def test_fetchall_compatibility(adapter):
    """Test fetchall() method used by UI components"""
    print("\n" + "=" * 70)
    print("STEP 4: TESTING FETCHALL() COMPATIBILITY")
    print("=" * 70)
    
    try:
        print("🔍 Testing execute() + fetchall() pattern...")
        
        # This is how many UI components work
        adapter.execute("SELECT * FROM customers")
        customers_fetchall = adapter.fetchall()
        print(f"   execute() + fetchall() for customers: {len(customers_fetchall)} results")
        
        adapter.execute("SELECT * FROM products")
        products_fetchall = adapter.fetchall()
        print(f"   execute() + fetchall() for products: {len(products_fetchall)} results")
        
        if len(customers_fetchall) > 0 and len(products_fetchall) > 0:
            print("   ✅ fetchall() compatibility working correctly")
            return True
        else:
            print("   ❌ fetchall() not returning data - this will cause empty dropdowns!")
            return False
            
    except Exception as e:
        print(f"❌ fetchall() compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_dropdown_data(adapter):
    """Test data format expected by UI dropdowns"""
    print("\n" + "=" * 70)
    print("STEP 5: TESTING UI DROPDOWN DATA FORMAT")
    print("=" * 70)
    
    try:
        print("🔍 Testing customer dropdown data...")
        customers = adapter.get_customers()
        
        print("   Expected format for customer dropdowns:")
        for i, customer in enumerate(customers[:3]):
            customer_id = customer.get('id', 'NO_ID')
            customer_name = customer.get('name', 'NO_NAME')
            print(f"   Customer {i+1}: ID='{customer_id}' Name='{customer_name}'")
            
            # Check if ID and name are valid
            if not customer_id or customer_id == 'NO_ID':
                print(f"   ❌ Customer {i+1} has no valid ID!")
                return False
            if not customer_name or customer_name == 'NO_NAME':
                print(f"   ❌ Customer {i+1} has no valid name!")
                return False
        
        print("\n🔍 Testing product dropdown data...")
        products = adapter.get_products()
        
        print("   Expected format for product dropdowns:")
        for i, product in enumerate(products[:3]):
            product_id = product.get('id', 'NO_ID')
            product_name = product.get('name', 'NO_NAME')
            print(f"   Product {i+1}: ID='{product_id}' Name='{product_name}'")
            
            # Check if ID and name are valid
            if not product_id or product_id == 'NO_ID':
                print(f"   ❌ Product {i+1} has no valid ID!")
                return False
            if not product_name or product_name == 'NO_NAME':
                print(f"   ❌ Product {i+1} has no valid name!")
                return False
        
        print("   ✅ Dropdown data format is correct")
        return True
        
    except Exception as e:
        print(f"❌ Dropdown data test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dashboard_kpi_queries(adapter):
    """Test specific queries used by dashboard KPIs"""
    print("\n" + "=" * 70)
    print("STEP 6: TESTING DASHBOARD KPI QUERIES")
    print("=" * 70)
    
    try:
        from datetime import date
        
        # Get current month start date
        current_month_start = date.today().replace(day=1).strftime("%Y-%m-%d")
        print(f"🔍 Using current month start: {current_month_start}")
        
        # Test KPI queries with real parameters
        kpi_queries = [
            (f"SELECT SUM(quantity * unit_price) FROM entries WHERE is_credit = 1 AND date >= '{current_month_start}'", "Current month sales"),
            (f"SELECT COUNT(*) FROM entries WHERE date >= '{current_month_start}'", "Current month transactions"),
            ("SELECT MAX(balance) FROM transactions", "Current balance"),
            ("SELECT SUM(quantity * unit_price) FROM entries WHERE is_credit = 1", "Total sales"),
            ("SELECT COUNT(*) FROM entries", "Total entries")
        ]
        
        all_passed = True
        results = {}
        
        for query, description in kpi_queries:
            try:
                print(f"\n🔍 Testing {description}...")
                print(f"   Query: {query}")
                result = adapter.execute(query)
                print(f"   Result: {result}")
                
                if result and len(result) > 0 and len(result[0]) > 0:
                    value = result[0][0]
                    results[description] = value
                    print(f"   ✅ {description}: {value}")
                else:
                    print(f"   ❌ {description}: No result!")
                    all_passed = False
                    
            except Exception as e:
                print(f"   ❌ {description} failed: {e}")
                all_passed = False
        
        if all_passed:
            print(f"\n📊 KPI Summary:")
            for desc, value in results.items():
                print(f"   - {desc}: {value}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Dashboard KPI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manage_data_tab_queries(adapter):
    """Test queries used by Manage Data tab"""
    print("\n" + "=" * 70)
    print("STEP 7: TESTING MANAGE DATA TAB QUERIES")
    print("=" * 70)
    
    try:
        print("🔍 Testing Manage Data tab table population...")
        
        # Test customer table data
        print("\n   Customer table test:")
        customers = adapter.get_customers()
        if customers:
            print(f"   ✅ {len(customers)} customers available for table")
            print("   | ID | Name | Contact | Address |")
            print("   " + "-" * 50)
            for customer in customers[:3]:
                print(f"   | {customer.get('id', '')[:8]}... | {customer.get('name', '')[:15]} | {customer.get('contact', '')[:10]} | {customer.get('address', '')[:15]} |")
        else:
            print("   ❌ No customers for table!")
            return False
        
        # Test product table data
        print("\n   Product table test:")
        products = adapter.get_products()
        if products:
            print(f"   ✅ {len(products)} products available for table")
            print("   | ID | Name | Description | Price | Batch | Expiry |")
            print("   " + "-" * 70)
            for product in products[:3]:
                print(f"   | {product.get('id', '')[:8]}... | {product.get('name', '')[:10]} | {product.get('description', '')[:10]} | {product.get('unit_price', 0)} | {product.get('batch_number', '')[:8]} | {product.get('expiry_date', '')} |")
        else:
            print("   ❌ No products for table!")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Manage Data tab test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_new_entry_dropdown_data(adapter):
    """Test data for New Entry tab dropdowns"""
    print("\n" + "=" * 70)
    print("STEP 8: TESTING NEW ENTRY TAB DROPDOWN DATA")
    print("=" * 70)
    
    try:
        print("🔍 Testing New Entry tab dropdown requirements...")
        
        # Test customer dropdown
        customers = adapter.get_customers()
        print(f"\n   Customer dropdown: {len(customers)} options")
        if customers:
            for i, customer in enumerate(customers[:3]):
                display_text = f"{customer.get('name', 'Unknown')} ({customer.get('contact', 'No contact')})"
                print(f"   Option {i+1}: '{display_text}' -> ID: {customer.get('id', 'NO_ID')}")
        else:
            print("   ❌ No customers for dropdown!")
            return False
        
        # Test product dropdown
        products = adapter.get_products()
        print(f"\n   Product dropdown: {len(products)} options")
        if products:
            for i, product in enumerate(products[:3]):
                display_text = f"{product.get('name', 'Unknown')} - {product.get('batch_number', 'No batch')} (Rs. {product.get('unit_price', 0)})"
                print(f"   Option {i+1}: '{display_text}' -> ID: {product.get('id', 'NO_ID')}")
        else:
            print("   ❌ No products for dropdown!")
            return False
        
        print("   ✅ New Entry dropdown data is ready")
        return True
        
    except Exception as e:
        print(f"❌ New Entry dropdown test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_comprehensive_test():
    """Run all tests in sequence"""
    print("🚀 STARTING COMPREHENSIVE UI DATA FLOW TEST")
    print("This will test every aspect of your MongoDB → UI data flow\n")
    
    # Step 1: Test MongoDB connection
    adapter, connection_ok = test_mongodb_connection()
    if not connection_ok:
        print("\n💥 CRITICAL FAILURE: Cannot connect to MongoDB!")
        print("Fix MongoDB connection before proceeding.")
        return False
    
    # Step 2: Test adapter methods
    adapter_ok = test_adapter_methods(adapter)
    if not adapter_ok:
        print("\n💥 CRITICAL FAILURE: MongoAdapter methods not working!")
        print("Fix adapter data retrieval methods.")
        return False
    
    # Step 3: Test SQL queries
    sql_ok = test_sql_queries(adapter)
    if not sql_ok:
        print("\n⚠️  SQL query issues detected - this will cause UI problems!")
    
    # Step 4: Test fetchall compatibility
    fetchall_ok = test_fetchall_compatibility(adapter)
    if not fetchall_ok:
        print("\n💥 CRITICAL FAILURE: fetchall() not working!")
        print("Many UI components use execute() + fetchall() pattern.")
        return False
    
    # Step 5: Test dropdown data
    dropdown_ok = test_ui_dropdown_data(adapter)
    if not dropdown_ok:
        print("\n💥 CRITICAL FAILURE: Dropdown data format issues!")
        return False
    
    # Step 6: Test dashboard KPIs
    kpi_ok = test_dashboard_kpi_queries(adapter)
    if not kpi_ok:
        print("\n⚠️  Dashboard KPI issues detected!")
    
    # Step 7: Test manage data tab
    manage_ok = test_manage_data_tab_queries(adapter)
    if not manage_ok:
        print("\n⚠️  Manage Data tab issues detected!")
    
    # Step 8: Test new entry dropdowns
    entry_ok = test_new_entry_dropdown_data(adapter)
    if not entry_ok:
        print("\n⚠️  New Entry tab dropdown issues detected!")
    
    # Final summary
    print("\n" + "=" * 70)
    print("🏁 COMPREHENSIVE TEST RESULTS")
    print("=" * 70)
    
    tests = [
        ("MongoDB Connection", connection_ok),
        ("Adapter Methods", adapter_ok),
        ("SQL Queries", sql_ok),
        ("Fetchall Compatibility", fetchall_ok),
        ("Dropdown Data", dropdown_ok),
        ("Dashboard KPIs", kpi_ok),
        ("Manage Data Tab", manage_ok),
        ("New Entry Dropdowns", entry_ok)
    ]
    
    passed = sum(1 for _, ok in tests if ok)
    total = len(tests)
    
    for test_name, ok in tests:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n📊 Overall Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your MongoDB adapter should work perfectly with the UI.")
        print("\nIf UI still shows no data:")
        print("1. Restart your application completely")
        print("2. Check browser console for JavaScript errors")
        print("3. Verify UI components are using the correct methods")
    elif passed >= 6:
        print("\n🔄 MOSTLY WORKING - Minor issues detected")
        print("Your UI should show some data, but there may be issues with specific features.")
    else:
        print("\n💥 MAJOR ISSUES DETECTED")
        print("Significant problems found. UI likely won't show data properly.")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    
    print(f"\n{'='*70}")
    print("🔧 NEXT STEPS:")
    print("="*70)
    
    if success:
        print("1. Run: python main.py")
        print("2. Check all tabs for data")
        print("3. Test dropdown functionality")
        print("4. If issues persist, check UI component implementations")
    else:
        print("1. Fix the failing tests above")
        print("2. Re-run this test script")
        print("3. Only start the application after all tests pass")