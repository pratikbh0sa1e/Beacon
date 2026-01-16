# Critical Fixes Needed for Scraping

## Issue 1: ❌ Wrong Scraper Being Used (CRITICAL)

### Problem:

Line 494 in `enhanced_processor.py`:

```python
scraper = get_scraper_for_site("moe")  # Default to MoE for now
```

This means:

- UGC uses MoE scraper → Only finds 20 docs (should find 1000+)
- AICTE uses MoE scraper → Only finds 20 docs (should find 500+)
- All sources use wrong scraper!

### Solution:

Need to detect which scraper to use based on the source URL:

```python
# Detect scraper from source URL
if 'ugc.gov.in' in source.url:
    scraper = get_scraper_for_site("ugc")
elif 'aicte' in source.url:
    scraper = get_scraper_for_site("aicte")
elif 'education.gov.in' in source.url or 'moe' in source.url:
    scraper = get_scraper_for_site("moe")
else:
    scraper = get_scraper_for_site("generic")
```

## Issue 2: ❌ Invalid Filenames with Special Characters

### Problem:

Filenames with colons, quotes cause Supabase errors:

```
Invalid key: scraped_20260116_043928_UGC letter regarding: Submission of Report on Observance of "Sexual Harassment Prevention Week"..pdf
```

### Solution:

Sanitize filenames better:

```python
# Remove/replace invalid characters
safe_filename = doc_info['title'][:100]
safe_filename = safe_filename.replace(':', '-')
safe_filename = safe_filename.replace('"', '')
safe_filename = safe_filename.replace('/', '_')
safe_filename = safe_filename.replace('\\', '_')
safe_filename = safe_filename.replace('?', '')
safe_filename = safe_filename.replace('*', '')
```

## Issue 3: ⚠️ Documents Already Exist

### Why:

- You already scraped these sources before
- Deduplication is working correctly
- Documents ARE in Supabase bucket

### Not a Problem:

This is actually good - it means deduplication works!

## Impact

### Current State:

- ❌ UGC: Only 20 docs (using wrong scraper)
- ❌ AICTE: Only 20 docs (using wrong scraper)
- ❌ Some docs fail due to filename issues
- ✅ Deduplication working
- ✅ Documents stored in Supabase

### After Fixes:

- ✅ UGC: 1000+ docs (using UGC scraper)
- ✅ AICTE: 500+ docs (using AICTE scraper)
- ✅ No filename errors
- ✅ All documents properly stored

## Priority

1. **HIGH**: Fix scraper selection (Issue 1)
2. **MEDIUM**: Fix filename sanitization (Issue 2)
3. **LOW**: Issue 3 is not a problem

## Should I Fix These Now?

These are quick fixes (10 minutes total). Should I:

- **A)** Fix both issues now
- **B)** Just fix scraper selection (most critical)
- **C)** Leave as is

Recommendation: **A** - Fix both issues to get thousands more documents.
