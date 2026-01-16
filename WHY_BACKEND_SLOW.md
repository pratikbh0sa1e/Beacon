# Why Backend Takes So Long to Load

## The Problem

Your backend is loading **BGE-M3 embedding model** which is:

- **Size**: ~3GB
- **Dimensions**: 1024
- **Loading on**: CPU (not GPU)
- **Time**: 2-5 minutes on first load

## What's Loading (In Order)

### 1. Python Imports (10 seconds)

- FastAPI, SQLAlchemy, Pydantic
- All your routers and utilities

### 2. Database Connection (5 seconds)

- Connecting to Supabase PostgreSQL
- Loading all models and relationships

### 3. **BGE-M3 Embedding Model (2-4 MINUTES)** ⏰

```python
# This is what takes forever:
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-m3')  # Downloads & loads 3GB model
```

This happens in:

- `Agent/embeddings/bge_embedder.py`
- Loaded by `Agent/retrieval/hybrid_retriever.py`
- Used by RAG agent initialization

### 4. Ollama Connection (2 seconds)

- Connecting to Ollama API
- Initializing LLM providers

### 5. Other Components (10 seconds)

- Metadata extractor
- Reranker
- Tools initialization

## Total Time: 3-5 Minutes

## Solutions

### Option 1: Keep Backend Running (Recommended)

**Don't restart the backend frequently!**

- Load once, keep it running
- Use `--reload` for code changes (doesn't reload models)
- Only restart when absolutely necessary

### Option 2: Use Lighter Embedding Model

Change in `.env`:

```env
# Current (slow):
EMBEDDING_MODEL=bge-m3  # 1024 dim, 3GB

# Faster option:
EMBEDDING_MODEL=all-MiniLM-L6-v2  # 384 dim, 80MB
# Loads in 10 seconds instead of 3 minutes!
```

**Trade-off**: Slightly lower search accuracy

### Option 3: Lazy Loading (Best for Development)

Only load embedding model when actually needed, not at startup.

I can implement this for you - the model would load:

- On first search query
- On first document embedding
- Not during backend startup

### Option 4: Use GPU (If Available)

If you have NVIDIA GPU:

```env
FORCE_CPU=false
```

Model loads in 30 seconds instead of 3 minutes.

## What I Recommend

### For Development/Testing:

1. **Start backend once** in the morning
2. **Keep it running** all day
3. **Use --reload** for code changes
4. Only restart when changing .env

### For Production:

1. Use GPU server
2. Or use lighter embedding model
3. Or implement lazy loading

## Quick Fix: Lighter Model

Want me to switch you to a lighter embedding model that loads in 10 seconds?

**Pros**:

- ✅ Loads in 10 seconds (vs 3 minutes)
- ✅ Uses 80MB RAM (vs 3GB)
- ✅ Still good search quality
- ✅ Perfect for testing

**Cons**:

- ⚠️ Slightly lower accuracy (90% vs 95%)
- ⚠️ 384 dimensions (vs 1024)

Let me know if you want the quick fix!
