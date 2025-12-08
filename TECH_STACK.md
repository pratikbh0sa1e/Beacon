# 🛠️ BEACON - Complete Technology Stack

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  React 18 + Vite + TailwindCSS + shadcn/ui                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API (Axios)
┌──────────────────────▼──────────────────────────────────────┐
│                        BACKEND                               │
│  FastAPI + Python 3.11+ + SQLAlchemy + Alembic              │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
│   Database   │ │ RAG      │ │  Storage   │
│  PostgreSQL  │ │ Gemini   │ │  Supabase  │
│  + pgvector  │ │ BGE-M3   │ │  S3 + CDN  │
└──────────────┘ └──────────┘ └────────────┘
```

---

## 🎨 Frontend Stack

### Core Framework
- **React 18.2.0** - UI library with latest features
- **Vite 7.2.4** - Lightning-fast build tool and dev server
- **React Router DOM 7.9.6** - Client-side routing

### UI Components & Styling
- **TailwindCSS 3.4.17** - Utility-first CSS framework
- **shadcn/ui** - High-quality React components built on Radix UI
- **Radix UI** - Unstyled, accessible component primitives
  - Dialog, Dropdown, Popover, Tabs, Toast, etc. (30+ components)
- **Lucide React 0.555.0** - Beautiful icon library (1000+ icons)
- **Framer Motion 12.23.24** - Animation library

### State Management & Forms
- **Zustand 5.0.9** - Lightweight state management
- **React Hook Form 7.66.1** - Performant form handling
- **Zod 4.1.13** - TypeScript-first schema validation

### Additional Libraries
- **Axios 1.13.2** - HTTP client for API calls
- **React Markdown 10.1.0** - Markdown rendering
- **Sonner 2.0.7** - Toast notifications
- **date-fns 4.1.0** - Date utility library
- **next-themes 0.4.6** - Theme management (light/dark mode)

### Development Tools
- **ESLint 9.39.1** - Code linting
- **PostCSS 8.5.6** - CSS processing
- **Autoprefixer 10.4.22** - CSS vendor prefixing

---

## ⚙️ Backend Stack

### Core Framework
- **FastAPI 0.115.12** - Modern, fast web framework
- **Python 3.11+** - Programming language
- **Uvicorn 0.34.0** - ASGI server
- **Starlette 0.46.1** - ASGI framework (FastAPI foundation)

### Database & ORM
- **PostgreSQL 15+** - Primary database
- **pgvector 0.3.6** - Vector similarity search extension
- **SQLAlchemy 1.4.0** - Python SQL toolkit and ORM
- **Alembic 1.15.2** - Database migration tool
- **psycopg2-binary 2.9.10** - PostgreSQL adapter

### AI & Machine Learning

#### LLM & Orchestration
- **LangChain 0.3.18** - LLM application framework
- **LangGraph 0.2.66** - Agent workflow orchestration
- **LangSmith** - LLM observability and monitoring
- **Google Gemini 2.0 Flash** - Primary LLM
  - `langchain-google-genai 2.0.8`
  - `google-generativeai 0.8.3`

#### Embeddings & Vector Search
- **Sentence Transformers 3.3.1** - Embedding models
- **BGE-M3** - Multilingual embeddings (1024-dim)
- **Transformers 4.57.3** - Hugging Face transformers
- **Hugging Face Hub 0.36.0** - Model repository access

#### Document Processing & OCR
- **PyMuPDF 1.25.2** - PDF processing
- **python-docx 1.1.2** - Word document processing
- **python-pptx 1.0.2** - PowerPoint processing
- **Pillow 11.1.0** - Image processing
- **EasyOCR 1.7.2** - Optical character recognition
- **OpenCV 4.10.0.84** - Computer vision library

#### Voice Processing
- **OpenAI Whisper** - Speech-to-text transcription
- **ffmpeg-python 0.2.0** - Audio processing
- **Google Cloud Speech 2.26.0** - Alternative speech API

### Storage & Cloud Services
- **Supabase 2.11.0** - Backend-as-a-Service
  - Storage3 0.11.3 - S3-compatible storage
  - PostgREST 0.19.3 - RESTful API
  - GoTrue 2.12.4 - Authentication
  - Realtime 2.0.0 - Real-time subscriptions

### Authentication & Security
- **PyJWT 2.10.1** - JSON Web Token implementation
- **python-jose 3.4.0** - JOSE implementation
- **bcrypt 4.3.0** - Password hashing
- **passlib 1.7.4** - Password hashing library
- **cryptography 44.0.2** - Cryptographic recipes

### Data Validation & Serialization
- **Pydantic 2.9.2** - Data validation using Python type hints
- **Pydantic Settings 2.6.0** - Settings management
- **orjson 3.10.16** - Fast JSON serialization
- **ujson 5.10.0** - Ultra-fast JSON encoder/decoder

### Performance & Caching
- **Redis 5.0.1** - In-memory data store
- **fastapi-cache2 0.2.2** - Caching decorator for FastAPI
- **Upstash Redis** - Serverless Redis (cloud)

### Search & Ranking
- **rank-bm25 0.2.2** - BM25 ranking algorithm
- **scikit-learn 1.7.2** - Machine learning utilities

### Utilities
- **python-dotenv 1.1.0** - Environment variable management
- **python-multipart 0.0.20** - Multipart form data parser
- **email-validator 2.2.0** - Email validation
- **dnspython 2.8.0** - DNS toolkit
- **schedule 1.2.2** - Job scheduling
- **python-dateutil 2.9.0** - Date utilities

### HTTP & Async
- **httpx 0.28.1** - Async HTTP client
- **aiohttp 3.13.2** - Async HTTP client/server
- **websockets 12.0** - WebSocket implementation

### Development & Testing
- **pytest 9.0.1** - Testing framework
- **pytest-mock 3.15.1** - Mocking plugin
- **Rich 13.9.4** - Terminal formatting
- **Click 8.1.8** - CLI creation

### Additional Libraries
- **NumPy 1.26.4** - Numerical computing
- **SciPy 1.16.3** - Scientific computing
- **PyYAML 6.0.2** - YAML parser
- **Jinja2 3.1.6** - Template engine
- **Markdown-it-py 3.0.0** - Markdown parser

---

## 🗄️ Database & Storage

### Primary Database
- **PostgreSQL 15+**
  - ACID compliance
  - JSON/JSONB support
  - Full-text search
  - Connection pooling (30 base + 60 overflow)

### Vector Database
- **pgvector Extension**
  - Vector similarity search
  - 1024-dimensional embeddings
  - Cosine similarity, L2 distance
  - Integrated with PostgreSQL

### Object Storage
- **Supabase Storage (S3-compatible)**
  - Document storage
  - CDN integration
  - Automatic backups
  - 99.9% uptime SLA

### Caching Layer
- **Redis (Upstash)**
  - In-memory caching
  - Session storage
  - Rate limiting
  - Pub/Sub messaging

---

## 🤖 AI/ML Pipeline

### Language Models
1. **Google Gemini 2.0 Flash**
   - Primary LLM for chat and analysis
   - 1M token context window
   - Fast inference (<2s)
   - Multimodal support

### Embedding Models
1. **BGE-M3 (BAAI/bge-m3)**
   - Multilingual embeddings
   - 1024 dimensions
   - 100+ languages
   - Cross-lingual search

### Voice Models
1. **OpenAI Whisper (Local)**
   - Speech-to-text
   - 98+ languages
   - GPU-accelerated
   - Free, private

2. **Google Cloud Speech (Cloud)**
   - Alternative STT
   - High accuracy
   - Cloud-based

### OCR Models
1. **EasyOCR**
   - 80+ languages
   - Handwriting support
   - GPU-accelerated

---

## 🔧 Development Tools

### Version Control
- **Git** - Source control
- **GitHub** - Repository hosting

### Database Management
- **Alembic** - Database migrations
- **pgAdmin** - PostgreSQL GUI (optional)

### API Development
- **FastAPI Swagger UI** - Interactive API docs
- **ReDoc** - Alternative API documentation

### Code Quality
- **ESLint** - JavaScript linting
- **Prettier** - Code formatting (optional)
- **Black** - Python code formatting (optional)

### Testing
- **pytest** - Python testing
- **pytest-mock** - Mocking
- **Hypothesis** - Property-based testing (optional)

---

## 🚀 Deployment Stack

### Application Server
- **Uvicorn** - ASGI server
- **Gunicorn** - Process manager (production)

### Web Server (Production)
- **Nginx** - Reverse proxy, load balancer
- **Caddy** - Alternative with auto-HTTPS

### Containerization (Optional)
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

### Cloud Platforms (Options)
- **AWS** - EC2, RDS, S3, CloudFront
- **Google Cloud** - Compute Engine, Cloud SQL
- **Azure** - Virtual Machines, PostgreSQL
- **Vercel** - Frontend hosting
- **Railway** - Full-stack hosting
- **Render** - Full-stack hosting

### CI/CD (Optional)
- **GitHub Actions** - Automated workflows
- **GitLab CI** - Alternative CI/CD

---

## 📦 Package Managers

### Frontend
- **npm** - Node package manager
- **pnpm** - Alternative (faster)
- **yarn** - Alternative

### Backend
- **pip** - Python package installer
- **poetry** - Alternative dependency manager
- **conda** - Alternative (with ML focus)

---

## 🔐 Security Stack

### Authentication
- **JWT (JSON Web Tokens)** - Stateless authentication
- **bcrypt** - Password hashing
- **Email verification** - Two-factor registration

### Authorization
- **Role-Based Access Control (RBAC)** - 6 role levels
- **Document-level permissions** - Visibility controls
- **Audit logging** - All actions tracked

### Data Protection
- **HTTPS/TLS** - Encrypted communication
- **SQL injection prevention** - SQLAlchemy ORM
- **XSS protection** - React escaping
- **CORS** - Cross-origin resource sharing

---

## 📊 Monitoring & Logging (Optional)

### Application Monitoring
- **Sentry** - Error tracking
- **LogRocket** - Session replay
- **New Relic** - APM

### Logging
- **Python logging** - Built-in logging
- **Winston** - Node.js logging (if needed)

### Analytics
- **Google Analytics** - User analytics
- **Mixpanel** - Product analytics
- **PostHog** - Open-source analytics

---

## 🌐 Browser Support

### Supported Browsers
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Opera 76+

### Mobile Support
- ✅ iOS Safari 14+
- ✅ Chrome Mobile 90+
- ✅ Samsung Internet 14+

---

## 💻 Development Environment

### Minimum Requirements
- **OS:** Windows 10+, macOS 11+, Ubuntu 20.04+
- **RAM:** 8GB (16GB recommended)
- **Storage:** 10GB free space
- **CPU:** 4 cores (8 cores recommended)
- **GPU:** Optional (for faster embeddings)

### Recommended IDE
- **VS Code** - Primary IDE
  - Extensions: Python, ESLint, Prettier, Tailwind CSS IntelliSense
- **PyCharm** - Alternative for Python
- **WebStorm** - Alternative for JavaScript

---

## 📈 Performance Specifications

### Response Times
- **API Endpoints:** <100ms (cached), <500ms (uncached)
- **Document Upload:** 3-7 seconds
- **AI Query (cached):** 4-7 seconds
- **AI Query (first time):** 12-19 seconds
- **Voice Transcription:** 5-10 seconds (1 min audio)

### Scalability
- **Concurrent Users:** 1,000+ (current), 10,000+ (with scaling)
- **Documents:** 10,000+ (current), 100,000+ (with Elasticsearch)
- **Queries per Day:** 1M+ (current), 10M+ (with CDN)

### Database Performance
- **Connection Pool:** 30 base + 60 overflow
- **Query Timeout:** 30 seconds
- **Connection Recycling:** 15 minutes

---

## 🔄 Version History

### Current Version: 2.0.0
- ✅ Migrated to pgvector
- ✅ Lazy RAG implementation
- ✅ Email verification system
- ✅ Redis caching
- ✅ Voice queries
- ✅ Document chat
- ✅ Analytics dashboard

### Previous Versions
- **1.0.0** - Initial release with FAISS
- **1.5.0** - Added approval workflows

---

## 📚 Documentation

### API Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Code Documentation
- **README.md** - Quick start guide
- **PROJECT_DESCRIPTION.md** - Comprehensive documentation
- **Phase Documentation** - 4 detailed phase files
- **ALEMBIC_GUIDE.md** - Database migration guide

---

## 🎯 Technology Choices - Why?

### Why FastAPI?
- ✅ Fastest Python framework
- ✅ Automatic API documentation
- ✅ Type hints and validation
- ✅ Async support

### Why React?
- ✅ Component-based architecture
- ✅ Large ecosystem
- ✅ Virtual DOM performance
- ✅ Strong community

### Why PostgreSQL + pgvector?
- ✅ ACID compliance
- ✅ Vector search in same database
- ✅ No separate vector DB needed
- ✅ Multi-machine support

### Why Gemini 2.0 Flash?
- ✅ 1M token context
- ✅ Fast inference
- ✅ Cost-effective
- ✅ Multimodal support

### Why BGE-M3?
- ✅ Best multilingual embeddings
- ✅ Supports 100+ languages
- ✅ Cross-lingual search
- ✅ Open-source

### Why Supabase?
- ✅ S3-compatible storage
- ✅ Built-in CDN
- ✅ PostgreSQL integration
- ✅ Easy to use

---

## 🔗 Useful Links

### Official Documentation
- **FastAPI:** https://fastapi.tiangolo.com/
- **React:** https://react.dev/
- **LangChain:** https://python.langchain.com/
- **PostgreSQL:** https://www.postgresql.org/docs/
- **pgvector:** https://github.com/pgvector/pgvector
- **Supabase:** https://supabase.com/docs

### Package Repositories
- **PyPI:** https://pypi.org/
- **npm:** https://www.npmjs.com/
- **Hugging Face:** https://huggingface.co/

---

## 📊 Tech Stack Summary

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Frontend Framework** | React | 18.2.0 | UI library |
| **Build Tool** | Vite | 7.2.4 | Dev server & bundler |
| **Backend Framework** | FastAPI | 0.115.12 | REST API |
| **Language** | Python | 3.11+ | Backend logic |
| **Database** | PostgreSQL | 15+ | Primary database |
| **Vector DB** | pgvector | 0.3.6 | Vector search |
| **ORM** | SQLAlchemy | 1.4.0 | Database ORM |
| **Migrations** | Alembic | 1.15.2 | Schema versioning |
| **LLM** | Gemini 2.0 Flash | Latest | AI chat & analysis |
| **Embeddings** | BGE-M3 | Latest | Multilingual vectors |
| **Voice** | Whisper | Latest | Speech-to-text |
| **OCR** | EasyOCR | 1.7.2 | Text extraction |
| **Storage** | Supabase S3 | Latest | Document storage |
| **Caching** | Redis (Upstash) | 5.0.1 | Performance |
| **Auth** | JWT + bcrypt | Latest | Security |
| **UI Components** | shadcn/ui | Latest | Component library |
| **Styling** | TailwindCSS | 3.4.17 | CSS framework |
| **State** | Zustand | 5.0.9 | State management |
| **Forms** | React Hook Form | 7.66.1 | Form handling |
| **Validation** | Zod | 4.1.13 | Schema validation |
| **HTTP Client** | Axios | 1.13.2 | API calls |
| **Icons** | Lucide React | 0.555.0 | Icon library |
| **Animation** | Framer Motion | 12.23.24 | Animations |

---

**Total Technologies:** 100+ packages and libraries  
**Primary Languages:** Python, JavaScript/TypeScript, SQL  
**Architecture:** Monorepo with separate frontend/backend  
**Deployment:** Cloud-ready, containerization-ready  

**Status:** ✅ Production-Ready | **Version:** 2.0.0 | **Last Updated:** December 2025
