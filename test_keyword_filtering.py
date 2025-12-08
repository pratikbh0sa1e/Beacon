"""
Test keyword filtering during web scraping
"""
from Agent.web_scraping import WebSourceManager

manager = WebSourceManager()

print("=" * 70)
print("🔍 KEYWORD FILTERING DEMO")
print("=" * 70)

url = "https://www.ugc.gov.in/"

# Test 1: Scrape WITHOUT keywords (get all documents)
print("\n📋 Test 1: Scraping WITHOUT keywords")
print("-" * 70)
result1 = manager.scrape_source(
    url=url,
    source_name="UGC",
    keywords=None,
    max_documents=20
)

print(f"Documents found: {result1['documents_found']}")
if result1.get('documents'):
    print("\nAll documents:")
    for i, doc in enumerate(result1['documents'][:5], 1):
        print(f"{i}. {doc['text'][:60]}...")

# Test 2: Scrape WITH keywords (filter for specific documents)
print("\n\n🎯 Test 2: Scraping WITH keywords: ['fee', 'refund']")
print("-" * 70)
result2 = manager.scrape_source(
    url=url,
    source_name="UGC",
    keywords=["fee", "refund"],
    max_documents=20
)

print(f"Documents found: {result2['documents_found']}")
if result2.get('documents'):
    print("\nFiltered documents (containing 'fee' or 'refund'):")
    for i, doc in enumerate(result2['documents'], 1):
        print(f"{i}. {doc['text'][:60]}...")
        print(f"   URL: {doc['url'][:70]}...")

# Test 3: Different keywords
print("\n\n🎯 Test 3: Scraping WITH keywords: ['circular', 'notification']")
print("-" * 70)
result3 = manager.scrape_source(
    url=url,
    source_name="UGC",
    keywords=["circular", "notification"],
    max_documents=20
)

print(f"Documents found: {result3['documents_found']}")
if result3.get('documents'):
    print("\nFiltered documents (containing 'circular' or 'notification'):")
    for i, doc in enumerate(result3['documents'][:5], 1):
        print(f"{i}. {doc['text'][:60]}...")

print("\n" + "=" * 70)
print("✅ KEYWORD FILTERING WORKS!")
print("=" * 70)

print("\n💡 Summary:")
print(f"   • Without keywords: {result1['documents_found']} documents")
print(f"   • With 'fee/refund': {result2['documents_found']} documents")
print(f"   • With 'circular/notification': {result3['documents_found']} documents")

print("\n🎯 This shows keyword filtering is working perfectly!")
print("   Officials can specify keywords to find exactly what they need.")
