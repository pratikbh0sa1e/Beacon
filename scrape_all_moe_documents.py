"""
Scrape ALL documents from Ministry of Education website
"""
import logging
from Agent.web_scraping.local_storage import LocalStorage
from Agent.web_scraping.web_source_manager import WebSourceManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def scrape_all_documents():
    """Scrape all documents from Ministry of Education"""
    
    logger.info("="*70)
    logger.info("🚀 SCRAPING ALL DOCUMENTS FROM MINISTRY OF EDUCATION")
    logger.info("="*70)
    
    # Initialize
    storage = LocalStorage()
    manager = WebSourceManager(storage)
    
    # Create source with high max_pages to get everything
    source = storage.create_source({
        'name': 'Ministry of Education - Complete',
        'url': 'https://www.education.gov.in/',
        'keywords': None,  # NO FILTERING - get everything
        'pagination_enabled': True,
        'max_pages': 100  # High limit to get all documents
    })
    
    logger.info(f"Source created: {source['name']} (ID: {source['id']})")
    logger.info(f"URL: {source['url']}")
    logger.info(f"Max pages: {source['max_pages']}")
    logger.info(f"Pagination: ENABLED")
    logger.info(f"Keyword filtering: DISABLED (scraping everything)")
    logger.info("")
    logger.info("Starting scraping... This may take several minutes.")
    logger.info("The system will automatically stop when no more pages are found.")
    logger.info("")
    
    # Scrape with pagination
    result = manager.scrape_source_with_pagination(
        source_id=source['id'],
        url=source['url'],
        source_name=source['name'],
        keywords=None,  # No filtering
        pagination_enabled=True,
        max_pages=100,  # Will stop automatically when no more pages
        incremental=False
    )
    
    # Display results
    logger.info("")
    logger.info("="*70)
    logger.info("📊 SCRAPING COMPLETE!")
    logger.info("="*70)
    logger.info(f"Status: {result['status']}")
    logger.info(f"Total documents found: {result.get('documents_new', 0)}")
    logger.info(f"Execution time: {result.get('execution_time_seconds', 0)} seconds")
    logger.info(f"Pagination used: {result.get('pagination_used', False)}")
    logger.info("")
    
    # Show sample documents
    if result.get('documents'):
        logger.info("📄 Sample documents (first 30):")
        logger.info("-"*70)
        for i, doc in enumerate(result['documents'][:30], 1):
            title = doc.get('text', 'No title')[:80]
            url = doc.get('url', 'No URL')
            logger.info(f"{i:3d}. {title}")
            logger.info(f"     URL: {url}")
            logger.info("")
    
    # Save summary
    logger.info("="*70)
    logger.info("💾 DATA SAVED")
    logger.info("="*70)
    logger.info(f"Location: data/scraping_storage/")
    logger.info(f"Files:")
    logger.info(f"  - sources.json (source configurations)")
    logger.info(f"  - document_tracker.json ({result.get('documents_new', 0)} documents tracked)")
    logger.info("")
    
    # Export data summary
    data = storage.export_data()
    logger.info(f"📈 STORAGE SUMMARY:")
    logger.info(f"  - Total sources: {len(data['sources'])}")
    logger.info(f"  - Total tracked documents: {len(data['tracker'])}")
    logger.info(f"  - Total jobs: {len(data['jobs'])}")
    logger.info("")
    
    logger.info("="*70)
    logger.info("✅ ALL DOCUMENTS SCRAPED SUCCESSFULLY!")
    logger.info("="*70)
    
    return result


if __name__ == "__main__":
    try:
        result = scrape_all_documents()
        
        print("\n" + "="*70)
        print(f"✅ SUCCESS! Scraped {result.get('documents_new', 0)} documents")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
        print("Partial results have been saved to data/scraping_storage/")
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
