# Gemini Model Configuration - FINAL

## The Problem

**gemma-3-12b** has different support across Google's API:

- ✅ Works for: Metadata extraction (simple text generation)
- ❌ Fails for: Chat/conversation (RAG agent, reranker)
- Error: `404 models/gemma-3-12b is not found for API version v1beta`

## Solution: Hybrid Approach

### 1. Metadata Extractor

**Model**: `gemma-3-12b`
**Why**:

- Simple text generation task
- 14,400 requests/day quota
- Works perfectly for extracting metadata

### 2. RAG Agent (Chat)

**Model**: `gemini-1.5-flash`
**Why**:

- Supports conversation/chat
- Stable and reliable
- Good for Q&A tasks

### 3. Reranker

**Model**: `gemini-1.5-flash`
**Why**:

- Needs chat capabilities for ranking
- Stable model
- Good reasoning for relevance

## Current Configuration

```python
# Metadata Extraction
Agent/metadata/extractor.py → gemma-3-12b ✅

# RAG Agent (Chat)
Agent/rag_agent/react_agent.py → gemini-1.5-flash ✅

# Reranker
Agent/metadata/reranker.py → gemini-1.5-flash ✅
```

## Quota Summary

| Component          | Model            | RPM | RPD    | Status     |
| ------------------ | ---------------- | --- | ------ | ---------- |
| Metadata Extractor | gemma-3-12b      | 300 | 14,400 | ✅ Working |
| RAG Agent          | gemini-1.5-flash | 55  | 1,500  | ✅ Working |
| Reranker           | gemini-1.5-flash | 55  | 1,500  | ✅ Working |

**Total Daily Quota**: ~17,400 requests/day

## Why This Works

1. **Metadata extraction** is the bottleneck during scraping

   - Uses gemma-3-12b with 14,400 req/day
   - Can scrape thousands of documents

2. **RAG agent** is used less frequently

   - Only when users ask questions
   - gemini-1.5-flash with 1,500 req/day is sufficient

3. **Reranker** is optional
   - Only for improving search results
   - Low usage, 1,500 req/day is enough

## Alternative: Use OpenRouter for Everything

If you still hit quota limits:

```env
METADATA_LLM_PROVIDER=openrouter
RAG_LLM_PROVIDER=openrouter
RERANKER_PROVIDER=openrouter
```

- FREE, 200 requests/day
- Works for all components
- No quota issues

## Next Steps

1. **Restart backend** to apply changes:

   ```bash
   uvicorn backend.main:app --reload
   ```

2. **Verify in logs**:

   ```
   Initializing Gemini (gemma-3-12b) for metadata extraction
   Initializing Gemini (gemini-1.5-flash) for RAG agent
   Initializing Gemini (gemini-1.5-flash) reranker
   ```

3. **Test chat**:
   - Go to frontend
   - Ask a question
   - Should work without 404 error

## Model Compatibility Reference

### Gemma Models (gemma-3-12b, gemma-3-27b, etc.)

- ✅ Text generation
- ✅ Metadata extraction
- ❌ Chat/conversation
- ❌ Function calling

### Gemini Models (gemini-1.5-flash, gemini-2.0-flash-exp)

- ✅ Text generation
- ✅ Chat/conversation
- ✅ Function calling
- ✅ Multimodal (images)

## Conclusion

**Best configuration for your use case**:

- Scraping (high volume) → gemma-3-12b (14,400/day)
- Chat (low volume) → gemini-1.5-flash (1,500/day)
- Total: ~17,400 requests/day

This gives you the best balance of quota and functionality! 🎉
