# How to Use the Fixed Pagination System

## Quick Start

The pagination system is now working correctly and will scrape up to 1500 documents from government websites.

## Option 1: Use the Frontend (Recommended)

1. **Start the backend server:**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm start
   ```

3. **Navigate to Web Scraping page:**
   - Log in as an admin user
   - Go to "Web Scraping" in the admin menu

4. **Scrape a source:**
   - Find the source you want to scrape (e.g., "Ministry of Education - Documents & Reports")
   - Click the "Scrape Now" button
   - The system will automatically use pagination settings from the source configuration

5. **Monitor progress:**
   - Check the scraping logs in real-time
   - View the number of documents found and processed

## Option 2: Use the API Directly

```bash
# Scrape with default settings (1500 docs, 100 pages)
curl -X POST "http://localhost:8000/api/web-scraping/sources/1/scrape" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# Scrape with custom settings
curl -X POST "http://localhost:8000/api/web-scraping/sources/1/scrape" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "max_documents": 500,
    "pagination_enabled": true,
    "max_pages": 50
  }'
```

## Option 3: Use Python Scripts

### Quick Test (No Database)
```bash
python test_pagination_fix.py
```

This will scrape the Ministry of Education website and show you how many documents are found.

### Full Integration Test (With Database)
```bash
python test_full_integration.py
```

This will:
- Create/use a source in the database
- Scrape with pagination
- Process and store documents
- Show full statistics

## Configuration Options

### Per-Source Settings

When creating or editing a source, you can configure:

- **Pagination Enabled:** Turn pagination on/off
- **Max Pages:** Maximum number of pages to scrape (default: 100)
- **Max Documents:** Maximum documents to collect (default: 1500)

### Global Settings

Edit `Agent/web_scraping/config.py`:

```python
class ScrapingConfig:
    MAX_DOCUMENTS_PER_SOURCE = 1500  # Change this to scrape more/fewer documents
    DEFAULT_MAX_PAGES = 100          # Default max pages
    PAGE_DELAY_SECONDS = 1.0         # Delay between page requests
```

## Understanding the Results

When scraping completes, you'll see:

- **Documents discovered:** Total documents found across all pages
- **Documents matched:** Documents that passed keyword filtering (if any)
- **Documents new:** New documents (not previously scraped)
- **Documents skipped:** Documents already in the database
- **Documents processed:** Documents successfully downloaded and stored
- **Documents failed:** Documents that failed to download/process

## Troubleshooting

### Only getting 30 documents?

Make sure you're using the **new API endpoint**:
- ✅ Correct: `/api/web-scraping/sources/{source_id}/scrape`
- ❌ Wrong: `/api/web-scraping/scrape`

### Pagination not working?

Check the source configuration:
```sql
SELECT id, name, pagination_enabled, max_pages, max_documents_per_scrape 
FROM web_scraping_sources 
WHERE url LIKE '%education.gov.in%';
```

Make sure `pagination_enabled = true`.

### Want to scrape more than 1500 documents?

Update the config:
```python
from Agent.web_scraping.config import ScrapingConfig
ScrapingConfig.set_max_documents(3000)  # Set to 3000 documents
```

Or pass it in the API request:
```json
{
  "max_documents": 3000,
  "pagination_enabled": true,
  "max_pages": 200
}
```

## Performance Tips

1. **Rate Limiting:** The system waits 1 second between page requests to be polite to the server
2. **Parallel Processing:** For multiple sources, use the "Scrape All" feature
3. **Incremental Scraping:** Enable incremental mode to skip already-scraped documents
4. **Document Limits:** Set reasonable limits to avoid overwhelming the system

## Example: Scraping 1000+ Documents

```python
from Agent.web_scraping.web_scraping_processor import WebScrapingProcessor
from backend.database import SessionLocal

db = SessionLocal()
processor = WebScrapingProcessor()

result = processor.scrape_and_process_source(
    source_id=1,
    db_session=db,
    max_documents=1500,      # Scrape up to 1500 documents
    pagination_enabled=True,  # Use pagination
    max_pages=100            # Check up to 100 pages
)

print(f"Processed {result['documents_processed']} documents")
db.close()
```

## Next Steps

1. Test the pagination with a small limit first (e.g., 50 documents)
2. Once confirmed working, increase to full limit (1500 documents)
3. Set up scheduled scraping for daily updates
4. Monitor scraping logs for any issues

## Support

If you encounter issues:
1. Check the scraping logs in the database or frontend
2. Review the backend logs for detailed error messages
3. Verify the source URL is accessible
4. Ensure pagination is enabled in the source configuration
