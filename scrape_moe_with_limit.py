"""
Scrape Ministry of Education with configurable document limit
Default: 1500 documents (can be changed in config)
"""
import logging
from Agent.web_scraping.local_storage import LocalStorage
from Agent.web_scraping.web_source_manager import WebSourceManager
from Agent.web_scraping.config import ScrapingConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Display current configuration
logger.info("=" * 80)
logger.info("SCRAPING CONFIGURATION")
logger.info("=" * 80)
config = ScrapingConfig.get_config_summary()
for key, value in config.items():
    logger.info(f"  {key}: {value}")
logger.info("=" * 80)

# Initialize
storage = LocalStorage()
manager = WebSourceManager(storage)

# Ministry of Education - With document limit
source = storage.create_source({
    'name': 'Ministry of Education - Limited',
    'url': 'https://www.education.gov.in/',
    'keywords': None,  # NO FILTERING - scrape everything!
    'pagination_enabled': True,
    'max_pages': 100  # High page limit, but will stop at document limit
})

logger.info(f"\n{'='*80}")
logger.info(f"SCRAPING MINISTRY OF EDUCATION")
logger.info(f"{'='*80}")
logger.info(f"Source: {source['url']}")
logger.info(f"Max documents: {ScrapingConfig.get_max_documents()}")
logger.info(f"Max pages: {source['max_pages']}")
logger.info(f"Keyword filtering: DISABLED")
logger.info(f"{'='*80}\n")

result = manager.scrape_source_with_pagination(
    source_id=source['id'],
    url=source['url'],
    source_name=source['name'],
    keywords=None,
    pagination_enabled=True,
    max_pages=100,
    incremental=False,
    max_documents=None  # Will use config default (1500)
)

logger.info(f"\n{'='*80}")
logger.info(f"SCRAPING COMPLETE!")
logger.info(f"{'='*80}")
logger.info(f"Status: {result['status']}")
logger.info(f"Total documents found: {result.get('documents_new', 0)}")
logger.info(f"Execution time: {result.get('execution_time_seconds', 0):.2f} seconds")
logger.info(f"Document limit: {ScrapingConfig.get_max_documents()}")

if result.get('documents'):
    logger.info(f"\n📄 Sample of documents found (first 10):")
    for i, doc in enumerate(result['documents'][:10], 1):
        logger.info(f"   {i}. {doc.get('text', 'No title')[:80]}")
        logger.info(f"      URL: {doc.get('url', 'No URL')}")
    
    if len(result['documents']) > 10:
        logger.info(f"\n   ... and {len(result['documents']) - 10} more documents")

logger.info(f"\n{'='*80}")
logger.info(f"✅ SUCCESS! Scraped {result.get('documents_new', 0)} documents")
logger.info(f"{'='*80}")

# Show how to change the limit
logger.info(f"\n{'='*80}")
logger.info(f"TO CHANGE THE DOCUMENT LIMIT:")
logger.info(f"{'='*80}")
logger.info(f"1. Edit Agent/web_scraping/config.py")
logger.info(f"2. Change MAX_DOCUMENTS_PER_SOURCE = 1500 to your desired limit")
logger.info(f"3. Or use: ScrapingConfig.set_max_documents(2000)")
logger.info(f"{'='*80}")
