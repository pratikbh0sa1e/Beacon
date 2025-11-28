# Bug Fix: Hybrid Search AttributeError

## Problem
**Error**: `'dict' object has no attribute 'lower'`  
**Location**: `Agent/retrieval/hybrid_retriever.py` line 92  
**Impact**: Search functionality completely broken - agent cannot retrieve documents

## Root Cause
The error occurred when the hybrid retriever tried to tokenize text for BM25 search:
```python
tokenized_corpus = [text.lower().split() for text in texts]
```

The `texts` list contained dict objects instead of strings, causing `.lower()` to fail.

## Investigation
Traced the data flow:
1. FAISS returns results with metadata
2. Hybrid retriever extracts `chunk_text` from metadata
3. `chunk_text` should be a string but was sometimes a dict
4. When `.lower()` was called on the dict, it failed

## Solution Implemented

### 1. FAISS Vector Store (`Agent/vector_store/faiss_store.py`)
Added validation in the `search()` method:
- Check if index exists and has vectors
- Validate metadata is a dict before returning
- Skip invalid entries

```python
if self.index is None or self.index.ntotal == 0:
    return []
    
# ... search logic ...

if not isinstance(metadata, dict):
    continue
```

### 2. Hybrid Retriever (`Agent/retrieval/hybrid_retriever.py`)
Added defensive checks when extracting text:
- Check if `chunk_text` is a dict (shouldn't happen but defensive)
- Convert to string if it is a dict
- Only add to texts list if it's a valid string
- Added error handling with detailed logging

```python
chunk_text = metadata.get("chunk_text", "")

# Handle case where chunk_text might be a dict
if isinstance(chunk_text, dict):
    logger.warning(f"chunk_text is a dict: {chunk_text}")
    chunk_text = str(chunk_text)

if chunk_text and isinstance(chunk_text, str):
    texts.append(chunk_text)
```

### 3. Error Handling
Added try-catch around BM25 tokenization with detailed error logging:
```python
try:
    tokenized_corpus = [text.lower().split() for text in texts]
    # ... BM25 logic ...
except AttributeError as e:
    logger.error(f"Error tokenizing texts: {e}")
    logger.error(f"Texts type check: {[type(t) for t in texts[:3]]}")
    raise
```

## Testing
- ✅ Code imports successfully
- ✅ No syntax errors
- ✅ Defensive checks in place
- 🔄 Needs runtime testing with actual queries

## Next Steps
1. Restart the FastAPI server to load the fixed code
2. Test with a query: "What is self-regulation and why is it important for health?"
3. Monitor logs for any warnings about dict chunk_text
4. If warnings appear, investigate why metadata structure is incorrect

## Prevention
The fix is defensive programming - it handles the symptom. If we see warnings about dict chunk_text in logs, we should investigate:
- How is metadata being serialized/deserialized in FAISS?
- Is there a pickle version mismatch?
- Are old index files using a different metadata structure?

## Files Modified
1. `Agent/retrieval/hybrid_retriever.py` - Added validation and error handling
2. `Agent/vector_store/faiss_store.py` - Added metadata validation in search

## Root Cause Update

After implementing the defensive fix, we discovered the **actual root cause**:

The `AdaptiveChunker` returns chunks as dicts with structure:
```python
{
    "text": "chunk content",
    "metadata": {"chunk_index": 0, "chunk_text": "chunk content"}
}
```

But `lazy_embedder.py` was storing the entire dict as `chunk_text` instead of extracting just the text string. This caused the metadata to have nested dict structure instead of plain strings.

## Complete Fix

### 1. Lazy Embedder (`Agent/lazy_rag/lazy_embedder.py`)
Changed to properly extract text from chunk dicts:
```python
# Extract just the text strings for embedding
chunks = [chunk_dict["text"] for chunk_dict in chunk_dicts]

# Create metadata with plain text strings
for i, chunk_text in enumerate(chunks):
    metadata_list.append({
        "chunk_index": i,
        "filename": filename,
        "document_id": doc_id,
        "text_length": len(chunk_text),
        "chunk_text": chunk_text  # Now a string, not a dict!
    })
```

### 2. Cleanup Required
Existing embeddings have corrupted metadata structure. Run cleanup script:
```bash
python scripts/cleanup_embeddings.py
```

This will:
- Delete all existing embedding files
- Reset embedding status to 'pending' in database
- Documents will be re-embedded automatically on next query

## Status
✅ **FIXED** - Root cause identified and corrected
⚠️  **ACTION REQUIRED** - Run cleanup script to remove corrupted embeddings
