# BEACON - Complete Solution for LLM Implementation

## 📋 Purpose of This Document

This document provides a comprehensive solution architecture for building BEACON - an AI-powered Government Policy Intelligence Platform. Use this as a complete prompt for another LLM to build a similar solution aligned with your requirements.

---

## 🎯 System Overview

**BEACON** is an AI-powered document management and policy intelligence platform for the Ministry of Education (MoE) and higher education institutions in India.

### Core Capabilities
1. **Multi-format Document Processing**: PDF, DOCX, PPTX, Images (with OCR)
2. **Multilingual Support**: 100+ languages including Hindi, Tamil, Telugu, Bengali
3. **Voice Queries**: Ask questions via audio (98+ languages)
4. **Smart Search**: Hybrid retrieval (semantic + keyword)
5. **Role-Based Access Control**: Hierarchical permissions system
6. **Approval Workflows**: Multi-level document and user approval
7. **AI Policy Assistant**: Natural language queries with cited sources
8. **Web Scraping**: Automated document discovery from government websites
9. **Real-time Notifications**: Hierarchical notification system

---

## 🏗️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ with pgvector extension
- **ORM**: SQLAlchemy with Alembic migrations
- **Authentication**: JWT tokens with bcrypt password hashing
- **Storage**: Supabase (S3-compatible) for document storage
- **AI/ML**: 
  - Google Gemini 2.0 Flash (LLM for chat)
  - BGE-M3 embeddings (multilingual, 1024-dim vectors)
  - OpenAI Whisper (voice transcription)
  - EasyOCR (image text extraction)
- **Vector Search**: pgvector for similarity search
- **Web Scraping**: BeautifulSoup4, Requests
- **Task Scheduling**: APScheduler

### Frontend
- **Framework**: React 18 with Vite
- **UI Library**: TailwindCSS + shadcn/ui (Radix UI components)
- **State Management**: Zustand
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Notifications**: Sonner (toast notifications)
- **Icons**: Lucide React

---

## 👥 User Roles & Hierarchy

### Role Hierarchy
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

### Business Rules
- **Developer**: Only 1 account system-wide (cannot be deleted)
- **Ministry Admin**: Maximum 5 active accounts
- **University Admin**: 1 per institution
- **Document Officers & Students**: Unlimited

### Permission Matrix
| Feature | Developer | Ministry Admin | University Admin | Document Officer | Student |
|---------|-----------|----------------|------------------|------------------|---------|
| View all documents | ✅ | ✅ | ❌ | ❌ | ❌ |
| View public docs | ✅ | ✅ | ✅ | ✅ | ✅ |
| View institution docs | ✅ | ✅ | ✅ (own) | ✅ (own) | ✅ (own) |
| Upload documents | ✅ | ✅ (auto-approved) | ✅ (needs approval) | ✅ (needs approval) | ❌ |
| Approve documents | ✅ | ✅ | ✅ (institution) | ❌ | ❌ |
| Approve users | ✅ | ✅ (limited) | ✅ (institution) | ❌ | ❌ |
| Manage institutions | ✅ | ✅ | ❌ | ❌ | ❌ |
| System analytics | ✅ | ✅ | ✅ (limited) | ❌ | ❌ |
| AI Chat | ✅ | ✅ | ✅ | ✅ | ✅ |
| Voice Queries | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 📊 Core Features

### 1. Document Management

**Supported Formats**:
- PDF (with OCR for scanned documents)
- DOCX (Microsoft Word)
- PPTX (PowerPoint presentations)
- Images (JPEG, PNG) with OCR
- TXT (plain text)

**Document Lifecycle**:
```
Upload → Draft → Pending Review → Under Review → Approved/Rejected
```

**Visibility Levels**:
- **Public**: Accessible to all authenticated users
- **Institution Only**: Restricted to same institution members
- **Restricted**: Requires specific approval
- **Confidential**: Ministry Admin and Developer only

**Key Features**:
- Drag-and-drop upload
- Automatic metadata extraction (title, description, category, tags)
- Text extraction with OCR fallback for images
- S3 storage with CDN
- Download control (per document)
- Soft delete with audit trail
- Version tracking
- Expiry date management

### 2. Approval Workflows

**Document Approval Flow**:
1. Student/Document Officer uploads → University Admin reviews
2. University Admin uploads → Ministry Admin reviews
3. Ministry Admin uploads → Auto-approved
4. Developer uploads → Auto-approved

**User Approval Flow**:
1. Student registers → University Admin approves
2. Document Officer registers → University Admin approves
3. University Admin registers → Ministry Admin approves
4. Ministry Admin registers → Developer approves

**Approval Actions**:
- Approve (with optional notes)
- Reject (with reason required)
- Request Changes
- Escalate to higher authority

### 3. AI-Powered RAG System

**Architecture**:
```
Query → Embedding → Vector Search (pgvector) → Rerank → LLM → Answer + Citations
```

**Key Features**:
- **Lazy Embedding**: Documents embedded on-demand (first query)
- **Hybrid Search**: Semantic (vector) + keyword (metadata)
- **Role-Based Filtering**: Users only search documents they can access
- **Multi-Machine Support**: Embeddings stored in PostgreSQL
- **Citation Tracking**: Every answer includes source documents
- **Approval Status**: Citations show if document is approved/pending

**Search Tools**:
- `search_documents_lazy()`: Semantic search across all accessible docs
- `search_specific_document_lazy()`: Search within a specific document
- `get_document_metadata()`: Retrieve document details

**Access Control in RAG**:
- Developer: Sees all documents
- Ministry Admin: Public + restricted + all institutions
- University Admin: Public + own institution docs
- Students: Public + own institution's public docs

### 4. Voice Query System

**Supported**:
- 98+ languages with auto-detection
- Audio formats: MP3, WAV, M4A, OGG, FLAC
- Local processing (Whisper) or cloud (Google Speech)

**Workflow**:
```
Audio Upload → Transcription → Text Query → RAG → Answer
```

### 5. Web Scraping System

**Purpose**: Automatically discover and ingest policy documents from government websites

**Key Features**:
- Automated document discovery (PDF, DOCX, PPTX)
- Keyword filtering during scraping (not after)
- Provenance tracking (source, credibility, metadata)
- Full pipeline integration (OCR, metadata extraction, RAG)
- User-friendly UI for managing sources

**Keyword Filtering**:
- Filter documents DURING scraping (saves bandwidth)
- Case-insensitive substring matching
- Multiple keywords support
- Tracks matched keywords per document
- Calculates filtering statistics

**Workflow**:
```
User adds source → Scraper finds documents → Keyword filter → 
Download matching docs → OCR/Extract text → Extract metadata → 
Store in database → Mark for lazy embedding
```

**Credibility Scores**:
- education.gov.in: 10/10 (Ministry of Education)
- ugc.ac.in: 9/10 (UGC)
- *.gov.in: 9/10 (Government domains)
- *.ac.in: 8/10 (Academic institutions)
- default: 5/10 (Unknown sources)

### 6. Notification System

**Hierarchical Routing**:
- Student action → University Admin notified
- Document Officer action → University Admin notified
- University Admin action → Ministry Admin notified
- Ministry Admin action → Developer notified
- Developer sees all notifications

**Priority Levels**:
- 🔥 **Critical**: Security alerts, system failures
- ⚠ **High**: Approval requests, role changes
- 📌 **Medium**: Upload confirmations, reminders
- 📨 **Low**: General info, read receipts

**Features**:
- Real-time toast notifications
- Persistent notification panel
- Grouped by priority
- Action buttons (Approve Now, Review, etc.)
- Mark read/unread
- Auto-expiry
- Polling for updates (30s interval)

### 7. Institution Management

**Features**:
- Create/edit institutions (universities, ministries)
- Link universities to parent ministries
- Domain-based email validation
- Soft delete with cascade handling
- User reassignment on deletion

**Institution Types**:
- **Ministry**: Parent organization (e.g., Ministry of Education)
- **University**: Educational institution linked to ministry

**Domain Management**:
- Whitelist email domains per institution
- Auto-validate user emails during registration
- Prevent unauthorized registrations

### 8. Analytics & Insights

**System Health Dashboard** (Developer Only):
- Component status (Database, S3, Vector Store, LLM)
- Vector store statistics
- Overall health indicator
- Manual refresh

**Analytics Dashboard** (Admin Roles):
- Total documents/users/institutions
- Activity stats (uploads, queries, approvals)
- Most active users
- Recent activity feed
- Time range filtering
- Chat history heatmap

**Audit Logs**:
- All user actions tracked
- Searchable by user, action type, date range
- Export functionality
- Retention policy

---

## 🗄️ Database Schema

### Core Tables

**users**:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    institution_id INTEGER REFERENCES institutions(id),
    approved BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**institutions**:
```sql
CREATE TABLE institutions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    type VARCHAR(50),
    parent_ministry_id INTEGER REFERENCES institutions(id),
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**documents**:
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    file_path TEXT,
    s3_url TEXT,
    extracted_text TEXT,
    visibility_level VARCHAR(50) DEFAULT 'public',
    institution_id INTEGER REFERENCES institutions(id),
    uploader_id INTEGER REFERENCES users(id) NOT NULL,
    approval_status VARCHAR(50) DEFAULT 'pending',
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    requires_moe_approval BOOLEAN DEFAULT FALSE,
    rejection_reason TEXT,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    expiry_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**document_metadata**:
```sql
CREATE TABLE document_metadata (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    title VARCHAR(500),
    description TEXT,
    category VARCHAR(100),
    tags TEXT[],
    language VARCHAR(10) DEFAULT 'en',
    page_count INTEGER,
    file_size BIGINT,
    embedding_status VARCHAR(50) DEFAULT 'pending',
    metadata_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**document_embeddings** (pgvector):
```sql
CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    embedding vector(1024),
    chunk_text TEXT NOT NULL,
    visibility_level VARCHAR(50),
    institution_id INTEGER,
    approval_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_embeddings_vector ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

**notifications**:
```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    action_url TEXT,
    action_label VARCHAR(100),
    action_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);
```

**audit_logs**:
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    action_metadata JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**chat_sessions**:
```sql
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    thread_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**chat_messages**:
```sql
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    citations JSONB,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**scraped_documents**:
```sql
CREATE TABLE scraped_documents (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    source_url TEXT NOT NULL,
    source_page TEXT,
    source_domain VARCHAR(255),
    credibility_score INTEGER,
    scraped_at TIMESTAMP NOT NULL,
    file_hash VARCHAR(64),
    provenance_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📡 API Endpoints

### Authentication (`/api/auth`)
- POST `/register` - User registration
- POST `/login` - User login
- POST `/verify-email/{token}` - Email verification
- GET `/me` - Get current user

### Users (`/api/users`)
- GET `/list` - List users (with filters)
- GET `/pending` - Get pending approvals
- POST `/approve/{user_id}` - Approve user
- POST `/reject/{user_id}` - Reject user
- PATCH `/change-role/{user_id}` - Change user role
- DELETE `/delete/{user_id}` - Delete user

### Documents (`/api/documents`)
- POST `/upload` - Upload document
- GET `/list` - List documents (role-filtered)
- GET `/{doc_id}` - Get document details
- GET `/{doc_id}/download` - Download document
- PATCH `/{doc_id}` - Update document
- DELETE `/{doc_id}` - Delete document
- POST `/{doc_id}/submit-for-review` - Submit for approval

### Approvals (`/api/approvals`)
- GET `/pending` - Get pending documents
- GET `/approved` - Get approved documents
- GET `/rejected` - Get rejected documents
- POST `/{doc_id}/approve` - Approve document
- POST `/{doc_id}/reject` - Reject document

### Chat (`/api/chat`)
- POST `/query` - Ask AI question
- POST `/query/stream` - Streaming response
- GET `/sessions` - Get chat history
- POST `/sessions` - Create new session
- DELETE `/sessions/{session_id}` - Delete session

### Voice (`/api/voice`)
- POST `/query` - Voice query (audio upload)
- POST `/query/stream` - Streaming voice response
- POST `/transcribe` - Transcribe only

### Web Scraping (`/api/web-scraping`)
- POST `/sources` - Create scraping source
- GET `/sources` - List sources
- GET `/sources/{id}` - Get source
- PUT `/sources/{id}` - Update source
- DELETE `/sources/{id}` - Delete source
- POST `/scrape` - Scrape now
- POST `/scrape-and-download` - Scrape and download
- POST `/scrape-and-process` - Full pipeline
- GET `/logs` - Get scraping logs
- GET `/scraped-documents` - Get scraped documents
- GET `/stats` - Get scraping statistics
- POST `/preview` - Preview source
- POST `/validate` - Validate source

### Institutions (`/api/institutions`)
- GET `/list` - List institutions
- POST `/create` - Create institution
- PATCH `/{inst_id}` - Update institution
- DELETE `/{inst_id}` - Delete institution (soft)
- POST `/{inst_id}/domains` - Add email domain

### Notifications (`/api/notifications`)
- GET `/list` - List notifications
- GET `/grouped` - Grouped by priority
- GET `/unread-count` - Unread count
- POST `/{id}/mark-read` - Mark as read
- POST `/mark-all-read` - Mark all read
- DELETE `/{id}` - Delete notification

### Analytics (`/api/analytics`)
- GET `/stats` - System statistics
- GET `/activity` - Activity feed
- GET `/heatmap` - Chat history heatmap
- GET `/system-health` - System health (Developer only)

### Audit (`/api/audit`)
- GET `/logs` - Get audit logs (filtered)

### Bookmarks (`/api/bookmarks`)
- GET `/list` - List user bookmarks
- POST `/add` - Add bookmark
- DELETE `/{id}` - Remove bookmark

---

## 🔐 Security Features

### Authentication & Authorization
- JWT tokens with expiry (default: 24 hours)
- Password hashing with bcrypt
- Email verification required
- Role-based access control (RBAC)
- Route-level protection

### Data Security
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (React escaping)
- CORS configuration
- File upload validation
- Soft deletes (preserve audit trail)

### Access Control
- Document-level permissions
- Institution-based isolation
- Approval workflows
- Audit logging
- IP tracking

### Compliance
- GDPR-ready (soft deletes, data export)
- Audit trail for all actions
- Role-based data access
- Secure file storage (S3)

---

## 📈 Performance Metrics

| Operation | Time | Notes |
|-----------|------|-------|
| Document Upload | 3-7s | Instant response, lazy embedding |
| RAG Query (embedded) | 4-7s | Fast retrieval |
| RAG Query (first time) | 12-19s | Includes embedding |
| Voice Transcription | 5-10s | 1 min audio |
| User Login | <1s | JWT generation |
| Document List | <2s | Paginated |
| Web Scraping | 5-30s | Depends on page size |

---

## 🚀 Implementation Guide

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- Node.js 18+
- Supabase account (or S3-compatible storage)
- Google API key (Gemini)

### Environment Variables

**Backend (.env)**:
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

JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=BEACON System
FRONTEND_URL=http://localhost:5173
```

**Frontend (.env)**:
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### Installation Steps

1. **Backend Setup**:
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. **Enable pgvector**:
```bash
python scripts/enable_pgvector.py
```

3. **Run Migrations**:
```bash
alembic upgrade head
```

4. **Initialize Developer Account**:
```bash
python backend/init_developer.py
```

5. **Start Backend**:
```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

6. **Frontend Setup**:
```bash
cd frontend
npm install
npm run dev
```

7. **Access Application**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📁 Project Structure

```
Beacon/
├── Agent/                      # AI/ML Components
│   ├── embeddings/            # BGE-M3 embeddings
│   ├── voice/                 # Whisper transcription
│   ├── rag_agent/             # ReAct agent
│   ├── retrieval/             # Hybrid search
│   ├── lazy_rag/              # On-demand embedding
│   ├── vector_store/          # pgvector integration
│   ├── tools/                 # Search tools
│   ├── web_scraping/          # Web scraping components
│   │   ├── scraper.py         # Core scraping logic
│   │   ├── keyword_filter.py  # Keyword filtering
│   │   ├── pdf_downloader.py  # Document download
│   │   ├── provenance_tracker.py  # Source tracking
│   │   ├── web_source_manager.py  # Orchestration
│   │   └── web_scraping_processor.py  # Pipeline integration
│   └── data_ingestion/        # External DB sync
│
├── backend/                    # FastAPI Backend
│   ├── routers/               # API endpoints
│   │   ├── auth_router.py
│   │   ├── user_router.py
│   │   ├── document_router.py
│   │   ├── approval_router.py
│   │   ├── chat_router.py
│   │   ├── voice_router.py
│   │   ├── institution_router.py
│   │   ├── notification_router.py
│   │   ├── analytics_router.py
│   │   ├── audit_router.py
│   │   ├── bookmark_router.py
│   │   └── web_scraping_router_temp.py
│   ├── utils/                 # Helper functions
│   │   ├── text_extractor.py
│   │   ├── supabase_storage.py
│   │   ├── email_service.py
│   │   └── notification_helper.py
│   ├── database.py            # SQLAlchemy models
│   ├── main.py                # FastAPI app
│   └── init_developer.py      # Initial setup
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   │   ├── layout/        # Header, Sidebar, Footer
│   │   │   ├── ui/            # shadcn components
│   │   │   ├── documents/     # Document cards, upload
│   │   │   ├── chat/          # Chat interface
│   │   │   └── notifications/ # Notification panel
│   │   ├── pages/             # Route pages
│   │   │   ├── admin/         # Admin dashboards
│   │   │   │   ├── WebScrapingPage.jsx
│   │   │   │   ├── UserManagementPage.jsx
│   │   │   │   ├── InstitutionsPage.jsx
│   │   │   │   └── AnalyticsPage.jsx
│   │   │   ├── documents/     # Document management
│   │   │   ├── auth/          # Login, register
│   │   │   └── AIChatPage.jsx # AI chat
│   │   ├── services/          # API calls
│   │   │   └── api.js
│   │   ├── stores/            # Zustand stores
│   │   │   ├── authStore.js
│   │   │   ├── themeStore.js
│   │   │   └── chatStore.js
│   │   ├── hooks/             # Custom hooks
│   │   ├── utils/             # Helper functions
│   │   ├── App.jsx            # Main app
│   │   └── main.jsx           # Entry point
│   └── package.json
│
├── alembic/                    # Database migrations
├── scripts/                    # Utility scripts
├── tests/                      # Test suite
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
└── README.md                   # Documentation
```

---

## 🎯 Key Implementation Details

### 1. Lazy RAG Architecture

**Problem**: Embedding 1000+ documents upfront takes hours
**Solution**: Lazy embedding - embed on first query

**Implementation**:
```python
# On document upload
document.embedding_status = 'pending'  # Don't embed yet

# On first query
if document.embedding_status == 'pending':
    embeddings = embed_document(document.text)
    store_embeddings(embeddings)
    document.embedding_status = 'completed'
```

**Benefits**:
- Instant document uploads (3-7s instead of 30-60s)
- Embeddings only for queried documents
- Multi-machine support (stored in PostgreSQL)

### 2. Keyword Filtering During Scraping

**Problem**: Downloading 1000+ documents wastes bandwidth
**Solution**: Filter DURING scraping, not after

**Implementation**:
```python
# In WebScraper.find_document_links()
keyword_filter = KeywordFilter(keywords)

for link in soup.find_all('a', href=True):
    if is_document(link):
        link_text = link.get_text()
        match_result = keyword_filter.evaluate(link_text)
        
        if match_result['matches']:
            documents.append({
                'url': link['href'],
                'matched_keywords': match_result['matched_keywords']
            })
```

**Benefits**:
- 70% reduction in downloads (based on 30% match rate)
- 70% reduction in processing time
- 70% reduction in storage

### 3. Role-Based Document Access

**Problem**: Users shouldn't see documents they can't access
**Solution**: Filter at database query level

**Implementation**:
```python
def get_accessible_documents(user):
    if user.role == 'developer':
        return Document.query.all()
    elif user.role == 'ministry_admin':
        return Document.query.filter(
            or_(
                Document.visibility_level == 'public',
                Document.visibility_level == 'restricted'
            )
        ).all()
    elif user.role == 'university_admin':
        return Document.query.filter(
            or_(
                Document.visibility_level == 'public',
                and_(
                    Document.institution_id == user.institution_id,
                    Document.visibility_level == 'institution_only'
                )
            )
        ).all()
    # ... etc
```

### 4. Hierarchical Notifications

**Problem**: Admins need to know about actions in their hierarchy
**Solution**: Route notifications based on role hierarchy

**Implementation**:
```python
def notify_hierarchy(action, actor):
    if actor.role == 'student':
        notify_user(actor.institution.university_admin)
    elif actor.role == 'university_admin':
        notify_user(ministry_admin)
    elif actor.role == 'ministry_admin':
        notify_user(developer)
```

### 5. Provenance Tracking

**Problem**: Need to know where documents came from
**Solution**: Track source, credibility, and metadata

**Implementation**:
```python
provenance = {
    'source_url': document_url,
    'source_domain': 'ugc.gov.in',
    'credibility_score': 9,
    'source_type': 'government',
    'scraped_at': datetime.now(),
    'matched_keywords': ['policy', 'circular'],
    'verified': True
}
```

---

## 🧪 Testing Strategy

### Unit Tests
- Test individual functions and classes
- Mock external dependencies
- Focus on edge cases

### Integration Tests
- Test API endpoints
- Test database operations
- Test file uploads/downloads

### Property-Based Tests
- Test with random inputs
- Verify invariants hold
- Use Hypothesis library

### Manual Testing
- Test user workflows
- Test role-based access
- Test approval workflows
- Test web scraping

---

## 📚 Additional Resources

### Documentation Files in Workspace
- `PROJECT_DESCRIPTION.md` - Comprehensive technical documentation
- `PROJECT_OVERVIEW.md` - System overview
- `README.md` - Quick start guide
- `WEB_SCRAPING_TECHNICAL_DOCUMENTATION.md` - Web scraping details
- `KEYWORD_FILTERING_IMPLEMENTATION_SUMMARY.md` - Filtering implementation
- `1000_DOCUMENTS_IMPLEMENTATION_PLAN.md` - Scaling to 1000+ documents
- `WORKFLOWS_AND_FEATURES.md` - Detailed workflows
- `TECHNICAL_REFERENCE.md` - Technical details

### Phase Documentation
- `PHASE_1_SETUP_AND_AUTHENTICATION.md` - Auth setup
- `PHASE_2_DOCUMENT_MANAGEMENT.md` - Document workflows
- `PHASE_3_INSTITUTION_AND_ROLE_MANAGEMENT.md` - Institution management
- `PHASE_4_ADVANCED_FEATURES_AND_OPTIMIZATIONS.md` - Advanced features

---

## 🎯 Success Criteria

### Functional Requirements
- ✅ Multi-format document processing
- ✅ Multilingual embeddings (100+ languages)
- ✅ Voice query system (98+ languages)
- ✅ Lazy RAG (instant uploads)
- ✅ Hybrid retrieval (semantic + keyword)
- ✅ Web scraping with keyword filtering
- ✅ Role-based access control
- ✅ Approval workflows
- ✅ Citation tracking
- ✅ Real-time notifications

### Non-Functional Requirements
- ✅ Document upload: <7s
- ✅ RAG query (embedded): <7s
- ✅ RAG query (first time): <20s
- ✅ Voice transcription: <10s
- ✅ User login: <1s
- ✅ Document list: <2s
- ✅ Web scraping: <30s per source

### Security Requirements
- ✅ JWT authentication
- ✅ Email verification
- ✅ Role-based access control
- ✅ Document-level permissions
- ✅ Audit logging
- ✅ SQL injection prevention
- ✅ XSS protection

---

## 🚀 Deployment Considerations

### Production Checklist
- [ ] Set up production database (PostgreSQL with pgvector)
- [ ] Configure Supabase storage
- [ ] Set up Google Gemini API
- [ ] Configure email service (SMTP)
- [ ] Set up domain and SSL
- [ ] Configure CORS for production domain
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline
- [ ] Load testing
- [ ] Security audit

### Scaling Considerations
- Use Redis for caching
- Use Elasticsearch for full-text search
- Use CDN for static assets
- Implement load balancing
- Use database read replicas
- Optimize vector index (HNSW)
- Implement rate limiting
- Use connection pooling

---

## 📞 Support & Maintenance

### Monitoring
- System health dashboard
- Error logging
- Performance metrics
- User activity tracking
- Audit logs

### Maintenance Tasks
- Database backups (daily)
- Log rotation (weekly)
- Cleanup old files (monthly)
- Update dependencies (monthly)
- Security patches (as needed)

---

## 🎉 Conclusion

This document provides a complete solution architecture for building BEACON. Use this as a comprehensive prompt for another LLM to build a similar system aligned with your requirements.

**Key Takeaways**:
1. Lazy RAG for instant uploads
2. Keyword filtering during scraping
3. Role-based access control
4. Hierarchical notifications
5. Provenance tracking
6. Multi-format document processing
7. Multilingual support
8. Voice queries
9. Web scraping automation
10. Production-ready architecture

**Status**: ✅ Production Ready  
**Version**: 2.0.0  
**Last Updated**: December 8, 2025

---

**Built with ❤️ for Government Policy Intelligence**
