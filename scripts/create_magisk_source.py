"""
Create Magisk Resumes data source
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Configuration
config = {
    "name": "Magisk_Resumes_Fixed",
    "ministry_name": "HR Department",
    "description": "Resume database with Supabase storage",
    "host": "db.qgwjktgkndmxrhhoaaez.supabase.co",
    "port": 5432,
    "database_name": "postgres",
    "username": "postgres",
    "password": "manaspat@930005",
    "table_name": "resumes",
    "file_column": "filename",
    "filename_column": "filename",
    "metadata_columns": ["id"],
    "storage_type": "supabase",
    "supabase_url": "https://qgwjktgkndmxrhhoaaez.supabase.co",
    "supabase_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFnd2prdGdrbmRteHJoaG9hYWV6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTcxODA0NywiZXhwIjoyMDc3Mjk0MDQ3fQ.Nfu8pwRCw2RQerNuKj6_pFVdLRRZDLR-ggz6RkKj0cU.Nfu8pwRCw2RQerNuKj6_pFVdLRRZDLR-ggz6RkKj0cU",
    "supabase_bucket": "resumes",
    "file_path_prefix": None,
    "sync_enabled": True,
    "sync_frequency": "daily"
}

print("Creating data source...")
print(json.dumps(config, indent=2))
print()

try:
    response = requests.post(f"{BASE_URL}/data-sources/create", json=config)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(json.dumps(result, indent=2))
        
        source_id = result.get("source_id")
        
        if source_id:
            print(f"\n📝 Your source_id is: {source_id}")
            print(f"\nNext steps:")
            print(f"1. Test sync: python scripts/test_sync.py {source_id}")
            print(f"2. Or run: curl -X POST http://localhost:8000/data-sources/{source_id}/sync?limit=2")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("❌ Error: Cannot connect to server")
    print("Make sure the server is running:")
    print("  uvicorn backend.main:app --reload")
except Exception as e:
    print(f"❌ Error: {str(e)}")
