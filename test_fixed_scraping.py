"""
Test script for fixed web scraping with increased limits
"""
import logging
from Agent.web_scraping.enhanced_processor import enhanced_scrape_source
from backend.database import SessionLocal, WebScrapingSource, Document

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_small_scrape():
    """Test with small limit first (50 documents)"""
    logger.info("=" * 80)
    logger.info("TEST 1: Small scrape (50 documents, 5 pages)")
    logger.info("=" * 80)
    
    try:
        result = enhanced_scrape_source(
            source_id=1,  # Adjust to your MoE source ID
            max_documents=50,
            max_pages=5,
            pagination_enabled=True,
            incremental=False  # Full scan
        )
        
        logger.info("\n" + "=" * 80)
        logger.info("SMALL SCRAPE RESULTS:")
        logger.info("=" * 80)
        logger.info(f"Status: {result['status']}")
        logger.info(f"Documents discovered: {result['documents_discovered']}")
        logger.info(f"Documents new: {result['documents_new']}")
        logger.info(f"Documents unchanged: {result['documents_unchanged']}")
        logger.info(f"Documents processed: {result['documents_processed']}")
        logger.info(f"Pages scraped: {result['pages_scraped']}")
        logger.info(f"Execution time: {result['execution_time']:.2f}s")
        logger.info(f"Errors: {len(result.get('errors', []))}")
        
        if result.get('errors'):
            logger.warning(f"First 3 errors: {result['errors'][:3]}")
        
        return result
        
    except Exception as e:
        logger.error(f"Small scrape failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_large_scrape():
    """Test with large limit (1500 documents, 100 pages)"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Large scrape (1500 documents, 100 pages)")
    logger.info("=" * 80)
    logger.info("⚠️  This will take 30-60 minutes!")
    logger.info("=" * 80)
    
    try:
        result = enhanced_scrape_source(
            source_id=1,  # Adjust to your MoE source ID
            max_documents=1500,
            max_pages=100,
            pagination_enabled=True,
            incremental=False  # Full scan
        )
        
        logger.info("\n" + "=" * 80)
        logger.info("LARGE SCRAPE RESULTS:")
        logger.info("=" * 80)
        logger.info(f"Status: {result['status']}")
        logger.info(f"Documents discovered: {result['documents_discovered']}")
        logger.info(f"Documents new: {result['documents_new']}")
        logger.info(f"Documents unchanged: {result['documents_unchanged']}")
        logger.info(f"Documents processed: {result['documents_processed']}")
        logger.info(f"Pages scraped: {result['pages_scraped']}")
        logger.info(f"Execution time: {result['execution_time']:.2f}s ({result['execution_time']/60:.1f} minutes)")
        logger.info(f"Errors: {len(result.get('errors', []))}")
        
        if result.get('errors'):
            logger.warning(f"First 5 errors: {result['errors'][:5]}")
        
        return result
        
    except Exception as e:
        logger.error(f"Large scrape failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def check_database_counts():
    """Check how many documents are in the database"""
    logger.info("\n" + "=" * 80)
    logger.info("DATABASE DOCUMENT COUNTS:")
    logger.info("=" * 80)
    
    db = SessionLocal()
    try:
        # Total documents
        total_docs = db.query(Document).count()
        logger.info(f"Total documents in database: {total_docs}")
        
        # Scraped documents (have source_url)
        scraped_docs = db.query(Document).filter(
            Document.source_url.isnot(None)
        ).count()
        logger.info(f"Scraped documents (with source_url): {scraped_docs}")
        
        # Manually uploaded documents
        manual_docs = db.query(Document).filter(
            Document.source_url.is_(None)
        ).count()
        logger.info(f"Manually uploaded documents: {manual_docs}")
        
        # Documents by approval status
        approved = db.query(Document).filter(
            Document.approval_status == 'approved'
        ).count()
        logger.info(f"Approved documents: {approved}")
        
        # Get source info
        sources = db.query(WebScrapingSource).all()
        logger.info(f"\nWeb scraping sources: {len(sources)}")
        for source in sources:
            logger.info(f"  - {source.name}: {source.total_documents_scraped} documents scraped")
            logger.info(f"    Last scraped: {source.last_scraped_at}")
            logger.info(f"    Status: {source.last_scrape_status}")
        
    except Exception as e:
        logger.error(f"Error checking database: {e}")
    finally:
        db.close()


def main():
    """Main test function"""
    logger.info("=" * 80)
    logger.info("WEB SCRAPING FIX TEST SUITE")
    logger.info("=" * 80)
    
    # Check initial state
    check_database_counts()
    
    # Test 1: Small scrape
    input("\nPress Enter to start SMALL scrape test (50 docs)...")
    small_result = test_small_scrape()
    
    if small_result and small_result['status'] == 'success':
        logger.info("\n✅ Small scrape test PASSED!")
        
        # Check database after small scrape
        check_database_counts()
        
        # Ask if user wants to continue with large scrape
        response = input("\n⚠️  Small scrape successful! Run LARGE scrape (1500 docs, ~30-60 min)? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            large_result = test_large_scrape()
            
            if large_result and large_result['status'] == 'success':
                logger.info("\n✅ Large scrape test PASSED!")
                logger.info(f"\n🎉 SUCCESS! Scraped {large_result['documents_new']} new documents!")
            else:
                logger.error("\n❌ Large scrape test FAILED!")
        else:
            logger.info("\nLarge scrape skipped by user.")
    else:
        logger.error("\n❌ Small scrape test FAILED!")
        logger.error("Fix the issues before attempting large scrape.")
    
    # Final database check
    logger.info("\n" + "=" * 80)
    logger.info("FINAL DATABASE STATE:")
    logger.info("=" * 80)
    check_database_counts()
    
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUITE COMPLETE")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
