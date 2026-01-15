# Quick Fix: Remove Web Scraping Limits

## Problem Found

Your web scraping is limited to **10 documents per scrape** due to a hard-coded testing limit in the code.

**Location:** `Agent/web_scraping/enhanced_processor.py` Line 442

## The Fix

### Step 1: Remove the 10-Document Limit

**File:** `Agent/web_scraping/enhanced_processor.py`

**Find this line (around line 442):**

```python
for doc_info in documents[:min(max_documents, 10)]:  # Limit to 10 for testing
```

**Replace with:**

```python
for doc_info in documents[:max_documents]:  # Use full max_documents limit
```

### Step 2: Add Pagination Support

**Add this code after line 445 (after the document discovery):**

```python
# Get pagination links and scrape additional pages
if pagination_enabled and len(documents) < max_documents:
    pagination_links = scraper.get_pagination_links(page_result['soup'], source.url)

    pages_scraped = 1
    for page_url in pagination_links:
        if pages_scraped >= max_pages:
            break

        if stats["documents_discovered"] >= max_documents:
            break

        try:
            logger.info(f"Scraping additional page {pages_scraped + 1}: {page_url}")

            page_result = scraper.scrape_page(page_url)
            if page_result['status'] != 'success':
                continue

            more_documents = scraper.get_document_links(page_result['soup'], page_url)
            documents.extend(more_documents)
            stats["documents_discovered"] += len(more_documents)
            stats["pages_scraped"] += 1
            pages_scraped += 1

            logger.info(f"Found {len(more_documents)} more documents on page {pages_scraped}")

            # Rate limiting between pages
            time.sleep(1)

        except Exception as e:
            logger.error(f"Error scraping page {page_url}: {e}")
            continue
```

### Step 3: Add Progress Logging

**Add this inside the document processing loop (around line 460):**

```python
# Add progress logging every 50 documents
if processed_count > 0 and processed_count % 50 == 0:
    logger.info(f"Progress: {processed_count}/{min(len(documents), max_documents)} documents processed")
    logger.info(f"Stats so far: {stats['documents_new']} new, {stats['documents_unchanged']} unchanged")
```

### Step 4: Adjust Rate Limiting

**Find this line (around line 540):**

```python
time.sleep(0.5)
```

**Replace with:**

```python
time.sleep(0.2)  # Faster rate limiting for large scrapes
```

## Complete Fixed Code Section

Here's the complete fixed section for `enhanced_processor.py`:

```python
# Around line 420-550
try:
    logger.info(f"Scraping page: {source.url}")

    # Get page content using site-specific scraper
    page_result = scraper.scrape_page(source.url)

    if page_result['status'] != 'success':
        raise Exception(f"Failed to scrape page: {page_result.get('error')}")

    stats["pages_scraped"] = 1

    # Extract document links
    documents = scraper.get_document_links(page_result['soup'], source.url)
    stats["documents_discovered"] = len(documents)

    logger.info(f"Found {len(documents)} document links on first page")

    # ✅ NEW: Add pagination support
    if pagination_enabled and len(documents) < max_documents:
        pagination_links = scraper.get_pagination_links(page_result['soup'], source.url)

        pages_scraped = 1
        for page_url in pagination_links:
            if pages_scraped >= max_pages:
                break

            if stats["documents_discovered"] >= max_documents:
                break

            try:
                logger.info(f"Scraping additional page {pages_scraped + 1}: {page_url}")

                page_result = scraper.scrape_page(page_url)
                if page_result['status'] != 'success':
                    continue

                more_documents = scraper.get_document_links(page_result['soup'], page_url)
                documents.extend(more_documents)
                stats["documents_discovered"] += len(more_documents)
                stats["pages_scraped"] += 1
                pages_scraped += 1

                logger.info(f"Found {len(more_documents)} more documents on page {pages_scraped}")

                # Rate limiting between pages
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error scraping page {page_url}: {e}")
                continue

    logger.info(f"Total documents discovered across {stats['pages_scraped']} pages: {stats['documents_discovered']}")

    # ✅ FIXED: Process all documents up to max_documents (removed 10-doc limit)
    processed_count = 0
    for doc_info in documents[:max_documents]:  # ✅ No more hard-coded limit!
        if processed_count >= max_documents:
            break

        try:
            # ✅ NEW: Progress logging
            if processed_count > 0 and processed_count % 50 == 0:
                logger.info(f"Progress: {processed_count}/{min(len(documents), max_documents)} documents processed")
                logger.info(f"Stats: {stats['documents_new']} new, {stats['documents_unchanged']} unchanged")

            # Filter by keywords if provided
            if keywords:
                title_lower = doc_info.get('title', '').lower()
                if not any(keyword.lower() in title_lower for keyword in keywords):
                    continue

            # Check if document already exists in database
            existing_doc = db.query(Document).filter(
                Document.source_url == doc_info['url']
            ).first()

            if existing_doc:
                stats["documents_unchanged"] += 1
                logger.debug(f"Document already exists: {doc_info['title']}")
                continue

            # ... rest of document processing code ...

            stats["documents_new"] += 1
            processed_count += 1

            logger.info(f"Successfully processed document {document.id}: {doc_info['title']}")

            # ✅ FIXED: Faster rate limiting
            time.sleep(0.2)  # Was 0.5, now 0.2 for faster scraping

        except Exception as e:
            logger.error(f"Error processing document {doc_info.get('url', 'unknown')}: {str(e)}")
            stats["errors"].append(f"Document processing error: {str(e)}")

    stats["documents_processed"] = processed_count
```

## Testing the Fix

### Test with Small Limit First

```bash
# In Python console or test script
from Agent.web_scraping.enhanced_processor import enhanced_scrape_source

# Test with 50 documents first
result = enhanced_scrape_source(
    source_id=1,  # Your MoE source ID
    max_documents=50,
    max_pages=5,
    pagination_enabled=True,
    incremental=False
)

print(f"Documents discovered: {result['documents_discovered']}")
print(f"Documents new: {result['documents_new']}")
print(f"Pages scraped: {result['pages_scraped']}")
```

### Then Test with Full Limit

```bash
# Full scrape for 1000+ documents
result = enhanced_scrape_source(
    source_id=1,
    max_documents=1500,
    max_pages=100,
    pagination_enabled=True,
    incremental=False
)

print(f"Documents discovered: {result['documents_discovered']}")
print(f"Documents new: {result['documents_new']}")
print(f"Pages scraped: {result['pages_scraped']}")
print(f"Execution time: {result['execution_time']:.2f}s")
```

## Expected Results

After applying these fixes:

- ✅ Should discover **1000+ documents** from MoE website
- ✅ Will scrape **multiple pages** (up to 100 pages)
- ✅ Will process **up to 1500 documents** per scrape
- ✅ Will take **30-60 minutes** for full scrape (with rate limiting)
- ✅ All documents will be saved to database
- ✅ Deduplication will prevent duplicates

## Monitoring Progress

Watch the logs to see progress:

```bash
# In your terminal where backend is running
tail -f Agent/agent_logs/pipeline.log

# You should see:
# "Found 50 document links on first page"
# "Scraping additional page 2: ..."
# "Found 45 more documents on page 2"
# "Progress: 50/1500 documents processed"
# "Progress: 100/1500 documents processed"
# etc.
```

## Troubleshooting

### If scraping is too slow:

- Reduce `time.sleep(0.2)` to `time.sleep(0.1)`
- Increase timeout: `response = self.session.get(doc_info['url'], timeout=60)`

### If you hit rate limits:

- Increase `time.sleep(0.2)` to `time.sleep(0.5)` or `time.sleep(1)`
- Add random delays: `time.sleep(random.uniform(0.5, 1.5))`

### If memory issues:

- Process in batches: `for doc_info in documents[i:i+100]:`
- Commit to database more frequently
- Clear processed documents from memory

## Next Steps

1. Apply the fixes above
2. Test with small limit (50 docs)
3. If successful, run full scrape (1500 docs)
4. Monitor database to confirm documents are being saved
5. Check document count: `SELECT COUNT(*) FROM documents WHERE source_url IS NOT NULL;`

Would you like me to create a script that applies these fixes automatically?
