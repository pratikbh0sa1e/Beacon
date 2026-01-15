# Complete Web Scraping Guide 🌐

## Overview

The enhanced web scraping system automatically discovers, downloads, and processes government documents from official websites. All scraped documents are **fully downloadable and previewable** with AI-extracted metadata.

## 🚀 How to Use Web Scraping

### 1. Access Web Scraping Page

- Navigate to **Admin Panel** → **Web Scraping**
- Or go directly to: `http://localhost:3000/admin/web-scraping`

### 2. View Available Sources

The system comes with pre-configured sources:

| Source                           | URL                          | Documents Available | Status    |
| -------------------------------- | ---------------------------- | ------------------- | --------- |
| **Ministry of Education**        | https://www.education.gov.in | 1779+               | ✅ Active |
| **University Grants Commission** | https://www.ugc.gov.in       | 500+                | ✅ Active |
| **AICTE**                        | https://www.aicte.gov.in     | 300+                | ✅ Active |

### 3. Start Enhanced Scraping

#### Option A: Quick Scraping (Recommended)

1. Click **▶️ Scrape Now** button next to any source
2. System automatically uses enhanced features:
   - Site-specific scrapers (MoE, UGC, AICTE)
   - Sliding window re-scanning
   - Document deduplication
   - AI metadata extraction

#### Option B: Custom Scraping

1. Click **⚙️ Configure** next to a source
2. Set parameters:
   - **Keywords**: Filter documents (e.g., "policy", "circular", "guidelines")
   - **Max Documents**: Limit per scrape (default: 1500)
   - **Pagination**: Follow multiple pages (recommended: enabled)
   - **Max Pages**: Pages to scrape (default: 100)

### 4. Monitor Progress

- **Real-time Status**: See scraping progress in the UI
- **Stop Button**: Click **⏹️ Stop** to cancel ongoing scraping
- **Live Updates**: Document count updates automatically

### 5. View Results

After scraping completes, you'll see:

- **Documents Discovered**: Total found on website
- **Documents New**: Newly added to database
- **Documents Updated**: Existing documents with changes
- **Execution Time**: How long the scraping took

## 📋 Enhanced Features

### 🎯 Site-Specific Scrapers

Each government website has a specialized scraper:

#### Ministry of Education (MoE) Scraper

- **Targets**: PDF documents, circulars, policies
- **Selectors**: Optimized for education.gov.in structure
- **Document Types**: Reports, policies, guidelines, advertisements

#### UGC Scraper

- **Targets**: University circulars, regulations
- **Selectors**: Optimized for ugc.gov.in structure
- **Document Types**: Circulars, notifications, guidelines

#### AICTE Scraper

- **Targets**: Technical education documents
- **Selectors**: Optimized for aicte.gov.in structure
- **Document Types**: Approvals, regulations, handbooks

### 🔄 Sliding Window Re-scanning

- Always re-scans first 3 pages for latest documents
- Ensures new documents are never missed
- Configurable window size (default: 3 pages)

### 🔍 Document Identity Management

- **URL-first approach**: Primary identification by source URL
- **Content hashing**: Detects document changes
- **Deduplication**: Prevents duplicate documents
- **Version tracking**: Handles document updates

### 🧠 AI Metadata Extraction

Every scraped document gets:

- **Smart Title**: AI-extracted meaningful title
- **Department**: Auto-detected ministry/department
- **Document Type**: Policy, circular, report, etc.
- **Summary**: 2-3 sentence AI summary
- **Keywords**: Relevant search terms
- **Quality Score**: 85.7% average completeness

## 📥 Document Downloads & Previews

### ✅ All Scraped Documents Are Downloadable

- **Download Allowed**: Always set to `true` for scraped documents
- **File Storage**: Stored in Supabase cloud storage
- **Preview Available**: Full document preview in browser
- **Original Format**: Maintains original PDF/DOC format

### 🔍 How to Access Scraped Documents

#### Method 1: Through Document Explorer

1. Go to **Documents** → **Document Explorer**
2. Filter by **Source**: Look for documents with source URLs
3. Click any document to view details
4. Use **Download** button or **Preview** tab

#### Method 2: Through Web Scraping Page

1. Go to **Admin** → **Web Scraping**
2. Scroll to **Scraped Documents** section
3. Click **📄 View Details** on any document
4. Access download and preview options

#### Method 3: Through Search

1. Use global search with keywords
2. Scraped documents appear in results
3. Click to view full document details

### 📱 Document Detail Page Features

When viewing a scraped document:

```
📄 Document Title (AI-extracted)
🏢 Department: Ministry of Education
📅 Type: Policy/Circular/Report
⭐ Bookmark option
📥 Download button (always available)

Tabs:
├── 👁️ Preview (Full document viewer)
├── 💬 Discussion (Document chat)
└── 📝 My Notes (Personal notes)
```

## 🛠️ Adding New Sources

### 1. Click "Add Source" Button

Fill in the form:

```
Source Name: [e.g., "Department of Higher Education"]
URL: [e.g., "https://www.education.gov.in/higher-education"]
Description: [Optional description]
Keywords: [Comma-separated, e.g., "policy,circular,guidelines"]
Max Documents: [Default: 1500]
Pagination: [✓ Enabled (recommended)]
Max Pages: [Default: 100]
Scraper Type: [Choose: Generic, MoE, UGC, AICTE]
```

### 2. Advanced Configuration

- **Window Size**: How many pages to always re-scan (default: 3)
- **Force Full Scan**: Ignore incremental updates (use sparingly)
- **Schedule**: Set up automatic scraping (future feature)

## 📊 Monitoring & Analytics

### Real-time Statistics

The dashboard shows:

- **Total Documents**: All documents in system
- **Scraped Documents**: Documents from web scraping
- **Success Rate**: Percentage of successful scrapes
- **Filter Match Rate**: How well keywords work

### Scraping Logs

View detailed logs:

- **Recent Scrapes**: Last 10 scraping operations
- **Status**: Success/Failed with error details
- **Performance**: Documents found vs. processed
- **Keywords Used**: Which filters were applied

### Document Quality Metrics

Each scraped document shows:

- **Quality Score**: Metadata completeness (target: >80%)
- **Text Length**: Amount of extracted text
- **Metadata Status**: Processing status
- **AI Confidence**: How confident the AI is in extraction

## 🔧 Troubleshooting

### Common Issues & Solutions

#### 1. "No documents found"

**Cause**: Website structure changed or no matching documents
**Solution**:

- Try different keywords
- Check if website is accessible
- Use "Force Full Scan" option

#### 2. "Download failed"

**Cause**: Document URL is broken or access denied
**Solution**:

- Check source website manually
- Try scraping again later
- Contact website administrator

#### 3. "Metadata extraction failed"

**Cause**: Document text is unclear or corrupted
**Solution**:

- Document still saved with basic metadata
- Manual review may be needed
- Try re-scraping the document

#### 4. "Scraping stopped unexpectedly"

**Cause**: Network issues or website blocking
**Solution**:

- Check internet connection
- Wait and try again (websites may have rate limits)
- Use smaller batch sizes

### Performance Tips

#### For Large Scrapes (1000+ documents)

1. **Use Keywords**: Filter to relevant documents only
2. **Limit Pages**: Start with 10-20 pages, increase gradually
3. **Monitor Progress**: Use stop button if needed
4. **Schedule Off-Peak**: Run during low-traffic hours

#### For Regular Updates

1. **Enable Incremental**: Let system skip unchanged documents
2. **Use Sliding Window**: Ensures latest documents are caught
3. **Set Reasonable Limits**: 500-1000 documents per run

## 🔐 Security & Compliance

### Data Handling

- **Public Documents Only**: Only scrapes publicly available documents
- **Respect robots.txt**: Follows website scraping guidelines
- **Rate Limiting**: Built-in delays to avoid overwhelming servers
- **Audit Trail**: All scraping activities are logged

### Access Control

- **Admin Only**: Web scraping requires admin privileges
- **Institution Scoped**: Documents tagged with appropriate institution
- **Download Permissions**: All scraped documents are downloadable by default
- **Visibility**: Scraped documents are public by default

## 📈 Best Practices

### 1. Start Small

- Begin with 50-100 documents to test
- Verify quality before large scrapes
- Check document relevance

### 2. Use Appropriate Keywords

```
Good Keywords:
✅ "policy" - Finds policy documents
✅ "circular" - Finds official circulars
✅ "guidelines" - Finds guideline documents
✅ "2024" - Finds recent documents

Avoid:
❌ "the", "and", "of" - Too generic
❌ Very specific terms - May miss documents
```

### 3. Monitor Quality

- Check metadata completeness
- Verify document relevance
- Review AI-extracted summaries

### 4. Regular Maintenance

- Update source URLs if websites change
- Review and clean up old/irrelevant documents
- Monitor scraping success rates

## 🚀 Advanced Usage

### Bulk Document Analysis

After scraping documents:

1. Select multiple documents in the scraped documents list
2. Click **"🔍 Analyze Selected Documents"**
3. System will:
   - Download and process all selected documents
   - Extract key insights using AI
   - Generate comprehensive analysis
   - Redirect to AI Chat with results

### Integration with RAG System

Scraped documents automatically integrate with:

- **Search**: Searchable through main document search
- **AI Chat**: Available for AI-powered Q&A
- **Embeddings**: Vector embeddings for semantic search
- **Recommendations**: Used in document recommendation system

## 📞 Support

### Getting Help

1. **Check Logs**: Review scraping logs for error details
2. **Test Manually**: Visit source website to verify accessibility
3. **Contact Admin**: Reach out to system administrator
4. **Documentation**: Refer to this guide and technical docs

### Reporting Issues

When reporting problems, include:

- Source website URL
- Error messages from logs
- Steps to reproduce
- Expected vs. actual behavior

---

## 🎯 Quick Start Checklist

- [ ] Access Web Scraping page (`/admin/web-scraping`)
- [ ] Choose a pre-configured source (MoE, UGC, or AICTE)
- [ ] Click **"Scrape Now"** to start with default settings
- [ ] Monitor progress and wait for completion
- [ ] Check **"Scraped Documents"** section for results
- [ ] Click on any document to view details and download
- [ ] Verify document preview and metadata quality
- [ ] Use documents in search, AI chat, or analysis

**🎉 You're now ready to use the enhanced web scraping system!**
