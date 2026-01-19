# 🚀 BEACON Platform - Complete Deployment Instructions

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [AI Models Configuration](#ai-models-configuration)
5. [Storage Configuration](#storage-configuration)
6. [Installation Steps](#installation-steps)
7. [Running the Application](#running-the-application)
8. [Testing & Verification](#testing--verification)
9. [Troubleshooting](#troubleshooting)
10. [Production Deployment](#production-deployment)

---

## Prerequisites

### System Requirements:

- **OS**: Windows 10/11, macOS, or Linux
- **Python**: 3.9 or higher
- **Node.js**: 16 or higher
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 10GB free space
- **Internet**: Required for AI models and database

### Required Accounts:

1. **Google AI Studio** - For Gemini API key
2. **Supabase** - For database and storage
3. **OpenRouter** (Optional) - For backup LLM
4. **Ollama** (Optional) - For local LLM

---

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd BEACON
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

## Database Configuration

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Wait for setup to complete
4. Go to Settings → Database
5. Copy connection details

### 2. Enable pgvector Extension

In Supabase SQL Editor, run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. Get Database Credentials

From Supabase Settings → Database:

- Host: `aws-1-ap-south-1.pooler.supabase.com`
- Port: `5432`
- Database: `postgres`
- Username: `postgres.xxxxx`
- Password: `your-password`

---

## AI Models Configuration

### 1. Google AI Studio (Primary)

1. Go to [ai.google.dev](https://ai.google.dev)
2. Create API key
3. Copy the key (starts with `AIzaSy...`)

### 2. OpenRouter (Backup - Optional)

1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up and get API key
3. Copy the key (starts with `sk-or-v1-...`)

### 3. Ollama (Local - Optional)

```bash
# Windows
# Download from https://ollama.com/download/windows

# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Install model
ollama pull llama3.2
```

---

## Storage Configuration

### 1. Supabase Storage

1. In Supabase Dashboard → Storage
2. Create bucket named `Docs`
3. Set bucket to **Public**
4. Go to Settings → API
5. Copy Project URL and anon key

---

## Installation Steps

### 1. Create `.env` File

Create `.env` in root directory:

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
# Authentication
# ============================================
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_SECRET_KEY=your-jwt-secret-here

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
# Ollama Configuration (Local LLM)
# ============================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# ============================================
# Storage Configuration (Supabase)
# ============================================
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_BUCKET_NAME=Docs

# ============================================
# Quality Control
# ============================================
DELETE_DOCS_WITHOUT_METADATA=false
REQUIRE_TITLE=false
REQUIRE_SUMMARY=false

# ============================================
# Email Configuration (Optional)
# ============================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=BEACON System
FRONTEND_URL=http://localhost:3000

# ============================================
# Additional Settings
# ============================================
ENABLE_DOMAIN_VALIDATION=false
DB_ENCRYPTION_KEY=your-encryption-key-here
REDIS_URL=your-redis-url-here
```

### 2. Generate Secret Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate DB_ENCRYPTION_KEY
python -c "import base64; import os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

### 3. Create Frontend Environment

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=BEACON Platform
```

### 4. Initialize Database

```bash
# Run database migrations
alembic upgrade head

# Create initial data (optional)
python scripts/setup_initial_data.py
```

---

## Running the Application

### 1. Start Backend

```bash
# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Start backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Frontend

```bash
# In new terminal
cd frontend
npm run dev
```

### 3. Start Ollama (If Using)

```bash
# In new terminal
ollama serve
```

### 4. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Testing & Verification

### 1. Test Backend

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{ "status": "healthy", "timestamp": "2026-01-16T10:00:00Z" }
```

### 2. Test Database Connection

```bash
python -c "from backend.database import engine; print('Database connected:', engine.connect())"
```

### 3. Test AI Models

```bash
# Test metadata extraction
python test_metadata_extraction.py

# Test RAG agent
python test_rag_agent.py
```

### 4. Test Storage

```bash
# Test Supabase storage
python test_storage.py
```

### 5. Test Frontend

1. Open http://localhost:3000
2. Register new account
3. Login successfully
4. Navigate to different pages

---

## Troubleshooting

### Common Issues:

#### 1. Database Connection Failed

```
Error: connection to server failed
```

**Solution**:

- Check DATABASE\_\* variables in `.env`
- Verify Supabase project is running
- Check internet connection

#### 2. AI Model Quota Exceeded

```
Error: 429 You exceeded your current quota
```

**Solution**:

- Check Google AI Studio quota
- Switch to OpenRouter: `RAG_LLM_PROVIDER=openrouter`
- Use Ollama: `RAG_LLM_PROVIDER=ollama`

#### 3. Storage Upload Failed

```
Error: Failed to upload to Supabase
```

**Solution**:

- Check SUPABASE_URL and SUPABASE_KEY
- Verify bucket exists and is public
- Check file permissions

#### 4. Frontend Build Failed

```
Error: Module not found
```

**Solution**:

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

#### 5. Ollama Not Working

```
Error: Connection refused to localhost:11434
```

**Solution**:

```bash
# Start Ollama
ollama serve

# Check if running
curl http://localhost:11434/api/version
```

### Debug Mode:

Set environment variables for detailed logging:

```env
LOG_LEVEL=DEBUG
LANGCHAIN_TRACING_V2=true
```

---

## Production Deployment

### 1. Environment Variables

Update `.env` for production:

```env
# Use production database
DATABASE_HOSTNAME=your-prod-db-host

# Use production URLs
FRONTEND_URL=https://your-domain.com
SUPABASE_URL=https://your-prod-project.supabase.co

# Enable security
ENABLE_DOMAIN_VALIDATION=true
```

### 2. Build Frontend

```bash
cd frontend
npm run build
```

### 3. Deploy Backend

```bash
# Using Docker
docker build -t beacon-backend .
docker run -p 8000:8000 beacon-backend

# Using systemd (Linux)
sudo systemctl enable beacon-backend
sudo systemctl start beacon-backend
```

### 4. Deploy Frontend

```bash
# Build static files
npm run build

# Deploy to CDN/hosting service
# Copy dist/ folder to your web server
```

### 5. Set up Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

### 6. SSL Certificate

```bash
# Using Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

---

## Configuration Profiles

### Development Profile

```env
METADATA_LLM_PROVIDER=gemini
RAG_LLM_PROVIDER=ollama
RERANKER_PROVIDER=local
DELETE_DOCS_WITHOUT_METADATA=false
```

### Production Profile

```env
METADATA_LLM_PROVIDER=gemini
RAG_LLM_PROVIDER=gemini
RERANKER_PROVIDER=gemini
DELETE_DOCS_WITHOUT_METADATA=true
```

### High-Volume Profile

```env
METADATA_LLM_PROVIDER=gemini    # 14,400/day
RAG_LLM_PROVIDER=openrouter     # 200/day
RERANKER_PROVIDER=local
```

### Offline Profile

```env
METADATA_LLM_PROVIDER=ollama
RAG_LLM_PROVIDER=ollama
RERANKER_PROVIDER=local
```

---

## Monitoring & Maintenance

### 1. Log Files

- Backend logs: `Agent/agent_logs/`
- Scraping logs: `data/web_scraping_sessions/`
- System logs: `/var/log/beacon/`

### 2. Database Maintenance

```bash
# Backup database
pg_dump $DATABASE_URL > backup.sql

# Clean old logs
python scripts/cleanup_logs.py

# Optimize embeddings
python scripts/optimize_embeddings.py
```

### 3. Health Checks

```bash
# Check all services
python scripts/health_check.py

# Monitor quotas
python scripts/check_quotas.py
```

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Enable HTTPS in production
- [ ] Set up firewall rules
- [ ] Enable database SSL
- [ ] Rotate API keys regularly
- [ ] Set up monitoring and alerts
- [ ] Enable audit logging
- [ ] Configure rate limiting
- [ ] Set up backup strategy

---

## Support & Resources

### Documentation:

- **API Docs**: http://localhost:8000/docs
- **Architecture**: `COMPLETE_SYSTEM_ARCHITECTURE.md`
- **Troubleshooting**: `TROUBLESHOOTING.md`

### External Resources:

- [Supabase Docs](https://supabase.com/docs)
- [Google AI Studio](https://ai.google.dev)
- [OpenRouter Docs](https://openrouter.ai/docs)
- [Ollama Docs](https://ollama.ai/docs)

### Community:

- GitHub Issues: Report bugs and feature requests
- Discord: Join community discussions
- Email: support@beacon-platform.com

---

## Quick Start Commands

### First Time Setup:

```bash
# 1. Clone and setup
git clone <repo>
cd BEACON
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Setup database
alembic upgrade head

# 4. Install frontend
cd frontend
npm install
cd ..

# 5. Start services
uvicorn backend.main:app --reload &
cd frontend && npm run dev &
```

### Daily Development:

```bash
# Start backend
.\venv\Scripts\activate
uvicorn backend.main:app --reload

# Start frontend (new terminal)
cd frontend
npm run dev
```

### Production Deployment:

```bash
# Build and deploy
npm run build
docker build -t beacon .
docker run -p 8000:8000 beacon
```

---

**🎉 Your BEACON Platform is now ready to use!**

For questions or issues, refer to the troubleshooting section or contact support.
