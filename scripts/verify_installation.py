"""
Verify that the data ingestion module is properly installed
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all critical imports"""
    print("\n🔍 Testing imports...")
    
    try:
        from backend.database import ExternalDataSource, SyncLog
        print("✅ Database models imported")
    except Exception as e:
        print(f"❌ Database models failed: {e}")
        return False
    
    try:
        from Agent.data_ingestion.db_connector import ExternalDBConnector
        print("✅ DB Connector imported")
    except Exception as e:
        print(f"❌ DB Connector failed: {e}")
        return False
    
    try:
        from Agent.data_ingestion.document_processor import ExternalDocumentProcessor
        print("✅ Document Processor imported")
    except Exception as e:
        print(f"❌ Document Processor failed: {e}")
        return False
    
    try:
        from Agent.data_ingestion.sync_service import SyncService
        print("✅ Sync Service imported")
    except Exception as e:
        print(f"❌ Sync Service failed: {e}")
        return False
    
    try:
        from Agent.data_ingestion.scheduler import get_scheduler
        print("✅ Scheduler imported")
    except Exception as e:
        print(f"❌ Scheduler failed: {e}")
        return False
    
    try:
        from backend.routers import data_source_router
        print("✅ API Router imported")
    except Exception as e:
        print(f"❌ API Router failed: {e}")
        return False
    
    return True


def test_encryption():
    """Test encryption functionality"""
    print("\n🔐 Testing encryption...")
    
    try:
        import os
        from cryptography.fernet import Fernet
        from Agent.data_ingestion.db_connector import ExternalDBConnector
        
        # Check if key exists
        key = os.getenv("DB_ENCRYPTION_KEY")
        if not key:
            print("❌ DB_ENCRYPTION_KEY not found in environment")
            return False
        
        print(f"✅ Encryption key found: {key[:20]}...")
        
        # Test encryption/decryption
        connector = ExternalDBConnector()
        test_password = "test_password_123"
        encrypted = connector.encrypt_password(test_password)
        decrypted = connector.decrypt_password(encrypted)
        
        if decrypted == test_password:
            print("✅ Encryption/decryption working")
            return True
        else:
            print("❌ Encryption/decryption failed")
            return False
    
    except Exception as e:
        print(f"❌ Encryption test failed: {e}")
        return False


def test_database():
    """Test database connection"""
    print("\n🗄️  Testing database...")
    
    try:
        from backend.database import engine, ExternalDataSource, SyncLog
        from sqlalchemy import inspect
        
        # Check if tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'external_data_sources' in tables:
            print("✅ external_data_sources table exists")
        else:
            print("❌ external_data_sources table not found")
            return False
        
        if 'sync_logs' in tables:
            print("✅ sync_logs table exists")
        else:
            print("❌ sync_logs table not found")
            return False
        
        return True
    
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def main():
    print("="*60)
    print("Data Ingestion Module - Installation Verification")
    print("="*60)
    
    results = []
    
    # Test imports
    results.append(("Imports", test_imports()))
    
    # Test encryption
    results.append(("Encryption", test_encryption()))
    
    # Test database
    results.append(("Database", test_database()))
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 All tests passed! Installation successful.")
        print("\nNext steps:")
        print("1. Start server: uvicorn backend.main:app --reload")
        print("2. Visit API docs: http://localhost:8000/docs")
        print("3. Register data sources via API")
        print("\nDocumentation:")
        print("- Quick Reference: QUICK_REFERENCE_DATA_INGESTION.md")
        print("- Complete Guide: DATA_INGESTION_GUIDE.md")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
