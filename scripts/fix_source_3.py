"""
Fix source 3 - remove the incorrect file_path_prefix
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Update to remove the "None" string prefix
update_config = {
    "file_path_prefix": None  # This will be sent as null in JSON
}

print("Fixing source 3...")

try:
    response = requests.put(f"{BASE_URL}/data-sources/3", json=update_config)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(json.dumps(result, indent=2))
        
        print("\nNow test the sync:")
        print("  python scripts/test_sync.py 3 5")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Error: {str(e)}")
