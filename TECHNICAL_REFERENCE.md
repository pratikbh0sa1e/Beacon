# BEACON - Technical Reference Guide

## Complete Technical Documentation

**Version**: 2.0.0  
**Last Updated**: December 4, 2025

---

## 📋 Table of Contents

1. [Technology Stack](#technology-stack)
2. [Database Schema](#database-schema)
3. [API Reference](#api-reference)
4. [AI/ML Components](#aiml-components)
5. [Security Implementation](#security-implementation)
6. [Performance Optimization](#performance-optimization)
7. [Deployment Guide](#deployment-guide)
8. [Testing](#testing)

---

## Technology Stack

### Backend

- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **Database**: PostgreSQL 15+ with pgvector extension
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic
- **Authentication**: JWT (PyJWT)
- **Password Hashing**: bcrypt
- **HTTP Client**: httpx
- **ASGI Server**: Uvicorn

### Frontend

- **Framework**: React 18
- **Build Tool**: Vite 5
- **Styling**: TailwindCSS 3
- **UI Components**: shadcn/ui
- **State Management**: Zustand
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Forms**: React Hook Form
- **Validation**: Zod
- **Notifications**: Sonner (toast)
- **Icons**: Lucide React

### AI/ML

- **LLM**: Google Gemini 2.0 Flash
- **Embeddings**: BGE-M3 (1024-dim, multilingual)
- **Vector Store**: pgvector (PostgreSQL extension)
- **Voice**: OpenAI Whisper (local) / Google Cloud Speech
- **OCR**: EasyOCR (English + Hindi)
- **Framework**: LangChain (optional)

### Storage

- **Object Storage**: Supabase S3
- **Database**: PostgreSQL
- **Vector Storage**: pgvector

### Infrastructure

- **Server**: Uvicorn ASGI
- **CORS**: FastAPI middleware
- **Connection Pooling**: SQLAlchemy
- **Scheduler**: APScheduler (background jobs)

---

## Database Schema

### Core Tables

#### users

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
    verification_token VARCHAR(255) UNIQUE,
    verification_token_expires TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_approved ON users(approved);
CREATE INDEX idx_users_email_verified ON users(email_verified);
```

#### institutions

```sql
CREATE TABLE institutions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    location VARCHAR(255),
    type VARCHAR(50) NOT NULL,
    parent_ministry_id INTEGER REFERENCES institutions(id),
    created_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(id)
);

CREATE INDEX idx_institutions_type ON institutions(type);
CREATE INDEX idx_institutions_deleted_at ON institutions(deleted_at);
```

#### documents

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR NOT NULL,
    file_type VARCHAR,
    file_path VARCHAR,
    s3_url VARCHAR,
    extracted_text TEXT,
    visibility_level VARCHAR(50) DEFAULT 'public',
    institution_id INTEGER REFERENCES institutions(id),
    uploader_id INTEGER REFERENCES users(id),
    download_allowed BOOLEAN DEFAULT FALSE,
    approval_status VARCHAR(50) DEFAULT 'draft',
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    requires_moe_approval BOOLEAN DEFAULT FALSE,
    escalated_at TIMESTAMP,
    rejection_reason TEXT,
    expiry_date TIMESTAMP,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    user_description TEXT,
    version VARCHAR(50) DEFAULT '1.0',
    additional_metadata TEXT
);

CREATE INDEX idx_documents_filename ON documents(filename);
CREATE INDEX idx_documents_approval_status ON documents(approval_status);
CREATE INDEX idx_documents_requires_moe_approval ON documents(requires_moe_approval);
```

#### document_embeddings (pgvector)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1024) NOT NULL,
    visibility_level VARCHAR(50) NOT NULL,
    institution_id INTEGER,
    approval_status VARCHAR(50) NOT NULL,
    chunk_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_doc_chunk ON document_embeddings(document_id, chunk_index);
CREATE INDEX idx_visibility_institution ON document_embeddings(visibility_level, institution_id);
CREATE INDEX idx_approval_status ON document_embeddings(approval_status);

-- Vector index for similarity search (production)
CREATE INDEX ON document_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

#### notifications

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
    action_url VARCHAR(500),
    action_label VARCHAR(100),
    action_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_priority ON notifications(priority);
CREATE INDEX idx_notifications_read ON notifications(read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
```

### Additional Tables

- document_metadata
- external_data_sources
- sync_logs
- audit_logs
- bookmarks
- chat_sessions
- chat_messages
- document_chat_messages
- document_chat_participants
- user_notes
- institution_domains

---

## API Reference

### Authentication Endpoints

#### POST /auth/register

```json
Request:
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "role": "student",
  "institution_id": 1
}

Response:
{
  "message": "Registration successful. Please verify your email.",
  "user_id": 123
}
```

#### POST /auth/login

```json
Request:
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "role": "student",
    "approved": true
  }
}
```

#### GET /auth/me

```json
Headers: Authorization: Bearer <token>

Response:
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "role": "student",
  "institution_id": 1,
  "approved": true,
  "email_verified": true
}
```

### Document Endpoints

#### POST /documents/upload

```
Content-Type: multipart/form-data

Form Data:
- file: <binary>
- title: "Education Policy 2024"
- description: "New education policy guidelines"
- visibility: "public"
- download_allowed: true

Response:
{
  "message": "Document uploaded successfully",
  "document_id": 456,
  "filename": "policy_2024.pdf",
  "s3_url": "https://...",
  "processing_time": 5.2
}
```

#### GET /documents/list

```
Query Params:
- category: "policy"
- visibility: "public"
- search: "education"
- limit: 20
- offset: 0

Response:
{
  "documents": [
    {
      "id": 456,
      "filename": "policy_2024.pdf",
      "title": "Education Policy 2024",
      "visibility_level": "public",
      "approval_status": "approved",
      "uploaded_at": "2024-12-01T10:00:00Z",
      "uploader": {
        "id": 123,
        "name": "John Doe"
      }
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

### Chat Endpoints

#### POST /chat/query

```json
Request:
{
  "question": "What are the education policy guidelines?",
  "thread_id": "session_123"
}

Response:
{
  "answer": "The education policy guidelines include...",
  "citations": [
    {
      "document_id": 456,
      "document_title": "Education Policy 2024",
      "approval_status": "approved",
      "text": "Relevant excerpt...",
      "score": 0.95
    }
  ],
  "confidence": 0.92,
  "processing_time": 6.3
}
```

#### POST /chat/query/stream

```
Content-Type: text/event-stream

Events:
data: {"type": "content", "token": "The education", "timestamp": 1234567890}
data: {"type": "content", "token": " policy", "timestamp": 1234567891}
data: {"type": "citation", "citation": {"document_id": 456, ...}}
data: {"type": "metadata", "confidence": 0.95, "status": "success"}
data: {"type": "done"}
```

### Voice Endpoints

#### POST /voice/query

```
Content-Type: multipart/form-data

Form Data:
- audio: <binary>
- language: "en" (optional)
- thread_id: "session_123" (optional)

Response:
{
  "transcription": "What are the education guidelines?",
  "language": "english",
  "answer": "The education guidelines include...",
  "citations": [...],
  "processing_time": 8.5
}
```

### Notification Endpoints

#### GET /notifications/list

```
Query Params:
- unread_only: true
- priority: "high"
- type: "document_approval"
- limit: 20
- offset: 0

Response:
{
  "notifications": [
    {
      "id": 789,
      "title": "New Document Approval",
      "message": "John Doe uploaded a document",
      "type": "document_approval",
      "priority": "high",
      "read": false,
      "action_url": "/admin/approvals",
      "action_label": "Review Now",
      "created_at": "2024-12-04T10:00:00Z"
    }
  ],
  "total": 50
}
```

#### GET /notifications/grouped

```json
Response:
{
  "critical": [
    {
      "id": 790,
      "title": "Security Alert",
      "priority": "critical",
      ...
    }
  ],
  "high": [...],
  "medium": [...],
  "low": [...]
}
```

---

## AI/ML Components

### Embedding Model (BGE-M3)

**Specifications**:

- Model: BAAI/bge-m3
- Dimension: 1024
- Languages: 100+
- Max Sequence Length: 8192 tokens
- Device: CUDA (GPU) or CPU

**Usage**:

```python
from Agent.embeddings.bge_embeddings import BGEEmbeddings

embedder = BGEEmbeddings()
text = "Education policy guidelines"
embedding = embedder.embed_query(text)
# Returns: numpy array of shape (1024,)
```

### LLM (Google Gemini)

**Model**: gemini-2.0-flash-exp
**Max Tokens**: 8192
**Temperature**: 0.7
**Top P**: 0.95

**Usage**:

```python
import google.generativeai as genai

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

response = model.generate_content(
    prompt,
    generation_config={
        "temperature": 0.7,
        "top_p": 0.95,
        "max_output_tokens": 8192
    }
)
```

### Voice Transcription (Whisper)

**Model**: openai/whisper-base
**Languages**: 98+
**Device**: CUDA (GPU)

**Usage**:

```python
import whisper

model = whisper.load_model("base", device="cuda")
result = model.transcribe("audio.mp3", language="en")
transcription = result["text"]
```

### Vector Search (pgvector)

**Similarity Metric**: Cosine Similarity
**Index Type**: IVFFlat (production) or HNSW

**Query**:

```python
from sqlalchemy import text

query_embedding = embedder.embed_query(query_text)

sql = text("""
    SELECT document_id, chunk_text,
           1 - (embedding <=> :query_embedding) AS similarity
    FROM document_embeddings
    WHERE visibility_level = :visibility
      AND approval_status IN ('approved', 'pending')
    ORDER BY embedding <=> :query_embedding
    LIMIT :limit
""")

results = db.execute(sql, {
    "query_embedding": query_embedding,
    "visibility": "public",
    "limit": 5
})
```

### Chunking Strategy

**Adaptive Chunking**:

```python
def get_chunk_params(text_length):
    if text_length < 5000:
        return {"chunk_size": 500, "overlap": 50}
    elif text_length < 20000:
        return {"chunk_size": 1000, "overlap": 100}
    elif text_length < 50000:
        return {"chunk_size": 1500, "overlap": 200}
    else:
        return {"chunk_size": 2000, "overlap": 300}
```

### Hybrid Search

**Weights**:

- Vector Search: 70%
- BM25 (Keyword): 30%

**Implementation**:

```python
def hybrid_search(query, documents):
    # Vector search
    vector_scores = vector_search(query, documents)

    # BM25 search
    bm25_scores = bm25_search(query, documents)

    # Combine scores
    final_scores = {}
    for doc_id in set(vector_scores.keys()) | set(bm25_scores.keys()):
        vector_score = vector_scores.get(doc_id, 0) * 0.7
        bm25_score = bm25_scores.get(doc_id, 0) * 0.3
        final_scores[doc_id] = vector_score + bm25_score

    return sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
```

---

## Security Implementation

### Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash("password123")

# Verify password
is_valid = pwd_context.verify("password123", hashed)
```

### JWT Authentication

```python
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 1440

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRATION_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload
```

### Role-Based Access Control

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

def get_current_user(token: str = Depends(security)):
    try:
        payload = verify_token(token.credentials)
        user_id = payload.get("user_id")
        # Fetch user from database
        return user
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

def require_role(allowed_roles: list):
    def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker
```

### SQL Injection Prevention

- Use SQLAlchemy ORM (parameterized queries)
- Never concatenate user input into SQL
- Validate all inputs

### XSS Protection

- React automatically escapes output
- Sanitize user input on backend
- Use Content Security Policy headers

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Performance Optimization

### Database Indexing

```sql
-- Frequently queried columns
CREATE INDEX idx_documents_approval_status ON documents(approval_status);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);

-- Composite indexes
CREATE INDEX idx_doc_chunk ON document_embeddings(document_id, chunk_index);
CREATE INDEX idx_visibility_institution ON document_embeddings(visibility_level, institution_id);

-- Vector index (production)
CREATE INDEX ON document_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### Connection Pooling

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # Number of connections to maintain
    max_overflow=20,       # Additional connections when pool is full
    pool_pre_ping=True,    # Verify connections before use
    pool_recycle=3600,     # Recycle connections after 1 hour
)
```

### Lazy Loading

- Documents embedded on-demand (first query)
- Metadata extracted in background
- Reduces upload time from 15s to 3-7s

### Caching (Future)

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_document_metadata(doc_id: int):
    # Cache frequently accessed metadata
    return db.query(DocumentMetadata).filter_by(document_id=doc_id).first()
```

### Pagination

```python
def list_documents(limit: int = 20, offset: int = 0):
    return db.query(Document).limit(limit).offset(offset).all()
```

---

## Deployment Guide

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgvector
- Node.js 18+
- Supabase account
- Google API key

### Environment Setup

**Backend (.env)**:

```env
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_NAME=beacon
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=your_password

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key
SUPABASE_BUCKET_NAME=Docs

GOOGLE_API_KEY=your_google_api_key

JWT_SECRET_KEY=your_secret_key_min_32_chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
```

**Frontend (.env)**:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Installation

**Backend**:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

pip install -r requirements.txt

# Enable pgvector
python scripts/enable_pgvector.py

# Run migrations
alembic upgrade head

# Initialize developer account
python backend/init_developer.py

# Start server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**:

```bash
cd frontend
npm install
npm run dev
```

### Production Deployment

**Backend (Uvicorn)**:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Frontend (Build)**:

```bash
npm run build
# Serve dist/ folder with nginx or similar
```

**Database**:

- Enable pgvector extension
- Create vector indexes
- Set up backups
- Configure connection pooling

**Monitoring**:

- Set up logging (Python logging module)
- Monitor API response times
- Track database query performance
- Monitor vector search latency

---

## Testing

### Backend Tests

```bash
# Run all tests
python tests/run_all_tests.py

# Individual tests
python tests/test_embeddings.py
python tests/test_retrieval.py
python tests/test_voice_query.py
python tests/test_multilingual_embeddings.py
```

### Frontend Tests

```bash
cd frontend
npm run test
```

### API Testing (Postman/cURL)

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password"}'

# Upload document
curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@test.pdf" \
  -F "title=Test Document"

# Query AI
curl -X POST http://localhost:8000/chat/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the policies?"}'
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# Using Locust
locust -f tests/load_test.py
```

---

## 🎯 Summary

This technical reference covers:
✅ Complete technology stack
✅ Database schema with indexes
✅ API endpoint specifications
✅ AI/ML component details
✅ Security implementation
✅ Performance optimization
✅ Deployment guide
✅ Testing procedures

For additional details, refer to:

- PROJECT_OVERVIEW.md
- WORKFLOWS_AND_FEATURES.md
- README.md
- COMPLETE_DOCUMENTATION.md

---

**Version**: 2.0.0  
**Status**: Production Ready  
**Last Updated**: December 4, 2025
