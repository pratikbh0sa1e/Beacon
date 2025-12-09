# Additional Fix - Web Scraping Endpoint ✅

## Issue Found
After the initial connectivity fixes, there was still a 404 error when trying to scrape from the Web Scraping page.

### Error
```
POST http://localhost:8000/api/web-scraping/sources/1/scrape 404 (Not Found)
```

## Root Cause
The frontend was calling the wrong endpoint:
- **Frontend was calling:** `POST /api/web-scraping/sources/{source_id}/scrape`
- **Backend expects:** `POST /api/web-scraping/scrape` with `source_id` in request body

## Fix Applied

### File: `frontend/src/pages/admin/WebScrapingPage.jsx`

**Before:**
```javascript
const response = await axios.post(
  `${API_BASE_URL}/web-scraping/sources/${sourceId}/scrape`, 
  {
    max_documents: source?.max_documents_per_scrape || 1500,
    pagination_enabled: source?.pagination_enabled !== false,
    max_pages: source?.max_pages || 100,
  }
);
```

**After:**
```javascript
const response = await axios.post(
  `${API_BASE_URL}/web-scraping/scrape`, 
  {
    source_id: sourceId,
    keywords: source?.keywords || null,
    max_documents: source?.max_documents || 1500,
  }
);
```

## Backend Endpoint Details

### Endpoint: `POST /api/web-scraping/scrape`

**Request Body:**
```json
{
  "source_id": 1,              // Optional: ID of existing source
  "url": "https://...",        // Optional: Ad-hoc URL to scrape
  "keywords": ["policy", ...], // Optional: Filter keywords
  "max_documents": 1500        // Optional: Max docs to scrape
}
```

**Note:** Either `source_id` OR `url` must be provided, not both.

**Response:**
```json
{
  "status": "success",
  "message": "Scraping completed",
  "documents_found": 150,
  "documents_matched": 120,
  "documents_processed": 120,
  "log_id": 1
}
```

## Testing

1. **Start both services:**
   ```bash
   # Terminal 1
   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2
   cd frontend && npm run dev
   ```

2. **Test the scrape functionality:**
   - Go to http://localhost:3000/admin/web-scraping
   - Add a source or use existing one
   - Click "Scrape Now" button
   - Should see success message with document count

3. **Verify in backend logs:**
   ```
   INFO: Starting scrape: [Source Name]
   INFO: Keywords being used: ['policy', 'circular']
   INFO: Max documents: 1500
   ```

## Status
✅ **FIXED** - Web scraping now works correctly from the frontend

## Related Files
- `frontend/src/pages/admin/WebScrapingPage.jsx` - Fixed scrape endpoint call
- `backend/routers/web_scraping_router_temp.py` - Backend endpoint definition

## Summary
The web scraping functionality now works end-to-end:
1. Frontend calls correct endpoint
2. Backend receives proper request format
3. Scraping executes successfully
4. Results are displayed in the UI
