"""
Scrape ALL documents from Ministry of Education website
No page limits - scrape everything!
"""
import logging
from Agent.web_scraping.local_storage import LocalStorage
from Agent.web_scraping.web_source_manager import WebSourceManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize
storage = LocalStorage()
manager = WebSourceManager(storage)

# Ministry of Education - Scrape EVERYTHING
source = storage.create_source({
    'name': 'Ministry of Education - Complete Website',
    'url': 'https://www.education.gov.in/',
    'keywords': None,  # NO FILTERING - scrape everything!
    'pagination_enabled': True,
    'max_pages': 100  # Set high limit to get all pages (will stop when no more documents found)
})

logger.info(f"=" * 80)
logger.info(f"SCRAPING ALL DOCUMENTS FROM MINISTRY OF EDUCATION WEBSITE")
logger.info(f"=" * 80)
logger.info(f"Source: {source['url']}")
logger.info(f"Max pages: {source['max_pages']} (will stop when no more documents found)")
logger.info(f"Keyword filtering: DISABLED (scraping everything)")
logger.info(f"=" * 80)

result = manager.scrape_source_with_pagination(
    source_id=source['id'],
    url=source['url'],
    source_name=source['name'],
    keywords=None,  # NO FILTERING
    pagination_enabled=True,
    max_pages=100,  # High limit - will stop when pagination ends
    incremental=False
)

logger.info(f"\n{'='*80}")
logger.info(f"SCRAPING COMPLETE!")
logger.info(f"{'='*80}")
logger.info(f"Status: {result['status']}")
logger.info(f"Total documents found: {result.get('documents_new', 0)}")
logger.info(f"Execution time: {result.get('execution_time_seconds', 0):.2f} seconds")
logger.info(f"Pages scraped: {result.get('pages_scraped', 'Unknown')}")

if result.get('documents'):
    logger.info(f"\n📄 Sample of documents found (first 20):")
    for i, doc in enumerate(result['documents'][:20], 1):
        logger.info(f"   {i}. {doc.get('text', 'No title')[:80]}")
        logger.info(f"      URL: {doc.get('url', 'No URL')}")
    
    if len(result['documents']) > 20:
        logger.info(f"\n   ... and {len(result['documents']) - 20} more documents")

logger.info(f"\n{'='*80}")
logger.info(f"✅ SUCCESS! Scraped {result.get('documents_new', 0)} documents from the entire website")
logger.info(f"{'='*80}")

# Save summary to file
with open('scraping_summary.txt', 'w', encoding='utf-8') as f:
    f.write(f"Ministry of Education - Complete Website Scraping\n")
    f.write(f"=" * 80 + "\n\n")
    f.write(f"Total documents found: {result.get('documents_new', 0)}\n")
    f.write(f"Execution time: {result.get('execution_time_seconds', 0):.2f} seconds\n")
    f.write(f"Pages scraped: {result.get('pages_scraped', 'Unknown')}\n\n")
    f.write(f"Documents:\n")
    f.write(f"-" * 80 + "\n")
    
    if result.get('documents'):
        for i, doc in enumerate(result['documents'], 1):
            f.write(f"\n{i}. {doc.get('text', 'No title')}\n")
            f.write(f"   URL: {doc.get('url', 'No URL')}\n")
            f.write(f"   Type: {doc.get('type', 'Unknown')}\n")

logger.info(f"\n📝 Summary saved to: scraping_summary.txt")
