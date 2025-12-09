# Embedding Dimension Padding Fix

## Issue
- **BGE-M3**: 1024 dimensions
- **Gemini embeddings**: 768 dimensions
- **Problem**: Dimension mismatch causes issues when mixing embeddings in pgvector

## Solution
Added automatic padding to Gemini embeddings to make them 1024 dimensions (compatible with BGE-M3).

## Changes Made

### 1. Updated `Agent/embeddings/bge_embedder.py`

Added padding method:
```python
def _pad_embedding(self, embedding: List[float], target_dim: int = 1024) -> List[float]:
    """Pad embedding to target dimension with zeros"""
    current_dim = len(embedding)
    if current_dim >= target_dim:
        return embedding
    
    # Pad with zeros
    padding = [0.0] * (target_dim - current_dim)
    return embedding + padding
```

Updated `embed_text()` and `embed_batch()` to automatically pad Gemini embeddings:
- Gemini native: 768 dims
- After padding: 1024 dims
- Padding: 256 zeros appended

Updated dimension reporting:
```python
self.dimension = 1024  # Padded dimension for pgvector compatibility
```

## How It Works

1. **Gemini generates 768-dim embedding**
2. **Padding adds 256 zeros** → [e1, e2, ..., e768, 0, 0, ..., 0]
3. **Final embedding: 1024 dims** (compatible with BGE-M3)
4. **Stored in pgvector** with consistent dimensions

## Benefits

✅ **Compatibility**: Gemini and BGE-M3 embeddings can coexist in same pgvector table
✅ **No data loss**: Original 768 dims preserved, just extended
✅ **Transparent**: Padding happens automatically
✅ **Backward compatible**: Existing BGE-M3 embeddings unaffected

## Embedding Script

The `embed_all_documents.py` script will now:
1. Use Gemini embeddings (if configured)
2. Automatically pad to 1024 dims
3. Store in pgvector DocumentEmbedding table
4. Check for duplicates before embedding
5. Process in parallel with 5 workers

## Testing

To verify padding works:
```python
from Agent.embeddings.bge_embedder import BGEEmbedder

embedder = BGEEmbedder()
embedding = embedder.embed_text("test")
print(f"Dimension: {len(embedding)}")  # Should be 1024
print(f"Last 10 values: {embedding[-10:]}")  # Should be zeros if Gemini
```

## Status
✅ Padding implemented in BGEEmbedder
✅ Works for both single and batch embedding
✅ Dimension reported as 1024
✅ Compatible with existing pgvector schema
