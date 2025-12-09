# Large-Scale Web Scraping System

A production-ready web scraping system designed to automatically collect 1000+ policy documents from government websites with scheduling, pagination, and incremental scraping capabilities.

## 🎯 Features

- **Automatic Pagination** - Detects and follows pagination links automatically
- **Incremental Scraping** - Only scrapes new documents, skips already-scraped ones
- **Parallel Processing** - Scrapes multiple sources concurrently (5 workers)
- **Scheduled Scraping** - Daily automated scraping at 2 AM
- **Health Monitoring** - Tracks success rates and alerts on failures
- **Retry Logic** - Exponential backoff for network errors (1s, 2s, 4s)
- **Rate Limiting** - Polite scraping with configurable delays
- **Local Storage** - JSON-based storage (no database required)

## 📦 Components

### Core Modules

1. **LocalStorage** (`local_storage.py`)
   - File-based data persistence
   - Stores sources, jobs, document tracker, health metrics
   - Location: `data/scraping_storage/`

2. **PaginationEngine** (`pagination_engine.py`)
   - Detects pagination patterns (query params, path segments, next buttons)
   - Automatically follows pagination links
   - Respects max_pages limit

3. **IncrementalScraper** (`incremental_scraper.py`)
   - Tracks scraped documents by URL and content hash
   - Filters out already-scraped documents
   - Detects content changes

4. **HealthMonitor** (`health_monitor.py`)
   - Tracks success rates and execution times
   - Alerts after 3 consecutive failures
   - Provides health status (healthy, warning, critical)

5. **RetryUtils** (`retry_utils.py`)
   - Exponential backoff retry logic
   - Handles network errors, timeouts, HTTP errors
   - Configurable retry attempts

6. **ParallelProcessor** (`parallel_processor.py`)
   - Concurrent scraping with ThreadPoolExecutor
   - Fault isolation (one failure doesn't affect others)
   - Per-domain rate limiting

7. **WebScraper** (`scraper.py` - Enhanced)
   - Pagination detection
   - Content validation
   - Retry support

8. **WebSourceManager** (`web_source_manager.py` - Enhanced)
   - Orchestrates all components
   - Supports pagination and incremental scraping
   - Parallel multi-source scraping

9. **ScrapingScheduler** (`scraping_scheduler.py`)
   - APScheduler-based job scheduling
   - Daily, weekly, interval, and custom schedules
   - Automatic job initialization

## 🚀 Quick Start

### Installation

```bash
# Install required packages
pip install apscheduler requests beautifulsoup4 pytz
```

### Basic Usage

```python
from Agent.web_scraping.local_storage import LocalStorage
from Agent.web_scraping.web_source_manager import WebSourceManager

# Initialize
storage = LocalStorage()
manager = WebSourceManager(storage)

# Create a source
source_data = {
    'name': 'UGC India',
    'url': 'https://www.ugc.gov.in/',
    'keywords': ['policy', 'circular'],
    'pagination_enabled': True,
    'max_pages': 10
}
source = storage.create_source(source_data)

# Scrape with pagination
result = manager.scrape_source_with_pagination(
    source_id=source['id'],
    url=source['url'],
    source_name=source['name'],
    keywords=source['keywords'],
    pagination_enabled=True,
    max_pages=10,
    incremental=False
)

print(f"Found {result['documents_new']} documents")
```

### Scheduled Scraping

```python
from Agent.web_scraping.scraping_scheduler import ScrapingScheduler
from Agent.web_scraping.health_monitor import HealthMonitor

# Initialize
health_monitor = HealthMonitor(storage)
scheduler = ScrapingScheduler(storage, manager, health_monitor)

# Schedule daily scraping at 2 AM
schedule_config = {
    'type': 'daily',
    'time': '02:00'
}
job_id = scheduler.schedule_source(source['id'], schedule_config)

# Start scheduler
scheduler.start()
```

### Parallel Scraping

```python
# Create multiple sources
sources = [
    storage.create_source({
        'name': 'Source 1',
        'url': 'https://example1.gov.in/',
        'keywords': ['policy']
    }),
    storage.create_source({
        'name': 'Source 2',
        'url': 'https://example2.gov.in/',
        'keywords': ['circular']
    })
]

# Scrape in parallel
result = manager.scrape_multiple_sources_parallel(
    sources=sources,
    rate_limit_delay=1.0
)

print(f"Scraped {result['total_documents']} documents from {result['successful']} sources")
```

## 🧪 Testing

Run the demo script to test all features:

```bash
python test_scraping_system.py
```

This will demonstrate:
1. Basic scraping with pagination
2. Incremental scraping (skipping already-scraped documents)
3. Health monitoring
4. Parallel scraping
5. Scheduler setup

## 📊 Data Storage

All data is stored in JSON files under `data/scraping_storage/`:

- `sources.json` - Source configurations
- `jobs.json` - Job execution history
- `document_tracker.json` - Tracked documents for incremental scraping
- `health_metrics.json` - Health metrics for each source

## 🔧 Configuration

### Source Configuration

```python
{
    'name': 'Source Name',
    'url': 'https://example.gov.in/',
    'keywords': ['policy', 'circular'],  # Optional keyword filtering
    'pagination_enabled': True,          # Enable pagination
    'max_pages': 10,                     # Max pages to scrape
    'schedule_enabled': True,            # Enable scheduling
    'schedule_type': 'daily',            # daily, weekly, interval, custom
    'schedule_time': '02:00'             # Time for daily/weekly
}
```

### Schedule Types

- **daily**: Run at specific time every day (e.g., '02:00')
- **weekly**: Run on specific day and time (e.g., Monday at '02:00')
- **interval**: Run every N minutes (e.g., '60' for hourly)
- **custom**: Custom cron expression (e.g., '0 2 * * *')

## 📈 Monitoring

### Health Status

```python
from Agent.web_scraping.health_monitor import HealthMonitor

health_monitor = HealthMonitor(storage)

# Get source health
health = health_monitor.get_source_health(source_id)
print(f"Status: {health['health_status']}")
print(f"Success rate: {health['success_rate']}%")
print(f"Consecutive failures: {health['consecutive_failures']}")

# Get overall health
summary = health_monitor.get_health_summary()
print(f"Overall status: {summary['overall_status']}")
print(f"Healthy: {summary['healthy']}, Critical: {summary['critical']}")
```

### Alerts

The system automatically alerts when:
- A source fails 3 times consecutively
- Success rate drops below 80%

## 🎯 Use Cases

### 1. Immediate Scraping (1-2 days)
Scrape 1000+ documents from 10-15 government sources immediately.

```python
# Create 10-15 sources
sources = [...]  # List of source configurations

# Scrape all in parallel
result = manager.scrape_multiple_sources_parallel(sources)
```

### 2. Daily Updates (2 AM)
Automatically scrape new documents every day at 2 AM.

```python
# Schedule all sources
for source in sources:
    scheduler.schedule_source(source['id'], {
        'type': 'daily',
        'time': '02:00'
    })

scheduler.start()
```

### 3. Comprehensive Coverage
Scrape everything from multiple sections of government websites.

```python
# Add multiple sections as separate sources
sections = [
    {'url': 'https://example.gov.in/policies/', 'name': 'Policies'},
    {'url': 'https://example.gov.in/circulars/', 'name': 'Circulars'},
    {'url': 'https://example.gov.in/archive/', 'name': 'Archive'}
]

for section in sections:
    storage.create_source(section)
```

## 🔍 Troubleshooting

### Issue: No documents found
- Check if keywords are too restrictive
- Verify URL is accessible
- Check pagination settings

### Issue: Scheduler not running
- Ensure `scheduler.start()` is called
- Check scheduler status: `scheduler.get_scheduler_status()`
- Verify source has `schedule_enabled=True`

### Issue: High failure rate
- Check health metrics: `health_monitor.get_source_health(source_id)`
- Review error logs in job records
- Verify source URL is still valid

## 📝 Requirements

- Python 3.8+
- apscheduler
- requests
- beautifulsoup4
- pytz

## 🎓 Architecture

```
┌─────────────────────────────────────────┐
│         ScrapingScheduler               │
│    (APScheduler - Daily at 2 AM)        │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│       WebSourceManager                  │
│  (Orchestrates all components)          │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│Pagination│ │Incremental│ │ Parallel │
│  Engine  │ │  Scraper  │ │Processor │
└──────────┘ └──────────┘ └──────────┘
        │         │         │
        └─────────┼─────────┘
                  ▼
        ┌──────────────────┐
        │   WebScraper     │
        │  (with Retry)    │
        └──────────────────┘
                  │
                  ▼
        ┌──────────────────┐
        │  LocalStorage    │
        │  (JSON files)    │
        └──────────────────┘
```

## 🚀 Next Steps

1. Run the demo: `python test_scraping_system.py`
2. Create your sources in `LocalStorage`
3. Configure scheduling for daily updates
4. Monitor health metrics
5. Scale to 1000+ documents!

## 📄 License

This system is part of the Beacon project.
