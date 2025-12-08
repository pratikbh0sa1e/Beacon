"""Test with a simple accessible website"""
from Agent.web_scraping import WebSourceManager

manager = WebSourceManager()

# Test with UGC website (usually more accessible)
url = "https://www.ugc.gov.in/"

print("Testing scraping on UGC website...")
print(f"URL: {url}\n")

try:
    result = manager.scrape_source(
        url=url,
        source_name="UGC",
        keywords=["policy", "circular", "notification"],
        max_documents=10
    )
    
    print(f"Status: {result['status']}")
    print(f"Documents found: {result.get('documents_found', 0)}")
    
    if result.get('documents'):
        print("\nDocuments:")
        for i, doc in enumerate(result['documents'][:5], 1):
            print(f"{i}. {doc['text'][:60]}...")
            print(f"   Type: {doc['type']}")
            print(f"   URL: {doc['url'][:80]}...")
            print()

except Exception as e:
    print(f"Error: {str(e)}")
