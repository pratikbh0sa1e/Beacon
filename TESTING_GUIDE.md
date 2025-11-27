# Testing Guide - Government Policy Intelligence Platform

## Overview
Comprehensive test suite for the RAG-based policy intelligence platform with citation tracking.

## Test Suite

### 1. Embedding Tests (`tests/test_embeddings.py`)
Tests the BGE embedding model and FAISS vector store:
- ✅ BGE model loading (GPU-accelerated)
- ✅ Single text embedding
- ✅ Batch embedding
- ✅ Adaptive chunking (small & large documents)
- ✅ FAISS vector storage and search

### 2. Retrieval Tests (`tests/test_retrieval.py`)
Tests the hybrid retrieval system:
- ✅ Hybrid search (70% vector + 30% BM25)
- ✅ Score normalization
- ✅ Multiple document queries
- ✅ Relevance ranking

### 3. Document Upload Tests (`tests/test_document_upload.py`)
Tests the FastAPI backend endpoints:
- ✅ List all documents
- ✅ Get specific document
- ✅ Vector statistics
- ✅ Document metadata

### 4. Agent Tests (`tests/test_agent.py`)
Tests the ReAct agent functionality:
- ✅ Health check
- ✅ Simple queries
- ✅ Search queries
- ✅ Tool execution

### 5. Citation Tests (`tests/test_citations.py`) ⭐ NEW
Tests citation extraction from agent responses:
- ✅ Agent initialization
- ✅ Citation extraction from tool outputs
- ✅ Document ID tracking
- ✅ Source filename tracking
- ✅ Confidence scoring based on citations

## Running Tests

### Run All Tests
```bash
python tests/run_all_tests.py
```

### Run Individual Tests
```bash
# Embeddings
python tests/test_embeddings.py

# Retrieval
python tests/test_retrieval.py

# Document Upload
python tests/test_document_upload.py

# Agent
python tests/test_agent.py

# Citations
python tests/test_citations.py
```

## Citation System

### How It Works
1. **Agent executes tools** (search_documents, search_specific_document, etc.)
2. **Tool outputs contain** document IDs and source filenames
3. **Agent extracts citations** from intermediate steps
4. **Response includes** structured citation data

### Citation Format
```json
{
  "answer": "Sarthak Bhoj is a B.Tech student...",
  "citations": [
    {
      "document_id": "16",
      "source": "Sarthak CV.pdf",
      "tool": "search_documents"
    }
  ],
  "confidence": 0.85,
  "status": "success"
}
```

### Confidence Scoring
- **0.95**: 3+ citations
- **0.90**: 2 citations
- **0.85**: 1 citation
- **0.70**: No citations

## Key Features

### Singleton Pattern for BGE Model
The BGE embedder uses a singleton pattern to avoid loading the model multiple times:
- First initialization: ~10 seconds
- Subsequent uses: Instant (reuses cached model)

### Automatic Cleanup
All tests automatically clean up temporary files:
- FAISS indexes
- Metadata files
- Hash files

### Rate Limit Handling
Citation tests include delays between queries to avoid API rate limits.

## Requirements

### Environment Variables
```bash
GOOGLE_API_KEY=your_gemini_api_key
DATABASE_URL=your_postgres_url
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### Dependencies
- Python 3.11+
- CUDA-capable GPU (optional, for faster embeddings)
- All packages from `requirements.txt`

## Troubleshooting

### Google API Quota Exceeded
**Error**: `429 You exceeded your current quota`
**Solution**: Wait 1-2 minutes between queries or upgrade API plan

### Model Not Found
**Error**: `404 models/gemini-X is not found`
**Solution**: Use `gemini-2.0-flash` model (confirmed working)

### No Citations Returned
**Issue**: Citations array is empty
**Solution**: Ensure `return_intermediate_steps=True` in AgentExecutor

### Module Not Found
**Error**: `ModuleNotFoundError: No module named 'Agent'`
**Solution**: Tests automatically add parent directory to path

## Test Results

All tests pass successfully:
- ✅ Embeddings: BGE model, chunking, FAISS
- ✅ Retrieval: Hybrid search working
- ✅ Document Upload: API endpoints functional
- ✅ Agent: ReAct agent operational
- ✅ Citations: Extraction working perfectly

## Next Steps

1. Add more test documents for comprehensive testing
2. Test with different document types (PDF, DOCX, images)
3. Add performance benchmarks
4. Test concurrent requests
5. Add integration tests for full workflow
