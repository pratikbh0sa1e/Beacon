#!/usr/bin/env python3
"""
Test Real Web Scraping
Tests the enhanced web scraping with a real government website
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_real_scraping():
    """Test scraping with a real government website"""
    print("🌐 Testing Real Web Scraping")
    print("=" * 60)
    
    try:
        from Agent.web_scraping.site_scrapers.moe_scraper import MoEScraper
        import requests
        from bs4 import BeautifulSoup
        
        # Test with MoE website
        scraper = MoEScraper()
        test_url = "https://www.education.gov.in/documents_reports_hi"
        
        print(f"\n🎯 Testing with: {test_url}")
        print("📡 Fetching page content...")
        
        # Scrape the page
        result = scraper.scrape_page(test_url)
        
        if result['status'] == 'success':
            print("✅ Page scraped successfully")
            
            # Extract documents
            documents = scraper.get_document_links(result['soup'], test_url)
            print(f"📄 Found {len(documents)} documents:")
            
            # Show first 5 documents
            for i, doc in enumerate(documents[:5]):
                print(f"   {i+1}. {doc['title'][:60]}...")
                print(f"      URL: {doc['url']}")
                print(f"      Type: {doc.get('file_type', 'unknown')}")
                print()
            
            if len(documents) > 5:
                print(f"   ... and {len(documents) - 5} more documents")
                
            # Test document filtering
            print("\n🔍 Testing keyword filtering:")
            keywords = ["policy", "नीति", "circular", "परिपत्र"]
            filtered_docs = []
            
            for doc in documents:
                title_lower = doc['title'].lower()
                if any(keyword.lower() in title_lower for keyword in keywords):
                    filtered_docs.append(doc)
            
            print(f"📋 Found {len(filtered_docs)} documents matching keywords {keywords}")
            for doc in filtered_docs[:3]:
                print(f"   - {doc['title'][:50]}...")
                
        else:
            print(f"❌ Failed to scrape page: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error in real scraping test: {e}")
        import traceback
        traceback.print_exc()

def test_enhanced_orchestrator():
    """Test the enhanced orchestrator with mock data"""
    print("\n" + "=" * 60)
    print("🎭 Testing Enhanced Orchestrator")
    print("=" * 60)
    
    try:
        from Agent.web_scraping.enhanced_scraping_orchestrator import EnhancedScrapingOrchestrator
        from backend.database import SessionLocal, WebScrapingSource
        
        # Create orchestrator
        orchestrator = EnhancedScrapingOrchestrator(window_size=2)
        print("✅ Enhanced Orchestrator initialized")
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Check if we have any sources
            sources = db.query(WebScrapingSource).all()
            print(f"📊 Found {len(sources)} sources in database")
            
            if sources:
                source = sources[0]
                print(f"🎯 Testing with source: {source.name}")
                print(f"   URL: {source.url}")
                
                # Get orchestrator statistics
                stats = orchestrator.get_orchestrator_statistics(source.id)
                print("📈 Orchestrator Statistics:")
                print(f"   - Timestamp: {stats.get('timestamp', 'N/A')}")
                print(f"   - Source ID: {stats.get('source_id', 'N/A')}")
                
                if 'page_hashing' in stats:
                    print(f"   - Page hashing stats: {stats['page_hashing']}")
                if 'document_identity' in stats:
                    print(f"   - Document identity stats: {stats['document_identity']}")
                    
            else:
                print("⚠️  No sources found in database")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error testing orchestrator: {e}")
        import traceback
        traceback.print_exc()

def test_document_processing():
    """Test document processing pipeline"""
    print("\n" + "=" * 60)
    print("📄 Testing Document Processing Pipeline")
    print("=" * 60)
    
    try:
        from Agent.web_scraping.document_identity_manager import DocumentIdentityManager
        
        manager = DocumentIdentityManager()
        print("✅ Document Identity Manager initialized")
        
        # Test document identity checking
        test_documents = [
            {
                "url": "https://example.gov.in/policy2023.pdf",
                "title": "Education Policy 2023",
                "content": "This is the education policy for 2023..."
            },
            {
                "url": "https://example.gov.in/policy2023.pdf",  # Same URL
                "title": "Education Policy 2023 (Updated)",
                "content": "This is the updated education policy for 2023..."
            },
            {
                "url": "https://example.gov.in/circular2023.pdf",
                "title": "Circular 2023",
                "content": "This is a circular for 2023..."
            }
        ]
        
        print("🔍 Testing document identity detection:")
        for i, doc in enumerate(test_documents):
            print(f"\n   Document {i+1}: {doc['title']}")
            print(f"   URL: {doc['url']}")
            
            # Test URL normalization
            normalized_url = manager._normalize_url(doc['url'])
            print(f"   Normalized URL: {normalized_url}")
            
            # Test content hash
            content_hash = manager._calculate_content_hash(doc['content'])
            print(f"   Content Hash: {content_hash[:16]}...")
            
    except Exception as e:
        print(f"❌ Error testing document processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_scraping()
    test_enhanced_orchestrator()
    test_document_processing()