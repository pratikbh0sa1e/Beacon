# BEACON - Government Policy Intelligence Platform

## Project Overview

**BEACON** is an AI-powered document management and policy intelligence platform designed for the Ministry of Education (MoE) and higher education institutions in India. It enables secure document storage, intelligent search, role-based access control, and AI-powered policy analysis through a sophisticated RAG (Retrieval-Augmented Generation) system.

**Version**: 2.0.0  
**Status**: Production Ready  
**Tech Stack**: FastAPI (Backend) + React (Frontend) + PostgreSQL + Supabase + Google Gemini AI

---

## Core Purpose

BEACON solves critical challenges in government policy management:

1. **Centralized Document Repository**: Single source of truth for all policy documents across ministries and institutions
2. **Intelligent Search & Retrieval**: AI-powered semantic search across 100+ languages
3. **Role-Based Access Control**: Hierarchical permissions ensuring document security
4. **Approval Workflows**: Multi-level document approval system with audit trails
5. **AI Policy Assistant**: Natural language queries with cited sources
6. **Voice Queries**: Multilingual voice-to-text for accessibility
7. **Cross-Institution Collaboration**: Secure document sharing between universities and ministries

---

## System Architecture

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

**Infrastructure**:

- Uvicorn ASGI server
- CORS-enabled API
- Connection pooling
- Lazy loading architecture

---

## Key Features

### 1. User Management & Authentication

**Role Hierarchy**:

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

**Features**:

- Two-step registration (register → admin approval)
- Email verification system
- JWT-based authentication
- Role-based route protection
- Institution-based user grouping
- Approval workflow with audit logs

**Business Rules**:

- Only 1 Developer account (system-wide)
- Maximum 5 Ministry Admins
- 1 University Admin per institution
- Unlimited Document Officers and Students

### 2. Document Management

**Supported Formats**:

- PDF, DOCX, PPTX
- Images (PNG, JPG) with OCR
- Text files

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

### 3. Approval Workflows

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

**Audit Trail**:

- All actions logged with timestamp
- Actor and target user/document tracked
- Notes and reasons preserved
- Searchable audit logs

### 4. AI-Powered RAG System

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

### 5. Voice Query System

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
- Chat history heatmap (visual activity calendar)

**Audit Logs**:

- All user actions tracked
- Searchable by user, action type, date range
- Export functionality
- Retention policy

### 9. Additional Features

**Bookmarks**:

- Save favorite documents
- Personal notes on bookmarks
- Quick access from sidebar

**Personal Notes**:

- Private notes on documents
- Markdown support
- Not visible to other users

**Search & Filters**:

- Full-text search across documents
- Filter by visibility, status, institution
- Sort by date, title, relevance
- Advanced filters (date range, uploader, etc.)

**Theme System**:

- Light/dark mode toggle
- Persists across sessions
- All components theme-aware

**External Data Sources**:

- Connect to ministry databases
- Scheduled sync jobs
- API integration support

---

## User Roles & Permissions

### Developer (Super Admin)

**Can**:

- Access all features and documents
- Manage all users and institutions
- View system health and analytics
- Approve Ministry Admins
- Delete any resource
- Access audit logs

**Cannot**:

- Be deleted (system protection)

### Ministry Admin (MoE Officials)

**Can**:

- View all public and restricted documents
- Upload documents (auto-approved)
- Approve University Admins
- Manage institutions
- View analytics
- Access documents from all institutions

**Cannot**:

- Access system health dashboard
- Delete Developer account
- Exceed 5 active Ministry Admins

### University Admin (Institution Heads)

**Can**:

- View public + own institution documents
- Upload documents (requires MoE approval)
- Approve Document Officers and Students
- Manage own institution users
- View institution analytics

**Cannot**:

- Access other institutions' restricted docs
- Approve other University Admins
- Delete institution

### Document Officer

**Can**:

- Upload documents (requires approval)
- View public + own institution docs
- Manage own uploads
- Add bookmarks and notes

**Cannot**:

- Approve documents or users
- Access admin dashboards
- View restricted documents

### Student

**Can**:

- View public + own institution's public docs
- Query AI assistant
- Add bookmarks and notes
- Use voice queries

**Cannot**:

- Upload documents
- Access admin features
- View restricted documents

### Public Viewer

**Can**:

- View public documents only
- Limited query access

**Cannot**:

- Upload documents
- Access institution-specific content

---

## Database Schema

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
- title, description, category, tags
- language, page_count, file_size
- embedding_status

**document_embeddings** (pgvector):

- id, document_id, chunk_index
- embedding (vector 1024)
- text_chunk
- visibility_level, institution_id, approval_status

**notifications**:

- id, user_id, title, message, type
- priority, read, read_at
- action_url, action_label, action_metadata
- created_at, expires_at

**audit_logs**:

- id, user_id, action, details
- ip_address, user_agent
- created_at

**bookmarks**:

- id, user_id, document_id
- notes, created_at

**chat_sessions**:

- id, user_id, title
- created_at, updated_at

**chat_messages**:

- id, session_id, role (user/assistant)
- content, citations
- created_at

**institution_domains**:

- id, institution_id, domain
- created_at

**external_data_sources**:

- id, name, type, connection_config
- sync_schedule, last_sync_at
- created_at

---

## API Endpoints

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
- POST `/revoke/{user_id}` - Revoke approval
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

### Audit (`/api/audit`)

- GET `/logs` - Get audit logs (filtered)

### Bookmarks (`/api/bookmarks`)

- GET `/list` - List user bookmarks
- POST `/add` - Add bookmark
- DELETE `/{id}` - Remove bookmark

---

## Security Features

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

## Deployment

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

1. **Clone Repository**:

```bash
git clone <repository-url>
cd Beacon__V1
```

2. **Backend Setup**:

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. **Enable pgvector**:

```bash
python scripts/enable_pgvector.py
```

4. **Run Migrations**:

```bash
alembic upgrade head
```

5. **Initialize Developer Account**:

```bash
python backend/init_developer.py
```

6. **Start Backend**:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

7. **Frontend Setup**:

```bash
cd frontend
npm install
npm run dev
```

8. **Access Application**:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Performance Metrics

| Operation              | Time   | Notes                            |
| ---------------------- | ------ | -------------------------------- |
| Document Upload        | 3-7s   | Instant response, lazy embedding |
| RAG Query (embedded)   | 4-7s   | Fast retrieval                   |
| RAG Query (first time) | 12-19s | Includes embedding               |
| Voice Transcription    | 5-10s  | 1 min audio                      |
| User Login             | <1s    | JWT generation                   |
| Document List          | <2s    | Paginated                        |

---

## Future Enhancements

### Planned Features

- [ ] WebSocket for real-time notifications
- [ ] Advanced analytics (ML-based insights)
- [ ] Multi-document comparison
- [ ] Policy compliance checker
- [ ] Automated document classification
- [ ] Mobile app (React Native)
- [ ] Offline mode
- [ ] Advanced search (boolean operators)
- [ ] Document versioning with diff view
- [ ] Collaborative annotations

### Scalability Improvements

- [ ] Redis caching layer
- [ ] Elasticsearch for full-text search
- [ ] CDN for static assets
- [ ] Load balancing
- [ ] Horizontal scaling
- [ ] Database read replicas
- [ ] Vector index optimization (HNSW)

---

## Project Structure

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
│   │   └── bookmark_router.py
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
│   │   │   ├── documents/     # Document management
│   │   │   ├── auth/          # Login, register
│   │   │   └── chat/          # AI chat
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
├── README.md                   # Quick start guide
└── PROJECT_DESCRIPTION.md      # This file
```

---

## Testing

### Backend Tests

```bash
python tests/test_embeddings.py
python tests/test_voice_query.py
python tests/test_multilingual_embeddings.py
python tests/run_all_tests.py
```

### Frontend Tests

```bash
cd frontend
npm run test
```

### Manual Testing Checklist

- [ ] User registration and approval flow
- [ ] Document upload and approval
- [ ] Role-based access control
- [ ] AI chat with citations
- [ ] Voice queries
- [ ] Notifications
- [ ] Bookmarks
- [ ] Analytics dashboard
- [ ] Theme toggle
- [ ] Search and filters

---

## Support & Documentation

### Documentation Files

- `README.md` - Quick start guide
- `COMPLETE_DOCUMENTATION.md` - Comprehensive guide
- `ROLE_BASED_RAG_IMPLEMENTATION.md` - RAG system details
- `NOTIFICATION_SYSTEM_IMPLEMENTATION.md` - Notification guide
- `COMPLETE_IMPLEMENTATION_STATUS.md` - Feature status
- `PROJECT_DESCRIPTION.md` - This file

### API Documentation

- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Logs

- Backend logs: Console output
- Agent logs: `Agent/agent_logs/`
- Audit logs: Database table

---

## Contributors & Acknowledgments

**Built for**: Ministry of Education, Government of India

**Technology Partners**:

- Google (Gemini AI)
- Supabase (Storage)
- OpenAI (Whisper)
- PostgreSQL (Database)

**Open Source Libraries**:

- FastAPI, React, SQLAlchemy, Alembic
- TailwindCSS, shadcn/ui
- BGE-M3, EasyOCR, pgvector

---

## License

[Specify License Here]

---

## Contact

For support, feature requests, or bug reports:

- Email: [contact email]
- GitHub: [repository URL]
- Documentation: [docs URL]

---

**Last Updated**: December 4, 2025  
**Version**: 2.0.0  
**Status**: ✅ Production Ready
