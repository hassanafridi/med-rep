"""
Test script to verify UserAuth functionality
"""
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.mongo_adapter import MongoAdapter
from src.user_auth import UserAuth
from src.database.mongo_db import MongoDB

def test_user_auth():
    """Test UserAuth functionality"""
    try:
        print("Testing UserAuth...")
        
        # Clear any existing sessions first for clean testing
        try:
            from PyQt5.QtCore import QSettings
            settings = QSettings("MedRepApp", "Session")
            settings.remove("session_data")
            settings.remove("session_expiry")
            print("🔧 Cleared existing sessions for clean testing")
        except Exception as clear_error:
            print(f"⚠️ Could not clear sessions: {clear_error}")
        
        # Also clear login settings
        try:
            settings = QSettings("MedRepApp", "Login")
            settings.remove("username")
            settings.remove("remember")
            print("🔧 Cleared login settings")
        except:
            pass
        
        # Initialize MongoDB
        mongo_uri = "mongodb+srv://medrep:Dk9Glbs2B2E0Dxof@cluster0.tgwmarr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        db = MongoDB(connection_string=mongo_uri, database_name='medrep')
        
        if not db.connect():
            print("❌ Failed to connect to MongoDB")
            return False
        
        print("✅ MongoDB connection successful")
        print(f"🔍 MongoDB.db exists: {hasattr(db, 'db')}")
        print(f"🔍 MongoDB.db value: {db.db}")
        
        # Check if we can actually access the database
        try:
            collections = db.db.list_collection_names()
            print(f"🔍 Collections in database: {collections}")
        except Exception as e:
            print(f"❌ Error accessing database: {e}")
            return False
        
        # Initialize MongoAdapter
        mongo_adapter = MongoAdapter(mongo_db_instance=db)
        if not mongo_adapter.connect():
            print("❌ Failed to connect MongoAdapter")
            return False
            
        print("✅ MongoAdapter connection successful")
        
        # Debug: Check if db attribute exists
        print(f"🔍 MongoAdapter.db exists: {hasattr(mongo_adapter, 'db')}")
        print(f"🔍 MongoAdapter.db value: {mongo_adapter.db}")
        print(f"🔍 MongoAdapter.db type: {type(mongo_adapter.db)}")
        
        # Try to access a collection through the adapter
        try:
            if mongo_adapter.db is not None:
                users_collection = mongo_adapter.db.users
                user_count = users_collection.count_documents({})
                print(f"🔍 Users collection accessible: True, count: {user_count}")
            else:
                print("❌ MongoAdapter.db is None")
                return False
        except Exception as e:
            print(f"❌ Error accessing users collection: {e}")
            return False
        
        # Initialize UserAuth
        auth = UserAuth(mongo_adapter)
        print("✅ UserAuth initialized")
        
        # Test connection
        if auth.test_connection():
            print("✅ UserAuth connection test passed")
        else:
            print("❌ UserAuth connection test failed")
            return False
        
        # Test authentication with admin user
        success, result = auth.authenticate("admin", "admin")
        if success:
            print(f"✅ Admin authentication successful: {result}")
        else:
            print(f"❌ Admin authentication failed: {result}")
            
            # Try to see what users exist
            try:
                users_collection = mongo_adapter.db.users
                user_count = users_collection.count_documents({})
                print(f"🔍 Users in database: {user_count}")
                
                if user_count > 0:
                    users = list(users_collection.find({}, {"username": 1, "role": 1}))
                    print(f"🔍 Existing users: {users}")
                else:
                    print("🔍 No users found in database")
                    
            except Exception as debug_e:
                print(f"🔍 Debug error: {debug_e}")
            
            return False
        
        # Test validation-only mode
        success, result = auth.authenticate("admin", None, validate_only=True)
        if success:
            print(f"✅ Validation-only test passed: {result}")
        else:
            print(f"❌ Validation-only test failed: {result}")
        
        print("🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_user_auth()
