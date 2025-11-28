"""
Example script to register and test external data sources
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"


def test_connection(host, port, database, username, password):
    """Test database connection"""
    print(f"\n🔌 Testing connection to {host}...")
    
    response = requests.post(
        f"{BASE_URL}/data-sources/test-connection",
        json={
            "host": host,
            "port": port,
            "database_name": database,
            "username": username,
            "password": password
        }
    )
    
    result = response.json()
    if result["status"] == "success":
        print(f"✅ Connection successful!")
    else:
        print(f"❌ Connection failed: {result['message']}")
    
    return result["status"] == "success"


def register_data_source(config):
    """Register a new external data source"""
    print(f"\n📝 Registering data source: {config['name']}...")
    
    response = requests.post(
        f"{BASE_URL}/data-sources/create",
        json=config
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Data source registered! ID: {result['source_id']}")
        return result['source_id']
    else:
        print(f"❌ Registration failed: {response.json()}")
        return None


def trigger_sync(source_id, limit=None):
    """Trigger manual sync"""
    print(f"\n🔄 Triggering sync for source {source_id}...")
    
    url = f"{BASE_URL}/data-sources/{source_id}/sync"
    if limit:
        url += f"?limit={limit}"
    
    response = requests.post(url)
    result = response.json()
    
    print(f"✅ {result['message']}")
    return result


def check_sync_logs(source_id):
    """Check sync logs"""
    print(f"\n📊 Checking sync logs for source {source_id}...")
    
    response = requests.get(f"{BASE_URL}/data-sources/{source_id}/sync-logs")
    logs = response.json()
    
    if logs['total_logs'] == 0:
        print("No sync logs yet")
        return
    
    print(f"\nRecent syncs ({logs['total_logs']} total):")
    for log in logs['logs'][:5]:
        status_icon = "✅" if log['status'] == 'success' else "❌"
        print(f"{status_icon} {log['started_at']}: {log['documents_processed']}/{log['documents_fetched']} docs processed")
        if log['error_message']:
            print(f"   Error: {log['error_message']}")


def list_data_sources():
    """List all registered data sources"""
    print("\n📋 Registered Data Sources:")
    
    response = requests.get(f"{BASE_URL}/data-sources/list")
    sources = response.json()
    
    if sources['total'] == 0:
        print("No data sources registered yet")
        return []
    
    for source in sources['sources']:
        status_icon = "✅" if source['sync_enabled'] else "⏸️"
        print(f"\n{status_icon} {source['name']} (ID: {source['id']})")
        print(f"   Ministry: {source['ministry_name']}")
        print(f"   Host: {source['host']}")
        print(f"   Last Sync: {source['last_sync_at'] or 'Never'}")
        print(f"   Status: {source['last_sync_status'] or 'N/A'}")
        print(f"   Total Docs: {source['total_documents_synced']}")
    
    return sources['sources']


# Example configurations for different ministries
EXAMPLE_CONFIGS = {
    "moe": {
        "name": "MoE_Primary_DB",
        "ministry_name": "Ministry of Education",
        "description": "Primary database for MoE policy documents",
        "host": "moe-db.example.com",
        "port": 5432,
        "database_name": "moe_documents",
        "username": "readonly_user",
        "password": "secure_password_123",
        "table_name": "policy_documents",
        "file_column": "document_data",
        "filename_column": "document_name",
        "metadata_columns": ["department", "policy_type", "date_published", "status"],
        "sync_enabled": True,
        "sync_frequency": "daily"
    },
    "aicte": {
        "name": "AICTE_Documents",
        "ministry_name": "AICTE",
        "description": "AICTE technical education policies",
        "host": "aicte-db.example.com",
        "port": 5432,
        "database_name": "aicte_docs",
        "username": "readonly",
        "password": "aicte_secure_123",
        "table_name": "regulations",
        "file_column": "pdf_content",
        "filename_column": "regulation_name",
        "metadata_columns": ["category", "year", "institution_type"],
        "sync_enabled": True,
        "sync_frequency": "daily"
    },
    "ugc": {
        "name": "UGC_Circulars",
        "ministry_name": "UGC",
        "description": "UGC circulars and guidelines",
        "host": "ugc-db.example.com",
        "port": 5432,
        "database_name": "ugc_circulars",
        "username": "readonly",
        "password": "ugc_secure_123",
        "table_name": "circulars",
        "file_column": "circular_file",
        "filename_column": "circular_title",
        "metadata_columns": ["circular_number", "issue_date", "subject"],
        "sync_enabled": True,
        "sync_frequency": "daily"
    }
}


def main():
    print("="*60)
    print("External Data Source Setup - Example Script")
    print("="*60)
    
    # List existing sources
    existing_sources = list_data_sources()
    
    print("\n" + "="*60)
    print("Example: Register a new data source")
    print("="*60)
    
    # Example: Register MoE database
    config = EXAMPLE_CONFIGS["moe"]
    
    print("\nConfiguration:")
    print(json.dumps(config, indent=2))
    
    # Test connection first
    if test_connection(
        config["host"],
        config["port"],
        config["database_name"],
        config["username"],
        config["password"]
    ):
        # Register data source
        source_id = register_data_source(config)
        
        if source_id:
            # Trigger test sync (limit to 5 documents)
            trigger_sync(source_id, limit=5)
            
            # Wait a bit and check logs
            import time
            print("\n⏳ Waiting 10 seconds for sync to complete...")
            time.sleep(10)
            
            check_sync_logs(source_id)
    
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Update the example configs with your actual database details")
    print("2. Register your ministry databases")
    print("3. Monitor sync logs")
    print("4. Query documents via /chat/query endpoint")
    print("\nAPI Documentation: http://localhost:8000/docs")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server")
        print("Make sure the server is running:")
        print("  uvicorn backend.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
