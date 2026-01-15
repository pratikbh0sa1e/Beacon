"""
Quick test of web scraping functionality (No DB required)
"""
from Agent.web_scraping import WebSourceManager

# Initialize manager
manager = WebSourceManager()

print("=" * 60)
print("🚀 BEACON Web Scraping Demo")
print("=" * 60)

# Test 1: Preview education.gov.in
print("\n📋 Test 1: Previewing education.gov.in...")
# Try the English version which might be more accessible
url = "https://www.education.gov.in/en/documents-reports"

try:
    preview = manager.get_source_preview(url)
    
    if preview['status'] == 'success':
        print(f"✅ Preview successful!")
        print(f"   Page Title: {preview.get('page_title', 'N/A')}")
        print(f"   Source Credibility: {preview['source_info']['credibility_score']}/10")
        print(f"   Trust Level: {preview['source_info']['trust_level']}")
        print(f"   Sample Documents Found: {preview['sample_documents']}")
        
        if preview.get('documents'):
            print(f"\n   📄 First 3 documents:")
            for i, doc in enumerate(preview['documents'][:3], 1):
                print(f"      {i}. {doc['text'][:60]}...")
                print(f"         URL: {doc['url'][:80]}...")
    else:
        print(f"❌ Preview failed: {preview.get('error')}")

except Exception as e:
    print(f"❌ Error: {str(e)}")

# Test 2: Validate source
print("\n🔍 Test 2: Validating source...")
try:
    validation = manager.validate_source(url)
    
    if validation['valid']:
        print(f"✅ Source is valid!")
        print(f"   Documents found: {validation['documents_found']}")
        print(f"   Credibility: {validation['credibility_score']}/10")
    else:
        print(f"❌ Source invalid: {validation.get('message')}")

except Exception as e:
    print(f"❌ Error: {str(e)}")

# Test 3: Actual scraping
print("\n🕷️  Test 3: Scraping documents...")
try:
    result = manager.scrape_source(
        url=url,
        source_name="Ministry of Education",
        keywords=None,
        max_documents=5
    )
    
    if result['status'] == 'success':
        print(f"✅ Scraping successful!")
        print(f"   Documents found: {result['documents_found']}")
        print(f"   Duration: {result['duration_seconds']:.2f}s")
        
        if result.get('documents'):
            print(f"\n   📄 Scraped documents:")
            for i, doc in enumerate(result['documents'][:5], 1):
                print(f"\n      {i}. {doc['text']}")
                print(f"         Type: {doc['type'].upper()}")
                print(f"         URL: {doc['url'][:80]}...")
                print(f"         Credibility: {doc['provenance']['credibility_score']}/10")
                print(f"         Source Type: {doc['provenance']['source_type']}")
    else:
        print(f"❌ Scraping failed: {result.get('error')}")

except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "=" * 60)
print("✅ Demo Complete!")
print("=" * 60)
print("\n💡 Next steps:")
print("   1. Start backend: uvicorn backend.main:app --reload")
print("   2. Test API: http://localhost:8000/api/web-scraping/demo/education-gov")
print("   3. View docs: http://localhost:8000/docs")
