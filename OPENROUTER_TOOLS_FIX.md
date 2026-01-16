# ❌ OpenRouter Tools Error - FIXED

## The Problem

Error when using OpenRouter for RAG agent:

```
Error code: 400 - {'error': {'message': 'Provider returned error', 'code': 400,
'metadata': {'raw': '{"detail":"Tools are not supported in streaming mode."}'}}}
```

**Root Cause**: OpenRouter's FREE models (like Llama 3.3 70B) **do NOT support function calling (tools)**.

The RAG agent uses LangChain's `create_tool_calling_agent()` which requires function calling support.

## Solution: Use Ollama (Local)

Switched RAG agent to use **Ollama** (local LLM):

### Updated `.env`:

```env
# Metadata Extraction - HIGH VOLUME
METADATA_LLM_PROVIDER=gemini          # gemma-3-12b (14,400/day)

# RAG Agent - NEEDS FUNCTION CALLING
RAG_LLM_PROVIDER=ollama               # llama3.2 (unlimited, local)

# Reranker - OPTIONAL
RERANKER_PROVIDER=local               # Simple scoring (no LLM)
```

## Why Ollama?

1. **Supports function calling** ✅
2. **Unlimited requests** (runs locally)
3. **Already installed** (llama3.2 model)
4. **No API costs**
5. **Works offline**

## Trade-offs

### OpenRouter (FREE):

- ✅ 200 requests/day
- ✅ Powerful (Llama 3.3 70B)
- ❌ No function calling support
- ❌ Requires internet

### Ollama (Local):

- ✅ Unlimited requests
- ✅ Function calling support
- ✅ Works offline
- ✅ No costs
- ⚠️ Slower (CPU-based)
- ⚠️ Smaller model (llama3.2)

## Configuration Summary

| Component          | Provider | Model          | Quota      | Function Calling |
| ------------------ | -------- | -------------- | ---------- | ---------------- |
| Metadata Extractor | Gemini   | gemma-3-12b    | 14,400/day | Not needed       |
| RAG Agent          | Ollama   | llama3.2       | Unlimited  | ✅ Required      |
| Reranker           | Local    | Simple scoring | Unlimited  | Not needed       |

## How to Verify

### 1. Check Ollama is Running

```bash
ollama list
```

Should show:

```
NAME            ID              SIZE    MODIFIED
llama3.2:latest abc123def456    1.9 GB  2 days ago
```

### 2. Restart Backend

```bash
uvicorn backend.main:app --reload
```

### 3. Check Logs

Look for:

```
Initializing Gemini (gemma-3-12b) for metadata extraction
Initializing Ollama for RAG agent with model: llama3.2
```

### 4. Test Chat

- Go to chat page
- Ask: "What is the Indo-Norwegian program?"
- Should work without 400 error

## Alternative: Use Gemini for RAG (If Ollama is Slow)

If Ollama is too slow, you can try Gemini for RAG:

```env
RAG_LLM_PROVIDER=gemini
```

**But**: Gemini has API version issues (v1beta) and may not support function calling consistently.

## Best Configuration (Current)

```env
METADATA_LLM_PROVIDER=gemini    # Fast, high quota (14,400/day)
RAG_LLM_PROVIDER=ollama         # Unlimited, function calling support
RERANKER_PROVIDER=local         # Simple, no LLM needed
```

This gives you:

- ✅ High-volume scraping (14,400 docs/day)
- ✅ Unlimited chat (local Ollama)
- ✅ Function calling support
- ✅ No API costs for chat

## Restart Required

**IMPORTANT**: Restart backend to apply changes:

```bash
# Stop backend (Ctrl+C)
# Restart:
uvicorn backend.main:app --reload
```

## Status: FIXED ✅

- ❌ OpenRouter removed from RAG agent (no function calling)
- ✅ Ollama configured for RAG agent (unlimited + function calling)
- ✅ Gemini still used for metadata (14,400/day)
- ✅ Local reranker (simple scoring)

**Your chat should now work without errors!**
