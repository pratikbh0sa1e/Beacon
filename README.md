# 🎯 BEACON - Government Policy Intelligence Platform

**AI-powered platform for Ministry of Education (MoE) and Higher-Education bodies to retrieve, understand, compare, explain, and audit government policies.**

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![Version](https://img.shields.io/badge/version-2.0.0-blue)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()

---

## ✨ Key Features

- 📄 **Multi-format Support:** PDF, DOCX, PPTX, Images (with OCR)
- 🌍 **Multilingual:** 100+ languages including Hindi, Tamil, Telugu, Bengali
- 🎤 **Voice Queries:** Ask questions via audio (MP3, WAV, etc.)
- 🔍 **Smart Search:** Hybrid retrieval (semantic + keyword)
- ⚡ **Lazy RAG:** Instant uploads, on-demand embedding
- 🔗 **External Data Sync:** Connect to ministry databases
- 📚 **Citation Tracking:** All answers include source documents

---

## 🚀 Quick Start

### 1. Install

```bash
# Clone and setup
git clone <repository-url>
cd Beacon__V1
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Install voice dependencies
pip install openai-whisper ffmpeg-python
```

### 2. Configure

Create `.env` file:
```env
DATABASE_HOSTNAME=your-db-host
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USERNAME=your-username
DATABASE_PASSWORD=your-password

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
SUPABASE_BUCKET_NAME=Docs

GOOGLE_API_KEY=your-google-api-key
```

### 3. Run

```bash
# Setup database
alembic upgrade head

# Start server
uvicorn backend.main:app --reload
```

### 4. Use

- **API Docs:** http://localhost:8000/docs
- **Upload:** `POST /documents/upload`
- **Query:** `POST /chat/query`
- **Voice:** `POST /voice/query`

---

## 📚 Documentation

**Complete Guide:** See [`COMPLETE_DOCUMENTATION.md`](COMPLETE_DOCUMENTATION.md) for:
- Detailed setup instructions
- Architecture overview
- API reference
- Multilingual support
- Voice query system
- Data ingestion
- Testing procedures
- Configuration options
- Troubleshooting

---

## 🏗️ Architecture

```
Upload → Process → Extract Metadata → Store
                                        ↓
Query → Search Metadata → Rerank → Embed (if needed) → Search → Answer + Citations
```

**Technology Stack:**
- Backend: FastAPI, PostgreSQL, SQLAlchemy
- Storage: Supabase (S3 + PostgreSQL)
- Embeddings: BGE-M3 (multilingual, 1024-dim)
- Vector Store: FAISS
- LLM: Google Gemini 2.0 Flash
- Voice: OpenAI Whisper (local) / Google Cloud Speech
- OCR: EasyOCR

---

## 📡 API Examples

### Upload Document
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@policy.pdf" \
  -F "title=Education Policy 2025"
```

### Ask Question
```bash
curl -X POST "http://localhost:8000/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the policy guidelines?"}'
```

### Voice Query
```bash
curl -X POST "http://localhost:8000/voice/query" \
  -F "audio=@question.mp3"
```

---

## 🧪 Testing

```bash
# Run all tests
python tests/run_all_tests.py

# Individual tests
python tests/test_embeddings.py
python tests/test_voice_query.py
python tests/test_multilingual_embeddings.py
```

---

## 🌍 Multilingual Support

**Supported Languages:** 100+ including:
- English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Urdu
- Spanish, French, German, Chinese, Japanese, Arabic, and more

**Cross-lingual Search:** Query in English, find Hindi documents (and vice versa)!

---

## 🎤 Voice Queries

**Supported Formats:** MP3, WAV, M4A, OGG, FLAC

**Languages:** 98+ languages with automatic detection

**Engines:**
- Whisper (Local) - Free, private, GPU-accelerated
- Google Cloud Speech - Cloud-based, high quality

---

## 📊 Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Upload | 3-7s | Instant response |
| Query (embedded) | 4-7s | Fast |
| Query (first time) | 12-19s | Includes embedding |
| Voice transcription | 5-10s | 1 min audio |

---

## 🔧 Configuration

### Switch Embedding Model
Edit `Agent/embeddings/embedding_config.py`:
```python
ACTIVE_MODEL = "bge-m3"  # Multilingual (current)
# ACTIVE_MODEL = "bge-large-en"  # English-only
```

### Switch Voice Engine
Edit `Agent/voice/speech_config.py`:
```python
ACTIVE_ENGINE = "whisper-local"  # Local (free)
# ACTIVE_ENGINE = "google-cloud"  # Cloud (paid)
```

---

## 📁 Project Structure

```
Beacon__V1/
├── Agent/                  # AI components
│   ├── embeddings/        # BGE-M3, Gemini
│   ├── voice/             # Whisper, Google Speech
│   ├── rag_agent/         # ReAct agent
│   ├── retrieval/         # Hybrid search
│   ├── lazy_rag/          # On-demand embedding
│   └── data_ingestion/    # External DB sync
├── backend/               # FastAPI server
│   ├── routers/          # API endpoints
│   └── utils/            # Text extraction, storage
├── tests/                # Test suite
├── scripts/              # Utility scripts
└── COMPLETE_DOCUMENTATION.md  # Full guide
```

---

## 🐛 Troubleshooting

**GPU not detected:**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

**Voice not working:**
```bash
# Install FFmpeg
# Windows: Download from https://ffmpeg.org/download.html
# Linux: sudo apt install ffmpeg
# Mac: brew install ffmpeg
```

**Database connection issues:**
- Check `.env` file
- Verify PostgreSQL is running
- Test connection: `psql -h HOST -U USER -d DATABASE`

**More help:** See [`COMPLETE_DOCUMENTATION.md`](COMPLETE_DOCUMENTATION.md)

---

## 🏆 Key Achievements

✅ Multi-format document processing  
✅ Multilingual embeddings (100+ languages)  
✅ Voice query system (98+ languages)  
✅ Lazy RAG (instant uploads)  
✅ Hybrid retrieval (semantic + keyword)  
✅ External data ingestion  
✅ Citation tracking  
✅ Production-ready

---

## 📞 Support

- **Documentation:** [`COMPLETE_DOCUMENTATION.md`](COMPLETE_DOCUMENTATION.md)
- **API Docs:** http://localhost:8000/docs
- **Logs:** `Agent/agent_logs/`
- **Tests:** `python tests/run_all_tests.py`

---

**Built with ❤️ for Government Policy Intelligence**

**Version:** 2.0.0 | **Status:** ✅ Production Ready | **Last Updated:** November 30, 2025
