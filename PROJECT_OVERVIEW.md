# BEACON - Government Policy Intelligence Platform

## Complete Project Overview

**Version**: 2.0.0  
**Status**: Production Ready  
**Last Updated**: December 4, 2025

---

## 📋 Executive Summary

BEACON is an AI-powered document management and policy intelligence platform designed for the Ministry of Education (MoE) and higher education institutions in India. It provides secure document storage, intelligent search, role-based access control, and AI-powered policy analysis through a sophisticated RAG (Retrieval-Augmented Generation) system.

### Key Capabilities

- **Multi-format Document Processing**: PDF, DOCX, PPTX, Images (with OCR)
- **Multilingual Support**: 100+ languages including Hindi, Tamil, Telugu, Bengali
- **Voice Queries**: Ask questions via audio (98+ languages)
- **Smart Search**: Hybrid retrieval (semantic + keyword)
- **Role-Based Access Control**: Hierarchical permissions system
- **Approval Workflows**: Multi-level document and user approval
- **AI Policy Assistant**: Natural language queries with cited sources
- **External Data Integration**: Connect to ministry databases
- **Real-time Notifications**: Hierarchical notification system

---

## 🏗️ System Architecture

### Technology Stack

**Backend**:

- FastAPI (Python 3.11+)
- PostgreSQL with pgvector extension
- SQLAlchemy ORM
- Alembic migrations
- JWT authentication

**Frontend**:

- React 18 with Vite
- TailwindCSS + shadcn/ui components
- Zustand state management
- React Router v6
- Axios for API calls

**AI/ML Components**:

- Google Gemini 2.0 Flash (LLM)
- BGE-M3 embeddings (multilingual, 1024-dim)
- OpenAI Whisper (voice transcription)
- EasyOCR (image text extraction)
- pgvector (vector similarity search)

**Storage**:

- Supabase S3 (document storage)
- PostgreSQL (metadata + embeddings)

### Architecture Diagram

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
                                     │ pgvector  │
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

---

## 👥 User Roles & Permissions

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

### Role Capabilities

| Feature               | Developer | Ministry Admin | University Admin | Document Officer | Student  | Public Viewer |
| --------------------- | --------- | -------------- | ---------------- | ---------------- | -------- | ------------- |
| View All Documents    | ✅        | ✅             | ❌               | ❌               | ❌       | ❌            |
| View Public Docs      | ✅        | ✅             | ✅               | ✅               | ✅       | ✅            |
| View Institution Docs | ✅        | ✅             | ✅ (own)         | ✅ (own)         | ✅ (own) | ❌            |
| Upload Documents      | ✅        | ✅             | ✅               | ✅               | ❌       | ❌            |
| Auto-Approve Upload   | ✅        | ✅             | ❌               | ❌               | ❌       | ❌            |
| Approve Documents     | ✅        | ✅             | ✅ (limited)     | ❌               | ❌       | ❌            |
| Approve Users         | ✅        | ✅ (limited)   | ✅ (limited)     | ❌               | ❌       | ❌            |
| Manage Institutions   | ✅        | ✅             | ❌               | ❌               | ❌       | ❌            |
| System Analytics      | ✅        | ✅             | ✅ (limited)     | ❌               | ❌       | ❌            |
| AI Chat               | ✅        | ✅             | ✅               | ✅               | ✅       | ✅ (limited)  |
| Voice Queries         | ✅        | ✅             | ✅               | ✅               | ✅       | ❌            |
| Bookmarks             | ✅        | ✅             | ✅               | ✅               | ✅       | ❌            |
| Personal Notes        | ✅        | ✅             | ✅               | ✅               | ✅       | ❌            |

### Business Rules

- **Developer**: Only 1 account system-wide (cannot be deleted)
- **Ministry Admin**: Maximum 5 active accounts
- **University Admin**: 1 per institution
- **Document Officers**: Unlimited
- **Students**: Unlimited

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

**Features**:

- Drag-and-drop upload
- Metadata extraction (title, description, version)
- Text extraction with OCR fallback
- S3 storage with CDN
- Download control (per document)
- Soft delete with audit trail
- Version tracking
- Expiry date management

### 2. Approval Workflows

**Document Approval Flow**:

1. **Student/Document Officer** uploads → **University Admin** reviews
2. **University Admin** uploads → **Ministry Admin** reviews
3. **Ministry Admin** uploads → Auto-approved
4. **Developer** uploads → Auto-approved

**User Approval Flow**:

1. **Student** registers → **University Admin** approves
2. **Document Officer** registers → **University Admin** approves
3. **University Admin** registers → **Ministry Admin** approves
4. **Ministry Admin** registers → **Developer** approves

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

**Features**:

- **Lazy Embedding**: Documents embedded on-demand (first query)
- **Hybrid Search**: Semantic (vector) + keyword (metadata)
- **Role-Based Filtering**: Users only search documents they can access
- **Multi-Machine Support**: Embeddings stored in PostgreSQL (not local files)
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

**Features**:

- Real-time transcription
- Language detection
- Fallback to text if transcription fails
- Same RAG pipeline as text queries

### 5. Notification System

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

### 6. Institution Management

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

### 7. Analytics & Insights

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
- Chat history heatmap (visual activity calendar)

**Audit Logs**:

- All user actions tracked
- Searchable by user, action type, date range
- Export functionality
- Retention policy

### 8. External Data Sources

**Features**:

- Connect to ministry databases
- Scheduled sync jobs (daily at 2 AM)
- API integration support
- Request/approval workflow
- Data classification (public, educational, confidential, institutional)
- Encrypted credentials
- Sync logs and monitoring

**Workflow**:

1. Ministry/University Admin submits request
2. Developer reviews and approves/rejects
3. Auto-sync starts on approval
4. Documents inherit visibility based on classification

---

## 🗄️ Database Schema

### Core Tables

**users**:

- id, name, email, password_hash
- role, institution_id, approved
- email_verified, verification_token
- created_at, updated_at

**institutions**:

- id, name, location, type
- parent_ministry_id
- deleted_at, deleted_by

**documents**:

- id, filename, file_type, file_path, s3_url
- extracted_text, visibility_level
- institution_id, uploader_id
- approval_status, approved_by, approved_at
- requires_moe_approval, rejection_reason
- uploaded_at, expiry_date

**document_metadata**:

- id, document_id
- title, description, department, document_type
- keywords, summary, key_topics, entities
- embedding_status, metadata_status
- bm25_keywords, text_length

**document_embeddings** (pgvector):

- id, document_id, chunk_index
- embedding (vector 1024)
- chunk_text
- visibility_level, institution_id, approval_status

**notifications**:

- id, user_id, title, message, type
- priority, read, read_at
- action_url, action_label, action_metadata
- created_at, expires_at

**audit_logs**:

- id, user_id, action, action_metadata
- timestamp

**bookmarks**:

- id, user_id, document_id
- created_at

**chat_sessions**:

- id, user_id, title, thread_id
- created_at, updated_at

**chat_messages**:

- id, session_id, role (user/assistant)
- content, citations, confidence
- created_at

**external_data_sources**:

- id, name, ministry_name, description
- db_type, host, port, database_name
- username, password_encrypted
- institution_id, requested_by_user_id, approved_by_user_id
- request_status, data_classification
- sync_enabled, sync_frequency, last_sync_at

**user_notes**:

- id, user_id, document_id
- title, content, tags
- is_pinned, color
- created_at, updated_at

---

## 📡 API Endpoints

### Authentication (`/auth`)

- POST `/register` - User registration
- POST `/login` - User login
- POST `/verify-email/{token}` - Email verification
- GET `/me` - Get current user

### Users (`/users`)

- GET `/list` - List users (with filters)
- GET `/pending` - Get pending approvals
- POST `/approve/{user_id}` - Approve user
- POST `/reject/{user_id}` - Reject user
- PATCH `/change-role/{user_id}` - Change user role
- DELETE `/delete/{user_id}` - Delete user

### Documents (`/documents`)

- POST `/upload` - Upload document
- GET `/list` - List documents (role-filtered)
- GET `/{doc_id}` - Get document details
- GET `/{doc_id}/download` - Download document
- PATCH `/{doc_id}` - Update document
- DELETE `/{doc_id}` - Delete document
- POST `/{doc_id}/submit-for-review` - Submit for approval

### Approvals (`/approvals`)

- GET `/pending` - Get pending documents
- GET `/approved` - Get approved documents
- GET `/rejected` - Get rejected documents
- POST `/{doc_id}/approve` - Approve document
- POST `/{doc_id}/reject` - Reject document

### Chat (`/chat`)

- POST `/query` - Ask AI question
- POST `/query/stream` - Streaming response
- GET `/sessions` - Get chat history
- POST `/sessions` - Create new session
- DELETE `/sessions/{session_id}` - Delete session

### Voice (`/voice`)

- POST `/query` - Voice query (audio upload)
- POST `/query/stream` - Streaming voice response
- POST `/transcribe` - Transcribe only

### Institutions (`/institutions`)

- GET `/list` - List institutions
- POST `/create` - Create institution
- PATCH `/{inst_id}` - Update institution
- DELETE `/{inst_id}` - Delete institution (soft)
- POST `/{inst_id}/domains` - Add email domain

### Notifications (`/notifications`)

- GET `/list` - List notifications
- GET `/grouped` - Grouped by priority
- GET `/unread-count` - Unread count
- POST `/{id}/mark-read` - Mark as read
- POST `/mark-all-read` - Mark all read
- DELETE `/{id}` - Delete notification

### Analytics (`/insights`)

- GET `/stats` - System statistics
- GET `/activity` - Activity feed
- GET `/heatmap` - Chat history heatmap
- GET `/system-health` - System health (Developer only)

### Data Sources (`/data-sources`)

- POST `/request` - Submit data source request
- GET `/my-requests` - View own requests
- GET `/requests/pending` - View pending (Developer)
- POST `/requests/{id}/approve` - Approve request
- POST `/requests/{id}/reject` - Reject request
- GET `/list` - List active sources
- POST `/{id}/sync` - Trigger sync
- GET `/{id}/sync-logs` - View sync logs

### Audit (`/audit`)

- GET `/logs` - Get audit logs (filtered)

### Bookmarks (`/bookmarks`)

- GET `/list` - List user bookmarks
- POST `/add` - Add bookmark
- DELETE `/{id}` - Remove bookmark

### Notes (`/notes`)

- GET `/list` - List user notes
- POST `/create` - Create note
- PATCH `/{id}` - Update note
- DELETE `/{id}` - Delete note

---

## 🔒 Security Features

### Authentication & Authorization

- JWT tokens with expiry
- Password hashing (bcrypt)
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

| Operation              | Time   | Notes                            |
| ---------------------- | ------ | -------------------------------- |
| Document Upload        | 3-7s   | Instant response, lazy embedding |
| RAG Query (embedded)   | 4-7s   | Fast retrieval                   |
| RAG Query (first time) | 12-19s | Includes embedding               |
| Voice Transcription    | 5-10s  | 1 min audio                      |
| User Login             | <1s    | JWT generation                   |
| Document List          | <2s    | Paginated                        |

---

## 🚀 Deployment

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
```

**Frontend (.env)**:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### Installation Steps

1. **Clone Repository**
2. **Backend Setup**: Create venv, install requirements
3. **Enable pgvector**: Run `python scripts/enable_pgvector.py`
4. **Run Migrations**: `alembic upgrade head`
5. **Initialize Developer Account**: `python backend/init_developer.py`
6. **Start Backend**: `uvicorn backend.main:app --reload`
7. **Frontend Setup**: Install npm packages
8. **Start Frontend**: `npm run dev`

### Access

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

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
│   ├── tools/                 # Search tools
│   └── data_ingestion/        # External DB sync
│
├── backend/                    # FastAPI Backend
│   ├── routers/               # API endpoints
│   ├── utils/                 # Helper functions
│   ├── database.py            # SQLAlchemy models
│   ├── main.py                # FastAPI app
│   └── init_developer.py      # Initial setup
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── pages/             # Route pages
│   │   ├── services/          # API calls
│   │   ├── stores/            # Zustand stores
│   │   ├── hooks/             # Custom hooks
│   │   └── utils/             # Helper functions
│   └── package.json
│
├── alembic/                    # Database migrations
├── scripts/                    # Utility scripts
├── tests/                      # Test suite
└── .env                        # Environment variables
```

---

## 📞 Support & Documentation

### Documentation Files

- `PROJECT_OVERVIEW.md` - This file
- `WORKFLOWS_AND_FEATURES.md` - Detailed workflows
- `TECHNICAL_REFERENCE.md` - Technical details
- `README.md` - Quick start guide
- `COMPLETE_DOCUMENTATION.md` - Comprehensive guide

### API Documentation

- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

**Built for**: Ministry of Education, Government of India  
**Version**: 2.0.0  
**Status**: ✅ Production Ready  
**Last Updated**: December 4, 2025
