# 🆓 BEACON Platform - Free Tier Deployment Guide

## Complete Guide for Zero-Cost Cloud Deployment with Quota Management

**Version**: 2.0.0 | **Cost**: $0/month | **Last Updated**: January 2026

---

## 🎯 Overview

This guide shows you how to deploy BEACON Platform completely **FREE** using cloud APIs with built-in quota management. The system automatically tracks usage and prevents exceeding free tier limits.

### 💰 Total Monthly Cost: $0

- **Frontend**: Vercel (Free)
- **Backend**: Render (Free)
- **Database**: Supabase (Free)
- **AI Services**: Google Cloud APIs (Free Tier)
- **Monitoring**: UptimeRobot (Free)

---

## 📊 Free Tier Quotas & Limits

### Google Cloud APIs (All FREE)

| Service               | Free Tier Limit            | Usage Tracking  |
| --------------------- | -------------------------- | --------------- |
| **Gemini Embeddings** | 1,500 requests/day         | ✅ Auto-tracked |
| **Gemini Chat**       | 1,500 requests/day, 15/min | ✅ Auto-tracked |
| **Speech-to-Text**    | 60 minutes/month           | ✅ Auto-tracked |
| **Vision OCR**        | 1,000 requests/month       | ✅ Auto-tracked |

### Infrastructure (All FREE)

| Service         | Free Tier          | Limits                     |
| --------------- | ------------------ | -------------------------- |
| **Vercel**      | Frontend hosting   | 100GB bandwidth/month      |
| **Render**      | Backend hosting    | 512MB RAM, 750 hours/month |
| **Supabase**    | Database + Storage | 500MB DB, 1GB storage      |
| **UptimeRobot** | Monitoring         | 50 monitors                |

---

## 🚀 Quick Deployment (15 minutes)

### Step 1: Get API Keys (5 minutes)

```bash
# 1. Google AI Studio API Key (FREE)
# Go to: https://ai.google.dev
# Create API key → Copy (starts with AIzaSy...)

# 2. Supabase Project (FREE)
# Go to: https://supabase.com
# Create project → Copy URL and anon key

# 3. GitHub Repository
# Fork or clone the BEACON repository
```

### Step 2: Deploy Backend to Render (5 minutes)

```bash
# 1. Go to https://render.com
# 2. Connect GitHub repository
# 3. Create Web Service with these settings:

Name: beacon-backend
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT

# 4. Add Environment Variables:
CLOUD_ONLY_MODE=true
GOOGLE_API_KEY=your_google_api_key_here
DATABASE_HOSTNAME=your_supabase_hostname
DATABASE_USERNAME=your_supabase_username
DATABASE_PASSWORD=your_supabase_password
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
JWT_SECRET_KEY=your_random_secret_here
```

### Step 3: Deploy Frontend to Vercel (3 minutes)

```bash
# 1. Go to https://vercel.com
# 2. Import GitHub repository
# 3. Set build settings:

Framework: React
Build Command: cd frontend && npm run build
Output Directory: frontend/dist

# 4. Add Environment Variable:
VITE_API_BASE_URL=https://your-render-app.onrender.com/api
```

### Step 4: Setup Database (2 minutes)

```bash
# 1. In Supabase Dashboard:
# Go to SQL Editor → Run this command:
CREATE EXTENSION IF NOT EXISTS vector;

# 2. Run migrations (from your local machine):
pip install -r requirements.txt
alembic upgrade head
```

---

## 🔧 Configuration Files

### Environment Variables (.env)

```env
# ============================================
# DEPLOYMENT CONFIGURATION
# ============================================
CLOUD_ONLY_MODE=true

# ============================================
# DATABASE (Supabase Free Tier)
# ============================================
DATABASE_HOSTNAME=your-project.supabase.co
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USERNAME=postgres.your-project-id
DATABASE_PASSWORD=your-database-password

# ============================================
# AI SERVICES (Google Cloud Free Tier)
# ============================================
GOOGLE_API_KEY=AIzaSyDkCCqQdgGtrd2t1yGjCJ4zv4QmNNjn93w

# ============================================
# LLM CONFIGURATION (Optimized for Free Tier)
# ============================================
METADATA_LLM_PROVIDER=gemini
RAG_LLM_PROVIDER=gemini
RERANKER_PROVIDER=local

# ============================================
# STORAGE (Supabase Free Tier)
# ============================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_BUCKET_NAME=Docs

# ============================================
# AUTHENTICATION
# ============================================
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# ============================================
# QUALITY CONTROL
# ============================================
DELETE_DOCS_WITHOUT_METADATA=false
REQUIRE_TITLE=false
REQUIRE_SUMMARY=false
```

### Frontend Environment (.env)

```env
VITE_API_BASE_URL=https://your-render-app.onrender.com/api
VITE_APP_NAME=BEACON Platform
```

---

## 📈 Quota Management Features

### Automatic Quota Tracking

The system automatically tracks usage for all services:

```python
# Example: Embedding with quota check
embedder = BGEEmbedder()
try:
    embedding = embedder.embed_text("sample text")
    # Quota automatically checked and consumed
except ValueError as e:
    if "quota exceeded" in str(e):
        # Show user-friendly error message
        return "Daily embedding quota exceeded. Please try again tomorrow."
```

### Real-time Quota Status

Access quota information via API:

```bash
# Get all quota status
GET /quota/status

# Get specific service quota
GET /quota/status/gemini_chat
```

### Frontend Quota Display

The QuotaStatus component shows real-time usage:

```jsx
import QuotaStatus from "./components/common/QuotaStatus";

// Display quota status in admin panel
<QuotaStatus className="mb-4" />;
```

---

## 🛡️ Error Handling & User Experience

### Quota Exceeded Messages

When quotas are exceeded, users see helpful messages:

- **Embeddings**: "Daily embedding quota exceeded. Please try again tomorrow."
- **Chat**: "Daily chat quota exceeded. Please try again tomorrow."
- **Voice**: "Monthly voice quota exceeded. Please try again next month."
- **OCR**: "Monthly OCR quota exceeded. Please try again next month."

### Fallback Mechanisms

- **OCR**: Falls back to Tesseract when Vision API quota exceeded
- **Chat**: Graceful degradation with informative error messages
- **Embeddings**: Clear error messages with retry suggestions

---

## 📊 Monitoring & Maintenance

### UptimeRobot Setup (FREE)

Keep your Render app awake with UptimeRobot:

```bash
# 1. Go to https://uptimerobot.com
# 2. Create HTTP(s) monitor:

Monitor Type: HTTP(s)
URL: https://your-render-app.onrender.com/health
Monitoring Interval: 5 minutes
Alert Contacts: Your email

# This pings your app every 5 minutes to prevent sleeping
```

### Health Check Endpoints

Monitor system health:

```bash
# Basic health check
GET /health

# Quota status check
GET /quota/status

# Service-specific quota
GET /quota/status/gemini_chat
```

### Daily Usage Patterns

Optimize usage based on patterns:

- **Peak Hours**: 9 AM - 6 PM (higher chat usage)
- **Off-Peak**: Night hours (good for batch processing)
- **Weekly Reset**: Quotas reset daily at midnight UTC

---

## 🔍 Troubleshooting

### Common Issues & Solutions

#### 1. "Quota Exceeded" Errors

```bash
# Check current usage
curl https://your-app.onrender.com/quota/status

# Wait for quota reset (daily/monthly)
# Or implement usage optimization
```

#### 2. Render App Sleeping

```bash
# Solution: UptimeRobot monitoring
# Pings app every 5 minutes to keep it awake
# Alternative: Upgrade to Render paid plan ($7/month)
```

#### 3. Database Connection Issues

```bash
# Check Supabase connection
# Verify DATABASE_* environment variables
# Ensure pgvector extension is enabled
```

#### 4. API Key Issues

```bash
# Verify Google API key is valid
curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
  "https://generativelanguage.googleapis.com/v1beta/models"
```

### Performance Optimization

#### Memory Usage (Render Free: 512MB)

- ✅ Cloud APIs only: ~200MB
- ❌ Local models: 4-8GB (won't fit)

#### Request Optimization

```python
# Batch embeddings when possible
embeddings = embedder.embed_batch(texts, batch_size=10)

# Cache frequently used results
# Use lazy embedding for efficiency
```

---

## 📈 Scaling Beyond Free Tier

### When to Upgrade

Consider upgrading when you hit these limits:

- **>1,500 chat requests/day**: Upgrade Google AI Studio
- **>60 minutes voice/month**: Upgrade Google Cloud Speech
- **>1,000 OCR requests/month**: Upgrade Google Cloud Vision
- **App sleeping issues**: Upgrade Render ($7/month)

### Upgrade Paths

| Service          | Free Tier       | Paid Tier      | Cost        |
| ---------------- | --------------- | -------------- | ----------- |
| Google AI Studio | 1,500/day       | Higher limits  | Pay-per-use |
| Render           | 512MB, sleeps   | 1GB, always on | $7/month    |
| Supabase         | 500MB DB        | 8GB DB         | $25/month   |
| Vercel           | 100GB bandwidth | 1TB bandwidth  | $20/month   |

---

## 🎉 Success Metrics

### Free Tier Capacity

With proper quota management, the free tier supports:

- **Daily Users**: 50-100 active users
- **Documents**: 1,000+ documents
- **Chat Sessions**: 100+ per day
- **Voice Queries**: 60 minutes/month total
- **OCR Processing**: 1,000 images/month

### Performance Expectations

- **Response Time**: 2-5 seconds (cloud APIs)
- **Uptime**: 99%+ with UptimeRobot
- **Reliability**: Automatic error handling
- **User Experience**: Smooth with quota awareness

---

## 🔐 Security Considerations

### API Key Security

- ✅ Store API keys in environment variables
- ✅ Use different keys for development/production
- ✅ Rotate keys quarterly
- ✅ Monitor usage for anomalies

### Database Security

- ✅ Use Supabase Row Level Security (RLS)
- ✅ Enable SSL connections
- ✅ Regular backups
- ✅ Monitor access logs

---

## 📞 Support & Resources

### Documentation

- **API Docs**: https://your-app.onrender.com/docs
- **Quota Status**: https://your-app.onrender.com/quota/status
- **Health Check**: https://your-app.onrender.com/health

### Community

- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Community support and tips
- **Documentation**: Comprehensive guides and tutorials

---

## 🏆 Conclusion

BEACON Platform can run completely **FREE** with proper quota management:

- ✅ **$0/month** operational cost
- ✅ **Automatic quota tracking** prevents overages
- ✅ **User-friendly error messages** when limits reached
- ✅ **Scalable architecture** for future growth
- ✅ **Production-ready** with monitoring and health checks

The quota management system ensures you never accidentally exceed free tier limits while providing a smooth user experience with clear feedback about usage status.

**Ready to deploy?** Follow the Quick Deployment guide above and have your free BEACON Platform running in 15 minutes!

---

**Built for**: Government and Educational Institutions  
**Deployment**: 100% Cloud-based, Zero Infrastructure Costs  
**Scalability**: Handles 50-100 daily users on free tier  
**Support**: Comprehensive documentation and community support
