# Agent Module - Vector Embedding Pipeline

## Overview
This module handles document chunking, embedding generation, and vector storage for the Government Policy Intelligence Platform.

## Architecture

### 1. Chunking Strategies (`Agent/chunking/`)
- **AdaptiveChunker**: Automatically adjusts chunk size based on document length
  - Small docs (<5K chars): 500 chars, 50 overlap
  - Medium docs (<20K chars): 1000 chars, 100 overlap
  - Large docs (<50K chars): 1500 chars, 200 overlap
  - Very large docs: 2000 chars, 300 overlap
  
- **FixedChunker**: Fixed-size chunks (configurable)

**Switching Chunkers:**
```python
from Agent.chunking.fixed_chunker import FixedChunker
from Agent.vector_store.embedding_pipeline import EmbeddingPipeline

# Use fixed chunker instead
pipeline = EmbeddingPipeline(chunker=FixedChunker(chunk_size=800, overlap=100))
```

### 2. Embeddings (`Agent/embeddings/`)
- **GeminiEmbedder**: Uses Google's `models/embedding-001`
- Generates 768-dimensional embeddings
- Batch processing support

### 3. Vector Store (`Agent/vector_store/`)
- **FAISSVectorStore**: Local FAISS index
  - Stores embeddings with metadata
  - Duplicate detection via document hashing
  - Persistent storage (saves to disk)
  
- **EmbeddingPipeline**: Orchestrates the full process
  - Chunks → Embeds → Stores
  - Handles duplicate detection
  - Returns processing status

## Features

### Duplicate Detection
Documents are hashed (SHA256) based on filename + content. If the same document is uploaded again, embeddings are reused.

### Metadata Storage
Each chunk stores:
- `document_id`: Database ID
- `filename`: Original filename
- `file_type`: pdf/docx/pptx/jpeg/png
- `source_department`: Department/ministry
- `chunk_index`: Position in document
- `chunk_size`: Size of this chunk
- `total_doc_size`: Total document size

### Background Processing
Embeddings are generated asynchronously after upload, so users don't wait.

## API Endpoints

### Upload with Embedding
```bash
POST /documents/upload?source_department=MoE
Content-Type: multipart/form-data
files: [file1.pdf, file2.docx]
```

### Vector Store Stats
```bash
GET /documents/vector-stats
```

### Reprocess Embeddings
```bash
POST /documents/reprocess-embeddings/123?source_department=AICTE
```

## Migration to pgvector

To switch from FAISS to Supabase pgvector:

1. Create new `Agent/vector_store/pgvector_store.py`
2. Implement same interface as `FAISSVectorStore`
3. Update `EmbeddingPipeline` initialization:

```python
from Agent.vector_store.pgvector_store import PgVectorStore

pipeline = EmbeddingPipeline(vector_store=PgVectorStore())
```

## File Structure
```
Agent/
├── chunking/
│   ├── base_chunker.py          # Abstract base class
│   ├── adaptive_chunker.py      # Adaptive strategy (default)
│   └── fixed_chunker.py         # Fixed-size strategy
├── embeddings/
│   └── gemini_embedder.py       # Gemini embedding model
└── vector_store/
    ├── faiss_store.py           # FAISS vector database
    ├── embedding_pipeline.py    # Main orchestrator
    └── faiss_index.*            # Persisted index files
```
