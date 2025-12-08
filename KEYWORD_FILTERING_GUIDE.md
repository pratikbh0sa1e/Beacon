# Keyword-Filtered Web Scraping Guide

## Overview

The keyword filtering feature allows you to filter documents **during** the web scraping process, not after. This significantly improves efficiency by:

- **Reducing bandwidth usage** - Only downloading relevant documents
- **Decreasing processing time** - Fewer documents through OCR/metadata pipeline
- **Lowering storage requirements** - Only storing relevant documents
- **Providing better user experience** - Faster results with clearer filtering feedback

## Features

### ✅ Core Functionality

1. **Keyword-Based Filtering**
   - Filter documents by keywords during scraping
   - Case-insensitive substring matching
   - Multiple keywords support
   - Special characters handled safely

2. **Filtering Statistics**
   - Documents discovered (total found)
   - Documents matched (passed filter)
   - Documents skipped (filtered out)
   - Match rate percentage

3. **Matched Keywords Tracking**
   - Each document records which keywords matched
   - Displayed in UI with badges
   - Stored in provenance metadata
   - Added to document tags for searchability

4. **Source Configuration**
   - Save keywords with web sources
   - Ad-hoc keywords override source keywords
   - Edit keywords for existing sources

5. **Backward Compatibility**
   - No keywords = no filtering (all documents scraped)
   - Existing functionality unchanged

## Usage

### Backend API

#### 1. Scrape with Keywords

```python
POST /api/web-scraping/scrape
{
  "url": "https://www.ugc.gov.in/",
  "keywords": ["policy", "circular", "notification"],
  "max_documents": 50
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Scraping completed: 16 documents found (filtered from 62 total)",
  "filtering_stats": {
    "keywords_used": ["policy", "circular", "notification"],
    "documents_discovered": 62,
    "documents_matched": 16,
    "documents_skipped": 46,
    "match_rate_percent": 25.81
  },
  "result": {
    "documents": [...]
  }
}
```

#### 2. Create Source with Keywords

```python
POST /api/web-scraping/sources
{
  "name": "UGC Official Website",
  "url": "https://www.ugc.gov.in/",
  "keywords": ["policy", "circular", "notification"],
  "max_documents": 50
}
```

#### 3. Scrape from Source (Uses Configured Keywords)

```python
POST /api/web-scraping/scrape
{
  "source_id": 1
}
```

#### 4. Override Source Keywords

```python
POST /api/web-scraping/scrape
{
  "source_id": 1,
  "keywords": ["fee", "admission"]  # Overrides source keywords
}
```

### Frontend UI

#### 1. Add Source with Keywords

1. Click "Add Source" button
2. Fill in source details
3. Enter keywords (comma-separated): `policy, circular, notification, fee, admission`
4. Click "Add Source"

#### 2. View Filtering Statistics

The dashboard shows:
- **Filter Match Rate** card (appears when filtering is used)
- **Recent Scrapes** with filtering details
- **Scraped Documents** with matched keyword badges

#### 3. View Matched Keywords

Each scraped document displays:
- Green badges showing which keywords matched
- Example: `policy` `circular` badges

### Python Code Examples

#### Basic Filtering

```python
from Agent.web_scraping.keyword_filter import KeywordFilter

# Create filter
filter = KeywordFilter(["policy", "circular"])

# Check if text matches
if filter.matches("New Policy Document"):
    print("Document matches!")

# Get matched keywords
matched = filter.get_matched_keywords("Policy and Circular Document")
print(f"Matched: {matched}")  # ['policy', 'circular']
```

#### Scraping with Filtering

```python
from Agent.web_scraping.scraper import WebScraper

scraper = WebScraper()

# Scrape with keywords
docs = scraper.find_document_links(
    url="https://www.ugc.gov.in/",
    keywords=["policy", "circular"]
)

# Each document has matched_keywords
for doc in docs:
    print(f"{doc['text']}: {doc['matched_keywords']}")
```

#### Full Pipeline with Statistics

```python
from Agent.web_scraping.web_source_manager import WebSourceManager

manager = WebSourceManager()

result = manager.scrape_source(
    url="https://www.ugc.gov.in/",
    source_name="UGC",
    keywords=["policy", "circular"],
    max_documents=50
)

print(f"Discovered: {result['documents_discovered']}")
print(f"Matched: {result['documents_matched']}")
print(f"Skipped: {result['documents_skipped']}")
print(f"Match rate: {result['filter_match_rate']}%")
```

## Effective Keywords for Government Documents

### General Policy Documents
- `policy`
- `circular`
- `notification`
- `guideline`
- `directive`
- `order`
- `resolution`

### Education-Specific
- `admission`
- `fee`
- `scholarship`
- `curriculum`
- `examination`
- `accreditation`
- `affiliation`

### Administrative
- `appointment`
- `transfer`
- `promotion`
- `recruitment`
- `tender`
- `procurement`

### Financial
- `budget`
- `grant`
- `fund`
- `allocation`
- `expenditure`
- `audit`

## Best Practices

### 1. Keyword Selection

✅ **Do:**
- Use specific, relevant keywords
- Include common variations (e.g., "policy", "policies")
- Start with 3-5 keywords, adjust based on results
- Use lowercase (matching is case-insensitive)

❌ **Don't:**
- Use too many keywords (reduces effectiveness)
- Use very common words (e.g., "the", "and")
- Use special regex characters expecting regex behavior

### 2. Monitoring Effectiveness

- Check the **Filter Match Rate** in the dashboard
- Aim for 20-40% match rate (good balance)
- If match rate is too low (<10%), keywords may be too specific
- If match rate is too high (>80%), keywords may be too broad

### 3. Iterative Refinement

1. Start with broad keywords
2. Review matched documents
3. Refine keywords based on results
4. Monitor match rate and adjust

## Technical Details

### Architecture

```
User Request (with keywords) → WebSourceManager → 
WebScraper.find_document_links(keywords) → 
KeywordFilter.evaluate(link_text) → 
Only matching documents → Download → Process → Store
```

### Filtering Logic

1. **Discovery**: Scraper finds all document links on page
2. **Evaluation**: Each link text is checked against keywords
3. **Matching**: Case-insensitive substring matching
4. **Recording**: Matched keywords stored with document
5. **Statistics**: Track discovered, matched, skipped counts

### Data Storage

**Document Metadata:**
- `matched_keywords` field in document record
- Keywords added to `tags` with `keyword:` prefix
- Stored in provenance metadata

**Scraping Logs:**
- `keywords_used`: Keywords applied
- `documents_discovered`: Total found
- `documents_matched`: Passed filter
- `documents_skipped`: Filtered out

## Troubleshooting

### No Documents Found

**Problem:** Scraping returns 0 documents with keywords

**Solutions:**
1. Check if keywords are too specific
2. Try broader keywords
3. Verify the website has documents with those keywords
4. Test without keywords to see total available

### Too Many Documents

**Problem:** Filter match rate is 90%+

**Solutions:**
1. Use more specific keywords
2. Add additional filtering keywords
3. Reduce `max_documents` limit

### Keywords Not Working

**Problem:** Documents don't seem filtered

**Solutions:**
1. Verify keywords are being passed to API
2. Check API response for `filtering_stats`
3. Ensure keywords match document link text (not content)
4. Remember: filtering is based on link text, not document content

## API Reference

### Endpoints

#### POST /api/web-scraping/scrape
Scrape documents with optional keyword filtering

**Request:**
```json
{
  "source_id": 1,  // Optional: use existing source
  "url": "https://...",  // Optional: ad-hoc URL
  "keywords": ["policy", "circular"],  // Optional: filter keywords
  "max_documents": 50  // Optional: limit results
}
```

**Response:**
```json
{
  "status": "success",
  "message": "...",
  "filtering_stats": {
    "keywords_used": [...],
    "documents_discovered": 62,
    "documents_matched": 16,
    "documents_skipped": 46,
    "match_rate_percent": 25.81
  },
  "result": {...}
}
```

#### GET /api/web-scraping/stats
Get overall scraping statistics including filtering effectiveness

**Response:**
```json
{
  "total_sources": 5,
  "total_scrapes": 20,
  "total_documents_scraped": 150,
  "filtering_stats": {
    "scrapes_with_keywords": 12,
    "scrapes_without_keywords": 8,
    "total_documents_discovered": 500,
    "total_documents_matched": 150,
    "total_documents_skipped": 350,
    "average_match_rate_percent": 30.0
  }
}
```

## Examples

### Example 1: UGC Policy Documents

```python
# Scrape UGC for policy documents
result = manager.scrape_source(
    url="https://www.ugc.gov.in/",
    source_name="UGC Policies",
    keywords=["policy", "circular", "notification"],
    max_documents=30
)

# Result: 16 documents matched from 62 discovered (25.8% match rate)
```

### Example 2: AICTE Technical Documents

```python
# Scrape AICTE for technical guidelines
result = manager.scrape_source(
    url="https://www.aicte-india.org/",
    source_name="AICTE Guidelines",
    keywords=["guideline", "approval", "accreditation"],
    max_documents=50
)
```

### Example 3: Fee-Related Documents

```python
# Scrape for fee-related documents
result = manager.scrape_source(
    url="https://www.ugc.gov.in/",
    source_name="Fee Documents",
    keywords=["fee", "refund", "payment", "scholarship"],
    max_documents=20
)
```

## Performance Impact

### Efficiency Gains

**Without Filtering:**
- Discover 100 documents
- Download 100 documents (bandwidth intensive)
- Process 100 documents (time intensive)
- Store 100 documents (storage intensive)

**With Filtering (30% match rate):**
- Discover 100 documents
- Download 30 documents (70% bandwidth saved)
- Process 30 documents (70% time saved)
- Store 30 documents (70% storage saved)

### Benchmarks

Based on testing with UGC website:
- **Discovery time**: ~2-3 seconds (same with/without filtering)
- **Filtering overhead**: <100ms (negligible)
- **Download time saved**: ~70% (for 30% match rate)
- **Processing time saved**: ~70% (for 30% match rate)

## Future Enhancements

Potential improvements for future versions:

1. **Boolean Operators**: Support AND, OR, NOT in keywords
2. **Regex Support**: Allow regex patterns for advanced matching
3. **ML-Based Filtering**: Suggest keywords based on content
4. **Keyword Analytics**: Show which keywords are most effective
5. **Saved Keyword Sets**: Reuse keyword sets across sources
6. **Content-Based Filtering**: Filter based on document content, not just link text

## Support

For issues or questions:
1. Check this guide first
2. Review the API documentation
3. Test with the demo endpoints
4. Check the logs for detailed error messages

## Changelog

### Version 1.0.0 (Current)
- Initial implementation of keyword filtering
- Case-insensitive substring matching
- Filtering statistics tracking
- Matched keywords recording
- Source keyword configuration
- Ad-hoc keyword override
- Frontend UI integration
- Backward compatibility maintained
