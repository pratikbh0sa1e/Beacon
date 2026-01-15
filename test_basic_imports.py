#!/usr/bin/env python3
"""
Basic test to check imports and database connection
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """Test basic imports step by step"""
    print("🧪 Basic Imports Test")
    print("=" * 30)
    
    try:
        print("1. Testing database import...")
        from backend.database import SessionLocal, Document, DocumentMetadata, WebScrapingSource
        print("   ✅ Database models imported")
        
        print("2. Testing database connection...")
        db = SessionLocal()
        result = db.execute("SELECT 1").fetchone()
        print(f"   ✅ Database connection works: {result}")
        
        print("3. Testing document count...")
        doc_count = db.query(Document).count()
        print(f"   ✅ Document count: {doc_count}")
        
        print("4. Testing web scraping sources...")
        source_count = db.query(WebScrapingSource).count()
        print(f"   ✅ Web scraping sources: {source_count}")
        
        if source_count > 0:
            sources = db.query(WebScrapingSource).all()
            for source in sources:
                print(f"      - {source.id}: {source.name}")
        
        print("5. Testing metadata extractor import...")
        from Agent.metadata.extractor import MetadataExtractor
        print("   ✅ MetadataExtractor imported")
        
        print("6. Testing enhanced processor import...")
        from Agent.web_scraping.enhanced_processor import enhanced_scrape_source
        print("   ✅ Enhanced processor imported")
        
        print("7. Testing site scrapers import...")
        from Agent.web_scraping.site_scrapers import get_scraper_for_site
        print("   ✅ Site scrapers imported")
        
        db.close()
        
        print("\n🎉 All imports successful!")
        print("✅ Enhanced scraping system is ready to use")
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_imports()