# 🔧 BEACON Platform - Technical Implementation Guide

## Complete Technical Reference & Setup Guide

**Version**: 2.0.0 | **Status**: Production Ready | **Last Updated**: January 2026

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Technology Stack](#technology-stack)
3. [Database Schema](#database-schema)
4. [AI/ML Implementation](#aiml-implementation)
5. [Installation & Setup](#installation--setup)
6. [Configuration Guide](#configuration-guide)
7. [API Reference](#api-reference)
8. [Security Implementation](#security-implementation)
9. [Performance Optimization](#performance-optimization)
10. [Deployment Guide](#deployment-guide)
11. [Troubleshooting](#troubleshooting)

---

## System Architecture

### High-Level Architecture

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

### Component Breakdown

**Frontend Layer**:

- React 18 with Vite build system
- TailwindCSS + shadcn/ui components
- Zustand state management
- Real-time updates via polling

**API Layer**:

- FastAPI with automatic OpenAPI documentation
- JWT authentication with role-based access
- RESTful endpoints with proper HTTP status codes
- CORS middleware for cross-origin requests

**Business Logic Layer**:

- Document processing pipeline
- AI metadata extraction
- Web scraping orchestration
- Notification routing system

**Data Layer**:

- PostgreSQL with pgvector for vector search
- Supabase S3 for document storage
- Redis for caching (optional)
- Audit logging for compliance

---

## Technology Stack

### Backend Technologies

```python
# Core Framework
fastapi==0.115.12          # Modern, fast web framework
uvicorn==0.34.0            # ASGI server
python==3.11+              # Programming language

# Database & ORM
sqlalchemy==1.4.0          # SQL toolkit and ORM
alembic==1.15.2            # Database migration tool
psycopg2-binary==2.9.10    # PostgreSQL adapter
pgvector==0.3.6            # Vector similarity search

# AI & Machine Learning
langchain==0.3.18          # LLM application framework
langchain-google-genai==2.0.8  # Google Gemini integration
sentence-transformers==3.3.1   # Embedding models
transformers==4.57.3       # Hugging Face transformers
torch==2.0.0               # PyTorch for ML models

# Document Processing
PyMuPDF==1.25.2           # PDF processing
python-docx==1.1.2        # Word documents
python-pptx==1.0.2        # PowerPoint files
Pillow==11.1.0             # Image processing
easyocr==1.7.2             # OCR for images

# Authentication & Security
PyJWT==2.10.1              # JSON Web Tokens
bcrypt==4.3.0              # Password hashing
cryptography==44.0.2       # Cryptographic functions

# Storage & Cloud
supabase==2.11.0           # Backend-as-a-Service
httpx==0.28.1              # Async HTTP client
```

### Frontend Technologies

```json
{
  "react": "18.2.0",
  "vite": "7.2.4",
  "typescript": "5.6.3",
  "@tailwindcss/typography": "0.5.15",
  "@radix-ui/react-dialog": "1.1.2",
  "@radix-ui/react-dropdown-menu": "2.1.2",
  "zustand": "5.0.9",
  "react-hook-form": "7.66.1",
  "zod": "4.1.13",
  "axios": "1.13.2",
  "lucide-react": "0.555.0",
  "sonner": "2.0.7"
}
```

---

## Database Schema

### Core Tables Structure

```sql
-- Users table with role-based access
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('developer', 'ministry_admin', 'university_admin', 'document_officer', 'student', 'public_viewer')),
    institution_id INTEGER REFERENCES institutions(id),
    approved BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Institutions with hierarchical structure
CREATE TABLE institutions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    location VARCHAR(255),
    type VARCHAR(50) NOT NULL CHECK (type IN ('ministry', 'university', 'hospital', 'research_center')),
    parent_ministry_id INTEGER REFERENCES institutions(id),
    created_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(id)
);

-- Documents with approval workflow
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR NOT NULL,
    file_type VARCHAR,
    s3_url VARCHAR,
    extracted_text TEXT,
    visibility_level VARCHAR(50) DEFAULT 'public' CHECK (visibility_level IN ('public', 'institution_only', 'restricted', 'confidential')),
    institution_id INTEGER REFERENCES institutions(id),
    uploader_id INTEGER REFERENCES users(id),
    approval_status VARCHAR(50) DEFAULT 'draft' CHECK (approval_status IN ('draft', 'pending', 'under_review', 'approved', 'rejected')),
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    expiry_date TIMESTAMP,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    source_url VARCHAR,  -- For web scraped documents
    version VARCHAR(50) DEFAULT '1.0'
);

-- Vector embeddings for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1024) NOT NULL,  -- BGE-M3 embeddings
    visibility_level VARCHAR(50) NOT NULL,
    institution_id INTEGER,
    approval_status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- AI-extracted metadata
CREATE TABLE document_metadata (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    title VARCHAR(500),
    department VARCHAR(255),
    document_type VARCHAR(100),
    date_published DATE,
    keywords TEXT[],
    summary TEXT,
    key_topics TEXT[],
    entities JSONB,
    metadata_status VARCHAR(50) DEFAULT 'processing' CHECK (metadata_status IN ('processing', 'ready', 'failed')),
    extraction_confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Notification system
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    read BOOLEAN DEFAULT FALSE,
    action_url VARCHAR(500),
    action_label VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);
```

### Indexes for Performance

```sql
-- User indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_approved ON users(approved);

-- Document indexes
CREATE INDEX idx_documents_approval_status ON documents(approval_status);
CREATE INDEX idx_documents_visibility ON documents(visibility_level);
CREATE INDEX idx_documents_uploader ON documents(uploader_id);
CREATE INDEX idx_documents_institution ON documents(institution_id);

-- Vector search indexes
CREATE INDEX idx_doc_embeddings_document ON document_embeddings(document_id);
CREATE INDEX idx_doc_embeddings_visibility ON document_embeddings(visibility_level, institution_id);

-- Vector similarity index (production)
CREATE INDEX ON document_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Notification indexes
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(read);
CREATE INDEX idx_notifications_priority ON notifications(priority);
```

---

## AI/ML Implementation

### Language Models Configuration

```python
# Metadata Extraction (High Volume)
METADATA_LLM_CONFIG = {
    "provider": "gemini",
    "model": "gemma-3-12b",
    "quota": "14,400 requests/day",
    "use_case": "Document metadata extraction",
    "temperature": 0.1,
    "max_tokens": 2048
}

# RAG Agent (Chat)
RAG_LLM_CONFIG = {
    "provider": "gemini",
    "model": "gemini-2.0-flash",
    "quota": "1,500 requests/day",
    "use_case": "Conversational AI, Q&A",
    "temperature": 0.7,
    "max_tokens": 4096
}

# Backup Provider
BACKUP_LLM_CONFIG = {
    "provider": "openrouter",
    "model": "meta-llama/llama-3.3-70b-instruct:free",
    "quota": "200 requests/day",
    "use_case": "Fallback for all operations"
}
```

### Embedding Model Implementation

```python
from sentence_transformers import SentenceTransformer
import numpy as np

class BGEEmbeddings:
    def __init__(self):
        self.model = SentenceTransformer('BAAI/bge-m3')
        self.dimension = 1024

    def embed_query(self, text: str) -> np.ndarray:
        """Generate embedding for search query"""
        return self.model.encode(text, normalize_embeddings=True)

    def embed_documents(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for document chunks"""
        return self.model.encode(texts, normalize_embeddings=True)
```

### Lazy RAG Implementation

```python
class LazyRAGSystem:
    def __init__(self):
        self.embedder = BGEEmbeddings()
        self.vector_store = PgVectorStore()

    async def search_with_lazy_embedding(self, query: str, user_role: str, limit: int = 5):
        """Search documents with on-demand embedding"""

        # 1. Get accessible documents for user role
        accessible_docs = await self.get_accessible_documents(user_role)

        # 2. Check which documents are already embedded
        embedded_docs = await self.vector_store.get_embedded_documents(accessible_docs)
        unembed_docs = [doc for doc in accessible_docs if doc.id not in embedded_docs]

        # 3. If unembed docs exist, rank by metadata and embed top candidates
        if unembed_docs:
            ranked_docs = self.rank_by_metadata(query, unembed_docs)
            top_candidates = ranked_docs[:3]  # Embed top 3

            for doc in top_candidates:
                await self.embed_document(doc)

        # 4. Perform vector search on all embedded documents
        query_embedding = self.embedder.embed_query(query)
        results = await self.vector_store.similarity_search(
            query_embedding,
            filter_by_role=user_role,
            limit=limit
        )

        return results
```

### Voice Processing Pipeline

```python
import whisper
import torch

class VoiceProcessor:
    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = whisper.load_model("base", device=device)

    def transcribe_audio(self, audio_file: bytes, language: str = None) -> dict:
        """Transcribe audio to text"""

        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav") as temp_file:
            temp_file.write(audio_file)
            temp_file.flush()

            # Transcribe with Whisper
            result = self.model.transcribe(
                temp_file.name,
                language=language,
                fp16=torch.cuda.is_available()
            )

            return {
                "text": result["text"],
                "language": result["language"],
                "confidence": result.get("confidence", 0.9)
            }
```

---

## Installation & Setup

### Prerequisites

```bash
# System requirements
Python 3.11+
Node.js 18+
PostgreSQL 15+ with pgvector
Git

# Hardware requirements
RAM: 8GB minimum (16GB recommended)
Storage: 50GB+ free space
CPU: 4+ cores (8+ for Ollama)
GPU: Optional (CUDA for faster processing)
```

### Step-by-Step Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd BEACON

# 2. Create Python virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install frontend dependencies
cd frontend
npm install
cd ..

# 5. Enable pgvector extension
python scripts/enable_pgvector.py

# 6. Run database migrations
alembic upgrade head

# 7. Initialize developer account (optional)
python backend/init_developer.py
```

---

## Configuration Guide

### Environment Variables (.env)

```env
# ============================================
# Database Configuration (Supabase)
# ============================================
DATABASE_HOSTNAME=aws-1-ap-south-1.pooler.supabase.com
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USERNAME=postgres.your-project-id
DATABASE_PASSWORD=your-database-password

# ============================================
# AI Models Configuration
# ============================================
# Google AI Studio API Key (Primary)
GOOGLE_API_KEY=AIzaSyDkCCqQdgGtrd2t1yGjCJ4zv4QmNNjn93w

# OpenRouter API Key (Backup)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# ============================================
# LLM Provider Configuration
# ============================================
# Metadata Extraction - HIGH VOLUME (14,400/day)
METADATA_LLM_PROVIDER=gemini
METADATA_FALLBACK_PROVIDER=gemini

# RAG Agent - CHAT (1,500/day)
RAG_LLM_PROVIDER=gemini
RAG_FALLBACK_PROVIDER=ollama

# Reranker - OPTIONAL
RERANKER_PROVIDER=local

# ============================================
# Storage Configuration (Supabase)
# ============================================
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_BUCKET_NAME=Docs

# ============================================
# Authentication
# ============================================
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# ============================================
# Quality Control
# ============================================
DELETE_DOCS_WITHOUT_METADATA=false
REQUIRE_TITLE=false
REQUIRE_SUMMARY=false
```

### Generate Secret Keys

```bash
# Generate JWT secret
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate encryption key
python -c "import base64; import os; print('DB_ENCRYPTION_KEY=' + base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

### Frontend Configuration

```env
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_NAME=BEACON Platform
```

---

## API Reference

### Authentication Endpoints

```python
# POST /auth/register
{
  "name": "John Doe",
  "email": "john@university.edu",
  "password": "SecurePass123!",
  "role": "student",
  "institution_id": 1
}

# Response
{
  "message": "Registration successful. Please verify your email.",
  "user_id": 123
}

# POST /auth/login
{
  "email": "john@university.edu",
  "password": "SecurePass123!"
}

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 123,
    "name": "John Doe",
    "role": "student",
    "approved": true
  }
}
```

### Document Management Endpoints

```python
# POST /documents/upload
# Content-Type: multipart/form-data
# Form fields: file, title, description, visibility, download_allowed

# Response
{
  "message": "Document uploaded successfully",
  "document_id": 456,
  "filename": "policy_2024.pdf",
  "s3_url": "https://...",
  "processing_time": 5.2
}

# GET /documents/list?category=policy&search=education&limit=20
{
  "documents": [
    {
      "id": 456,
      "filename": "policy_2024.pdf",
      "title": "Education Policy 2024",
      "approval_status": "approved",
      "uploader": {"name": "John Doe"}
    }
  ],
  "total": 100,
  "limit": 20
}
```

### AI Chat Endpoints

```python
# POST /chat/query
{
  "question": "What are the education policy guidelines?",
  "thread_id": "session_123"
}

# Response
{
  "answer": "The education policy guidelines include...",
  "citations": [
    {
      "document_id": 456,
      "document_title": "Education Policy 2024",
      "text": "Relevant excerpt...",
      "score": 0.95
    }
  ],
  "confidence": 0.92,
  "processing_time": 6.3
}

# POST /voice/query
# Content-Type: multipart/form-data
# Form fields: audio, language (optional)

# Response
{
  "transcription": "What are the education guidelines?",
  "language": "english",
  "answer": "The education guidelines include...",
  "citations": [...],
  "processing_time": 8.5
}
```

---

## Security Implementation

### JWT Authentication

```python
from jose import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

### Role-Based Access Control

```python
from enum import Enum
from fastapi import Depends, HTTPException, status

class UserRole(str, Enum):
    DEVELOPER = "developer"
    MINISTRY_ADMIN = "ministry_admin"
    UNIVERSITY_ADMIN = "university_admin"
    DOCUMENT_OFFICER = "document_officer"
    STUDENT = "student"
    PUBLIC_VIEWER = "public_viewer"

def require_role(allowed_roles: List[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Usage in endpoints
@app.get("/admin/users")
async def list_users(
    current_user: User = Depends(require_role([UserRole.DEVELOPER, UserRole.MINISTRY_ADMIN]))
):
    # Only developers and ministry admins can access
    pass
```

### Document Access Control

```python
def filter_documents_by_role(query, user: User):
    """Filter documents based on user role and institution"""

    if user.role == UserRole.DEVELOPER:
        # Developers see everything
        return query

    elif user.role == UserRole.MINISTRY_ADMIN:
        # Ministry admins see public + restricted + all institutions
        return query.filter(
            or_(
                Document.visibility_level == 'public',
                Document.visibility_level == 'restricted'
            )
        )

    elif user.role in [UserRole.UNIVERSITY_ADMIN, UserRole.DOCUMENT_OFFICER]:
        # Institution users see public + own institution
        return query.filter(
            or_(
                Document.visibility_level == 'public',
                and_(
                    Document.visibility_level == 'institution_only',
                    Document.institution_id == user.institution_id
                )
            )
        )

    else:  # STUDENT, PUBLIC_VIEWER
        # Students see only approved public documents
        return query.filter(
            and_(
                Document.visibility_level == 'public',
                Document.approval_status == 'approved'
            )
        )
```

---

## Performance Optimization

### Database Optimization

```sql
-- Connection pooling configuration
CREATE OR REPLACE FUNCTION optimize_database() RETURNS void AS $$
BEGIN
    -- Update table statistics
    ANALYZE documents;
    ANALYZE document_embeddings;
    ANALYZE users;

    -- Vacuum tables
    VACUUM ANALYZE documents;
    VACUUM ANALYZE document_embeddings;

    -- Reindex vector indexes
    REINDEX INDEX CONCURRENTLY document_embeddings_embedding_idx;
END;
$$ LANGUAGE plpgsql;
```

### Vector Search Optimization

```python
class OptimizedVectorStore:
    def __init__(self):
        self.connection_pool = create_engine(
            DATABASE_URL,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600
        )

    async def similarity_search(self, query_embedding, limit=5, filter_params=None):
        """Optimized vector similarity search"""

        # Use prepared statement for better performance
        sql = text("""
            SELECT
                de.document_id,
                de.chunk_text,
                d.filename,
                dm.title,
                1 - (de.embedding <=> :query_embedding) AS similarity
            FROM document_embeddings de
            JOIN documents d ON de.document_id = d.id
            LEFT JOIN document_metadata dm ON d.id = dm.document_id
            WHERE de.visibility_level = :visibility
              AND de.approval_status IN ('approved', 'pending')
              AND (:institution_id IS NULL OR de.institution_id = :institution_id)
            ORDER BY de.embedding <=> :query_embedding
            LIMIT :limit
        """)

        async with self.connection_pool.connect() as conn:
            result = await conn.execute(sql, {
                "query_embedding": query_embedding,
                "visibility": filter_params.get("visibility", "public"),
                "institution_id": filter_params.get("institution_id"),
                "limit": limit
            })

            return result.fetchall()
```

### Caching Strategy

```python
from functools import lru_cache
import redis

# In-memory caching for frequently accessed data
@lru_cache(maxsize=1000)
def get_user_permissions(user_id: int) -> dict:
    """Cache user permissions to avoid repeated DB queries"""
    user = db.query(User).filter(User.id == user_id).first()
    return {
        "role": user.role,
        "institution_id": user.institution_id,
        "approved": user.approved
    }

# Redis caching for expensive operations
class CacheManager:
    def __init__(self):
        self.redis_client = redis.from_url(REDIS_URL)

    async def get_or_set_embeddings(self, document_id: int, text: str):
        """Cache document embeddings to avoid recomputation"""
        cache_key = f"embedding:{document_id}"

        # Try to get from cache
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

        # Compute and cache
        embedding = self.embedder.embed_query(text)
        await self.redis_client.setex(
            cache_key,
            3600,  # 1 hour TTL
            json.dumps(embedding.tolist())
        )

        return embedding
```

---

## Deployment Guide

### Production Environment Setup

```bash
# 1. Server preparation (Ubuntu 20.04+)
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3.11-venv nodejs npm postgresql-15 nginx

# 2. Clone and setup application
git clone <repository-url> /opt/beacon
cd /opt/beacon

# 3. Create production virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Build frontend
cd frontend
npm ci --production
npm run build
cd ..

# 5. Configure environment
cp .env.production .env
# Edit .env with production values

# 6. Setup database
alembic upgrade head
python scripts/setup_production_data.py
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: "3.8"

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    depends_on:
      - postgres
      - redis

  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: beacon
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html

volumes:
  postgres_data:
```

### Nginx Configuration

```nginx
# nginx.conf
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;

    # Frontend
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Issues

```bash
# Error: connection to server failed
# Solution: Check database credentials and network connectivity

# Test connection
psql -h $DATABASE_HOSTNAME -U $DATABASE_USERNAME -d $DATABASE_NAME

# Check environment variables
echo $DATABASE_HOSTNAME
echo $DATABASE_USERNAME

# Verify pgvector extension
psql -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

#### 2. AI Model Quota Exceeded

```bash
# Error: 429 You exceeded your current quota
# Solution: Switch to backup provider or check quota limits

# Check current quota usage
curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
  https://generativelanguage.googleapis.com/v1beta/models

# Switch to OpenRouter
echo "RAG_LLM_PROVIDER=openrouter" >> .env

# Use local Ollama
ollama pull llama3.2
echo "RAG_LLM_PROVIDER=ollama" >> .env
```

#### 3. Vector Search Performance Issues

```sql
-- Check index usage
EXPLAIN ANALYZE SELECT * FROM document_embeddings
ORDER BY embedding <=> '[0.1,0.2,...]' LIMIT 5;

-- Rebuild vector index
DROP INDEX IF EXISTS document_embeddings_embedding_idx;
CREATE INDEX ON document_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Update table statistics
ANALYZE document_embeddings;
```

#### 4. Memory Issues with Embeddings

```python
# Reduce batch size for embedding generation
def embed_documents_batch(self, texts: List[str], batch_size: int = 32):
    """Process embeddings in smaller batches to reduce memory usage"""
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = self.model.encode(batch)
        embeddings.extend(batch_embeddings)

        # Clear GPU cache if using CUDA
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return embeddings
```

#### 5. Frontend Build Issues

```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+

# Build with verbose output
npm run build --verbose
```

### Monitoring and Logging

```python
# Setup structured logging
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id

        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id

        return json.dumps(log_entry)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/application.log'),
        logging.StreamHandler()
    ]
)

# Add request ID middleware for tracing
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    with logging_context(request_id=request_id):
        response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    return response
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_embeddings.py
import pytest
from Agent.embeddings.bge_embedder import BGEEmbeddings

class TestEmbeddings:
    def setup_method(self):
        self.embedder = BGEEmbeddings()

    def test_embed_query(self):
        text = "What is the education policy?"
        embedding = self.embedder.embed_query(text)

        assert embedding.shape == (1024,)
        assert -1 <= embedding.min() <= embedding.max() <= 1

    def test_multilingual_embedding(self):
        english_text = "Education policy"
        hindi_text = "शिक्षा नीति"

        eng_embedding = self.embedder.embed_query(english_text)
        hindi_embedding = self.embedder.embed_query(hindi_text)

        # Should be similar (cosine similarity > 0.7)
        similarity = np.dot(eng_embedding, hindi_embedding)
        assert similarity > 0.7
```

### Integration Tests

```python
# tests/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestAPIIntegration:
    def test_document_upload_and_search(self):
        # 1. Upload document
        with open("test_document.pdf", "rb") as f:
            response = client.post(
                "/documents/upload",
                files={"file": f},
                data={"title": "Test Document"}
            )

        assert response.status_code == 200
        doc_id = response.json()["document_id"]

        # 2. Wait for processing
        time.sleep(5)

        # 3. Search for document
        response = client.post(
            "/chat/query",
            json={"question": "What is in the test document?"}
        )

        assert response.status_code == 200
        assert doc_id in str(response.json()["citations"])
```

### Load Testing

```python
# tests/load_test.py
from locust import HttpUser, task, between

class BeaconUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login
        response = self.client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "password"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def search_documents(self):
        self.client.get("/documents/list", headers=self.headers)

    @task(1)
    def ask_question(self):
        self.client.post(
            "/chat/query",
            json={"question": "What are the education policies?"},
            headers=self.headers
        )
```

---

## Maintenance and Monitoring

### Health Checks

```python
# backend/routers/health.py
@router.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }

    # Database health
    try:
        db.execute(text("SELECT 1"))
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["components"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Vector store health
    try:
        db.execute(text("SELECT COUNT(*) FROM document_embeddings LIMIT 1"))
        health_status["components"]["vector_store"] = "healthy"
    except Exception as e:
        health_status["components"]["vector_store"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # AI model health
    try:
        # Test metadata extraction
        test_response = await extract_metadata("Test document")
        health_status["components"]["ai_models"] = "healthy"
    except Exception as e:
        health_status["components"]["ai_models"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    return health_status
```

### Backup Strategy

```bash
#!/bin/bash
# scripts/backup.sh

# Database backup
pg_dump $DATABASE_URL > "backups/db_$(date +%Y%m%d_%H%M%S).sql"

# Document storage backup (if using local storage)
tar -czf "backups/documents_$(date +%Y%m%d_%H%M%S).tar.gz" data/

# Configuration backup
cp .env "backups/env_$(date +%Y%m%d_%H%M%S).backup"

# Cleanup old backups (keep last 30 days)
find backups/ -name "*.sql" -mtime +30 -delete
find backups/ -name "*.tar.gz" -mtime +30 -delete
```

---

## Conclusion

This technical implementation guide provides comprehensive coverage of the BEACON platform's architecture, setup, and maintenance. The system is designed for production use with proper security, performance optimization, and monitoring capabilities.

For additional support or specific implementation questions, refer to the API documentation at `/docs` or contact the development team.

**Status**: ✅ Production Ready  
**Version**: 2.0.0  
**Last Updated**: January 2026
