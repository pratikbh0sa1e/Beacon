# Embed All Documents Guide

## Overview
Script to embed all unembed documents in parallel using Gemini embeddings with automatic padding to 1024 dimensions for BGE-M3 compatibility.

## Features

✅ **Parallel Processing**: 5 workers for faster embedding
✅ **Duplicate Detection**: Skips documents already embedded
✅ **Dimension Padding**: Gemini (768) → 1024 dims automatically
✅ **Progress Tracking**: Real-time statistics
✅ **Error Handling**: Continues even if some documents fail
✅ **Comprehensive Logging**: Both file and console output

## Prerequisites

1. **Environment Variables**:
   ```bash
   # .env file must contain:
   GOOGLE_API_KEY=your_gemini_api_key
   ```

2. **Database**: PostgreSQL with pgvector extension

3. **Python Dependencies**: Already installed in your environment

## Usage

### Basic Usage
```bash
python embed_all_documents.py
```

### What It Does

1. **Fetches unembed documents** from database
   - Where `embedding_status != 'embedded'`
   - Where `metadata_status == 'ready'`
   - Where `approval_status` in ['approved', 'pending']

2. **Checks for duplicates**
   - Queries `document_embeddings` table
   - Skips if embeddings already exist

3. **Embeds in parallel**
   - 5 workers process documents simultaneously
   - Gemini embeddings padded from 768 to 1024 dims
   - Stores in pgvector `document_embeddings` table

4. **Updates metadata**
   - Sets `embedding_status = 'embedded'`
   - Tracks progress and statistics

## Output Example

```
================================================================================
🚀 PARALLEL DOCUMENT EMBEDDING SCRIPT
================================================================================
Workers: 5
Log file: embed_all_documents.log
================================================================================
🚀 Starting parallel embedding with 5 workers
================================================================================
📊 Total documents to process: 150
================================================================================
🔄 Embedding document 1: policy_document.pdf
✅ Successfully embedded document 1: 45 chunks
🔄 Embedding document 2: guideline.pdf
⚠️  Document 5 already has embeddings - SKIPPING (duplicate)
📈 Progress: 10/150 (6.7%) - ✅ 8 | ⚠️ 2 duplicates | ❌ 0 failed
...
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
```

## Logs

Two types of logs:

1. **Console Output**: Real-time progress with emojis
2. **File Log**: `embed_all_documents.log` - Detailed log for debugging

## Error Handling

### If a document fails:
- Error is logged
- Script continues with other documents
- Failed documents counted in statistics

### If interrupted (Ctrl+C):
- Shows partial statistics
- Already embedded documents remain embedded
- Can re-run script to continue

## Verification

After running, verify embeddings:

```sql
-- Check total embeddings
SELECT COUNT(*) FROM document_embeddings;

-- Check embeddings per document
SELECT document_id, COUNT(*) as num_chunks
FROM document_embeddings
GROUP BY document_id
ORDER BY document_id;

-- Check embedding dimensions
SELECT document_id, array_length(embedding, 1) as dimension
FROM document_embeddings
LIMIT 5;
-- Should show 1024 for all
```

## Performance

- **5 workers**: ~3-5 seconds per document
- **150 documents**: ~7-10 minutes
- **1000 documents**: ~50-70 minutes

Adjust `NUM_WORKERS` in script if needed (line 28).

## Troubleshooting

### "GOOGLE_API_KEY not found"
- Add `GOOGLE_API_KEY` to `.env` file
- Restart script

### "Document not found"
- Document may have been deleted
- Check `documents` table

### "No text available for embedding"
- Document has no `extracted_text`
- Check if text extraction failed

### Dimension mismatch errors
- Should not occur - padding is automatic
- Check `bge_embedder.py` if issues persist

## Re-running

Safe to re-run multiple times:
- Duplicate detection prevents re-embedding
- Only processes unembed documents
- No data corruption risk

## Next Steps

After embedding:
1. Test search queries
2. Verify RAG responses
3. Check citation accuracy
4. Monitor embedding quality

## Status

✅ Script ready to use
✅ Padding implemented (768 → 1024)
✅ Duplicate detection working
✅ Parallel processing enabled
✅ Comprehensive logging
