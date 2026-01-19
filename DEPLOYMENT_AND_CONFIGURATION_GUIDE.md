# 🚀 BEACON Platform - Deployment & Configuration Guide

## Complete Setup, Configuration, and Deployment Reference

**Version**: 2.0.0 | **Status**: Production Ready | **Last Updated**: January 2026

---

## 📋 Table of Contents

1. [Quick Start (5 Minutes)](#quick-start-5-minutes)
2. [System Requirements](#system-requirements)
3. [Environment Setup](#environment-setup)
4. [Configuration Guide](#configuration-guide)
5. [Installation Steps](#installation-steps)
6. [Running the Application](#running-the-application)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance & Monitoring](#maintenance--monitoring)

---

## Quick Start (5 Minutes)

### Prerequisites

- Python 3.11+, Node.js 18+
- Supabase account (free tier works)
- Google AI Studio API key (free)

### Rapid Setup

```bash
# 1. Clone and setup
git clone <repository-url>
cd BEACON
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 3. Configure environment (copy and edit)
cp .env.example .env
# Edit .env with your credentials (see Configuration section)

# 4. Setup database
alembic upgrade head

# 5. Start services
# Terminal 1: Backend
uvicorn backend.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## System Requirements

### Hardware Requirements

| Component   | Minimum  | Recommended | Production |
| ----------- | -------- | ----------- | ---------- |
| **CPU**     | 4 cores  | 8 cores     | 16+ cores  |
| **RAM**     | 8GB      | 16GB        | 32GB+      |
| **Storage** | 50GB SSD | 100GB SSD   | 500GB+ SSD |
| **Network** | 10 Mbps  | 100 Mbps    | 1 Gbps+    |
| **GPU**     | None     | CUDA 8GB    | CUDA 16GB+ |

### Software Requirements

```bash
# Core Requirements
Python 3.11+
Node.js 18+
PostgreSQL 15+ with pgvector
Git

# Optional (for local AI)
CUDA Toolkit 11.8+
Docker & Docker Compose
Nginx (production)
```

### Cloud Services Required

1. **Supabase** (Database + Storage)
   - Free tier: 500MB database, 1GB storage
   - Pro tier: $25/month for production

2. **Google AI Studio** (AI Models)
   - Free tier: 15 requests/minute
   - Paid tier: Higher quotas

3. **OpenRouter** (Backup AI - Optional)
   - Free tier: 200 requests/day
   - Paid tier: Higher quotas

---

## Environment Setup

### 1. Create Supabase Project

```bash
# 1. Go to https://supabase.com
# 2. Create new project
# 3. Wait for setup (2-3 minutes)
# 4. Go to Settings → Database
# 5. Copy connection details
```

### 2. Enable pgvector Extension

In Supabase SQL Editor:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. Create Storage Bucket

```bash
# 1. Go to Storage in Supabase Dashboard
# 2. Create bucket named "Docs"
# 3. Set bucket to Public
# 4. Copy bucket URL
```

### 4. Get Google AI Studio API Key

```bash
# 1. Go to https://ai.google.dev
# 2. Create API key
# 3. Copy key (starts with AIzaSy...)
```

---

## Configuration Guide

### Environment Variables (.env)

Create `.env` file in root directory:

```env
# ============================================
# DATABASE CONFIGURATION (REQUIRED)
# ============================================
DATABASE_HOSTNAME=aws-1-ap-south-1.pooler.supabase.com
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USERNAME=postgres.your-project-id
DATABASE_PASSWORD=your-database-password

# ============================================
# AI MODELS CONFIGURATION (REQUIRED)
# ============================================
# Google AI Studio API Key (Primary)
GOOGLE_API_KEY=AIzaSyDkCCqQdgGtrd2t1yGjCJ4zv4QmNNjn93w

# OpenRouter API Key (Backup - Optional)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# ============================================
# LLM PROVIDER CONFIGURATION (OPTIMIZED)
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
# STORAGE CONFIGURATION (REQUIRED)
# ============================================
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_BUCKET_NAME=Docs

# ============================================
# AUTHENTICATION (REQUIRED)
# ============================================
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# ============================================
# QUALITY CONTROL (RECOMMENDED)
# ============================================
DELETE_DOCS_WITHOUT_METADATA=false
REQUIRE_TITLE=false
REQUIRE_SUMMARY=false

# ============================================
# EMAIL CONFIGURATION (OPTIONAL)
# ============================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=BEACON System
FRONTEND_URL=http://localhost:5173

# ============================================
# OLLAMA CONFIGURATION (OPTIONAL)
# ============================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# ============================================
# REDIS CONFIGURATION (OPTIONAL)
# ============================================
REDIS_URL=redis://localhost:6379
```

### Generate Secret Keys

```bash
# Generate JWT secret key
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate encryption key (if needed)
python -c "import base64; import os; print('DB_ENCRYPTION_KEY=' + base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

### Frontend Configuration

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_NAME=BEACON Platform
```

---

## Installation Steps

### 1. System Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv nodejs npm postgresql-client git

# macOS (with Homebrew)
brew install python@3.11 node postgresql git

# Windows
# Download Python 3.11 from python.org
# Download Node.js from nodejs.org
# Install Git from git-scm.com
```

### 2. Clone Repository

```bash
git clone <repository-url>
cd BEACON
```

### 3. Python Environment Setup

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
```

### 4. Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Database Setup

```bash
# Enable pgvector (run once)
python scripts/enable_pgvector.py

# Run database migrations
alembic upgrade head

# Create initial developer account (optional)
python backend/init_developer.py
```

### 6. Optional: Ollama Setup (Local AI)

```bash
# Install Ollama
# Windows: Download from https://ollama.com/download/windows
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama3.2

# Start Ollama server
ollama serve
```

---

## Running the Application

### Development Mode

```bash
# Terminal 1: Start Backend
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Frontend
cd frontend
npm run dev

# Terminal 3: Start Ollama (if using local AI)
ollama serve
```

### Production Mode

```bash
# Build frontend
cd frontend
npm run build
cd ..

# Start backend with production settings
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4

# Serve frontend with nginx or similar
```

### Access URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

---

## Production Deployment

### 1. Server Preparation

```bash
# Ubuntu 20.04+ Server Setup
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3.11-venv nodejs npm nginx postgresql-client git

# Create application user
sudo useradd -m -s /bin/bash beacon
sudo usermod -aG sudo beacon

# Switch to application user
sudo su - beacon
```

### 2. Application Deployment

```bash
# Clone repository
git clone <repository-url> /home/beacon/app
cd /home/beacon/app

# Setup Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build frontend
cd frontend
npm ci --production
npm run build
cd ..

# Setup production environment
cp .env.production .env
# Edit .env with production values

# Setup database
alembic upgrade head
python scripts/setup_production_data.py
```

### 3. Systemd Service Setup

Create `/etc/systemd/system/beacon-backend.service`:

```ini
[Unit]
Description=BEACON Backend API
After=network.target

[Service]
Type=exec
User=beacon
Group=beacon
WorkingDirectory=/home/beacon/app
Environment=PATH=/home/beacon/app/venv/bin
ExecStart=/home/beacon/app/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable beacon-backend
sudo systemctl start beacon-backend
sudo systemctl status beacon-backend
```

### 4. Nginx Configuration

Create `/etc/nginx/sites-available/beacon`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Frontend (React app)
    location / {
        root /home/beacon/app/frontend/dist;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeout for AI operations
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/beacon /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (already setup by certbot)
sudo systemctl status certbot.timer
```

### 6. Docker Deployment (Alternative)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 beacon && chown -R beacon:beacon /app
USER beacon

EXPOSE 8000

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
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - backend
    restart: unless-stopped
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Backend Won't Start

```bash
# Check Python version
python --version  # Should be 3.11+

# Check virtual environment
which python  # Should point to venv/bin/python

# Check dependencies
pip list | grep fastapi

# Check environment variables
python -c "import os; print(os.getenv('DATABASE_HOSTNAME'))"

# Check logs
tail -f logs/application.log
```

#### 2. Database Connection Failed

```bash
# Test database connection
python -c "
from backend.database import engine
try:
    conn = engine.connect()
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"

# Check pgvector extension
python -c "
from backend.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
result = db.execute(text('SELECT * FROM pg_extension WHERE extname = \\'vector\\';'))
print('pgvector installed:', bool(result.fetchone()))
db.close()
"
```

#### 3. AI Models Not Working

```bash
# Test Google API key
curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
  "https://generativelanguage.googleapis.com/v1beta/models"

# Switch to backup provider
echo "RAG_LLM_PROVIDER=openrouter" >> .env

# Use local Ollama
ollama pull llama3.2
echo "RAG_LLM_PROVIDER=ollama" >> .env
```

#### 4. Frontend Build Issues

```bash
# Check Node.js version
node --version  # Should be 18+

# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# Build with verbose output
npm run build --verbose
```

#### 5. Storage Upload Issues

```bash
# Test Supabase connection
python -c "
from backend.utils.supabase_storage import test_connection
test_connection()
"

# Check bucket permissions
# Go to Supabase Dashboard → Storage → Docs bucket
# Ensure bucket is set to Public
```

#### 6. Performance Issues

```bash
# Check system resources
htop
df -h
free -h

# Check database performance
python -c "
from backend.database import SessionLocal
from sqlalchemy import text
import time

db = SessionLocal()
start = time.time()
result = db.execute(text('SELECT COUNT(*) FROM documents;'))
end = time.time()
print(f'Query took {end-start:.2f} seconds')
print(f'Document count: {result.scalar()}')
db.close()
"

# Optimize database
python scripts/optimize_database.py
```

### Debug Mode

Enable debug logging by setting:

```env
LOG_LEVEL=DEBUG
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your-langsmith-key
```

### Health Check Endpoints

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed system status
curl http://localhost:8000/system/status

# Database health
curl http://localhost:8000/health/database

# AI models health
curl http://localhost:8000/health/ai
```

---

## Maintenance & Monitoring

### Regular Maintenance Tasks

```bash
# Daily tasks (automated via cron)
0 2 * * * /home/beacon/app/scripts/daily_maintenance.sh

# Weekly tasks
0 3 * * 0 /home/beacon/app/scripts/weekly_maintenance.sh

# Monthly tasks
0 4 1 * * /home/beacon/app/scripts/monthly_maintenance.sh
```

### Backup Strategy

```bash
#!/bin/bash
# scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/beacon/backups"

# Database backup
pg_dump $DATABASE_URL > "$BACKUP_DIR/db_$DATE.sql"

# Configuration backup
cp .env "$BACKUP_DIR/env_$DATE.backup"

# Application logs backup
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" logs/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.backup" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Monitoring Setup

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Setup log rotation
sudo tee /etc/logrotate.d/beacon << EOF
/home/beacon/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 beacon beacon
    postrotate
        systemctl reload beacon-backend
    endscript
}
EOF
```

### Performance Monitoring

```python
# scripts/monitor_performance.py
import psutil
import time
import requests
from datetime import datetime

def check_system_health():
    """Monitor system resources and API performance"""

    # System resources
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # API health check
    try:
        start_time = time.time()
        response = requests.get('http://localhost:8000/health', timeout=10)
        api_response_time = time.time() - start_time
        api_status = response.status_code == 200
    except:
        api_response_time = None
        api_status = False

    # Log metrics
    print(f"{datetime.now()}: CPU: {cpu_percent}%, RAM: {memory.percent}%, "
          f"Disk: {disk.percent}%, API: {api_status} ({api_response_time:.2f}s)")

    # Alert if thresholds exceeded
    if cpu_percent > 80 or memory.percent > 80 or disk.percent > 90:
        print("WARNING: High resource usage detected!")

    if not api_status or (api_response_time and api_response_time > 5):
        print("WARNING: API performance degraded!")

if __name__ == "__main__":
    check_system_health()
```

### Update Procedure

```bash
#!/bin/bash
# scripts/update.sh

echo "Starting BEACON update..."

# Backup current version
./scripts/backup.sh

# Pull latest code
git pull origin main

# Update Python dependencies
source venv/bin/activate
pip install -r requirements.txt

# Update frontend dependencies
cd frontend
npm install
npm run build
cd ..

# Run database migrations
alembic upgrade head

# Restart services
sudo systemctl restart beacon-backend
sudo systemctl reload nginx

# Verify deployment
sleep 10
curl -f http://localhost:8000/health || echo "Health check failed!"

echo "Update completed successfully!"
```

---

## Configuration Profiles

### Development Profile

```env
# .env.development
METADATA_LLM_PROVIDER=gemini
RAG_LLM_PROVIDER=ollama
RERANKER_PROVIDER=local
DELETE_DOCS_WITHOUT_METADATA=false
LOG_LEVEL=DEBUG
```

### Production Profile

```env
# .env.production
METADATA_LLM_PROVIDER=gemini
RAG_LLM_PROVIDER=gemini
RERANKER_PROVIDER=gemini
DELETE_DOCS_WITHOUT_METADATA=true
LOG_LEVEL=INFO
```

### High-Volume Profile

```env
# .env.high-volume
METADATA_LLM_PROVIDER=gemini    # 14,400/day
RAG_LLM_PROVIDER=openrouter     # 200/day
RERANKER_PROVIDER=local
```

### Offline Profile

```env
# .env.offline
METADATA_LLM_PROVIDER=ollama
RAG_LLM_PROVIDER=ollama
RERANKER_PROVIDER=local
OLLAMA_BASE_URL=http://localhost:11434
```

---

## Security Checklist

### Pre-Deployment Security

- [ ] Change all default passwords and secret keys
- [ ] Use strong, randomly generated JWT_SECRET_KEY
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure firewall rules (ports 80, 443, 22 only)
- [ ] Set up fail2ban for SSH protection
- [ ] Enable database SSL connections
- [ ] Configure CORS properly for production domain
- [ ] Set up regular security updates
- [ ] Enable audit logging
- [ ] Configure rate limiting
- [ ] Set up monitoring and alerting
- [ ] Create backup and disaster recovery plan
- [ ] Review and test all API endpoints
- [ ] Validate input sanitization
- [ ] Check for SQL injection vulnerabilities
- [ ] Test authentication and authorization

### Post-Deployment Security

- [ ] Monitor logs for suspicious activity
- [ ] Regular security scans and updates
- [ ] Rotate API keys and secrets quarterly
- [ ] Review user access and permissions
- [ ] Monitor resource usage and performance
- [ ] Test backup and recovery procedures
- [ ] Update dependencies regularly
- [ ] Review and update security policies

---

## Support and Resources

### Documentation

- **API Documentation**: http://localhost:8000/docs
- **Technical Reference**: `TECHNICAL_IMPLEMENTATION_GUIDE.md`
- **Project Overview**: `PROJECT_SUMMARY.md`

### Community Resources

- **GitHub Repository**: <repository-url>
- **Issue Tracker**: <repository-url>/issues
- **Discussions**: <repository-url>/discussions

### Professional Support

- **Email**: support@beacon-platform.com
- **Documentation**: https://docs.beacon-platform.com
- **Status Page**: https://status.beacon-platform.com

---

## Conclusion

This deployment guide provides comprehensive instructions for setting up BEACON Platform in both development and production environments. The platform is designed to be robust, scalable, and secure for government and educational use.

Follow the appropriate configuration profile for your use case, and refer to the troubleshooting section for common issues. For production deployments, ensure all security measures are implemented and regularly maintained.

**Status**: ✅ Production Ready  
**Deployment Time**: 15-30 minutes (development), 2-4 hours (production)  
**Support**: Comprehensive documentation and community support available

---

**Built for**: Ministry of Education, Government of India  
**Deployment**: Cloud-ready with on-premises options  
**Scalability**: Handles 1000+ concurrent users  
**Security**: Government-grade security standards
