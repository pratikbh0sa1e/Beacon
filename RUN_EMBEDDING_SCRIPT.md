# Run Embedding Script - Complete Guide

## 🎯 What This Does

Embeds ALL unembed documents in your database using **Google Gemini multilingual embeddings** with:
- ✅ **5 parallel workers** for speed
- ✅ **Automatic padding** (768 → 1024 dims for BGE-M3 compatibility)
- ✅ **Duplicate detection** (skips already embedded docs)
- ✅ **Stores in pgvector** (document_embeddings table)
- ✅ **Progress tracking** and comprehensive logging

## 📋 Prerequisites

### 1. Environment Setup
Ensure `.env` file contains:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 2. Database
- PostgreSQL with pgvector extension
- Documents with `metadata_status='ready'`

### 3. Configuration
The script is already configured to use Gemini:
- `Agent/embeddings/embedding_config.py` → `ACTIVE_MODEL = "gemini-embedding"`
- Embeddings will be padded from 768 to 1024 dimensions automatically

## 🚀 Running the Script

### Step 1: Verify Configuration
```bash
# Check active model
python -c "from Agent.embeddings.embedding_config import ACTIVE_MODEL; print(f'Active: {ACTIVE_MODEL}')"
```

Should output: `Active: gemini-embedding`

### Step 2: Run the Script
```bash
python embed_all_documents.py
```

### Step 3: Monitor Progress
The script will show:
```
================================================================================
🚀 PARALLEL DOCUMENT EMBEDDING SCRIPT
🌐 Using Google Gemini Multilingual Embeddings
================================================================================
Workers: 5
Embedding dimension: 1024 (768 native + 256 padding)
Log file: embed_all_documents.log
================================================================================
📋 EMBEDDING CONFIGURATION
================================================================================

Active Embedding Model: gemini-embedding
Model Name: models/embedding-001
Dimension: 1024
Languages: 100+ languages
Description: Google Gemini embeddings via API (auto-padded to 1024 dims)
Use Case: Cloud-based embeddings, no local GPU needed, multilingual
Engine: gemini
Requires API Key: GOOGLE_API_KEY

================================================================================
🚀 Starting parallel embedding with 5 workers
================================================================================
📊 Total documents to process: 150
================================================================================
🔄 Embedding document 1: policy_document.pdf
✅ Successfully embedded document 1: 45 chunks
🔄 Embedding document 2: guideline.pdf
✅ Successfully embedded document 2: 38 chunks
⚠️  Document 5 already has embeddings - SKIPPING (duplicate)
📈 Progress: 10/150 (6.7%) - ✅ 8 | ⚠️ 2 duplicates | ❌ 0 failed
...
```

## 📊 What Happens

### For Each Document:

1. **Duplicate Check**
   - Queries `document_embeddings` table
   - Skips if embeddings exist

2. **Text Chunking**
   - Splits document into semantic chunks
   - Adaptive chunking based on content

3. **Embedding Generation**
   - Calls Gemini API for each chunk
   - Native: 768 dimensions
   - Padded: 1024 dimensions (256 zeros added)

4. **Storage in pgvector**
   - Stores in `document_embeddings` table
   - Includes metadata (chunk_index, filename, etc.)
   - Updates `document_metadata.embedding_status = 'embedded'`

### Parallel Processing:
- 5 workers process documents simultaneously
- ~3-5 seconds per document
- Automatic rate limiting for Gemini API

## 📈 Expected Output

### During Processing:
```
📈 Progress: 50/150 (33.3%) - ✅ 45 | ⚠️ 3 duplicates | ❌ 2 failed
📈 Progress: 100/150 (66.7%) - ✅ 92 | ⚠️ 5 duplicates | ❌ 3 failed
📈 Progress: 150/150 (100.0%) - ✅ 140 | ⚠️ 8 duplicates | ❌ 2 failed
```

### Final Statistics:
```
================================================================================
🎉 EMBEDDING COMPLETE!
================================================================================
📊 Final Statistics:
   Total documents: 150
   ✅ Successfully embedded: 140
   ⚠️  Duplicates skipped: 8
   ⏭️  Other skipped: 0
   ❌ Failed: 2
   ⏱️  Duration: 450.23 seconds (7.50 minutes)
   ⚡ Average time per document: 3.22 seconds
================================================================================
🔍 Verifying embeddings in database...
   Total embeddings in database: 6300
   Recent embedding dimensions: [1024, 1024, 1024, 1024, 1024]
   ✅ All embeddings have correct dimension (1024)
================================================================================
```

## 📝 Logs

Two types of logs are created:

1. **Console Output**: Real-time progress with emojis
2. **File Log**: `embed_all_documents.log` - Detailed log for debugging

## ✅ Verification

After completion, verify in database:

```sql
-- Check total embeddings
SELECT COUNT(*) FROM document_embeddings;

-- Check embeddings per document
SELECT document_id, COUNT(*) as num_chunks
FROM document_embeddings
GROUP BY document_id
ORDER BY document_id;

-- Verify dimensions (should all be 1024)
SELECT DISTINCT array_length(embedding, 1) as dimension
FROM document_embeddings;

-- Check recent embeddings
SELECT document_id, chunk_index, array_length(embedding, 1) as dim
FROM document_embeddings
ORDER BY id DESC
LIMIT 10;
```

## 🔧 Troubleshooting

### Error: "GOOGLE_API_KEY not found"
**Solution**: Add to `.env` file:
```bash
GOOGLE_API_KEY=your_api_key_here
```

### Error: "Active model is not gemini-embedding"
**Solution**: Edit `Agent/embeddings/embedding_config.py`:
```python
ACTIVE_MODEL = "gemini-embedding"
```

### Error: "No text available for embedding"
**Cause**: Document has no `extracted_text`
**Solution**: Check text extraction logs, may need to re-extract

### Slow Performance
**Cause**: Gemini API rate limits
**Solution**: 
- Reduce `NUM_WORKERS` in script (line 28)
- Add delays between requests

### Dimension Mismatch
**Should not occur** - padding is automatic
**If it does**: Check `Agent/embeddings/bge_embedder.py` padding logic

## 🔄 Re-running

Safe to re-run multiple times:
- ✅ Duplicate detection prevents re-embedding
- ✅ Only processes unembed documents
- ✅ No data corruption risk
- ✅ Can resume after interruption (Ctrl+C)

## 📊 Performance Estimates

| Documents | Estimated Time | Workers |
|-----------|---------------|---------|
| 50        | 2-3 minutes   | 5       |
| 150       | 7-10 minutes  | 5       |
| 500       | 25-35 minutes | 5       |
| 1000      | 50-70 minutes | 5       |

## 🎯 After Embedding

Once complete, your RAG system will:
1. ✅ Use Gemini embeddings for all queries
2. ✅ Search across all embedded documents
3. ✅ Return relevant chunks with citations
4. ✅ Support multilingual queries (100+ languages)

## 🧪 Test the RAG

After embedding, test with queries:
```python
# Test query
"provide me latest scholarship guideline document"

# Expected: Should find and return relevant documents
```

## 📞 Support

If issues persist:
1. Check `embed_all_documents.log` for detailed errors
2. Verify database connection
3. Check Gemini API quota/limits
4. Ensure pgvector extension is installed

## ✨ Summary

```bash
# Quick start:
python embed_all_documents.py

# That's it! The script handles everything:
# - Fetches unembed documents
# - Checks for duplicates
# - Embeds in parallel with Gemini
# - Pads to 1024 dimensions
# - Stores in pgvector
# - Verifies results
```

🎉 **Ready to embed all your documents!**
