# 🚀 Lazy RAG Quick Start Guide

## ✅ System Status: READY

All components are implemented and tested. Here's how to use the new Lazy RAG system.

---

## 🏃 Quick Start

### 1. Start the Server
```bash
uvicorn backend.main:app --reload
```

### 2. Upload a Document (Instant!)
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "files=@your_document.pdf" \
  -F "source_department=Ministry of Education"
```

**Response** (in 3-7 seconds):
```json
{
  "results": [{
    "document_id": 17,
    "status": "success",
    "metadata_status": "processing",
    "embedding_status": "not_embedded"
  }]
}
```

### 3. Check Status (Optional)
```bash
curl "http://localhost:8000/documents/17/status"
```

**Response**:
```json
{
  "doc_id": 17,
  "status": "ready",
  "metadata_extracted": true,
  "embedding_status": "not_embedded",
  "title": "Education Policy 2024",
  "department": "Ministry of Education"
}
```

### 4. Query the System
```bash
curl -X POST "http://localhost:8000/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the education policy about?"}'
```

**What Happens**:
1. System searches metadata (instant)
2. Reranks with Gemini (1-2 sec)
3. Embeds if needed (8-12 sec first time)
4. Searches and returns results

**Response**:
```json
{
  "answer": "The education policy focuses on...",
  "citations": [{
    "document_id": "17",
    "source": "Education_Policy_2024.pdf",
    "tool": "search_documents"
  }],
  "confidence": 0.85,
  "status": "success"
}
```

---

## 📚 Browse Documents

### Filter by Department
```bash
curl "http://localhost:8000/documents/browse/metadata?department=Education"
```

### Filter by Type
```bash
curl "http://localhost:8000/documents/browse/metadata?document_type=policy"
```

### Filter by Year
```bash
curl "http://localhost:8000/documents/browse/metadata?year=2024"
```

**Response**:
```json
{
  "total": 45,
  "documents": [
    {
      "doc_id": 17,
      "title": "Education Policy 2024",
      "department": "Ministry of Education",
      "document_type": "policy",
      "summary": "Comprehensive education reform...",
      "keywords": ["education", "reform", "teachers"],
      "embedding_status": "not_embedded"
    }
  ]
}
```

---

## ⚡ Manual Embedding (Optional)

If you want to pre-embed documents:

```bash
curl -X POST "http://localhost:8000/documents/embed" \
  -H "Content-Type: application/json" \
  -d '{"doc_ids": [17, 18, 19]}'
```

**Response**:
```json
{
  "status": "embedding_started",
  "doc_ids": [17, 18, 19],
  "estimated_time": 6
}
```

---

## 🧪 Run Tests

### Test Lazy RAG Components
```bash
python tests/test_lazy_rag.py
```

### Test Everything
```bash
python tests/run_all_tests.py
```

---

## 📊 Performance Expectations

| Operation | Time | Notes |
|-----------|------|-------|
| Upload | 3-7 sec | Instant response |
| Metadata extraction | 3-4 sec | Background |
| Query (embedded) | 4-7 sec | Fast |
| Query (not embedded) | 12-19 sec | First time |
| Subsequent queries | 4-7 sec | Cached |

---

## 🎯 Key Features

### ✅ Instant Uploads
Documents are uploaded and saved immediately. Metadata extraction happens in the background.

### ✅ Smart Search
System filters by metadata before expensive embedding operations.

### ✅ Lazy Embedding
Documents are only embedded when actually queried.

### ✅ Automatic Citations
All responses include source documents and confidence scores.

### ✅ Browse by Metadata
Filter documents by department, type, or year without querying.

---

## 🔧 Configuration

### Change Reranker
Edit `Agent/tools/lazy_search_tools.py`:
```python
# Use Gemini (current)
reranker = DocumentReranker(provider="gemini")

# Use local model (future)
reranker = DocumentReranker(provider="local")
```

### Adjust Limits
Edit `Agent/tools/lazy_search_tools.py`:
```python
# BM25 candidates
top_indices = bm25_scores.argsort()[-20:][::-1]  # Change 20

# Rerank top K
reranked_docs = reranker.rerank(query, candidates, top_k=5)  # Change 5
```

---

## 🐛 Troubleshooting

### Metadata Not Extracting
**Check**: Google API key in `.env`
```bash
GOOGLE_API_KEY=your_key_here
```

### Embedding Fails
**Check**: GPU availability
```python
import torch
print(torch.cuda.is_available())  # Should be True
```

### Search Returns Nothing
**Check**: Metadata extraction completed
```bash
curl "http://localhost:8000/documents/{doc_id}/status"
```

### Database Issues
**Check**: Migration applied
```bash
alembic current
# Should show: 002 (head)
```

---

## 📖 Documentation

- `LAZY_RAG_COMPLETE.md` - Full technical documentation
- `INTEGRATION_SUMMARY.md` - Integration overview
- `LAZY_RAG_IMPLEMENTATION.md` - Implementation details

---

## 🎓 How It Works

### Upload Flow
```
User uploads → Extract text → Save to DB → Return immediately
                                ↓
                        Background: Extract metadata
                        (filename, keywords, LLM summary)
```

### Query Flow
```
User queries → BM25 on metadata (20 docs)
                    ↓
            Gemini rerank (5 docs)
                    ↓
            Check embedding status
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
    Embedded              Not Embedded
        ↓                       ↓
    Search              Embed → Search
        ↓                       ↓
        └───────────┬───────────┘
                    ↓
            Return results + citations
```

---

## ✨ Example Workflow

### Scenario: MoE uploads 100 policy documents

**Before (Eager Embedding)**:
- Upload time: 100 docs × 30 sec = **50 minutes**
- All documents embedded upfront
- Many never queried (wasted resources)

**After (Lazy RAG)**:
- Upload time: 100 docs × 5 sec = **8 minutes** ⚡
- Metadata extracted in background
- Only queried documents get embedded
- 80% resource savings if only 20% queried

---

## 🎉 You're Ready!

The Lazy RAG system is fully operational. Start uploading documents and querying!

**Questions?** Check the documentation files or logs in `Agent/agent_logs/`

---

**Status**: ✅ Production Ready
**Version**: 1.0.0
**Date**: November 28, 2024
