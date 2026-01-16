# Scraping System Improvement Plan

## Current Issues

### 1. Session Storage Duplication

- Documents stored in local JSON files (unnecessary)
- Only metadata should be in session storage
- Actual documents should ONLY be in Supabase

### 2. Low Document Count

- Only getting ~300 documents from MoE
- Should be getting 1000+ documents
- Pagination not working properly
- Document link detection incomplete

### 3. Limited Sources

- Only MoE configured
- Need UGC, AICTE, CBSE, etc.

## Quick Fix Implementation

### Phase 1: Remove Session Storage for Documents (10 min)

**What**: Stop storing full documents in session storage
**Keep**: Only store scraping logs and source info
**Remove**: Document content from session storage

**Files to modify**:

- `Agent/web_scraping/session_storage.py` - Remove document storage
- `Agent/web_scraping/enhanced_processor.py` - Don't save to session storage

### Phase 2: Fix Pagination (10 min)

**What**: Improve pagination to actually scrape multiple pages
**Fix**: Better pagination link detection
**Add**: More robust page following

**Files to modify**:

- `Agent/web_scraping/site_scrapers/moe_scraper.py` - Better pagination
- `Agent/web_scraping/enhanced_processor.py` - Verify pagination works

### Phase 3: Improve Document Detection (5 min)

**What**: Find more document links on each page
**Fix**: Better CSS selectors and link patterns
**Add**: Support for more document types

**Files to modify**:

- `Agent/web_scraping/site_scrapers/moe_scraper.py` - Better selectors

### Phase 4: Add More Sources (5 min)

**What**: Add UGC, AICTE, CBSE sources
**How**: Use the API endpoint to create sources
**Result**: More documents from multiple sources

**Script**: `add_scraping_sources.py`

## Expected Results

### Before:

- ❌ ~300 documents from MoE
- ❌ Session storage bloat
- ❌ Only 1 source
- ❌ Slow scraping

### After:

- ✅ 1000+ documents from MoE
- ✅ Clean session storage (logs only)
- ✅ 8+ sources (MoE, UGC, AICTE, etc.)
- ✅ Faster scraping
- ✅ All documents in Supabase bucket

## Implementation Order

1. **First**: Remove session storage for documents
2. **Second**: Fix pagination
3. **Third**: Improve document detection
4. **Fourth**: Add more sources
5. **Test**: Scrape MoE again and verify 1000+ documents

## Timeline

- Total time: ~30 minutes
- Testing: ~10 minutes
- **Total**: 40 minutes

Ready to start?
