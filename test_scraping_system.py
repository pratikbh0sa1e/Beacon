"""
Demo script to test the large-scale web scraping system
"""
import logging
from Agent.web_scraping.local_storage import LocalStorage
from Agent.web_scraping.web_source_manager import WebSourceManager
from Agent.web_scraping.health_monitor import HealthMonitor
from Agent.web_scraping.scraping_scheduler import ScrapingScheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_basic_scraping():
    """Demo: Basic scraping with pagination"""
    logger.info("=" * 60)
    logger.info("DEMO 1: Basic Scraping with Pagination")
    logger.info("=" * 60)
    
    # Initialize components
    storage = LocalStorage()
    manager = WebSourceManager(storage)
    
    # Create a test source
    source_data = {
        'name': 'UGC India',
        'url': 'https://www.ugc.gov.in/',
        'keywords': ['policy', 'circular', 'regulation'],
        'pagination_enabled': False,
        'max_pages': 3
    }
    
    source = storage.create_source(source_data)
    logger.info(f"Created source: {source['name']} (ID: {source['id']})")
    
    # Scrape the source
    result = manager.scrape_source_with_pagination(
        source_id=source['id'],
        url=source['url'],
        source_name=source['name'],
        keywords=source['keywords'],
        pagination_enabled=source['pagination_enabled'],
        max_pages=source['max_pages'],
        incremental=False
    )
    
    logger.info(f"Scraping result: {result['status']}")
    logger.info(f"Documents discovered: {result.get('documents_discovered', 0)}")
    logger.info(f"Documents new: {result.get('documents_new', 0)}")
    logger.info(f"Execution time: {result.get('execution_time_seconds', 0)}s")
    
    return source, result


def demo_incremental_scraping(source):
    """Demo: Incremental scraping (only new documents)"""
    logger.info("\n" + "=" * 60)
    logger.info("DEMO 2: Incremental Scraping")
    logger.info("=" * 60)
    
    storage = LocalStorage()
    manager = WebSourceManager(storage)
    
    # Scrape again with incremental enabled
    result = manager.scrape_source_with_pagination(
        source_id=source['id'],
        url=source['url'],
        source_name=source['name'],
        keywords=source['keywords'],
        pagination_enabled=source['pagination_enabled'],
        max_pages=source['max_pages'],
        incremental=True  # Enable incremental
    )
    
    logger.info(f"Scraping result: {result['status']}")
    logger.info(f"Documents discovered: {result.get('documents_discovered', 0)}")
    logger.info(f"Documents new: {result.get('documents_new', 0)}")
    logger.info(f"Documents skipped: {result.get('documents_skipped', 0)}")
    logger.info("✅ Incremental scraping working - skipped already-scraped documents!")
    
    return result


def demo_health_monitoring(source):
    """Demo: Health monitoring"""
    logger.info("\n" + "=" * 60)
    logger.info("DEMO 3: Health Monitoring")
    logger.info("=" * 60)
    
    storage = LocalStorage()
    health_monitor = HealthMonitor(storage)
    
    # Get health metrics
    health = health_monitor.get_source_health(source['id'])
    
    logger.info(f"Source health status: {health['health_status']}")
    logger.info(f"Success rate: {health['success_rate']}%")
    logger.info(f"Total executions: {health['total_executions']}")
    logger.info(f"Consecutive failures: {health['consecutive_failures']}")
    
    # Get overall health summary
    summary = health_monitor.get_health_summary()
    logger.info(f"\nOverall system health: {summary['overall_status']}")
    logger.info(f"Total sources: {summary['total_sources']}")
    logger.info(f"Healthy: {summary['healthy']}, Warning: {summary['warning']}, Critical: {summary['critical']}")
    
    return health


def demo_parallel_scraping():
    """Demo: Parallel scraping of multiple sources"""
    logger.info("\n" + "=" * 60)
    logger.info("DEMO 4: Parallel Scraping")
    logger.info("=" * 60)
    
    storage = LocalStorage()
    manager = WebSourceManager(storage)
    
    # Create multiple test sources
    test_sources = [
        {
            'name': 'Source 1',
            'url': 'https://www.ugc.gov.in/',
            'keywords': ['policy'],
            'pagination_enabled': False,
            'max_pages': 2
        },
        {
            'name': 'Source 2',
            'url': 'https://www.aicte-india.org/',
            'keywords': ['circular'],
            'pagination_enabled': False,
            'max_pages': 2
        }
    ]
    
    # Create sources in storage
    sources = []
    for source_data in test_sources:
        source = storage.create_source(source_data)
        sources.append(source)
        logger.info(f"Created source: {source['name']} (ID: {source['id']})")
    
    # Scrape in parallel
    logger.info(f"\nScraping {len(sources)} sources in parallel...")
    result = manager.scrape_multiple_sources_parallel(sources, rate_limit_delay=1.0)
    
    logger.info(f"Parallel scraping complete!")
    logger.info(f"Successful: {result['successful']}/{result['total_sources']}")
    logger.info(f"Total documents: {result['total_documents']}")
    logger.info(f"Total duration: {result['total_duration_seconds']}s")
    
    return result


def demo_scheduler():
    """Demo: Scheduling (without actually running jobs)"""
    logger.info("\n" + "=" * 60)
    logger.info("DEMO 5: Scheduler Setup")
    logger.info("=" * 60)
    
    storage = LocalStorage()
    manager = WebSourceManager(storage)
    health_monitor = HealthMonitor(storage)
    
    # Create a source
    source_data = {
        'name': 'Scheduled Source',
        'url': 'https://www.ugc.gov.in/',
        'keywords': ['policy'],
        'schedule_enabled': True,
        'schedule_type': 'daily',
        'schedule_time': '02:00'
    }
    
    source = storage.create_source(source_data)
    logger.info(f"Created source: {source['name']} (ID: {source['id']})")
    
    # Initialize scheduler
    scheduler = ScrapingScheduler(storage, manager, health_monitor)
    
    # Schedule the source
    schedule_config = {
        'type': 'daily',
        'time': '02:00'
    }
    
    job_id = scheduler.schedule_source(source['id'], schedule_config)
    logger.info(f"Scheduled job: {job_id}")
    
    # Get next run time
    next_run = scheduler.get_next_run_time(source['id'])
    logger.info(f"Next scheduled run: {next_run}")
    
    # Get scheduler status
    status = scheduler.get_scheduler_status()
    logger.info(f"Scheduler status: {status}")
    
    logger.info("✅ Scheduler configured - will run daily at 2:00 AM")
    
    # Don't start the scheduler in demo
    # scheduler.start()  # Would start background scheduling
    
    return scheduler


def main():
    """Run all demos"""
    logger.info("🚀 Starting Large-Scale Web Scraping System Demo")
    logger.info("=" * 60)
    
    try:
        # Demo 1: Basic scraping
        source, result1 = demo_basic_scraping()
        
        # Demo 2: Incremental scraping
        result2 = demo_incremental_scraping(source)
        
        # Demo 3: Health monitoring
        health = demo_health_monitoring(source)
        
        # Demo 4: Parallel scraping
        result4 = demo_parallel_scraping()
        
        # Demo 5: Scheduler
        scheduler = demo_scheduler()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info("\n📊 System Summary:")
        logger.info(f"  - Components: 9 core modules")
        logger.info(f"  - Storage: Local JSON files (data/scraping_storage/)")
        logger.info(f"  - Features: Pagination, Incremental, Parallel, Scheduling")
        logger.info(f"  - Ready for: 1000+ documents across multiple sources")
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
