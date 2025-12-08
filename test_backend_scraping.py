"""
Quick test to verify backend scraping and document storage
"""
import requests
import json

API_BASE = "http://localhost:8000/api/web-scraping"

print("=" * 60)
print("🧪 Testing Backend Web Scraping")
print("=" * 60)

# Test 1: Check current stats
print("\n📊 Test 1: Current Stats")
print("-" * 60)
response = requests.get(f"{API_BASE}/stats")
stats = response.json()
print(f"Total Sources: {stats['total_sources']}")
print(f"Total Scrapes: {stats['total_scrapes']}")
print(f"Documents Scraped: {stats['total_documents_scraped']}")
print(f"Available Docs: {stats['scraped_documents_available']}")

# Test 2: Check scraped documents
print("\n📄 Test 2: Scraped Documents")
print("-" * 60)
response = requests.get(f"{API_BASE}/scraped-documents?limit=10")
docs = response.json()
print(f"Found {len(docs)} documents")

if docs:
    print("\nFirst 3 documents:")
    for i, doc in enumerate(docs[:3], 1):
        print(f"\n{i}. {doc.get('title', 'No title')[:60]}")
        print(f"   Type: {doc.get('type', 'unknown').upper()}")
        print(f"   URL: {doc.get('url', 'No URL')[:70]}...")
        if doc.get('provenance'):
            print(f"   Credibility: {doc['provenance'].get('credibility_score', 'N/A')}/10")
else:
    print("⚠️  No documents found yet")
    print("\n💡 Try running the demo:")
    print("   POST http://localhost:8000/api/web-scraping/demo/education-gov")

# Test 3: Debug endpoint
print("\n🔍 Test 3: Debug Info")
print("-" * 60)
try:
    response = requests.get(f"{API_BASE}/debug/scraped-docs-count")
    debug = response.json()
    print(f"Total in memory: {debug['total_scraped_docs']}")
    if debug.get('sample'):
        print(f"Sample available: {len(debug['sample'])} docs")
except:
    print("Debug endpoint not available")

# Test 4: Run quick demo
print("\n🚀 Test 4: Running Quick Demo")
print("-" * 60)
print("Scraping UGC website...")

try:
    response = requests.post(f"{API_BASE}/demo/education-gov")
    result = response.json()
    
    print(f"✅ {result['message']}")
    print(f"Documents found: {len(result.get('documents', []))}")
    
    if result.get('documents'):
        print("\nFirst 3 documents:")
        for i, doc in enumerate(result['documents'][:3], 1):
            print(f"\n{i}. {doc.get('text', 'No title')[:60]}")
            print(f"   Type: {doc.get('type', 'unknown').upper()}")
            print(f"   Credibility: {doc.get('provenance', {}).get('credibility_score', 'N/A')}/10")
    
    # Check again after demo
    print("\n📊 Stats After Demo:")
    print("-" * 60)
    response = requests.get(f"{API_BASE}/stats")
    stats = response.json()
    print(f"Documents Scraped: {stats['total_documents_scraped']}")
    print(f"Available Docs: {stats['scraped_documents_available']}")
    
except Exception as e:
    print(f"❌ Demo failed: {str(e)}")

print("\n" + "=" * 60)
print("✅ Test Complete!")
print("=" * 60)
print("\n💡 If documents aren't showing:")
print("   1. Check backend logs for errors")
print("   2. Verify UGC website is accessible")
print("   3. Refresh frontend page")
print("   4. Check browser console for errors")
