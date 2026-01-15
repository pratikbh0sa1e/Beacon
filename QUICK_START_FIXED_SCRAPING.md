# Quick Start: Test Fixed Web Scraping

## ✅ Changes Applied Successfully!

All fixes have been implemented in `Agent/web_scraping/enhanced_processor.py`:

- ✅ Removed 10-document hard limit
- ✅ Added multi-page pagination support
- ✅ Added progress logging every 50 documents
- ✅ Added rate limiting (0.2s between documents, 1s between pages)

## Test Now!

### Option 1: Automated Test Script (Recommended)

```bash
# Run the comprehensive test script
python test_fixed_scraping.py
```

This will:

1. Show current database document counts
2. Run a small test (50 documents, 5 pages) - takes ~2-5 minutes
3. Ask if you want to run full scrape (1500 documents) - takes ~30-60 minutes
4. Show final results and statistics

### Option 2: Manual Test via Frontend

1. **Start Backend:**

   ```bash
   python -m uvicorn backend.main:app --reload
   ```

2. **Start Frontend:**

   ```bash
   cd frontend
   npm run dev
   ```

3. **Navigate to Web Scraping:**

   - Open browser: http://localhost:5173
   - Login as admin
   - Go to Web Scraping page

4. **Configure Source (if needed):**

   - Click "Add Source" or "Edit" existing MoE source
   - Set **Max Documents:** 1500
   - Set **Max Pages:** 100
   - Enable **Pagination:** ✅
   - Check **Force Full Scan:** ✅ (for first-time scraping)
   - Save

5. **Start Scraping:**
   - Click "Scrape Now" button
   - Watch the progress in the UI
   - Check backend logs for detailed progress

### Option 3: Python Console Test

```python
from Agent.web_scraping.enhanced_processor import enhanced_scrape_source

# Small test first
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
print(f"Time: {result['execution_time']:.2f}s")
```

## What to Expect

### Small Test (50 documents, 5 pages)

- **Time:** 2-5 minutes
- **Documents discovered:** 150-250 (across 5 pages)
- **Documents new:** 50 (limited by max_documents)
- **Pages scraped:** 5
- **Success rate:** 85-95%

### Full Scrape (1500 documents, 100 pages)

- **Time:** 30-60 minutes
- **Documents discovered:** 1000-2000+ (across many pages)
- **Documents new:** 1000-1500 (limited by max_documents)
- **Pages scraped:** 20-50 (depends on documents per page)
- **Success rate:** 85-95%

## Monitor Progress

### Backend Logs

Watch for these messages:

```
INFO - Starting enhanced scraping for Ministry of Education
INFO - Found 50 document links on first page
INFO - Scraping additional page 2: https://...
INFO - Found 45 more documents on page 2
INFO - Total documents discovered across 5 pages: 245
INFO - Progress: 50/1500 documents processed
INFO - Stats: 45 new, 5 unchanged
INFO - Progress: 100/1500 documents processed
INFO - Successfully processed document 123: Policy Document Title
INFO - Enhanced scraping completed in 1234.56s
```

### Database Check

```bash
# Check document count
python -c "
from backend.database import SessionLocal, Document
db = SessionLocal()
count = db.query(Document).filter(Document.source_url.isnot(None)).count()
print(f'Scraped documents: {count}')
db.close()
"
```

## Troubleshooting

### Issue: "Source not found"

**Solution:** Check your source_id. List sources:

```python
from backend.database import SessionLocal, WebScrapingSource
db = SessionLocal()
sources = db.query(WebScrapingSource).all()
for s in sources:
    print(f"ID: {s.id}, Name: {s.name}")
db.close()
```

### Issue: "No documents found"

**Possible causes:**

- Source URL is incorrect
- Website structure changed
- Network issues
- Keywords filtering too strict

**Solution:** Check the source URL is accessible and contains documents.

### Issue: Many "Document already exists" messages

**This is normal!** It means deduplication is working. Documents that were already scraped are being skipped.

### Issue: Scraping is slow

**This is expected!** Each document needs to be:

1. Downloaded (network time)
2. Text extracted (OCR if needed)
3. Uploaded to Supabase
4. Metadata extracted (AI processing)
5. Saved to database

**Average:** 0.5-2 seconds per document

### Issue: Some documents fail

**This is normal!** Some failures are expected:

- Broken links on source website
- Network timeouts
- Unsupported file formats
- Access denied (403)

**Acceptable failure rate:** 5-15%

## Success Indicators

✅ **Scraping is working if you see:**

- "Found X document links on first page" (X > 10)
- "Scraping additional page 2, 3, 4..." (pagination working)
- "Progress: 50/1500 documents processed" (no 10-doc limit)
- "Successfully processed document X" (documents being saved)
- Database count increasing

❌ **Something is wrong if you see:**

- Only 10 documents processed (limit still there)
- Only 1 page scraped (pagination not working)
- All documents failing to download
- No documents in database after scraping

## Verify Results

### Check Database

```sql
-- Total scraped documents
SELECT COUNT(*) FROM documents WHERE source_url IS NOT NULL;

-- Recent scrapes
SELECT filename, uploaded_at, source_url
FROM documents
WHERE source_url IS NOT NULL
ORDER BY uploaded_at DESC
LIMIT 20;

-- Documents by source
SELECT
    CASE
        WHEN source_url LIKE '%moe.gov.in%' THEN 'Ministry of Education'
        WHEN source_url LIKE '%ugc.gov.in%' THEN 'UGC'
        ELSE 'Other'
    END as source,
    COUNT(*) as count
FROM documents
WHERE source_url IS NOT NULL
GROUP BY source;
```

### Test RAG Queries

After scraping, test if documents are searchable:

1. Go to AI Chat page
2. Ask: "What are the latest education policies?"
3. Check if scraped documents appear in results
4. Verify citations include scraped documents

## Next Steps After Successful Test

1. ✅ **Verify 1000+ documents in database**
2. ✅ **Test RAG queries work with scraped docs**
3. ✅ **Set up scheduled scraping** (optional)
4. ✅ **Add more sources** (UGC, AICTE, etc.)
5. ✅ **Configure incremental scraping** (only get new docs)

## Need Help?

Check these files for more details:

- `WEB_SCRAPING_ANALYSIS_AND_ISSUES.md` - Full analysis
- `FIX_WEB_SCRAPING_LIMITS.md` - Detailed fix documentation
- `SCRAPING_FIX_IMPLEMENTATION_SUMMARY.md` - What was changed

## Ready to Test?

```bash
# Run this now!
python test_fixed_scraping.py
```

Good luck! 🚀
