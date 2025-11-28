"""
Update source 2 with correct credentials
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Update configuration - Try pooler with port 6543
update_config = {
    "host": "aws-1-ap-south-1.pooler.supabase.com",
    "port": 5432,
    "username": "postgres.qgwjktgkndmxrhhoaaez",
    "password": "manaspat@930005"
}

print("Updating data source 2...")

try:
    response = requests.put(f"{BASE_URL}/data-sources/2", json=update_config)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(json.dumps(result, indent=2))
        
        print("\nNow test the sync:")
        print("  python scripts/test_sync.py 2 2")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Error: {str(e)}")
