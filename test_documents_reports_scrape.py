"""
Test scraping from https://www.education.gov.in/documents_reports_hi
"""
import logging
from Agent.web_scraping.local_storage import LocalStorage
from Agent.web_scraping.web_source_manager import WebSourceManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize
storage = LocalStorage()
manager = WebSourceManager(storage)

# Create source for documents_reports_hi page
source = storage.create_source({
    'name': 'Ministry of Education - Documents & Reports (Hindi)',
    'url': 'https://www.education.gov.in/documents_reports_hi',
    'keywords': None,  # NO FILTERING
    'pagination_enabled': True,
    'max_pages': 100
})

logger.info(f"=" * 80)
logger.info(f"TESTING SCRAPE: {source['url']}")
logger.info(f"=" * 80)
logger.info(f"Pagination: {source['pagination_enabled']}")
logger.info(f"Max Pages: {source['max_pages']}")
logger.info(f"=" * 80)

result = manager.scrape_source_with_pagination(
    source_id=source['id'],
    url=source['url'],
    source_name=source['name'],
    keywords=None,
    pagination_enabled=True,
    max_pages=100,
    incremental=False,
    max_documents=1500
)

logger.info(f"\n{'='*80}")
logger.info(f"RESULTS:")
logger.info(f"{'='*80}")
logger.info(f"Status: {result['status']}")
logger.info(f"Documents found: {result.get('documents_new', 0)}")
logger.info(f"Execution time: {result.get('execution_time_seconds', 0)}s")

if result.get('documents'):
    logger.info(f"\n📄 Sample documents (first 10):")
    for i, doc in enumerate(result['documents'][:10], 1):
        logger.info(f"   {i}. {doc.get('text', 'No title')[:80]}")
        logger.info(f"      URL: {doc.get('url', 'No URL')}")

logger.info(f"\n✅ Test complete! Found {result.get('documents_new', 0)} documents")
