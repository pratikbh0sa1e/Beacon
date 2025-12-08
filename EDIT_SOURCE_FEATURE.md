# Edit Source Feature - Implementation Summary

## ✅ Feature Added: Edit Web Scraping Sources

You can now edit existing web scraping sources to change keywords without having to delete and recreate them!

## What Was Implemented

### Backend (`backend/routers/web_scraping_router_temp.py`)

**New Endpoint:**
```python
PUT /api/web-scraping/sources/{source_id}
```

**Functionality:**
- Updates an existing source's details
- Allows changing keywords, URL, description, max_documents
- Returns the updated source

### Frontend (`frontend/src/pages/admin/WebScrapingPage.jsx`)

**New Features:**
1. **Edit Button** - Added next to each source (eye icon)
2. **Edit Dialog** - Full form to update source details
3. **Edit Handler** - Manages the update process

**UI Changes:**
- Each source now has 3 buttons: Play (scrape), Edit (eye icon), Delete (trash)
- Edit dialog pre-fills with current source data
- Keywords can be easily changed for different scraping needs

## How to Use

### 1. Edit an Existing Source

1. Go to Web Scraping page
2. Find your source (e.g., "MoE Website")
3. Click the **eye icon** button (Edit)
4. Update the keywords field
5. Click "Update Source"

### 2. Change Keywords for Different Scrapes

**Example: MoE Website**

**For Annual Reports:**
- Keywords: `report, annual`
- Result: Gets all annual reports

**For Policy Documents:**
- Keywords: `policy, circular, notification`
- Result: Gets policy-related documents

**For All Documents:**
- Keywords: (leave empty)
- Result: Gets all 14 documents

### 3. Keep Sources Permanent

Now you can:
- Add MoE Website once
- Change keywords whenever you need different documents
- No need to delete and recreate!

## Example Workflow

### Setup (One Time)
```
1. Add Source:
   - Name: "Ministry of Education"
   - URL: https://www.education.gov.in/documents_reports_hi
   - Keywords: report, annual
   - Max Documents: 50
```

### Daily Use
```
Day 1: Need annual reports
- Edit source → Keywords: "report, annual"
- Scrape → Get 11 annual reports

Day 2: Need all documents
- Edit source → Keywords: (empty)
- Scrape → Get all 14 documents

Day 3: Need NCERT reports
- Edit source → Keywords: "ncert"
- Scrape → Get NCERT reports only
```

## Benefits

✅ **No Repetition** - Add source once, use forever
✅ **Quick Changes** - Change keywords in seconds
✅ **Flexible** - Different keywords for different needs
✅ **Organized** - Keep your sources list clean
✅ **Efficient** - No need to remember URLs

## API Reference

### Update Source

**Request:**
```http
PUT /api/web-scraping/sources/1
Content-Type: application/json

{
  "name": "Ministry of Education",
  "url": "https://www.education.gov.in/documents_reports_hi",
  "description": "Official MoE documents",
  "keywords": ["report", "annual", "ncert"],
  "max_documents": 50,
  "scraping_enabled": true
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Ministry of Education",
  "url": "https://www.education.gov.in/documents_reports_hi",
  "description": "Official MoE documents",
  "keywords": ["report", "annual", "ncert"],
  "max_documents": 50,
  "scraping_enabled": true,
  "last_scraped_at": "2025-12-08T17:50:49",
  "last_scrape_status": "success",
  "total_documents_scraped": 11,
  "created_at": "2025-12-08T17:50:44"
}
```

## Tips

### Keyword Strategies

**Broad Keywords** (more results):
- `report`
- `document`
- `policy`

**Specific Keywords** (fewer, targeted results):
- `annual report 2023`
- `admission policy`
- `ncert circular`

**Multiple Keywords** (OR logic):
- `report, policy, circular` - Gets documents with ANY of these words

### Common Use Cases

**1. Regular Monitoring:**
- Keep source with broad keywords
- Scrape daily to get new documents

**2. Specific Research:**
- Edit keywords to narrow down
- Scrape once to get targeted documents

**3. Comprehensive Collection:**
- Remove all keywords
- Scrape to get everything

## Troubleshooting

### Issue: Edit button not showing

**Solution:** Refresh the page after the backend restarts

### Issue: Keywords not updating

**Solution:** 
1. Check that you clicked "Update Source"
2. Refresh the sources list
3. Check backend logs for confirmation

### Issue: Still getting zero documents

**Solution:**
1. Try broader keywords first (e.g., just "report")
2. Or remove keywords to see all available documents
3. Then refine based on what you see

## Next Steps

Now that you have edit functionality:

1. **Add your common sources once:**
   - Ministry of Education
   - UGC
   - AICTE
   - NCERT

2. **Edit keywords as needed:**
   - Change based on what you're looking for
   - No need to remember URLs

3. **Build your collection:**
   - Scrape regularly with different keywords
   - Build a comprehensive document database

---

**Status:** ✅ Complete and Ready to Use

**Features Added:**
- ✅ Edit source endpoint (backend)
- ✅ Edit button in UI
- ✅ Edit dialog with pre-filled data
- ✅ Update handler
- ✅ Keyword change support

**Test It:**
1. Restart backend if needed
2. Go to Web Scraping page
3. Click edit (eye icon) on any source
4. Change keywords
5. Update and scrape!
