#!/usr/bin/env python3
"""
Test Enhanced Scraping Database Save
Test that enhanced scraping properly saves documents to database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_scraping_db_save():
    """Test enhanced scraping with database saving"""
    print("🧪 Testing Enhanced Scraping Database Save")
    print("=" * 60)
    
    try:
        from backend.database import SessionLocal, Document
        from Agent.web_scraping.enhanced_processor import enhanced_scrape_source
        
        # Count documents before scraping
        db = SessionLocal()
        
        try:
            docs_before = db.query(Document).count()
            scraped_docs_before = db.query(Document).filter(
                Document.source_url.isnot(None)
            ).count()
            
            print(f"📊 Before scraping:")
            print(f"   Total documents: {docs_before}")
            print(f"   Scraped documents: {scraped_docs_before}")
            
        finally:
            db.close()
        
        # Test enhanced scraping with source ID 3 (MoE)
        print(f"\n🚀 Running enhanced scraping test...")
        
        result = enhanced_scrape_source(
            source_id=3,  # MoE source
            keywords=None,
            max_documents=5,  # Small number for testing
            pagination_enabled=False,
            max_pages=1,
            incremental=False
        )
        
        print(f"✅ Enhanced scraping completed!")
        print(f"📊 Results:")
        print(f"   Status: {result.get('status')}")
        print(f"   Execution time: {result.get('execution_time', 0):.2f}s")
        print(f"   Scraper used: {result.get('scraper_used', 'Unknown')}")
        print(f"   Documents discovered: {result.get('documents_discovered', 0)}")
        print(f"   Documents new: {result.get('documents_new', 0)}")
        print(f"   Documents processed: {result.get('documents_processed', 0)}")
        print(f"   Pages scraped: {result.get('pages_scraped', 0)}")
        
        if result.get('errors'):
            print(f"   Errors: {len(result['errors'])}")
            for error in result['errors'][:3]:
                print(f"     - {error}")
        
        # Count documents after scraping
        db = SessionLocal()
        
        try:
            docs_after = db.query(Document).count()
            scraped_docs_after = db.query(Document).filter(
                Document.source_url.isnot(None)
            ).count()
            
            print(f"\n📊 After scraping:")
            print(f"   Total documents: {docs_after}")
            print(f"   Scraped documents: {scraped_docs_after}")
            print(f"   New documents added: {docs_after - docs_before}")
            
            # Show sample new documents
            if docs_after > docs_before:
                print(f"\n📋 Sample new documents:")
                new_docs = db.query(Document).filter(
                    Document.source_url.isnot(None)
                ).order_by(Document.uploaded_at.desc()).limit(3).all()
                
                for doc in new_docs:
                    print(f"   - {doc.filename}")
                    print(f"     URL: {doc.source_url}")
                    print(f"     Type: {doc.file_type}")
                    print(f"     Uploaded: {doc.uploaded_at}")
                    print()
            
        finally:
            db.close()
        
    except Exception as e:
        print(f"❌ Error in enhanced scraping test: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoint():
    """Test the enhanced scraping API endpoint"""
    print("\n" + "=" * 60)
    print("🌐 Testing Enhanced Scraping API Endpoint")
    print("=" * 60)
    
    try:
        import requests
        
        # Test the enhanced scraping endpoint
        print("📡 Testing enhanced scraping API...")
        
        response = requests.post(
            "http://localhost:8000/api/enhanced-web-scraping/scrape-enhanced",
            json={
                "source_id": 3,
                "keywords": None,
                "max_documents": 3,
                "pagination_enabled": False,
                "max_pages": 1,
                "incremental": False
            }
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 403:
            print("   ⚠️  Authentication required (expected)")
        elif response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success! Message: {result.get('message', 'No message')}")
            print(f"   📊 Documents processed: {result.get('documents_new', 0)}")
        else:
            print(f"   ❌ Unexpected status: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")

def check_scraped_documents_api():
    """Check the scraped documents API"""
    print("\n" + "=" * 60)
    print("📄 Testing Scraped Documents API")
    print("=" * 60)
    
    try:
        import requests
        
        response = requests.get("http://localhost:8000/api/web-scraping/scraped-documents?limit=5")
        
        print(f"📡 Scraped Documents API Status: {response.status_code}")
        
        if response.status_code == 200:
            docs = response.json()
            print(f"✅ Found {len(docs)} scraped documents")
            
            for i, doc in enumerate(docs):
                print(f"   {i+1}. {doc.get('title', 'No title')[:50]}...")
                print(f"      URL: {doc.get('url', 'No URL')}")
                print(f"      Source: {doc.get('source_name', 'Unknown')}")
                print(f"      Type: {doc.get('type', 'Unknown')}")
                print()
        else:
            print(f"❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_enhanced_scraping_db_save()
    test_api_endpoint()
    check_scraped_documents_api()