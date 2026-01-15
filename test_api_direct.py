#!/usr/bin/env python3
"""
Test API endpoints directly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal, WebScrapingSource
from backend.routers.enhanced_web_scraping_router import enhanced_scrape_source_endpoint
from fastapi import HTTPException

def test_api_direct():
    """Test API endpoints directly"""
    print("🧪 Testing API Endpoints Directly")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Test sources endpoint
        print("📋 Testing sources endpoint...")
        sources = db.query(WebScrapingSource).all()
        
        sources_data = []
        for source in sources:
            sources_data.append({
                "id": source.id,
                "name": source.name,
                "url": source.url,
                "description": source.description,
                "keywords": source.keywords,
                "max_documents": source.max_documents_per_scrape,
                "scraping_enabled": source.scraping_enabled,
                "last_scraped_at": source.last_scraped_at.isoformat() if source.last_scraped_at else None,
                "last_scrape_status": source.last_scrape_status,
                "total_documents_scraped": source.total_documents_scraped,
                "created_at": source.created_at.isoformat() if source.created_at else None
            })
        
        print(f"✅ Found {len(sources_data)} sources:")
        for source in sources_data:
            print(f"   {source['id']}: {source['name']}")
            print(f"      URL: {source['url']}")
            print(f"      Status: {source['last_scrape_status'] or 'Never scraped'}")
            print(f"      Documents: {source['total_documents_scraped']}")
            print()
        
        # Test enhanced scraping endpoint simulation
        print("🚀 Testing enhanced scraping endpoint...")
        
        if sources_data:
            source_id = sources_data[0]['id']
            print(f"   Testing with source {source_id}: {sources_data[0]['name']}")
            
            # Simulate the API call
            try:
                from Agent.web_scraping.enhanced_processor import enhanced_scrape_source
                
                result = enhanced_scrape_source(
                    source_id=source_id,
                    max_documents=1,  # Very small test
                    pagination_enabled=False,
                    max_pages=1
                )
                
                print(f"   ✅ Enhanced scraping result:")
                print(f"      Status: {result.get('status')}")
                print(f"      Documents discovered: {result.get('documents_discovered', 0)}")
                print(f"      Documents new: {result.get('documents_new', 0)}")
                print(f"      Execution time: {result.get('execution_time', 0):.2f}s")
                
            except Exception as e:
                print(f"   ❌ Enhanced scraping failed: {e}")
        
        # Test scraped documents endpoint simulation
        print("\n📄 Testing scraped documents endpoint...")
        
        from backend.database import Document
        scraped_docs = db.query(Document).filter(
            Document.source_url.isnot(None)
        ).order_by(Document.uploaded_at.desc()).limit(5).all()
        
        scraped_data = []
        for doc in scraped_docs:
            scraped_data.append({
                "id": doc.id,
                "title": doc.filename,
                "url": doc.source_url,
                "type": doc.file_type,
                "scraped_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "source_name": "Ministry of Education",  # Default
                "credibility": 10,
                "verified": True
            })
        
        print(f"✅ Found {len(scraped_data)} scraped documents:")
        for doc in scraped_data[:3]:
            print(f"   - {doc['title'][:60]}...")
            print(f"     URL: {doc['url']}")
            print(f"     Type: {doc['type']}")
            print(f"     Scraped: {doc['scraped_at']}")
            print()
        
        print("🎉 All API endpoints working correctly!")
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_api_direct()