"""
Re-sync existing documents to extract metadata
This will process documents that were synced before metadata extraction was added
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("Re-syncing Magisk data source to extract metadata...")
print("This will process the documents again and extract metadata for lazy RAG\n")

try:
    # Force a full sync to reprocess all documents
    response = requests.post(
        f"{BASE_URL}/data-sources/4/sync",
        params={
            "limit": 10,  # Process 10 documents
            "force_full": True  # Force full sync to reprocess
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Sync completed!")
        print(json.dumps(result, indent=2))
        
        print("\n📊 Check the results:")
        print("  - Documents should now appear in document_metadata table")
        print("  - Lazy RAG should be able to find these documents")
        print("\n🧪 Test with a query:")
        print("  Ask: 'What is Manas Pathak currently pursuing?'")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Error: {str(e)}")
