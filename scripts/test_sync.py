"""
Test sync for a data source
"""
import requests
import sys
import time
import json

BASE_URL = "http://localhost:8000"

if len(sys.argv) < 2:
    print("Usage: python scripts/test_sync.py <source_id> [limit]")
    print("Example: python scripts/test_sync.py 2 5")
    sys.exit(1)

source_id = sys.argv[1]
limit = sys.argv[2] if len(sys.argv) > 2 else 2

print(f"🔄 Triggering sync for source {source_id} (limit: {limit} documents)...")

try:
    # Trigger sync
    response = requests.post(f"{BASE_URL}/data-sources/{source_id}/sync?limit={limit}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Sync started!")
        print(json.dumps(result, indent=2))
        
        print("\n⏳ Waiting 10 seconds for sync to complete...")
        time.sleep(10)
        
        # Check logs
        print("\n📊 Checking sync logs...")
        logs_response = requests.get(f"{BASE_URL}/data-sources/{source_id}/sync-logs")
        
        if logs_response.status_code == 200:
            logs = logs_response.json()
            
            if logs.get("total_logs", 0) > 0:
                latest_log = logs["logs"][0]
                print("\n📝 Latest sync result:")
                print(f"  Status: {latest_log['status']}")
                print(f"  Documents fetched: {latest_log['documents_fetched']}")
                print(f"  Documents processed: {latest_log['documents_processed']}")
                print(f"  Documents failed: {latest_log['documents_failed']}")
                print(f"  Duration: {latest_log['sync_duration_seconds']} seconds")
                
                if latest_log.get('error_message'):
                    print(f"  Error: {latest_log['error_message']}")
                
                if latest_log['documents_processed'] > 0:
                    print("\n✅ Success! Documents were processed.")
                    print("\nYou can now query them:")
                    print('  curl -X POST http://localhost:8000/chat/query -H "Content-Type: application/json" -d \'{"question": "What skills does the candidate have?", "thread_id": "test_1"}\'')
                else:
                    print("\n⚠️ No documents were processed. Check the error above.")
            else:
                print("No sync logs found yet. The sync might still be running.")
        else:
            print(f"Error getting logs: {logs_response.status_code}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("❌ Error: Cannot connect to server")
    print("Make sure the server is running:")
    print("  uvicorn backend.main:app --reload")
except Exception as e:
    print(f"❌ Error: {str(e)}")
