# ⚡ Quick Configuration Guide

## 🚀 5-Minute Setup

### 1. Copy Environment File

```bash
cp .env.example .env
```

### 2. Update These Key Variables in `.env`:

```env
# 🔑 REQUIRED - Get from Google AI Studio (ai.google.dev)
GOOGLE_API_KEY=AIzaSyDkCCqQdgGtrd2t1yGjCJ4zv4QmNNjn93w

# 🗄️ REQUIRED - Get from Supabase Dashboard
DATABASE_HOSTNAME=aws-1-ap-south-1.pooler.supabase.com
DATABASE_USERNAME=postgres.your-project-id
DATABASE_PASSWORD=your-database-password
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# 🔐 REQUIRED - Generate random strings
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
```

### 3. Generate Secret Keys

```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

### 4. Start Application

```bash
# Backend
uvicorn backend.main:app --reload

# Frontend (new terminal)
cd frontend && npm run dev
```

---

## 🎯 Current Optimal Configuration

### For Best Performance & Reliability:

```env
# ============================================
# AI Models - OPTIMIZED SETUP
# ============================================
# Metadata Extraction - HIGH VOLUME
METADATA_LLM_PROVIDER=gemini          # gemma-3-12b (14,400/day)
METADATA_FALLBACK_PROVIDER=gemini

# RAG Agent - CHAT with Hindi Support
RAG_LLM_PROVIDER=gemini               # gemini-2.5-flash (1,500/day)
RAG_FALLBACK_PROVIDER=ollama          # llama3.2 (unlimited, local)

# Reranker - OPTIONAL
RERANKER_PROVIDER=local               # Simple scoring (no API calls)

# ============================================
# Quality Control - RECOMMENDED
# ============================================
DELETE_DOCS_WITHOUT_METADATA=false   # Keep docs even if metadata fails
REQUIRE_TITLE=false                   # Don't require title
REQUIRE_SUMMARY=false                 # Don't require summary
```

---

## 🌍 Language Configuration

### For Hindi + English Support:

The system is already configured for multilingual support:

1. **Search**: Automatically translates Hindi queries to English for searching
2. **Response**: Responds in the same language as the user's question
3. **Documents**: Can handle mixed language content

### Test Hindi Support:

```bash
python test_hindi_search.py
```

---

## 🔧 Provider Switching

### If Gemini Quota Exceeded:

```env
RAG_LLM_PROVIDER=ollama
```

### If Want All Free:

```env
METADATA_LLM_PROVIDER=ollama
RAG_LLM_PROVIDER=ollama
RERANKER_PROVIDER=local
```

### If Want Cloud-Only:

```env
METADATA_LLM_PROVIDER=gemini
RAG_LLM_PROVIDER=openrouter
RERANKER_PROVIDER=openrouter
OPENROUTER_API_KEY=your-openrouter-key
```

---

## 📊 Quota Summary

| Provider       | Model            | Daily Limit | Use Case            |
| -------------- | ---------------- | ----------- | ------------------- |
| **Gemini**     | gemma-3-12b      | 14,400      | Metadata extraction |
| **Gemini**     | gemini-2.5-flash | 1,500       | Chat/RAG            |
| **OpenRouter** | llama-3.3-70b    | 200         | Backup chat         |
| **Ollama**     | llama3.2         | Unlimited   | Local fallback      |

**Total Daily Capacity**: 15,900+ operations

---

## 🚨 Common Issues & Quick Fixes

### Issue 1: Backend Won't Start

```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt

# Check .env file exists
ls -la .env
```

### Issue 2: Database Connection Failed

```bash
# Test connection
python -c "from backend.database import engine; print(engine.connect())"

# Check Supabase project is running
# Verify DATABASE_* variables in .env
```

### Issue 3: AI Models Not Working

```bash
# Test Google API key
curl -H "Authorization: Bearer $GOOGLE_API_KEY" https://generativelanguage.googleapis.com/v1beta/models

# Switch to Ollama
echo "RAG_LLM_PROVIDER=ollama" >> .env
ollama pull llama3.2
```

### Issue 4: Hindi Responses in English

```bash
# Restart backend to apply prompt changes
# Test with: python test_hindi_search.py
```

### Issue 5: No Documents Found

```bash
# Check if documents exist
python -c "from backend.database import SessionLocal, Document; db = SessionLocal(); print(f'Documents: {db.query(Document).count()}')"

# Run web scraping to add documents
# Go to frontend → Enhanced Web Scraping → Start scraping
```

---

## 🎯 Quick Test Commands

### Test Everything:

```bash
# 1. Test backend
curl http://localhost:8000/health

# 2. Test database
python -c "from backend.database import engine; print('DB OK:', bool(engine.connect()))"

# 3. Test AI models
python test_hindi_search.py

# 4. Test frontend
curl http://localhost:3000
```

### Test Specific Features:

```bash
# Test web scraping
python test_scraping_system.py

# Test document upload
python test_document_upload.py

# Test embeddings
python test_embeddings.py
```

---

## 📱 Access URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database Admin**: https://your-project.supabase.co

---

## 🔄 Restart Commands

### Full Restart:

```bash
# Stop all services (Ctrl+C)

# Restart backend
uvicorn backend.main:app --reload

# Restart frontend (new terminal)
cd frontend && npm run dev

# Restart Ollama (if using)
ollama serve
```

### Quick Reload:

```bash
# Backend auto-reloads on file changes
# Frontend auto-reloads on file changes
# Just save your changes!
```

---

## 📋 Environment Variables Checklist

### ✅ Required (Must Set):

- [ ] `GOOGLE_API_KEY` - From ai.google.dev
- [ ] `DATABASE_HOSTNAME` - From Supabase
- [ ] `DATABASE_USERNAME` - From Supabase
- [ ] `DATABASE_PASSWORD` - From Supabase
- [ ] `SUPABASE_URL` - From Supabase
- [ ] `SUPABASE_KEY` - From Supabase
- [ ] `SECRET_KEY` - Generate random
- [ ] `JWT_SECRET_KEY` - Generate random

### ⚙️ Optional (Has Defaults):

- [ ] `OPENROUTER_API_KEY` - For backup LLM
- [ ] `OLLAMA_BASE_URL` - For local LLM
- [ ] `SMTP_*` - For email features
- [ ] `REDIS_URL` - For caching

### 🎛️ Configuration (Pre-set):

- [ ] `METADATA_LLM_PROVIDER=gemini`
- [ ] `RAG_LLM_PROVIDER=gemini`
- [ ] `RERANKER_PROVIDER=local`

---

## 🎉 You're Ready!

Once you've set the required variables:

1. **Start backend**: `uvicorn backend.main:app --reload`
2. **Start frontend**: `cd frontend && npm run dev`
3. **Open browser**: http://localhost:3000
4. **Test Hindi**: Ask "राष्ट्रीय शिक्षा नीति 2020 के बारे में बताएं"

**Need help?** Check `DEPLOYMENT_INSTRUCTIONS.md` for detailed setup or `TROUBLESHOOTING.md` for common issues.
