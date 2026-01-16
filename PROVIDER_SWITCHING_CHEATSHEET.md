# 🎯 Provider Switching Cheatsheet

## Quick Reference for Switching LLM Providers

### 🔄 Switch All to OpenRouter (RECOMMENDED)

```env
RAG_LLM_PROVIDER=openrouter
METADATA_LLM_PROVIDER=openrouter
RERANKER_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key_here
```

**Restart backend** → Done! ✅

---

### 🔄 Switch All to Gemini

```env
RAG_LLM_PROVIDER=gemini
METADATA_LLM_PROVIDER=gemini
RERANKER_PROVIDER=gemini
```

**Restart backend** → Done! ✅

---

### 🔄 Hybrid: OpenRouter for Metadata, Gemini for RAG

```env
METADATA_LLM_PROVIDER=openrouter
RAG_LLM_PROVIDER=gemini
RERANKER_PROVIDER=gemini
OPENROUTER_API_KEY=your_key_here
```

**Restart backend** → Done! ✅

---

## 📊 Quick Comparison

| Provider       | Daily Limit | Minute Limit | Quality        | Cost |
| -------------- | ----------- | ------------ | -------------- | ---- |
| **OpenRouter** | 200 ✅      | 20 ⚠️        | 70B ⭐⭐⭐⭐⭐ | FREE |
| **Gemini**     | 20 🔴       | 55 ✅        | Good ⭐⭐⭐⭐  | FREE |

---

## 🎯 Use Case Recommendations

### Production (100+ users/day)

```env
RAG_LLM_PROVIDER=openrouter
METADATA_LLM_PROVIDER=openrouter
RERANKER_PROVIDER=openrouter
```

### Development (<20 queries/day)

```env
RAG_LLM_PROVIDER=gemini
METADATA_LLM_PROVIDER=gemini
RERANKER_PROVIDER=gemini
```

### Web Scraping (1000 docs)

```env
METADATA_LLM_PROVIDER=openrouter  # Takes 5 days vs 50 days
```

---

## 🚀 Quick Commands

### Test Configuration

```bash
python -c "from Agent.rag_agent.react_agent import PolicyRAGAgent; print('✅ OK')"
```

### Start Backend

```bash
.\venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload
```

### Check Logs

```bash
# Look for these lines:
# INFO - RAG agent initialized with primary LLM: openrouter
# INFO - Metadata extractor initialized with primary LLM: openrouter
# INFO - Reranker initialized with provider: openrouter
```

---

## 🔑 Get OpenRouter API Key

1. Visit: https://openrouter.ai/
2. Sign up → Keys → Create
3. Copy key (starts with `sk-or-v1-...`)
4. Add to .env: `OPENROUTER_API_KEY=your_key_here`

---

## 💡 Pro Tips

✅ **OpenRouter for production** - 10x more requests  
✅ **Gemini for bursts** - 55 RPM vs 20 RPM  
✅ **Mix providers** - Use best of both  
✅ **No code changes** - Just edit .env  
✅ **Both FREE** - No ongoing costs

---

**That's it!** Just change .env and restart. 🎉
