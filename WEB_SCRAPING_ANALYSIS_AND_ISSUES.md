# Web Scraping System Analysis & Issues

## Current Web Scraping Algorithm

### Architecture Overview

Your system uses a **multi-layered enhanced scraping architecture** with the following components:

1. **Site-Specific Scrapers** (`Agent/web_scraping/site_scrapers/`)

   - `MoEScraper` - Ministry of Education specific
   - `BaseScraper` - Generic government sites
   - Each has hardcoded CSS selectors for better accuracy

2. **Enhanced Scraping Orchestrator** (`enhanced_scraping_orchestrator.py`)

   - Coordinates all scraping components
   - Implements sliding window re-scanning
   - Page content hashing for change detection
   - Document identity management

3. **Document Identity Manager** (`document_identity_manager.py`)

   - URL-first deduplication approach
   - Content hash checking
   - Version tracking

4. **Enhanced Processor** (`enhanced_processor.py`)
   - Downloads documents
   - Extracts text using OCR if needed
   - Uploads to Supabase storage
   - Creates database records
   - Runs metadata extraction

### How It Works

```
1. User clicks "Scrape Now" on WebScrapingPage.jsx
   ↓
2. Frontend calls: POST /api/enhanced-web-scraping/scrape-enhanced
   ↓
3. Backend (enhanced_web_scraping_router.py) calls enhanced_scrape_source()
   ↓
4. Enhanced Processor:
   - Gets site-specific scraper (MoEScraper for MoE)
   - Scrapes page using scraper.scrape_page()
   - Extracts document links using scraper.get_document_links()
   - For each document:
     a. Checks if already exists (by source_url)
     b. Downloads document
     c. Extracts text (with OCR if needed)
     d. Uploads to Supabase
     e. Creates Document record in database
     f. Creates DocumentMetadata record
     g. Runs metadata extraction (AI-powered)
   ↓
5. Returns stats to frontend
```

## Database Storage - YES, IT SAVES TO DB! ✅

### Documents ARE Being Saved

Your scraping system **DOES save documents to the database**. Here's the proof:

**File: `Agent/web_scraping/enhanced_processor.py` (Lines 500-550)**

```python
# Create document record (following normal workflow)
document = Document(
    filename=unique_filename,
    file_type=doc_info.get('file_type', 'pdf'),
    s3_url=s3_url,  # Stored in Supabase
    extracted_text=extracted_text,
    source_url=doc_info['url'],  # Original URL
    visibility_level="public",
    approval_status="approved",  # Auto-approved
    uploaded_at=datetime.utcnow(),
    content_hash=hashlib.sha256(...).hexdigest(),
    download_allowed=True
)

db.add(document)
db.flush()

# Create metadata
doc_metadata = DocumentMetadata(
    document_id=document.id,
    title=doc_info['title'][:500],
    text_length=len(extracted_text),
    metadata_status='processing',
    embedding_status='uploaded'
)

db.add(doc_metadata)
db.commit()
```

### Database Tables Used

1. **`documents`** - Main document records

   - `id`, `filename`, `file_type`, `s3_url`
   - `extracted_text` - Full text content
   - `source_url` - Original URL (for deduplication)
   - `content_hash` - SHA256 hash (for duplicate detection)
   - `approval_status` - Auto-set to "approved"
   - `visibility_level` - Set to "public"

2. **`document_metadata`** - AI-extracted metadata

   - `title`, `department`, `document_type`
   - `summary`, `keywords`, `entities`
   - `embedding_status`, `metadata_status`

3. **`scraped_documents`** - Provenance tracking
   - Links documents to their scraping source
   - Tracks credibility scores
   - Stores provenance metadata

## Deduplication System

### Three-Level Deduplication ✅

Your system has **excellent deduplication** using a URL-first approach:

**Level 1: URL-Based (Primary)**

```python
# Check by source URL first
existing_doc = db.query(Document).filter(
    Document.source_url == url
).first()

if existing_doc:
    if existing_doc.content_hash == content_hash:
        return "skip_unchanged"  # Same URL, same content
    else:
        return "update_version"  # Same URL, different content (new version)
```

**Level 2: Content Hash (Duplicate Detection)**

```python
# Check by content hash (different URL, same content)
existing_doc = db.query(Document).filter(
    Document.content_hash == content_hash,
    Document.source_url != url  # Different URL
).first()

if existing_doc:
    return "link_duplicate"  # Same content at different URL
```

**Level 3: Normalized URL (URL Variations)**

```python
# Handle URL variations (query params, fragments, etc.)
normalized_url = self._normalize_url(url)
similar_docs = db.query(Document).filter(
    Document.source_url.like(f"{normalized_url}%")
).all()
```

### Deduplication Assessment: **EXCELLENT** ✅

Your deduplication is sophisticated and should work well!

## THE REAL PROBLEM: Why Only 245 Documents?

### Issue #1: **HARD-CODED LIMIT IN CODE** 🚨

**File: `Agent/web_scraping/enhanced_processor.py` Line 442**

```python
# Process each document (limit for testing)
processed_count = 0
for doc_info in documents[:min(max_documents, 10)]:  # ⚠️ LIMIT TO 10 FOR TESTING
    if processed_count >= max_documents:
        break
```

**THIS IS YOUR PROBLEM!** The code has a hard-coded limit of **10 documents per scrape** for testing purposes!

Even though you set `max_documents=1500` in the frontend, the backend overrides it to 10.

### Issue #2: **Single Page Scraping Only**

**File: `Agent/web_scraping/enhanced_processor.py` Lines 420-425**

```python
# Scrape the source URL
try:
    logger.info(f"Scraping page: {source.url}")

    # Get page content using site-specific scraper
    page_result = scraper.scrape_page(source.url)

    # ... only scrapes ONE page, no pagination!
```

The enhanced processor **only scrapes the first page** and doesn't follow pagination links, even though pagination is implemented in the orchestrator!

### Issue #3: **Not Using the Full Orchestrator**

The `enhanced_scrape_source()` function doesn't use the `EnhancedScrapingOrchestrator` which has:

- Sliding window management
- Page hash tracking
- Pagination support
- Multi-page scraping

Instead, it implements a simplified version that only scrapes one page.

## How to Fix: Get All 1000+ Documents

### Fix #1: Remove the 10-Document Limit

**File: `Agent/web_scraping/enhanced_processor.py` Line 442**

Change:

```python
for doc_info in documents[:min(max_documents, 10)]:  # ❌ WRONG
```

To:

```python
for doc_info in documents[:max_documents]:  # ✅ CORRECT
```

### Fix #2: Enable Multi-Page Scraping

**Option A: Use the Full Orchestrator (Recommended)**

Replace the simplified scraping logic with the full orchestrator:

```python
def enhanced_scrape_source(...):
    # Use the full orchestrator instead
    orchestrator = EnhancedScrapingOrchestrator(window_size=3)

    result = orchestrator.scrape_source_enhanced(
        source_id=source_id,
        max_pages=max_pages,  # Will scrape multiple pages
        max_documents=max_documents,
        force_full_scan=True  # For first-time scraping
    )

    return result
```

**Option B: Add Pagination to Current Code**

Add pagination loop after line 445:

```python
# Get pagination links
pagination_links = scraper.get_pagination_links(page_result['soup'], source.url)

# Process additional pages
for page_url in pagination_links[:max_pages-1]:
    page_result = scraper.scrape_page(page_url)
    if page_result['status'] == 'success':
        more_documents = scraper.get_document_links(page_result['soup'], page_url)
        documents.extend(more_documents)
```

### Fix #3: Increase Timeout and Rate Limiting

For 1000+ documents, you need:

```python
# Increase timeout for large scrapes
timeout = 300  # 5 minutes instead of 30 seconds

# Add progress logging
if processed_count % 50 == 0:
    logger.info(f"Progress: {processed_count}/{len(documents)} documents processed")

# Adjust rate limiting
time.sleep(0.2)  # Faster than current 0.5s
```

## Web Scraping Page - How to Stop Scraping

### Current Stop Functionality

**Frontend: `WebScrapingPage.jsx` Lines 280-305**

```javascript
const handleStopScraping = async (sourceId) => {
  try {
    const jobId = scrapingJobs[sourceId];
    if (!jobId) {
      toast.error("No active scraping job found");
      return;
    }

    // Call stop endpoint
    await axios.post(`${API_BASE_URL}/enhanced-web-scraping/stop-scraping`, {
      source_id: sourceId,
      job_id: jobId,
    });

    toast.success("Scraping stopped successfully");

    // Update state
    setScrapingInProgress((prev) => ({ ...prev, [sourceId]: false }));
    setScrapingJobs((prev) => {
      const newJobs = { ...prev };
      delete newJobs[sourceId];
      return newJobs;
    });
  } catch (error) {
    console.error("Error stopping scraping:", error);
    toast.error("Failed to stop scraping");
  }
};
```

### How It Works

1. **Start Scraping**:

   - User clicks "Scrape Now" button
   - Frontend generates unique `jobId = scrape_${sourceId}_${Date.now()}`
   - Stores in `scrapingJobs` state
   - Sets `scrapingInProgress[sourceId] = true`
   - Shows "Stop" button

2. **Stop Scraping**:
   - User clicks "Stop" button
   - Frontend calls `/enhanced-web-scraping/stop-scraping`
   - Backend logs the stop request (but doesn't actually cancel)
   - Frontend updates UI to show scraping stopped

### Current Limitation

**Backend: `enhanced_web_scraping_router.py` Lines 260-285**

```python
@router.post("/stop-scraping")
async def stop_scraping(request: dict, ...):
    # For now, we'll just return success since we don't have persistent job tracking
    # In a production system, you'd track active jobs and cancel them
    logger.info(f"Stop scraping requested for source {source_id}, job {job_id}")

    return {
        "status": "success",
        "message": f"Scraping job {job_id} stopped"
    }
```

**The stop functionality is a PLACEHOLDER!** It doesn't actually stop the scraping process.

### Why Stop Doesn't Work

The scraping runs **synchronously** in the API endpoint:

```python
@router.post("/scrape-enhanced")
async def scrape_source_enhanced(...):
    # This blocks until scraping completes
    result = enhanced_scrape_source(...)  # Runs to completion
    return result
```

There's no way to interrupt it mid-execution.

### How to Implement Real Stop Functionality

**Option 1: Use Background Tasks with Cancellation**

```python
from fastapi import BackgroundTasks
import asyncio

# Global dict to track cancellation
scraping_cancellation = {}

@router.post("/scrape-enhanced")
async def scrape_source_enhanced(request, background_tasks: BackgroundTasks, ...):
    job_id = f"scrape_{request.source_id}_{int(time.time())}"
    scraping_cancellation[job_id] = False

    # Run in background
    background_tasks.add_task(
        run_scraping_with_cancellation,
        job_id,
        request.source_id,
        request.max_documents
    )

    return {"status": "started", "job_id": job_id}

def run_scraping_with_cancellation(job_id, source_id, max_documents):
    for doc in documents:
        # Check if cancelled
        if scraping_cancellation.get(job_id, False):
            logger.info(f"Scraping {job_id} cancelled")
            break

        # Process document
        process_document(doc)

@router.post("/stop-scraping")
async def stop_scraping(request: dict, ...):
    job_id = request.get("job_id")
    scraping_cancellation[job_id] = True
    return {"status": "cancelled"}
```

**Option 2: Use Celery for Async Tasks**

```python
from celery import Celery

celery_app = Celery('scraping', broker='redis://localhost:6379')

@celery_app.task(bind=True)
def scrape_task(self, source_id, max_documents):
    for doc in documents:
        # Check if task was revoked
        if self.request.id in celery_app.control.revoked():
            break

        process_document(doc)

@router.post("/stop-scraping")
async def stop_scraping(request: dict, ...):
    job_id = request.get("job_id")
    celery_app.control.revoke(job_id, terminate=True)
    return {"status": "cancelled"}
```

## Summary & Recommendations

### Current State

✅ **What's Working:**

- Documents ARE being saved to database
- Deduplication is excellent (3-level system)
- Site-specific scrapers are well-designed
- Metadata extraction is automated
- Frontend UI is complete

❌ **What's Broken:**

- Hard-coded 10-document limit in code
- Only scrapes first page (no pagination)
- Stop button doesn't actually stop scraping
- Not using the full orchestrator capabilities

### Immediate Actions

1. **Remove the 10-document limit** (Line 442 in enhanced_processor.py)
2. **Enable multi-page scraping** (add pagination loop)
3. **Use force_full_scan=True** for first-time scraping
4. **Implement real stop functionality** (use background tasks)

### Expected Results After Fixes

- Should scrape **1000+ documents** from MoE website
- Will take **30-60 minutes** for full scrape (with rate limiting)
- Stop button will actually work
- All documents will be saved to database with proper deduplication

### Testing Command

After fixes, test with:

```python
# Test scraping with high limits
result = enhanced_scrape_source(
    source_id=1,  # MoE source
    max_documents=1500,
    max_pages=100,
    pagination_enabled=True,
    incremental=False  # Full scan
)

print(f"Documents scraped: {result['documents_new']}")
print(f"Pages scraped: {result['pages_scraped']}")
```

Would you like me to create the fix files for you?
