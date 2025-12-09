# Scraping Logs System

## Overview

The scraping logs system provides real-time monitoring and historical tracking of all web scraping activities. It includes both backend logging infrastructure and a frontend dashboard for visualization.

## Features

### Backend Features

1. **Comprehensive Logging**
   - Start/end timestamps
   - Progress tracking (pages scraped, documents found)
   - Error tracking with timestamps
   - Activity messages log
   - Execution time tracking

2. **Storage**
   - File-based storage in `data/scraping_storage/scraping_logs.json`
   - Automatic log rotation (configurable retention period)
   - Efficient querying by source or time range

3. **API Endpoints**
   - `GET /api/scraping-logs/recent` - Get recent logs
   - `GET /api/scraping-logs/{log_id}` - Get specific log
   - `GET /api/scraping-logs/source/{source_id}` - Get logs for a source
   - `GET /api/scraping-logs/stats/summary` - Get summary statistics
   - `DELETE /api/scraping-logs/old` - Clear old logs

### Frontend Features

1. **Real-time Dashboard**
   - Auto-refresh every 5 seconds (toggleable)
   - Live progress bars for running scrapes
   - Status indicators (running/success/error)

2. **Summary Statistics**
   - Total logs count
   - Running/successful/failed counts
   - Total documents scraped
   - Total pages scraped

3. **Detailed Log View**
   - Expandable rows for detailed information
   - Activity log with all messages
   - Error details with timestamps
   - Progress tracking

## Usage

### Backend Integration

```python
from Agent.web_scraping.scraping_logger import ScrapingLogger
from Agent.web_scraping.local_storage import LocalStorage

# Initialize
storage = LocalStorage()
logger = ScrapingLogger(storage)

# Start logging
log_id = logger.log_scraping_start(
    source_id=1,
    source_name="Ministry of Education",
    source_url="https://www.education.gov.in/",
    max_documents=1500,
    max_pages=100
)

# Log progress
logger.log_page_scraped(log_id, page_num=1, documents_on_page=30)
logger.log_page_scraped(log_id, page_num=2, documents_on_page=30)

# Log document limit reached
logger.log_document_limit_reached(log_id, total_documents=1500)

# Log errors
logger.log_error(log_id, "Connection timeout on page 5")

# Complete logging
logger.log_scraping_complete(
    log_id=log_id,
    status='success',
    documents_found=1500,
    pages_scraped=50,
    execution_time=73.5
)
```

### Frontend Integration

Add the component to your React app:

```tsx
import ScrapingLogs from './components/ScrapingLogs';

function App() {
  return (
    <div>
      <ScrapingLogs />
    </div>
  );
}
```

## File Structure

```
backend/
  routers/
    scraping_logs.py          # API endpoints

Agent/
  web_scraping/
    scraping_logger.py        # Logging logic
    local_storage.py          # Storage methods (updated)

frontend/
  src/
    components/
      ScrapingLogs.tsx        # Dashboard component

data/
  scraping_storage/
    scraping_logs.json        # Log storage file
```

## Log Entry Structure

```json
{
  "id": 1,
  "source_id": 1,
  "source_name": "Ministry of Education",
  "source_url": "https://www.education.gov.in/",
  "status": "success",
  "started_at": "2025-12-09T01:30:00.000Z",
  "completed_at": "2025-12-09T01:31:13.000Z",
  "max_documents": 1500,
  "max_pages": 100,
  "documents_found": 1500,
  "pages_scraped": 50,
  "current_page": 50,
  "execution_time": 73.5,
  "errors": [],
  "messages": [
    "Started scraping Ministry of Education",
    "Page 1: Found 30 documents (total: 30)",
    "Page 2: Found 30 documents (total: 60)",
    "...",
    "⚠️ Document limit reached: 1500 documents collected",
    "✅ Scraping complete: 1500 documents in 73.5s"
  ]
}
```

## Configuration

### Log Retention

Clear logs older than 30 days (default):

```python
logger.clear_old_logs(days=30)
```

Or via API:

```bash
curl -X DELETE "http://localhost:8000/api/scraping-logs/old?days=30"
```

### Auto-refresh Interval

Modify in `ScrapingLogs.tsx`:

```tsx
// Change from 5000ms (5 seconds) to desired interval
interval = setInterval(fetchLogs, 5000);
```

## API Examples

### Get Recent Logs

```bash
curl "http://localhost:8000/api/scraping-logs/recent?limit=50"
```

### Get Specific Log

```bash
curl "http://localhost:8000/api/scraping-logs/1"
```

### Get Logs for Source

```bash
curl "http://localhost:8000/api/scraping-logs/source/1?limit=20"
```

### Get Summary Statistics

```bash
curl "http://localhost:8000/api/scraping-logs/stats/summary"
```

Response:
```json
{
  "total_logs": 25,
  "running": 2,
  "successful": 20,
  "failed": 3,
  "total_documents_scraped": 15000,
  "total_pages_scraped": 500
}
```

## Benefits

1. **Real-time Monitoring** - See scraping progress as it happens
2. **Historical Analysis** - Review past scraping jobs
3. **Error Tracking** - Identify and debug issues quickly
4. **Performance Metrics** - Track execution times and throughput
5. **Audit Trail** - Complete record of all scraping activities

## Next Steps

1. Register the API router in your FastAPI app
2. Add the frontend component to your navigation
3. Configure log retention policies
4. Set up alerts for failed scrapes (optional)
