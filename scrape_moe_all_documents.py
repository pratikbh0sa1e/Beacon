"""
Scrape Ministry of Education - ALL documents (no keyword filtering)
"""
import logging
from Agent.web_scraping.local_storage import LocalStorage
from Agent.web_scraping.web_source_manager import WebSourceManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize
storage = LocalStorage()
manager = WebSourceManager(storage)

# Ministry of Education - NO keyword filtering
source = storage.create_source({
    'name': 'Ministry of Education - All Documents',
    'url': 'https://www.education.gov.in/',
    'keywords': None,  # NO FILTERING - scrape everything!
    'pagination_enabled': True,
    'max_pages': 10  # Scrape up to 10 pages
})

logger.info(f"Scraping Ministry of Education (ALL documents, no filtering)...")

result = manager.scrape_source_with_pagination(
    source_id=source['id'],
    url=source['url'],
    source_name=source['name'],
    keywords=None,  # NO FILTERING
    pagination_enabled=True,
    max_pages=10,
    incremental=False
)

logger.info(f"\n{'='*60}")
logger.info(f"RESULTS:")
logger.info(f"{'='*60}")
logger.info(f"Status: {result['status']}")
logger.info(f"Documents found: {result.get('documents_new', 0)}")
logger.info(f"Execution time: {result.get('execution_time_seconds', 0)}s")

if result.get('documents'):
    logger.info(f"\n📄 Documents found:")
    for i, doc in enumerate(result['documents'][:20], 1):
        logger.info(f"   {i}. {doc.get('text', 'No title')[:100]}")
        logger.info(f"      URL: {doc.get('url', 'No URL')}")

logger.info(f"\n✅ Scraping complete! Found {result.get('documents_new', 0)} documents")
