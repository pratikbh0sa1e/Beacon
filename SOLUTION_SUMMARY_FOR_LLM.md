# BEACON Solution - Quick Reference for LLM Implementation

## 🎯 What to Build

An AI-powered Government Policy Intelligence Platform with:
- Document management (PDF, DOCX, PPTX, Images with OCR)
- AI chat with RAG (Retrieval-Augmented Generation)
- Voice queries (98+ languages)
- Web scraping with keyword filtering
- Role-based access control
- Approval workflows
- Real-time notifications

## 🏗️ Tech Stack

**Backend**: FastAPI + PostgreSQL (pgvector) + SQLAlchemy + JWT  
**Frontend**: React 18 + Vite + TailwindCSS + shadcn/ui + Zustand  
**AI/ML**: Google Gemini 2.0 + BGE-M3 embeddings + Whisper + EasyOCR  
**Storage**: Supabase (S3-compatible)  
**Web Scraping**: BeautifulSoup4 + Requests

## 👥 User Roles (Hierarchy)

```
Developer (Super Admin) → Ministry Admin → University Admin → Document Officer → Student → Public Viewer
```

## 📊 Core Features

### 1. Document Management
- Upload: PDF, DOCX, PPTX, Images (with OCR)
- Visibility: Public, Institution Only, Restricted, Confidential
- Lifecycle: Upload → Draft → Pending → Under Review → Approved/Rejected
- Features: Metadata extraction, soft delete, version tracking, expiry dates

### 2. Approval Workflows
- Documents: Student/Officer → Uni Admin → Ministry Admin
- Users: Student → Uni Admin → Ministry Admin → Developer
- Actions: Approve, Reject, Request Changes, Escalate

### 3. AI-Powered RAG
- **Lazy Embedding**: Embed on first query (not on upload)
- **Hybrid Search**: Semantic (vector) + keyword (metadata)
- **Role-Based**: Users only see documents they can access
- **Citations**: Every answer includes source documents

### 4. Voice Queries
- 98+ languages with auto-detection
- Audio formats: MP3, WAV, M4A, OGG, FLAC
- Workflow: Audio → Transcription → Text Query → RAG → Answer

### 5. Web Scraping
- Automated document discovery from government websites
- **Keyword Filtering**: Filter DURING scraping (not after)
- Provenance tracking (source, credibility, metadata)
- Full pipeline: Scrape → Filter → Download → OCR → Metadata → Store → RAG

### 6. Notifications
- Hierarchical routing based on role
- Priority levels: Critical, High, Medium, Low
- Real-time toast + persistent panel
- Action buttons (Approve Now, Review, etc.)

### 7. Institution Management
- Create/edit institutions (universities, ministries)
- Link universities to parent ministries
- Domain-based email validation
- Soft delete with cascade handling

### 8. Analytics
- System health dashboard (Developer only)
- Activity stats (uploads, queries, approvals)
- Most active users
- Chat history heatmap
- Audit logs

## 🗄️ Key Database Tables

1. **users**: id, name, email, password_hash, role, institution_id, approved, email_verified
2. **institutions**: id, name, location, type, parent_ministry_id, deleted_at
3. **documents**: id, filename, file_type, s3_url, extracted_text, visibility_level, institution_id, uploader_id, approval_status
4. **document_metadata**: id, document_id, title, description, category, tags, language, embedding_status
5. **document_embeddings**: id, document_id, chunk_index, embedding (vector 1024), chunk_text, visibility_level
6. **notifications**: id, user_id, title, message, type, priority, read, action_url
7. **chat_sessions**: id, user_id, title, thread_id
8. **chat_messages**: id, session_id, role, content, citations
9. **scraped_documents**: id, document_id, source_url, source_domain, credibility_score, file_hash, provenance_metadata
10. **audit_logs**: id, user_id, action, action_metadata, ip_address

## 📡 Key API Endpoints

### Authentication
- POST `/api/auth/register`, `/api/auth/login`, `/api/auth/verify-email/{token}`, GET `/api/auth/me`

### Documents
- POST `/api/documents/upload`, GET `/api/documents/list`, GET `/api/documents/{id}`, GET `/api/documents/{id}/download`

### Approvals
- GET `/api/approvals/pending`, POST `/api/approvals/{id}/approve`, POST `/api/approvals/{id}/reject`

### Chat
- POST `/api/chat/query`, POST `/api/chat/query/stream`, GET `/api/chat/sessions`

### Voice
- POST `/api/voice/query`, POST `/api/voice/query/stream`

### Web Scraping
- POST `/api/web-scraping/sources`, GET `/api/web-scraping/sources`, POST `/api/web-scraping/scrape`
- POST `/api/web-scraping/scrape-and-download`, POST `/api/web-scraping/scrape-and-process`
- GET `/api/web-scraping/logs`, GET `/api/web-scraping/scraped-documents`, GET `/api/web-scraping/stats`

### Notifications
- GET `/api/notifications/list`, GET `/api/notifications/grouped`, POST `/api/notifications/{id}/mark-read`

### Analytics
- GET `/api/analytics/stats`, GET `/api/analytics/activity`, GET `/api/analytics/system-health`

## 🎯 Key Implementation Details

### 1. Lazy RAG (Critical!)
```python
# On upload: Don't embed yet
document.embedding_status = 'pending'

# On first query: Embed now
if document.embedding_status == 'pending':
    embeddings = embed_document(document.text)
    store_embeddings(embeddings)
    document.embedding_status = 'completed'
```

**Why**: Instant uploads (3-7s instead of 30-60s), embeddings only for queried documents

### 2. Keyword Filtering During Scraping (Critical!)
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

**Why**: 70% reduction in downloads, processing time, and storage

### 3. Role-Based Document Access (Critical!)
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
```

**Why**: Users only see documents they can access

### 4. Hierarchical Notifications (Critical!)
```python
def notify_hierarchy(action, actor):
    if actor.role == 'student':
        notify_user(actor.institution.university_admin)
    elif actor.role == 'university_admin':
        notify_user(ministry_admin)
    elif actor.role == 'ministry_admin':
        notify_user(developer)
```

**Why**: Admins know about actions in their hierarchy

### 5. Provenance Tracking (Critical!)
```python
provenance = {
    'source_url': document_url,
    'source_domain': 'ugc.gov.in',
    'credibility_score': 9,  # .gov.in = 9/10
    'source_type': 'government',
    'scraped_at': datetime.now(),
    'matched_keywords': ['policy', 'circular'],
    'verified': True
}
```

**Why**: Know where documents came from and trust level

## 🔐 Security

- JWT authentication with bcrypt password hashing
- Email verification required
- Role-based access control (RBAC)
- Document-level permissions
- Audit logging for all actions
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (React escaping)
- Soft deletes (preserve audit trail)

## 📈 Performance Targets

- Document Upload: <7s
- RAG Query (embedded): <7s
- RAG Query (first time): <20s
- Voice Transcription: <10s
- User Login: <1s
- Document List: <2s
- Web Scraping: <30s per source

## 🚀 Quick Start

1. **Backend**: FastAPI + PostgreSQL (pgvector) + SQLAlchemy
2. **Frontend**: React 18 + Vite + TailwindCSS + shadcn/ui
3. **AI**: Google Gemini 2.0 + BGE-M3 embeddings + Whisper
4. **Storage**: Supabase (S3-compatible)
5. **Web Scraping**: BeautifulSoup4 + Requests

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
│   └── web_scraping/          # Web scraping components
├── backend/                    # FastAPI Backend
│   ├── routers/               # API endpoints
│   ├── utils/                 # Helper functions
│   ├── database.py            # SQLAlchemy models
│   └── main.py                # FastAPI app
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── pages/             # Route pages
│   │   ├── services/          # API calls
│   │   └── stores/            # Zustand stores
│   └── package.json
├── alembic/                    # Database migrations
├── scripts/                    # Utility scripts
└── tests/                      # Test suite
```

## 🎯 Success Criteria

### Must Have
- ✅ Multi-format document processing (PDF, DOCX, PPTX, Images)
- ✅ Lazy RAG (instant uploads)
- ✅ Role-based access control
- ✅ Approval workflows
- ✅ Web scraping with keyword filtering
- ✅ AI chat with citations
- ✅ Voice queries
- ✅ Real-time notifications

### Nice to Have
- Redis caching
- Elasticsearch for full-text search
- WebSocket for real-time updates
- Mobile app
- Advanced analytics

## 📚 Reference Documents

For complete details, see:
- `COMPLETE_SOLUTION_PROMPT.md` - Full solution architecture (this is the main document)
- `PROJECT_DESCRIPTION.md` - Comprehensive technical documentation
- `WEB_SCRAPING_TECHNICAL_DOCUMENTATION.md` - Web scraping details
- `KEYWORD_FILTERING_IMPLEMENTATION_SUMMARY.md` - Filtering implementation
- `1000_DOCUMENTS_IMPLEMENTATION_PLAN.md` - Scaling to 1000+ documents

## 🎉 Key Differentiators

1. **Lazy RAG**: Instant uploads, embed on first query
2. **Keyword Filtering**: Filter DURING scraping, not after
3. **Role-Based Access**: Filter at database query level
4. **Hierarchical Notifications**: Route based on role hierarchy
5. **Provenance Tracking**: Know where documents came from
6. **Multi-format Support**: PDF, DOCX, PPTX, Images with OCR
7. **Multilingual**: 100+ languages for embeddings, 98+ for voice
8. **Web Scraping**: Automated document discovery
9. **Approval Workflows**: Multi-level document and user approval
10. **Production Ready**: Security, performance, scalability

---

**Status**: ✅ Production Ready  
**Version**: 2.0.0  
**Last Updated**: December 8, 2025

**Use `COMPLETE_SOLUTION_PROMPT.md` as the main prompt for another LLM to build this solution.**
