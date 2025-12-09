"""
Test scraping Ministry of Education website with pagination
"""
import logging
from Agent.web_scraping.local_storage import LocalStorage
from Agent.web_scraping.web_source_manager import WebSourceManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_moe_scraping():
    """Test Ministry of Education scraping with pagination"""
    
    # Initialize
    storage = LocalStorage()
    manager = WebSourceManager(storage)
    
    # Ministry of Education URL
    moe_url = input("Enter Ministry of Education URL: ").strip()
    if not moe_url:
        moe_url = "https://www.education.gov.in/"
    
    logger.info(f"Testing scraping for: {moe_url}")
    
    # Test 1: Without pagination (first page only)
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Scraping WITHOUT pagination (first page only)")
    logger.info("="*60)
    
    source1 = storage.create_source({
        'name': 'Ministry of Education - No Pagination',
        'url': moe_url,
        'keywords': ['policy', 'circular', 'notification', 'order', 'scheme'],
        'pagination_enabled': False,
        'max_pages': 1
    })
    
    result1 = manager.scrape_source_with_pagination(
        source_id=source1['id'],
        url=source1['url'],
        source_name=source1['name'],
        keywords=source1['keywords'],
        pagination_enabled=False,
        max_pages=1,
        incremental=False
    )
    
    logger.info(f"✅ Result WITHOUT pagination:")
    logger.info(f"   - Status: {result1['status']}")
    logger.info(f"   - Documents discovered: {result1.get('documents_discovered', 0)}")
    logger.info(f"   - Documents matched: {result1.get('documents_new', 0)}")
    
    # Test 2: With pagination (multiple pages)
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Scraping WITH pagination (up to 10 pages)")
    logger.info("="*60)
    
    source2 = storage.create_source({
        'name': 'Ministry of Education - With Pagination',
        'url': moe_url,
        'keywords': ['policy', 'circular', 'notification', 'order', 'scheme'],
        'pagination_enabled': True,
        'max_pages': 10  # Scrape up to 10 pages
    })
    
    result2 = manager.scrape_source_with_pagination(
        source_id=source2['id'],
        url=source2['url'],
        source_name=source2['name'],
        keywords=source2['keywords'],
        pagination_enabled=True,
        max_pages=10,
        incremental=False
    )
    
    logger.info(f"✅ Result WITH pagination:")
    logger.info(f"   - Status: {result2['status']}")
    logger.info(f"   - Documents discovered: {result2.get('documents_discovered', 0)}")
    logger.info(f"   - Documents matched: {result2.get('documents_new', 0)}")
    logger.info(f"   - Pagination used: {result2.get('pagination_used', False)}")
    
    # Compare results
    logger.info("\n" + "="*60)
    logger.info("COMPARISON")
    logger.info("="*60)
    
    docs_without_pagination = result1.get('documents_new', 0)
    docs_with_pagination = result2.get('documents_new', 0)
    
    logger.info(f"Without pagination: {docs_without_pagination} documents")
    logger.info(f"With pagination:    {docs_with_pagination} documents")
    logger.info(f"Additional documents found: {docs_with_pagination - docs_without_pagination}")
    
    if docs_with_pagination > docs_without_pagination:
        logger.info(f"\n✅ SUCCESS! Pagination found {docs_with_pagination - docs_without_pagination} more documents!")
    else:
        logger.info(f"\n⚠️  No additional documents found. The website might not have pagination,")
        logger.info(f"   or pagination detection didn't work for this site.")
    
    # Show sample documents
    if result2.get('documents'):
        logger.info(f"\n📄 Sample documents found:")
        for i, doc in enumerate(result2['documents'][:5], 1):
            logger.info(f"   {i}. {doc.get('text', 'No title')[:80]}...")
    
    return result1, result2


if __name__ == "__main__":
    logger.info("🚀 Ministry of Education Scraping Test")
    logger.info("="*60)
    
    try:
        result1, result2 = test_moe_scraping()
        
        logger.info("\n" + "="*60)
        logger.info("✅ TEST COMPLETE!")
        logger.info("="*60)
        logger.info("\nTo scrape more pages, increase max_pages parameter.")
        logger.info("To scrape specific sections, use the section URL directly.")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}", exc_info=True)
