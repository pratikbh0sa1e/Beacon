# Test Suite for Government Policy Intelligence Platform

## Overview
Comprehensive test suite covering all system functionalities.

## Test Files

### 1. `test_embeddings.py`
Tests embedding and vector store functionality:
- BGE embedder (single & batch)
- Adaptive chunker (small & large documents)
- FAISS vector store (add, search, stats)

**Run:**
```bash
python tests/test_embeddings.py
```

### 2. `test_retrieval.py`
Tests hybrid retrieval system:
- Vector search (semantic)
- BM25 search (keyword)
- Combined scoring
- Result ranking

**Run:**
```bash
python tests/test_retrieval.py
```

### 3. `test_document_upload.py`
Tests document upload and processing:
- PDF upload
- DOCX upload
- Document listing
- Document retrieval
- Vector statistics

**Run:**
```bash
python tests/test_document_upload.py
```

**Note:** Add test files to `tests/test_data/` folder:
- `sample.pdf`
- `sample.docx`

### 4. `test_agent.py`
Tests RAG agent and tools:
- Chat service health
- Simple Q&A
- Search queries
- Policy comparison
- Web search
- Multi-step reasoning

**Run:**
```bash
# Make sure server is running first
uvicorn backend.main:app --reload

# Then run tests
python tests/test_agent.py
```

### 5. `run_all_tests.py`
Runs all test suites and provides summary.

**Run:**
```bash
python tests/run_all_tests.py
```

## Prerequisites

1. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install rank-bm25 duckduckgo-search langchain-community
```

2. **Setup environment:**
- Configure `.env` file with all API keys
- Ensure database is running
- Start the server

3. **Add test data:**
```bash
mkdir tests/test_data
# Add sample.pdf and sample.docx to this folder
```

## Running Tests

### Quick Test (Individual)
```bash
# Test embeddings only
python tests/test_embeddings.py

# Test retrieval only
python tests/test_retrieval.py

# Test uploads only (server must be running)
python tests/test_document_upload.py

# Test agent only (server must be running)
python tests/test_agent.py
```

### Full Test Suite
```bash
# Run all tests
python tests/run_all_tests.py
```

## Expected Output

Each test will show:
- ✅ Success indicators
- ❌ Failure indicators
- 📝 Test details
- 📊 Summary statistics

## Troubleshooting

**Server not running:**
```bash
uvicorn backend.main:app --reload
```

**Missing dependencies:**
```bash
pip install -r requirements.txt
```

**GPU not detected:**
- Check CUDA installation
- Verify PyTorch CUDA support: `python -c "import torch; print(torch.cuda.is_available())"`

**Test data missing:**
- Add sample files to `tests/test_data/`
- Or comment out upload tests

## CI/CD Integration

Add to your CI pipeline:
```yaml
- name: Run tests
  run: python tests/run_all_tests.py
```
