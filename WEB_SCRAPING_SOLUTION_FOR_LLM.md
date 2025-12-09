# Web Scraping Solution - 1000+ Documents Implementation

## 🎯 Goal

Build a web scraping system that can automatically discover and ingest 1000+ policy documents from government websites with real-time updates and keyword filtering.

## 📊 Current Implementation

### What We Have
- ✅ Single page scraping (14-62 documents per source)
- ✅ Keyword filtering DURING scraping (not after)
- ✅ Manual scraping (user clicks button)
- ✅ Basic source management
- ✅ Provenance tracking (source, credibility, metadata)
- ✅ Full pipeline integration (OCR, metadata extraction, RAG)

### What We Need for 1000+ Documents
- ❌ Multi-page scraping (pagination support)
- ❌ Multiple sources aggregation (10-15 sources)
- ❌ Automatic/scheduled scraping
- ❌ Real-time updates
- ❌ 1000+ documents capacity

## 🏗️ Architecture

### Component Structure

```
WebScrapingPage.jsx (Frontend)
    ↓
web_scraping_router_temp.py (API Layer)
    ↓
WebSourceManager (Orchestration)
    ↓
WebScraper (Core Scraping) + KeywordFilter (Filtering)
    ↓
PDFDownloader (Document Download)
    ↓
ProvenanceTracker (Metadata)
    ↓
WebScrapingProcessor (Pipeline Integration)
    ↓
BEACON Agent Pipeline (OCR, Metadata, Storage, RAG)
```

### Data Flow

```
1. User adds source with keywords
2. Scraper finds document links on page
3. KeywordFilter evaluates each link
4. Only matching documents are downloaded
5. Documents processed through pipeline
6. Stored in database with provenance
7. Marked for lazy embedding (RAG)
```

## 🔑 Key Components

### 1. KeywordFilter (`Agent/web_scraping/keyword_filter.py`)

**Purpose**: Filter documents DURING scraping (not after)

**Key Methods**:
```python
class KeywordFilter:
    def __init__(self, keywords: Optional[List[str]]):
        # Initialize with keywords
        
    def evaluate(self, text: str) -> Dict:
        # Returns {matches: bool, matched_keywords: List[str]}
        # Case-insensitive substring matching
        
    def get_filter_stats(self, total, matched) -> Dict:
        # Returns filtering statistics
```

**Algorithm**:
1. Convert text to lowercase
2. For each keyword:
   - Convert keyword to lowercase
   - Check if keyword substring in text
   - If yes, add to matched list
3. Return matches=True if any keywords matched

**Benefits**:
- 70% reduction in downloads (based on 30% match rate)
- 70% reduction in processing time
- 70% reduction in storage

### 2. WebScraper (`Agent/web_scraping/scraper.py`)

**Purpose**: Core web scraping functionality

**Key Methods**:
```python
class WebScraper:
    def find_document_links(self, url, extensions, keywords) -> List[Dict]:
        # Main scraping method
        # Finds all document links on page
        # Applies keyword filtering
        # Returns list of matching documents
        
    def scrape_with_pagination(self, base_url, page_param, max_pages):
        # Scrape multiple pages automatically
        # Handles pagination
```

**Document Detection**:
- Looks for `<a>` tags with `href` attribute
- Checks if URL ends with: .pdf, .docx, .doc, .pptx, .xlsx, .xls
- Converts relative URLs to absolute

**Filtering Process**:
1. Find all links on page
2. Filter by file extension
3. For each document link:
   - Get link text
   - Evaluate against keyword filter
   - If matches: add to results with matched_keywords
   - If not: skip and increment filtered_out counter
4. Log statistics

### 3. WebSourceManager (`Agent/web_scraping/web_source_manager.py`)

**Purpose**: Orchestrates scraping operations

**Key Methods**:
```python
class WebSourceManager:
    def scrape_source(self, url, source_name, keywords, max_documents):
        # Main orchestration method
        # Calls WebScraper
        # Creates provenance records
        # Calculates statistics
        
    def scrape_and_download(self, url, source_name, keywords, max_documents):
        # Scrapes AND downloads documents
        
    def scrape_multiple_sources(self, sources: List[Dict]):
        # Scrapes multiple sources in sequence
```

**Statistics Calculation**:
```python
documents_discovered = len(all_found_documents)
documents_matched = len(filtered_documents)
documents_skipped = discovered - matched
filter_match_rate = (matched / discovered * 100) if discovered > 0 else 0
```

### 4. ProvenanceTracker (`Agent/web_scraping/provenance_tracker.py`)

**Purpose**: Tracks document source and credibility

**Credibility Scores**:
```python
education.gov.in: 10/10  # Ministry of Education
ugc.ac.in: 9/10          # UGC
aicte-india.org: 9/10    # AICTE
*.gov.in: 9/10           # Government domains
*.ac.in: 8/10            # Academic institutions
*.edu.in: 8/10           # Educational institutions
*.nic.in: 8/10           # National Informatics Centre
default: 5/10            # Unknown sources
```

**Provenance Record Structure**:
```python
{
    "source_url": "https://...",
    "source_page": "https://...",
    "source_domain": "ugc.gov.in",
    "source_type": "government",
    "document_title": "Policy Document",
    "scraped_at": "2025-12-08T17:50:49",
    "credibility_score": 9,
    "ingestion_method": "web_scraping",
    "verified": True,
    "metadata": {
        "matched_keywords": ["policy", "circular"]
    }
}
```

### 5. WebScrapingProcessor (`Agent/web_scraping/web_scraping_processor.py`)

**Purpose**: Integrates scraping with BEACON Agent pipeline

**Processing Pipeline**:
```
1. Extract Text
   - PDF: PyPDF2 or pdfplumber
   - DOCX: python-docx
   - Images: Tesseract OCR
   
2. Upload to Supabase
   - Uploads file to S3-compatible storage
   
3. Extract Metadata (AI)
   - Uses OpenAI API
   - Extracts: title, description, category, tags, language
   
4. Store in Database
   - Creates Document record
   - Creates DocumentMetadata record
   - Creates ScrapedDocument record (provenance)
   - Adds matched_keywords to tags (prefix: "keyword:")
   
5. Mark for Lazy Embedding
   - Sets embedding_status = 'pending'
   - Embedding happens on first query (lazy)
```

## 📡 API Endpoints

### Web Scraping (`/api/web-scraping`)

1. **Create Source**
```http
POST /sources
{
  "name": "UGC Official Website",
  "url": "https://www.ugc.gov.in/",
  "description": "University Grants Commission",
  "keywords": ["policy", "circular", "notification"],
  "max_documents": 50,
  "scraping_enabled": true
}
```

2. **Scrape Now**
```http
POST /scrape
{
  "source_id": 1
}

Response:
{
  "status": "success",
  "message": "Scraping completed: 16 documents found (filtered from 62 total)",
  "filtering_stats": {
    "keywords_used": ["policy", "circular"],
    "documents_discovered": 62,
    "documents_matched": 16,
    "documents_skipped": 46,
    "match_rate_percent": 25.81
  }
}
```

3. **Scrape and Download**
```http
POST /scrape-and-download
{
  "source_id": 1
}
```

4. **Scrape and Process (Full Pipeline)**
```http
POST /scrape-and-process
{
  "source_id": 1
}
```

5. **Get Statistics**
```http
GET /stats

Response:
{
  "total_sources": 5,
  "total_scrapes": 20,
  "total_documents_scraped": 150,
  "filtering_stats": {
    "total_documents_discovered": 500,
    "total_documents_matched": 150,
    "total_documents_skipped": 350,
    "average_match_rate_percent": 30.0
  }
}
```

## 🚀 Implementation Plan for 1000+ Documents

### Phase 1: Expand Document Discovery (Target: 1000+ documents)

**Goal**: Identify and add sources that collectively have 1000+ documents

**Recommended Sources**:
```
1. UGC (ugc.gov.in) - ~60 documents
2. AICTE (aicte-india.org) - ~50 documents
3. MoE Main (education.gov.in) - ~40 documents
4. NCERT (ncert.nic.in) - ~30 documents
5. NITI Aayog (niti.gov.in) - ~100 documents
6. State Education Departments (multiple) - ~500 documents
7. University websites (multiple) - ~300 documents
```

**Implementation**:
1. Add 10-15 government sources manually
2. Add archive/historical pages (100-500 documents each)
3. Add multiple sections from same site

**Expected Result**: 1000-1600 documents

### Phase 2: Add Pagination Support

**Goal**: Scrape multiple pages automatically

**Implementation**:
```python
def scrape_with_pagination(self, base_url, max_pages=10):
    all_documents = []
    current_page = 1
    
    while current_page <= max_pages:
        page_url = f"{base_url}?page={current_page}"
        docs = self.find_document_links(page_url, keywords)
        if not docs:
            break  # No more documents
        all_documents.extend(docs)
        current_page += 1
    
    return all_documents
```

**UI Enhancement**:
- Add "Enable Pagination" checkbox in source form
- Add "Max Pages" field (default: 10)

**Expected Result**: 2-5x multiplier (2000-5000 documents)

### Phase 3: Implement Scheduled Scraping

**Goal**: Automatic scraping without manual clicks

**Implementation**:
```python
from apscheduler.schedulers.background import BackgroundScheduler

class ScrapingScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.web_manager = WebSourceManager()
    
    def schedule_source(self, source_id, cron_expression):
        self.scheduler.add_job(
            func=self.scrape_source,
            trigger='cron',
            args=[source_id],
            **parse_cron(cron_expression)
        )
    
    def scrape_source(self, source_id):
        # Perform scraping
        # Log results
        # Send notifications if needed
```

**UI Enhancement**:
- Add scheduling options to source form
- Options: Manual, Daily, Weekly, Custom
- Time selection for scheduled scrapes

**Expected Result**: Automatic daily/weekly updates

### Phase 4: Add Incremental Scraping

**Goal**: Only scrape NEW documents (not already scraped)

**Implementation**:
```python
def scrape_incremental(self, url, keywords, last_scraped_at):
    # Get all documents
    documents = self.find_document_links(url, keywords)
    
    # Filter out already scraped (by URL or hash)
    new_documents = [
        doc for doc in documents 
        if not self.is_already_scraped(doc['url'])
    ]
    
    return new_documents
```

**Expected Result**: Faster scraping, no duplicates

## 📊 Performance Metrics

### Efficiency Gains (Based on 30% Match Rate)
- **Bandwidth**: 70% reduction
- **Processing Time**: 70% reduction
- **Storage**: 70% reduction
- **Filtering Overhead**: <100ms (negligible)

### Example Results
```
Without Filtering:
- Discovered: 62 documents
- Downloaded: 62 documents
- Processed: 62 documents

With Filtering (keywords: ["policy", "circular"]):
- Discovered: 62 documents
- Matched: 16 documents (25.8%)
- Skipped: 46 documents (74.2%)
- Downloaded: 16 documents (74% reduction)
- Processed: 16 documents (74% reduction)
```

## 🎯 Quick Start Options

### Option A: Manual Multi-Source (1-2 days)
1. Add 15 government sources manually
2. Set max_documents to 200 for each
3. Scrape all sources manually
4. **Result**: 1000+ documents immediately

### Option B: Automated System (4 weeks)
1. Implement all 4 phases
2. **Result**: Self-sustaining system with 5000+ documents

### Option C: Hybrid (1 week) ⭐ RECOMMENDED
1. Add 15 government sources (Phase 1)
2. Add basic pagination (Phase 2 - partial)
3. Add daily scheduler (Phase 3 - basic)
4. **Result**: 1000-2000+ documents with automatic daily updates

## 🔧 Implementation Code Examples

### 1. Keyword Filtering
```python
# In WebScraper.find_document_links()
keyword_filter = KeywordFilter(keywords)

for link in soup.find_all('a', href=True):
    if is_document(link):
        link_text = link.get_text()
        match_result = keyword_filter.evaluate(link_text)
        
        if match_result['matches']:
            documents.append({
                'url': link['href'],
                'matched_keywords': match_result['matched_keywords']
            })
```

### 2. Pagination
```python
def scrape_with_pagination(self, base_url, max_pages=10):
    all_documents = []
    
    for page_num in range(1, max_pages + 1):
        page_url = f"{base_url}?page={page_num}"
        documents = self.find_document_links(page_url)
        
        if not documents:
            break
        
        all_documents.extend(documents)
        time.sleep(1)  # Be polite
    
    return all_documents
```

### 3. Scheduled Scraping
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# Schedule daily scraping at 2 AM
scheduler.add_job(
    func=scrape_all_sources,
    trigger='cron',
    hour=2,
    minute=0
)

scheduler.start()
```

### 4. Incremental Scraping
```python
def scrape_incremental(self, url, keywords):
    documents = self.find_document_links(url, keywords)
    
    # Filter out already scraped
    new_documents = []
    for doc in documents:
        if not db.query(ScrapedDocument).filter_by(source_url=doc['url']).first():
            new_documents.append(doc)
    
    return new_documents
```

## 🎉 Success Criteria

### After Phase 1:
- ✅ 1000-1600 documents available
- ✅ 10-15 government sources added
- ✅ Manual scraping works for all sources

### After Phase 2:
- ✅ 2000-5000 documents (with pagination)
- ✅ Automatic multi-page scraping
- ✅ Configurable page limits

### After Phase 3:
- ✅ Automatic daily/weekly scraping
- ✅ Real-time updates
- ✅ No manual intervention needed

### After Phase 4:
- ✅ Incremental scraping (only new docs)
- ✅ No duplicates
- ✅ Faster scraping

## 📚 Reference Files

- `Agent/web_scraping/scraper.py` - Core scraping logic
- `Agent/web_scraping/keyword_filter.py` - Keyword filtering
- `Agent/web_scraping/web_source_manager.py` - Orchestration
- `Agent/web_scraping/provenance_tracker.py` - Source tracking
- `Agent/web_scraping/web_scraping_processor.py` - Pipeline integration
- `backend/routers/web_scraping_router_temp.py` - API endpoints
- `frontend/src/pages/admin/WebScrapingPage.jsx` - UI

## 🎯 Key Takeaways

1. **Keyword Filtering**: Filter DURING scraping (not after) - 70% efficiency gain
2. **Lazy RAG**: Embed on first query (not on upload) - instant uploads
3. **Provenance Tracking**: Know where documents came from and trust level
4. **Pagination**: Scrape multiple pages automatically - 2-5x more documents
5. **Scheduled Scraping**: Automatic daily/weekly updates - no manual work
6. **Incremental Scraping**: Only new documents - faster, no duplicates

---

**Status**: ✅ Core Implementation Complete  
**Next Steps**: Add pagination, scheduling, and incremental scraping for 1000+ documents  
**Version**: 2.0.0  
**Last Updated**: December 8, 2025

**Use this document along with `COMPLETE_SOLUTION_PROMPT.md` for full implementation details.**
