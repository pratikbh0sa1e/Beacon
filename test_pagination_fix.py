"""
Test script to verify pagination is working correctly
"""
import logging
from Agent.web_scraping.web_source_manager import WebSourceManager
from Agent.web_scraping.config import ScrapingConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
logger.info("=" * 80)
logger.info("PAGINATION FIX TEST")
logger.info("=" * 80)
logger.info(f"Max documents per source: {ScrapingConfig.get_max_documents()}")
logger.info(f"Default max pages: {ScrapingConfig.DEFAULT_MAX_PAGES}")
logger.info("=" * 80)

# Create manager
manager = WebSourceManager()

# Test source
source = {
    'id': 1,
    'name': 'Ministry of Education - Documents & Reports (Hindi)',
    'url': 'https://www.education.gov.in/documents_reports_hi',
    'keywords': None  # No filtering to get all documents
}

logger.info(f"\nTesting source: {source['name']}")
logger.info(f"URL: {source['url']}")
logger.info(f"Pagination: ENABLED")
logger.info(f"Max pages: 100")
logger.info(f"Max documents: 1500")
logger.info("=" * 80)

# Scrape with pagination
result = manager.scrape_source_with_pagination(
    source_id=source['id'],
    url=source['url'],
    source_name=source['name'],
    keywords=source['keywords'],
    pagination_enabled=True,
    max_pages=100,
    incremental=False,
    max_documents=1500
)

# Display results
logger.info("\n" + "=" * 80)
logger.info("RESULTS")
logger.info("=" * 80)
logger.info(f"Status: {result.get('status')}")
logger.info(f"Documents discovered: {result.get('documents_discovered', 0)}")
logger.info(f"Documents matched: {result.get('documents_matched', 0)}")
logger.info(f"Documents new: {result.get('documents_new', 0)}")
logger.info(f"Documents skipped: {result.get('documents_skipped', 0)}")
logger.info(f"Pagination used: {result.get('pagination_used', False)}")
logger.info(f"Execution time: {result.get('execution_time_seconds', 0)}s")

if result.get('status') == 'error':
    logger.error(f"Error: {result.get('error')}")
    logger.error(f"Error type: {result.get('error_type')}")

logger.info("=" * 80)
logger.info(f"TEST COMPLETE - Found {result.get('documents_new', 0)} documents")
logger.info("=" * 80)
