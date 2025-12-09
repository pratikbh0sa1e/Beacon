"""
Test full integration of pagination fix with database
"""
import logging
from Agent.web_scraping.web_scraping_processor import WebScrapingProcessor
from backend.database import SessionLocal, WebScrapingSource

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("FULL INTEGRATION TEST - Pagination with Database")
logger.info("=" * 80)

# Create database session
db = SessionLocal()

try:
    # Get or create a test source
    source = db.query(WebScrapingSource).filter(
        WebScrapingSource.url == 'https://www.education.gov.in/documents_reports_hi'
    ).first()
    
    if not source:
        logger.info("Creating test source...")
        source = WebScrapingSource(
            name='Ministry of Education - Documents & Reports (Hindi)',
            url='https://www.education.gov.in/documents_reports_hi',
            description='Test source for pagination',
            source_type='government',
            credibility_score=10,
            scraping_enabled=True,
            pagination_enabled=True,
            max_pages=100,
            max_documents_per_scrape=1500,
            created_by_user_id=1
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        logger.info(f"Created source with ID: {source.id}")
    else:
        logger.info(f"Using existing source with ID: {source.id}")
    
    logger.info(f"Source: {source.name}")
    logger.info(f"URL: {source.url}")
    logger.info(f"Pagination enabled: {source.pagination_enabled}")
    logger.info(f"Max pages: {source.max_pages}")
    logger.info(f"Max documents: {source.max_documents_per_scrape}")
    logger.info("=" * 80)
    
    # Create processor
    processor = WebScrapingProcessor()
    
    # Test scraping (limit to 50 documents for quick test)
    logger.info("\nStarting scrape with pagination (limited to 50 docs for testing)...")
    result = processor.scrape_and_process_source(
        source_id=source.id,
        db_session=db,
        max_documents=50,  # Limit for testing
        pagination_enabled=True,
        max_pages=10
    )
    
    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("RESULTS")
    logger.info("=" * 80)
    logger.info(f"Status: {result.get('status')}")
    logger.info(f"Documents found: {result.get('documents_found', 0)}")
    logger.info(f"Documents processed: {result.get('documents_processed', 0)}")
    logger.info(f"Documents failed: {result.get('documents_failed', 0)}")
    logger.info(f"Execution time: {result.get('execution_time_seconds', 0)}s")
    
    if result.get('status') == 'error':
        logger.error(f"Error: {result.get('error')}")
    else:
        logger.info("\n✅ Integration test PASSED!")
        logger.info(f"Successfully scraped and processed {result.get('documents_processed', 0)} documents")
    
    logger.info("=" * 80)

except Exception as e:
    logger.error(f"Test failed with error: {str(e)}", exc_info=True)

finally:
    db.close()
    logger.info("Database session closed")
