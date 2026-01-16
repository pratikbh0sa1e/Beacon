# 🚀 Quick Start: Multi-Provider LLM Setup

## ✅ Implementation Complete!

Your system now supports **OpenRouter, Gemini, and OpenAI** for all LLM tasks.

## 🎯 Recommended Configuration

### For Production (100+ users/day):

```env
# Use OpenRouter (200 requests/day, better quality)
RAG_LLM_PROVIDER=openrouter
METADATA_LLM_PROVIDER=openrouter
RERANKER_PROVIDER=openrouter

# Gemini as fallback
RAG_FALLBACK_PROVIDER=gemini
METADATA_FALLBACK_PROVIDER=gemini

# OpenRouter API Key
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
```

## 📝 Setup Steps (5 Minutes)

### 1. Get OpenRouter API Key (2 minutes)

1. Visit: https://openrouter.ai/
2. Sign up (Google/GitHub/Email)
3. Click profile → "Keys" → Create new key
4. Copy key (starts with `sk-or-v1-...`)

### 2. Update .env

```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

### 3. Test

```bash
# Activate venv
.\venv\Scripts\Activate.ps1

# Test import
python -c "from Agent.rag_agent.react_agent import PolicyRAGAgent; print('✅ Success')"
```

### 4. Start Backend

```bash
python -m uvicorn backend.main:app --reload
```

Watch for:

```
INFO - RAG agent initialized with primary LLM: openrouter
INFO - Metadata extractor initialized with primary LLM: openrouter
INFO - Reranker initialized with provider: openrouter
```

## 🔄 Switching Providers

### Switch to Gemini (No API Key)

```env
RAG_LLM_PROVIDER=gemini
METADATA_LLM_PROVIDER=gemini
RERANKER_PROVIDER=gemini
```

Restart backend - done!

### Switch to OpenRouter

```env
RAG_LLM_PROVIDER=openrouter
METADATA_LLM_PROVIDER=openrouter
RERANKER_PROVIDER=openrouter
```

Restart backend - done!

## 📊 Rate Limits

| Provider             | Requests/Day | Requests/Min | Cost         |
| -------------------- | ------------ | ------------ | ------------ |
| **Gemini**           | 20 🔴        | 55 ✅        | FREE         |
| **OpenRouter FREE**  | 200 ✅       | 20 ⚠️        | FREE         |
| **OpenRouter ($10)** | 1,000 ✅     | 20 ⚠️        | $10 one-time |

## 💡 Key Benefits

✅ **10x More Requests** - 200/day vs Gemini's 20/day  
✅ **Better Quality** - 70B parameter model  
✅ **Environment Variable Switching** - No code changes  
✅ **Automatic Fallback** - Gemini backup  
✅ **FREE** - No ongoing costs

## 📚 Documentation

- `MULTI_PROVIDER_LLM_IMPLEMENTATION.md` - Complete guide
- `OPENROUTER_IMPLEMENTATION_COMPLETE.md` - OpenRouter details
- `HOW_TO_GET_OPENROUTER_KEY.md` - API key setup

## ⚡ Quick Commands

```bash
# Test RAG agent
python -c "from Agent.rag_agent.react_agent import PolicyRAGAgent; print('✅ RAG Agent OK')"

# Test metadata extractor
python -c "from Agent.metadata.extractor import MetadataExtractor; print('✅ Metadata Extractor OK')"

# Test reranker
python -c "from Agent.metadata.reranker import DocumentReranker; print('✅ Reranker OK')"

# Start backend
python -m uvicorn backend.main:app --reload
```

## 🎉 You're Ready!

1. ✅ Multi-provider support implemented
2. ✅ Environment variable switching
3. ✅ Automatic fallback configured
4. ⏳ Get OpenRouter API key (2 minutes)
5. ⏳ Test and deploy

---

**Next Step:** Get your OpenRouter API key and start using 200 requests/day! 🚀
