# 🎯 BEACON - Government Policy Intelligence Platform

**AI-powered platform for Ministry of Education (MoE) and Higher-Education institutions to retrieve, understand, compare, explain, and audit government policies.**

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![Version](https://img.shields.io/badge/version-2.0.0-blue)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![React](https://img.shields.io/badge/react-18-blue)]()

---

## 📚 Documentation Structure

This project uses a **phase-based documentation system** for better organization:

### Core Documentation

- **README.md** (this file) - Quick start and overview
- **PROJECT_DESCRIPTION.md** - Comprehensive technical documentation

### Phase Documentation

1. **PHASE_1_SETUP_AND_AUTHENTICATION.md** (7 documents)
   - Email verification system
   - Two-step registration
   - University email domain validation
   - Authentication setup guides

2. **PHASE_2_DOCUMENT_MANAGEMENT.md** (15 documents)
   - Document approval workflows
   - Draft and review processes
   - Access control and security
   - Status visibility and badges
   - Search and sorting features

3. **PHASE_3_INSTITUTION_AND_ROLE_MANAGEMENT.md** (22 documents)
   - Institution hierarchy management
   - Ministry and university relationships
   - Role-based permissions
   - Institution deletion workflows
   - User management strategies

4. **PHASE_4_ADVANCED_FEATURES_AND_OPTIMIZATIONS.md** (61 documents)
   - Chat system and voice queries
   - Notification system
   - RAG and vector store optimizations
   - Performance improvements (Redis, caching, indexing)
   - External data sources
   - Analytics and insights
   - UI/UX fixes and enhancements
   - Security audits and fixes

---

## ✨ Key Features

### Document Management
- 📄 **Multi-format Support:** PDF, DOCX, PPTX, Images (with OCR)
- 🔍 **Smart Search:** Hybrid retrieval (semantic + keyword)
- ⚡ **Lazy RAG:** Instant uploads, on-demand embedding
- 📚 **Citation Tracking:** All answers include source documents
- 🔐 **Role-Based Access:** Hierarchical document visibility

### AI-Powered Intelligence
- 🤖 **AI Chat Assistant:** Natural language queries with cited sources
- 🎤 **Voice Queries:** Ask questions via audio (98+ languages)
- 🌍 **Multilingual:** 100+ languages including Hindi, Tamil, Telugu, Bengali
- 📊 **Policy Analysis:** Compare documents, detect conflicts, check compliance

### User & Institution Management
- 👥 **Role Hierarchy:** Developer → Ministry Admin → University Admin → Document Officer → Student
- 🏛️ **Institution Types:** Universities, Hospitals, Research Centers, Defense Academies
- ✅ **Approval Workflows:** Multi-level document and user approval system
- 📧 **Email Verification:** Secure two-step registration process

### Advanced Features
- 🔔 **Real-time Notifications:** Hierarchical notification routing
- 📈 **Analytics Dashboard:** System health, activity tracking, user insights
- 🔗 **External Data Sync:** Connect to ministry databases
- 🎨 **Theme Support:** Light/dark mode with persistent preferences

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- Node.js 18+
- Supabase account (or S3-compatible storage)
- Google API key (Gemini)

### 1. Clone Repository

```bash
git clone <repository-url>
cd Beacon__V1
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file in root directory:

```env
# Database
DATABASE_HOSTNAME=your-db-host
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USERNAME=your-username
DATABASE_PASSWORD=your-password

# Supabase Storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
SUPABASE_BUCKET_NAME=Docs

# AI Service
GOOGLE_API_KEY=your-google-api-key

# JWT Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Email (Optional - for verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=BEACON System
FRONTEND_URL=http://localhost:5173

# Redis (Optional - for caching)
REDIS_URL=redis://localhost:6379
```

### 4. Database Setup

```bash
# Enable pgvector extension
python scripts/enable_pgvector.py

# Run migrations
alembic upgrade head

# Initialize developer account (optional)
python backend/init_developer.py
```

### 5. Start Backend

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Backend will be available at: http://localhost:8000

### 6. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_BASE_URL=http://localhost:8000/api" > .env

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:5173

---

## 🏗️ System Architecture

### Technology Stack

**Backend:**
- FastAPI (Python 3.11+)
- PostgreSQL with pgvector extension
- SQLAlchemy ORM
- Alembic migrations
- JWT authentication

**Frontend:**
- React 18 with Vite
- TailwindCSS + shadcn/ui components
- Zustand state management
- React Router v6
- Axios for API calls

**AI/ML:**
- Google Gemini 2.0 Flash (LLM)
- BGE-M3 embeddings (multilingual, 1024-dim)
- OpenAI Whisper (voice transcription)
- EasyOCR (image text extraction)
- pgvector (vector similarity search)

**Storage:**
- Supabase S3 (document storage)
- PostgreSQL (metadata + embeddings)

### RAG Architecture

```
Upload → Process → Extract Metadata → Store
                                        ↓
Query → Search Metadata → Rerank → Embed (if needed) → Search → Answer + Citations
```

**Lazy Embedding Strategy:**
- Documents uploaded instantly (no waiting for embedding)
- Embeddings generated on first query
- Subsequent queries use cached embeddings
- Multi-machine support via PostgreSQL storage

---

## 👥 User Roles & Hierarchy

```
Developer (Super Admin)
    ↓
Ministry Admin (MoE Officials)
    ↓
University Admin (Institution Heads)
    ↓
Document Officer (Upload/Manage Docs)
    ↓
Student (Read-Only Access)
    ↓
Public Viewer (Limited Access)
```

### Role Permissions

| Feature | Developer | Ministry Admin | University Admin | Document Officer | Student |
|---------|-----------|----------------|------------------|------------------|---------|
| View all documents | ✅ | ✅ (restricted) | ✅ (institution) | ✅ (institution) | ✅ (public) |
| Upload documents | ✅ | ✅ (auto-approved) | ✅ (needs approval) | ✅ (needs approval) | ❌ |
| Approve documents | ✅ | ✅ | ✅ (institution) | ❌ | ❌ |
| Manage users | ✅ | ✅ (limited) | ✅ (institution) | ❌ | ❌ |
| System health | ✅ | ❌ | ❌ | ❌ | ❌ |
| Analytics | ✅ | ✅ | ✅ (institution) | ❌ | ❌ |

---

## 📡 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/verify-email/{token}` - Email verification
- `GET /api/auth/me` - Get current user

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/list` - List documents (role-filtered)
- `GET /api/documents/{id}` - Get document details
- `GET /api/documents/{id}/download` - Download document
- `DELETE /api/documents/{id}` - Delete document

### Approvals
- `GET /api/approvals/pending` - Get pending documents
- `POST /api/approvals/{id}/approve` - Approve document
- `POST /api/approvals/{id}/reject` - Reject document

### Chat & AI
- `POST /api/chat/query` - Ask AI question
- `POST /api/voice/query` - Voice query (audio upload)
- `GET /api/chat/sessions` - Get chat history

### Institutions
- `GET /api/institutions/list` - List institutions
- `POST /api/institutions/create` - Create institution
- `DELETE /api/institutions/{id}` - Delete institution

### Notifications
- `GET /api/notifications/list` - List notifications
- `GET /api/notifications/unread-count` - Unread count
- `POST /api/notifications/{id}/mark-read` - Mark as read

### Analytics
- `GET /api/analytics/stats` - System statistics
- `GET /api/analytics/activity` - Activity feed
- `GET /api/audit/logs` - Audit logs

**Full API Documentation:** http://localhost:8000/docs

---

## 🧪 Testing

```bash
# Run all tests
python tests/run_all_tests.py

# Individual tests
python tests/test_embeddings.py
python tests/test_voice_query.py
python tests/test_multilingual_embeddings.py
python tests/test_compliance_api.py
python tests/test_conflict_detection_api.py
```

---

## 📊 Performance Metrics

| Operation | Time | Notes |
|-----------|------|-------|
| Document Upload | 3-7s | Instant response |
| Query (embedded) | 4-7s | Fast |
| Query (first time) | 12-19s | Includes embedding |
| Voice transcription | 5-10s | 1 min audio |
| User Login | <1s | JWT generation |

---

## 🔐 Security Features

- ✅ JWT-based authentication
- ✅ Email verification required
- ✅ Role-based access control (RBAC)
- ✅ Document-level permissions
- ✅ Audit logging for all actions
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ XSS protection (React escaping)
- ✅ Soft deletes (preserve audit trail)

---

## 📁 Project Structure

```
Beacon__V1/
├── Agent/                      # AI/ML Components
│   ├── embeddings/            # BGE-M3 embeddings
│   ├── voice/                 # Whisper transcription
│   ├── rag_agent/             # ReAct agent
│   ├── retrieval/             # Hybrid search
│   ├── lazy_rag/              # On-demand embedding
│   ├── vector_store/          # pgvector integration
│   └── tools/                 # Search tools
│
├── backend/                    # FastAPI Backend
│   ├── routers/               # API endpoints
│   ├── utils/                 # Helper functions
│   ├── database.py            # SQLAlchemy models
│   └── main.py                # FastAPI app
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── pages/             # Route pages
│   │   ├── services/          # API calls
│   │   └── stores/            # Zustand stores
│   └── package.json
│
├── alembic/                    # Database migrations
├── scripts/                    # Utility scripts
├── tests/                      # Test suite
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── PROJECT_DESCRIPTION.md      # Detailed documentation
```

---

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
psql -h HOST -U USER -d DATABASE

# Verify .env file has correct credentials
# Test connection: python test_redis_connection.py
```

### GPU Not Detected
```bash
# Install PyTorch with CUDA support
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### Voice Not Working
```bash
# Install FFmpeg
# Windows: Download from https://ffmpeg.org/download.html
# Linux: sudo apt install ffmpeg
# Mac: brew install ffmpeg
```

### Email Verification Not Sending
```bash
# For Gmail:
# 1. Enable 2-Factor Authentication
# 2. Generate App Password: https://myaccount.google.com/apppasswords
# 3. Use App Password as SMTP_PASSWORD in .env
```

---

## 🔄 Recent Updates

### Version 2.0.0 (December 2025)
- ✅ Migrated from FAISS to pgvector for multi-machine support
- ✅ Implemented lazy RAG for instant document uploads
- ✅ Added email verification system
- ✅ Enhanced notification system with hierarchical routing
- ✅ Improved analytics dashboard with system health monitoring
- ✅ Optimized performance with Redis caching
- ✅ Added voice query support (98+ languages)
- ✅ Implemented document approval workflows
- ✅ Enhanced role-based access control

---

## 📞 Support

- **Documentation:** See phase documentation files for detailed guides
- **API Docs:** http://localhost:8000/docs
- **Logs:** `Agent/agent_logs/`
- **Tests:** `python tests/run_all_tests.py`

---

## 🎯 Key Achievements

✅ Multi-format document processing  
✅ Multilingual embeddings (100+ languages)  
✅ Voice query system (98+ languages)  
✅ Lazy RAG (instant uploads)  
✅ Hybrid retrieval (semantic + keyword)  
✅ External data ingestion  
✅ Citation tracking  
✅ Production-ready  

---

**Built with ❤️ for Government Policy Intelligence**

**Version:** 2.0.0 | **Status:** ✅ Production Ready | **Last Updated:** December 5, 2025
