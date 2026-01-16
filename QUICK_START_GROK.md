# Quick Start: Grok Integration

## ✅ Implementation Complete!

Grok has been integrated for metadata extraction with automatic quality control and fallback to Gemini.

## Setup (5 minutes)

### Step 1: Get Grok API Key

1. Visit https://x.ai/
2. Sign up / Login
3. Get your API key
4. Copy it

### Step 2: Update .env File

Open `.env` and add your Grok API key:

```env
# Find this section and update:
XAI_API_KEY=paste_your_actual_grok_key_here

# Make sure these are set:
METADATA_LLM_PROVIDER=grok
METADATA_FALLBACK_PROVIDER=gemini
DELETE_DOCS_WITHOUT_METADATA=true
```

### Step 3: Install Dependencies

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install new packages
pip install openai langchain-openai
```

### Step 4: Test It!

```bash
# Start backend
python -m uvicorn backend.main:app --reload
```

Then in another terminal:

```bash
# Run test
python test_fixed_scraping.py
```

## What to Expect

### Logs You'll See

```
✅ Good signs:
INFO - Metadata extractor initialized with primary LLM: grok
INFO - Fallback LLM configured: gemini
INFO - Calling primary LLM (grok) for metadata extraction...
INFO - Primary LLM (grok) extraction successful
INFO - Metadata quality acceptable

⚠️ Fallback (normal):
WARNING - Primary LLM (grok) returned incomplete metadata
INFO - Retrying with fallback LLM (gemini)...
INFO - Fallback LLM (gemini) extraction successful

❌ Deletion (quality control working):
WARNING - Metadata quality check failed: Missing or invalid title
WARNING - Deleting document 123 due to failed metadata extraction
```

### Statistics

After scraping, you'll see:

```
Documents discovered: 1000
Documents new: 920
Documents failed_metadata: 80  # Deleted due to poor quality
Success rate: 92%
```

## Configuration Options

### Maximum Quality (Recommended)

```env
METADATA_LLM_PROVIDER=grok
DELETE_DOCS_WITHOUT_METADATA=true
REQUIRE_TITLE=true
REQUIRE_SUMMARY=true
```

**Result:** Only high-quality documents

### Testing Mode

```env
METADATA_LLM_PROVIDER=grok
DELETE_DOCS_WITHOUT_METADATA=false  # Don't delete while testing
```

**Result:** Keep all documents, see what would be deleted

### Gemini Only (Fallback)

```env
METADATA_LLM_PROVIDER=gemini
```

**Result:** Use original Gemini, no Grok

## Verify It's Working

### Check 1: Logs Show Grok

```
INFO - Metadata extractor initialized with primary LLM: grok
```

### Check 2: Metadata Quality

```sql
-- All documents should have title and summary
SELECT COUNT(*) FROM document_metadata
WHERE title IS NOT NULL AND summary IS NOT NULL;
```

### Check 3: Deletion Stats

```
documents_failed_metadata: 50-100  # Some deletions = quality control working
```

## Troubleshooting

### "XAI_API_KEY not found"

**Fix:** Add your key to `.env`:

```env
XAI_API_KEY=your_actual_key_here
```

### All documents being deleted

**Fix:** Temporarily disable deletion:

```env
DELETE_DOCS_WITHOUT_METADATA=false
```

Then check logs to see why metadata extraction is failing.

### Grok not being used

**Fix:** Check `.env`:

```env
METADATA_LLM_PROVIDER=grok  # Make sure this is set
```

## Benefits

✅ **Better Rate Limits** - Grok has more generous limits  
✅ **Cost Effective** - Lower/free tier for bulk scraping  
✅ **Quality Control** - Only keeps documents with good metadata  
✅ **Automatic Fallback** - Uses Gemini if Grok fails  
✅ **Better RAG** - Higher quality metadata = better search

## Ready to Test!

```bash
# 1. Add Grok API key to .env
# 2. Install dependencies: pip install openai langchain-openai
# 3. Start backend: python -m uvicorn backend.main:app --reload
# 4. Run test: python test_fixed_scraping.py
```

Good luck! 🚀
