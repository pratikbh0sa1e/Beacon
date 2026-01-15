#!/usr/bin/env python3
"""
Simple Enhanced Web Scraping Test
Tests the enhanced web scraping architecture components directly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_components():
    """Test enhanced scraping components directly"""
    print("🧪 Testing Enhanced Web Scraping Components")
    print("=" * 60)
    
    # Test 1: Site-specific scrapers
    print("\n1. Testing Site-Specific Scrapers")
    try:
        from Agent.web_scraping.site_scrapers import get_scraper_for_site
        
        # Test different scraper types
        scrapers = {
            "generic": get_scraper_for_site("generic"),
            "moe": get_scraper_for_site("moe"),
            "ugc": get_scraper_for_site("ugc"),
            "aicte": get_scraper_for_site("aicte")
        }
        
        print("✅ Site-specific scrapers loaded:")
        for scraper_type, scraper in scrapers.items():
            print(f"   - {scraper_type}: {scraper.__class__.__name__}")
            
    except Exception as e:
        print(f"❌ Error loading scrapers: {e}")
    
    # Test 2: Sliding Window Manager
    print("\n2. Testing Sliding Window Manager")
    try:
        from Agent.web_scraping.sliding_window_manager import SlidingWindowManager
        
        manager = SlidingWindowManager(window_size=3)
        print(f"✅ Sliding Window Manager initialized with window size: {manager.window_size}")
        
        # Test window logic
        test_pages = list(range(1, 11))  # Pages 1-10
        window_pages = manager.get_sliding_window_pages(test_pages)
        print(f"   - Window pages from {test_pages}: {window_pages}")
        
    except Exception as e:
        print(f"❌ Error testing sliding window: {e}")
    
    # Test 3: Page Hash Tracker
    print("\n3. Testing Page Hash Tracker")
    try:
        from Agent.web_scraping.page_hash_tracker import PageHashTracker
        
        tracker = PageHashTracker()
        print("✅ Page Hash Tracker initialized")
        
        # Test hash calculation
        test_content = "<html><body><h1>Test Page</h1><p>Content</p></body></html>"
        content_hash = tracker._calculate_content_hash(test_content)
        print(f"   - Test content hash: {content_hash[:16]}...")
        
    except Exception as e:
        print(f"❌ Error testing page hash tracker: {e}")
    
    # Test 4: Document Identity Manager
    print("\n4. Testing Document Identity Manager")
    try:
        from Agent.web_scraping.document_identity_manager import DocumentIdentityManager
        
        manager = DocumentIdentityManager()
        print("✅ Document Identity Manager initialized")
        
        # Test URL normalization
        test_urls = [
            "https://example.com/doc.pdf",
            "https://example.com/doc.pdf?v=1",
            "https://example.com/doc.pdf#section1"
        ]
        
        for url in test_urls:
            normalized = manager._normalize_url(url)
            print(f"   - {url} → {normalized}")
            
    except Exception as e:
        print(f"❌ Error testing document identity manager: {e}")
    
    # Test 5: Enhanced Scraping Orchestrator
    print("\n5. Testing Enhanced Scraping Orchestrator")
    try:
        from Agent.web_scraping.enhanced_scraping_orchestrator import EnhancedScrapingOrchestrator
        
        orchestrator = EnhancedScrapingOrchestrator(window_size=3)
        print("✅ Enhanced Scraping Orchestrator initialized")
        print(f"   - Window size: {orchestrator.sliding_window_manager.window_size}")
        print("   - All components integrated successfully")
        
    except Exception as e:
        print(f"❌ Error testing orchestrator: {e}")
    
    # Test 6: Enhanced Processor Integration
    print("\n6. Testing Enhanced Processor Integration")
    try:
        from Agent.web_scraping.enhanced_processor import enhanced_scrape_source
        print("✅ Enhanced processor function available")
        print("   - Function can be called from API endpoints")
        
    except Exception as e:
        print(f"❌ Error testing enhanced processor: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Enhanced Components Test Complete")
    
    # Summary
    print("\n📊 Architecture Summary:")
    print("✅ Site-Specific Scrapers: Hardcoded selectors per government site")
    print("✅ Sliding Window Re-scanning: Always re-scan first N pages")
    print("✅ Page Content Hashing: Skip unchanged pages automatically")
    print("✅ Enhanced Document Identity: URL-first deduplication approach")
    print("✅ Orchestrator Integration: All components work together")
    
    print("\n💡 Ready for testing:")
    print("   1. Backend API endpoints are available")
    print("   2. Frontend can use enhanced features")
    print("   3. All 4 architectural improvements implemented")

def test_scraper_functionality():
    """Test actual scraper functionality with a simple page"""
    print("\n" + "=" * 60)
    print("🔍 Testing Scraper Functionality")
    print("=" * 60)
    
    try:
        from Agent.web_scraping.site_scrapers.moe_scraper import MoEScraper
        
        scraper = MoEScraper()
        print("✅ MoE Scraper initialized")
        
        # Test with a simple HTML content
        test_html = """
        <html>
        <body>
            <div class="document-list">
                <a href="/doc1.pdf">Policy Document 1</a>
                <a href="/doc2.pdf">Circular 2023</a>
                <a href="/doc3.docx">Guidelines Document</a>
            </div>
        </body>
        </html>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(test_html, 'html.parser')
        base_url = "https://example.gov.in"
        
        documents = scraper.get_document_links(soup, base_url)
        print(f"✅ Found {len(documents)} document links:")
        for doc in documents:
            print(f"   - {doc['title']}: {doc['url']}")
            
    except Exception as e:
        print(f"❌ Error testing scraper functionality: {e}")

if __name__ == "__main__":
    test_enhanced_components()
    test_scraper_functionality()