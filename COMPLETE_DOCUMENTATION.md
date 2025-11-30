# 🎯 BEACON - Government Policy Intelligence Platform
## Complete Documentation & User Guide

**Version:** 2.0.0  
**Last Updated:** November 30, 2025  
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Core Features](#core-features)
5. [API Reference](#api-reference)
6. [Multilingual Support](#multilingual-support)
7. [Voice Query System](#voice-query-system)
8. [Data Ingestion](#data-ingestion)
9. [Testing](#testing)
10. [Configuration](#configuration)
11. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

BEACON is an AI-powered platform designed for Ministry of Education (MoE) and Higher-Education bodies (AICTE/UGC) to retrieve, understand, compare, explain, and audit government policies using advanced AI technologies.

### Key Capabilities

- **Document Processing:** PDF, DOCX, PPTX, Images (with OCR)
- **Multilingual Support:** 100+ languages including Hindi, Tamil, Telugu, Bengali
- **Voice Queries:** Ask questions via audio (MP3, WAV, etc.)
- **Smart Search:** Hybrid retrieval (semantic + keyword)
- **Lazy RAG:** On-demand embedding for instant uploads
- **External Data Sync:** Connect to ministry databases
- **Citation Tracking:** All answers include source documents

### Technology Stack

- **Backend:** FastAPI, PostgreSQL, SQLAlchemy
- **Storage:** Supabase (S3 + PostgreSQL)
- **Embeddings:** BGE-M3 (multilingual, 1024-dim)
- **Vector Store:** FAISS (per-document indexes)
- **LLM:** Google Gemini 2.0 Flash
- **Voice:** OpenAI Whisper (local) or Google Cloud Speech
- **OCR:** EasyOCR (English + Hindi)

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone <repository-url>
cd Beacon__V1

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install PyTorch with CUDA (for GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install voice dependencies
pip install openai-whisper ffmpeg-python

# Install FFmpeg (system dependency)
# Windows: Download from https://ffmpeg.org/download.html
# Linux: sudo apt install ffmpeg
# Mac: brew install ffmpeg
```

### 2. Configuration

Create `.env` file:

```env
# Database
DATABASE_HOSTNAME=your-db-host
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USERNAME=your-username
DATABASE_PASSWORD=your-password

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
SUPABASE_BUCKET_NAME=Docs

# API Keys
GOOGLE_API_KEY=your-google-api-key
OPENAI_API_KEY=your-openai-key (optional)

# Data Ingestion (auto-generated)
DB_ENCRYPTION_KEY=your-encryption-key
```

### 3. Database Setup

```bash
# Run migrations
alembic upgrade head

# Initialize developer account
# (happens automatically on first run)
```

### 4. Start Server

```bash
uvicorn backend.main:app --reload
```

### 5. Access API

- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    External Sources                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Ministry │  │  Voice   │  │  Direct  │  │ External │   │
│  │   DBs    │  │  Input   │  │  Upload  │  │   APIs   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                          │
                    ┌─────▼─────┐
                    │  FastAPI  │
                    │  Backend  │
                    └─────┬─────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
   │Document │      │  Voice  │      │  Data   │
   │Processor│      │Transcribe│     │Ingestion│
   └────┬────┘      └────┬────┘      └────┬────┘
        │                 │                 │
        └─────────────────┴─────────────────┘
                          │
                    ┌─────▼─────┐
                    │  Metadata │
                    │ Extractor │
                    └─────┬─────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
   │Supabase │      │PostgreSQL│     │  Lazy   │
   │Storage  │      │ Metadata │     │   RAG   │
   └─────────┘      └─────────┘      └────┬────┘
                                           │
                                     ┌─────▼─────┐
                                     │ BGE-M3    │
                                     │Embeddings │
                                     └─────┬─────┘
                                           │
                                     ┌─────▼─────┐
                                     │   FAISS   │
                                     │  Vector   │
                                     │   Store   │
                                     └─────┬─────┘
                                           │
                                     ┌─────▼─────┐
                                     │  Hybrid   │
                                     │ Retrieval │
                                     └─────┬─────┘
                                           │
                                     ┌─────▼─────┐
                                     │ RAG Agent │
                                     │  (Gemini) │
                                     └───────────┘
```

### Data Flow

**Upload Flow:**
```
Upload → Extract Text → Save DB → Return (3-7s)
                           ↓
                   Background: Extract Metadata (3-4s)
```

**Query Flow:**
```
Query → BM25 Search → Rerank → Check Embedding
                                      ↓
                              ┌───────┴───────┐
                              ↓               ↓
                          Embedded      Not Embedded
                              ↓               ↓
                          Search      Embed → Search
                              ↓               ↓
                              └───────┬───────┘
                                      ↓
                              Generate Answer + Citations
```

---

## ✨ Core Features

### 1. Document Processing

**Supported Formats:**
- PDF (with OCR for scanned documents)
- DOCX (Microsoft Word)
- PPTX (PowerPoint presentations)
- Images (JPEG, PNG) with OCR
- TXT (plain text)

**Processing Pipeline:**
1. Text extraction (format-specific)
2. OCR for images/scanned PDFs
3. Upload to Supabase S3
4. Save metadata to PostgreSQL
5. Background metadata extraction (AI-powered)
6. Lazy embedding (on-demand)

**Upload Example:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@policy.pdf" \
  -F "title=Education Policy 2025" \
  -F "category=Policy" \
  -F "department=MoE"
```

### 2. Multilingual Embeddings

**Active Model:** BGE-M3
- **Dimension:** 1024
- **Languages:** 100+ (English, Hindi, Tamil, Telugu, Bengali, etc.)
- **Cross-lingual:** Search in English, find Hindi documents

**Switch Models:**
Edit `Agent/embeddings/embedding_config.py`:
```python
ACTIVE_MODEL = "bge-m3"           # Multilingual (current)
# ACTIVE_MODEL = "bge-large-en"   # English-only
# ACTIVE_MODEL = "gemini-embedding"  # Cloud-based
```

**Available Models:**
| Model | Dimension | Languages | Use Case |
|-------|-----------|-----------|----------|
| bge-m3 ⭐ | 1024 | 100+ | Multilingual govt docs |
| bge-large-en | 1024 | English | English-only |
| gemini-embedding | 768 | 100+ | Cloud-based |
| labse | 768 | 109 | Smaller, faster |

### 3. Voice Query System

**Supported Formats:** MP3, WAV, M4A, OGG, FLAC

**Active Engine:** Whisper (Local)
- **Model:** OpenAI Whisper base
- **Device:** CUDA (GPU)
- **Languages:** 98+
- **Cost:** Free

**Voice Query Example:**
```bash
curl -X POST "http://localhost:8000/voice/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio=@question.mp3" \
  -F "language=en"
```

**Response:**
```json
{
  "transcription": "What are the education policy guidelines?",
  "language": "en",
  "answer": "The education policy guidelines include...",
  "processing_time": 5.27
}
```

**Switch Engines:**
Edit `Agent/voice/speech_config.py`:
```python
ACTIVE_ENGINE = "whisper-local"  # Local (free, private)
# ACTIVE_ENGINE = "google-cloud"  # Cloud (paid, high quality)
```

### 4. Lazy RAG

**Benefits:**
- ✅ Instant uploads (3-7 seconds)
- ✅ On-demand embedding (only when queried)
- ✅ 80% resource savings
- ✅ Metadata-based filtering

**How It Works:**
1. Upload document → Save immediately
2. Extract metadata in background
3. Query arrives → Filter by metadata
4. Embed only relevant documents
5. Search and return results

### 5. Hybrid Retrieval

**Combination:**
- 70% Vector Search (semantic similarity)
- 30% BM25 Search (keyword matching)

**Benefits:**
- Better recall (finds more relevant docs)
- Handles both semantic and exact matches
- Robust to query variations

### 6. RAG Agent

**Model:** Google Gemini 2.0 Flash
**Architecture:** ReAct (Reasoning + Acting)

**Available Tools:**
1. `search_documents` - Search all documents
2. `search_specific_document` - Search one document
3. `compare_policies` - Compare multiple documents
4. `get_document_metadata` - Get document info
5. `summarize_document` - Summarize document

**Query Example:**
```bash
curl -X POST "http://localhost:8000/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the education policy guidelines?",
    "thread_id": "session_1"
  }'
```

**Response with Citations:**
```json
{
  "answer": "The education policy guidelines include...",
  "citations": [
    {
      "document_id": "17",
      "source": "Education_Policy_2025.pdf",
      "tool": "search_documents"
    }
  ],
  "confidence": 0.85
}
```

### 7. External Data Ingestion

**Connect to Ministry Databases:**
- PostgreSQL databases
- Automatic daily syncing
- Encrypted credentials
- Supabase storage support

**Register Data Source:**
```bash
curl -X POST "http://localhost:8000/data-sources/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MoE_Primary_DB",
    "ministry_name": "Ministry of Education",
    "host": "moe-db.example.com",
    "port": 5432,
    "database_name": "moe_documents",
    "username": "readonly_user",
    "password": "secure_password",
    "table_name": "policy_documents",
    "file_column": "document_data",
    "filename_column": "document_name",
    "sync_enabled": true
  }'
```

**Trigger Sync:**
```bash
curl -X POST "http://localhost:8000/data-sources/1/sync"
```

---

## 📡 API Reference

### Document Management

#### Upload Document
```
POST /documents/upload
```
**Form Data:**
- `file`: Document file
- `title`: Document title (optional)
- `category`: Document category (optional)
- `department`: Department name (optional)
- `description`: User description (optional)

#### List Documents
```
GET /documents/list?category=Policy&search=education
```

#### Get Document
```
GET /documents/{document_id}
```

#### Document Status
```
GET /documents/{document_id}/status
```

### Chat/Query

#### Ask Question
```
POST /chat/query
```
**Body:**
```json
{
  "question": "What are the policy guidelines?",
  "thread_id": "session_1"
}
```

#### Health Check
```
GET /chat/health
```

### Voice Queries

#### Voice Query (Transcribe + Answer)
```
POST /voice/query
```
**Form Data:**
- `audio`: Audio file (MP3, WAV, etc.)
- `language`: Language code (optional)
- `thread_id`: Thread ID (optional)

#### Transcribe Only
```
POST /voice/transcribe
```
**Form Data:**
- `audio`: Audio file
- `language`: Language code (optional)

#### Voice Health
```
GET /voice/health
```

### Data Sources

#### Create Data Source
```
POST /data-sources/create
```

#### List Data Sources
```
GET /data-sources/list
```

#### Sync Data Source
```
POST /data-sources/{source_id}/sync?limit=10
```

#### Sync Logs
```
GET /data-sources/{source_id}/sync-logs
```

---

## 🌍 Multilingual Support

### Supported Languages

**Major Indian Languages:**
- Hindi (hi)
- Tamil (ta)
- Telugu (te)
- Bengali (bn)
- Marathi (mr)
- Gujarati (gu)
- Kannada (kn)
- Malayalam (ml)
- Punjabi (pa)
- Urdu (ur)

**Plus 90+ other languages including:**
- English, Spanish, French, German, Chinese, Japanese, Arabic, etc.

### Cross-Lingual Search

**Example:** Search in English, find Hindi documents

```bash
# Upload Hindi document
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@hindi_policy.pdf" \
  -F "title=शिक्षा नीति"

# Query in English
curl -X POST "http://localhost:8000/chat/query" \
  -d '{"question": "What is the education policy?"}'

# Result: Finds both English AND Hindi documents!
```

### Performance

| Model | English | Hindi | Cross-Lingual |
|-------|---------|-------|---------------|
| bge-m3 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| bge-large-en | ⭐⭐⭐⭐⭐ | ❌ | ❌ |

---

## 🎤 Voice Query System

### Setup

1. **Install Whisper:**
```bash
pip install openai-whisper ffmpeg-python
```

2. **Install FFmpeg:**
- Windows: Download from https://ffmpeg.org/download.html
- Linux: `sudo apt install ffmpeg`
- Mac: `brew install ffmpeg`

3. **Test:**
```bash
venv\Scripts\python.exe tests/test_voice_query.py
```

### Usage

**Record audio** (MP3, WAV, etc.) and send:

```bash
curl -X POST "http://localhost:8000/voice/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio=@question.mp3"
```

**Response:**
```json
{
  "transcription": "What are the education guidelines?",
  "language": "english",
  "answer": "The education guidelines include...",
  "processing_time": 5.27
}
```

### Engines

| Engine | Type | Cost | Speed | Quality |
|--------|------|------|-------|---------|
| whisper-local ⭐ | Local | Free | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ |
| google-cloud | Cloud | $0.006/15s | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ |

### Whisper Models

| Model | Speed | Accuracy | GPU Memory |
|-------|-------|----------|------------|
| tiny | ⚡⚡⚡⚡⚡ | ⭐⭐ | ~1GB |
| base ⭐ | ⚡⚡⚡⚡ | ⭐⭐⭐ | ~1GB |
| small | ⚡⚡⚡ | ⭐⭐⭐⭐ | ~2GB |
| medium | ⚡⚡ | ⭐⭐⭐⭐⭐ | ~5GB |

---

## 📊 Data Ingestion

### Connect External Databases

**Supported:**
- PostgreSQL databases
- Supabase storage
- BLOB storage
- File path references

### Configuration

**Database Storage (BLOB):**
```json
{
  "storage_type": "database",
  "file_column": "file_data"
}
```

**Supabase Storage:**
```json
{
  "storage_type": "supabase",
  "file_column": "file_path",
  "supabase_url": "https://project.supabase.co",
  "supabase_key": "your-key",
  "supabase_bucket": "documents",
  "file_path_prefix": "policies/"
}
```

### Scheduler

**Default:** Daily sync at 2:00 AM

**Change Time:**
Edit `backend/main.py`:
```python
start_scheduler(sync_time="03:30")  # 3:30 AM
```

### Security

- ✅ Encrypted passwords (Fernet)
- ✅ Read-only database access
- ✅ SSL/TLS support
- ✅ VPN recommended

---

## 🧪 Testing

### Run All Tests

```bash
python tests/run_all_tests.py
```

### Individual Tests

```bash
# Embeddings
python tests/test_embeddings.py

# Retrieval
python tests/test_retrieval.py

# Voice
python tests/test_voice_query.py

# Multilingual
python tests/test_multilingual_embeddings.py

# PPTX Support
python tests/test_pptx_support.py
```

### Test Coverage

- ✅ Embeddings (BGE-M3, chunking, FAISS)
- ✅ Retrieval (hybrid search)
- ✅ Document upload
- ✅ RAG agent
- ✅ Citations
- ✅ Voice queries
- ✅ Multilingual
- ✅ PPTX support

---

## ⚙️ Configuration

### Embedding Models

**File:** `Agent/embeddings/embedding_config.py`

```python
ACTIVE_MODEL = "bge-m3"  # Change here
```

### Voice Engines

**File:** `Agent/voice/speech_config.py`

```python
ACTIVE_ENGINE = "whisper-local"  # Change here
WHISPER_MODEL_SIZE = "base"      # tiny, base, small, medium, large
```

### Chunking Strategy

**File:** `Agent/chunking/adaptive_chunker.py`

Adaptive based on document size:
- Small (<5K): 500 chars, 50 overlap
- Medium (<20K): 1000 chars, 100 overlap
- Large (<50K): 1500 chars, 200 overlap
- Very large: 2000 chars, 300 overlap

### Hybrid Search Weights

**File:** `Agent/retrieval/hybrid_retriever.py`

```python
vector_weight = 0.7  # 70% semantic
bm25_weight = 0.3    # 30% keyword
```

---

## 🐛 Troubleshooting

### GPU Not Detected

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

**If False:**
```bash
pip uninstall torch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Database Connection Issues

**Check:**
1. DATABASE_* variables in `.env`
2. PostgreSQL is running
3. Test connection: `psql -h HOST -U USER -d DATABASE`

### Supabase Upload Fails

**Check:**
1. SUPABASE_URL and SUPABASE_KEY in `.env`
2. Bucket permissions
3. Bucket name matches SUPABASE_BUCKET_NAME

### Voice Transcription Fails

**Check:**
1. FFmpeg installed: `ffmpeg -version`
2. Whisper installed: `pip list | grep whisper`
3. Audio format supported (MP3, WAV, etc.)

### Poor Search Results

**Solutions:**
1. Re-embed documents with multilingual model
2. Use more detailed queries
3. Check if metadata extraction completed
4. Verify documents are indexed

### Agent Not Responding

**Check:**
1. GOOGLE_API_KEY is valid
2. Documents are indexed
3. Logs in `Agent/agent_logs/`

---

## 📈 Performance Metrics

### Upload Performance
- Small doc (<1MB): 3-5 seconds
- Medium doc (1-5MB): 5-10 seconds
- Large doc (>5MB): 10-20 seconds

### Query Performance
- Metadata search: <1 second
- Embedded doc search: 4-7 seconds
- First-time embedding: 12-19 seconds
- Subsequent queries: 4-7 seconds

### Voice Performance
- Transcription (1 min audio): 5-10 seconds
- Total voice query: 10-20 seconds

### Embedding Performance
- BGE-M3: ~45 chunks/second (GPU)
- Model load: ~10 seconds (one-time)
- Dimension: 1024

---

## 🎯 Best Practices

### 1. Document Upload
- Provide metadata (title, category, department)
- Use descriptive filenames
- Batch upload for multiple documents

### 2. Queries
- Be specific and detailed
- Use natural language
- Include context when needed

### 3. Voice Queries
- Clear audio quality
- Minimal background noise
- Specify language if known

### 4. Multilingual
- Mix languages in queries for better results
- Use cross-lingual search for broader coverage
- Specify language metadata when uploading

### 5. Data Ingestion
- Test connection before registering
- Use read-only database users
- Schedule syncs during off-peak hours
- Monitor sync logs regularly

---

## 📚 Additional Resources

### Documentation Files
- `PROJECT_SUMMARY.md` - Project overview
- `ARCHITECTURE_DIAGRAM.md` - System architecture
- `MULTILINGUAL_EMBEDDINGS_GUIDE.md` - Multilingual features
- `VOICE_QUERY_GUIDE.md` - Voice system details
- `DATA_INGESTION_GUIDE.md` - External data sync
- `TESTING_GUIDE.md` - Testing procedures

### API Documentation
- Interactive docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json

### Logs
- Embeddings: `Agent/agent_logs/embeddings.log`
- Pipeline: `Agent/agent_logs/pipeline.log`
- Retrieval: `Agent/agent_logs/retrieval.log`
- Voice: `Agent/agent_logs/voice.log`
- Agent: `Agent/agent_logs/agent.log`

---

## 🏆 Key Achievements

✅ **Multi-format document processing** (PDF, DOCX, PPTX, Images)  
✅ **Multilingual embeddings** (100+ languages, cross-lingual search)  
✅ **Voice query system** (98+ languages, local + cloud)  
✅ **Lazy RAG** (instant uploads, on-demand embedding)  
✅ **Hybrid retrieval** (semantic + keyword)  
✅ **External data ingestion** (ministry database sync)  
✅ **Citation tracking** (source documents + confidence)  
✅ **Production-ready** (comprehensive testing, logging, monitoring)

---

## 📞 Support

For issues or questions:
1. Check logs in `Agent/agent_logs/`
2. Run tests: `python tests/run_all_tests.py`
3. Review API docs: http://localhost:8000/docs
4. Check this documentation

---

**Built with ❤️ for Government Policy Intelligence**

**Version:** 2.0.0  
**Last Updated:** November 30, 2025  
**Status:** ✅ Production Ready
