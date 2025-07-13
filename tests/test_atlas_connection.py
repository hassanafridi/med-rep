# test_atlas_connection.py

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.mongo_db import MongoDB

def test_connection():
    """Test MongoDB Atlas connection"""
    print("Testing MongoDB Atlas connection...")
    print("=" * 50)
    
    try:
        # Create MongoDB instance (uses your Atlas connection)
        mongo_db = MongoDB()
        
        print("Attempting to connect to MongoDB Atlas...")
        if mongo_db.connect():
            print("✅ Successfully connected to MongoDB Atlas!")
            
            # Get database info
            info = mongo_db.get_database_info()
            print(f"\nDatabase Information:")
            print(f"  - Database Name: {info.get('database_name', 'Unknown')}")
            print(f"  - Total Collections: {len(info.get('collections', {}))}")
            print(f"  - Total Documents: {info.get('total_documents', 0)}")
            
            # List collections
            collections = info.get('collections', {})
            if collections:
                print(f"\nCollections:")
                for collection_name, count in collections.items():
                    print(f"  - {collection_name}: {count} documents")
            else:
                print("\nNo collections found (database is empty)")
            
            # Test basic operations
            print(f"\nTesting basic operations...")
            
            # Test sample data insertion
            if mongo_db.insert_sample_data():
                print("✅ Sample data insertion test passed")
            else:
                print("❌ Sample data insertion test failed")
            
            # Test customer operations
            customers = mongo_db.get_customers()
            print(f"✅ Retrieved {len(customers)} customers")
            
            # Test product operations
            products = mongo_db.get_products()
            print(f"✅ Retrieved {len(products)} products")
            
            mongo_db.close()
            print(f"\n🎉 MongoDB Atlas connection test completed successfully!")
            print(f"Your database is ready for migration.")
            
            return True
            
        else:
            print("❌ Failed to connect to MongoDB Atlas")
            print("\nPossible issues:")
            print("1. Check your internet connection")
            print("2. Verify MongoDB Atlas cluster is running")
            print("3. Check if your IP address is whitelisted in Atlas")
            print("4. Verify the connection string in mongo_db.py")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed with error: {str(e)}")
        print("\nPossible solutions:")
        print("1. Install required dependencies: pip install pymongo dnspython")
        print("2. Check your MongoDB Atlas connection string")
        print("3. Ensure your IP is whitelisted in MongoDB Atlas")
        print("4. Verify your Atlas username and password")
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        print(f"\n" + "="*50)
        print("READY FOR MIGRATION!")
        print("="*50)
        print("You can now run the migration with:")
        print("python migration/sqlite_to_mongo_atlas.py --sqlite-path data/medtran.db --create-backup")
    else:
        print(f"\n" + "="*50)
        print("CONNECTION ISSUES FOUND")
        print("="*50)
        print("Please fix the connection issues before running migration.")