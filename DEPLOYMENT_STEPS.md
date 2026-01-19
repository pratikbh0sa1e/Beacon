# 🚀 BEACON Platform - Complete Deployment Guide

## Ready for FREE Cloud Deployment!

Your BEACON Platform is now optimized for **$0/month** deployment with quota management.

---

## 📋 Pre-Deployment Checklist

✅ **Quota Management System**: Active and tested  
✅ **Cloud-Only Mode**: Configured (`CLOUD_ONLY_MODE=true`)  
✅ **Google API Key**: Valid and working  
✅ **Supabase Database**: Connected and configured  
✅ **Vercel Config**: Created (`vercel.json`, `_redirects`)  
✅ **Requirements**: Optimized for 512MB RAM

---

## 🚀 Step-by-Step Deployment

### Step 1: Push to GitHub

```bash
# Add all changes
git add .

# Commit with deployment message
git commit -m "Add quota management system for free-tier deployment"

# Push to GitHub
git push origin main
```

### Step 2: Deploy Backend to Render

1. **Go to [render.com](https://render.com)**
2. **Sign up/Login** with GitHub
3. **Click "New +"** → **"Web Service"**
4. **Connect your GitHub repository**
5. **Configure the service:**

```yaml
Name: beacon-backend
Environment: Python 3
Branch: main
Root Directory: (leave empty)
Build Command: pip install -r requirements.txt
Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

6. **Add Environment Variables:**

```env
CLOUD_ONLY_MODE=true
GOOGLE_API_KEY=AIzaSyBtrkvDpYbWLQZStyD8x8tOtnOHgme4jsE
DATABASE_HOSTNAME=aws-1-ap-south-1.pooler.supabase.com
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USERNAME=postgres.ppqdbqzlfxddfroxlycx
DATABASE_PASSWORD=suyashgandu
SUPABASE_URL=https://ppqdbqzlfxddfroxlycx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBwcWRicXpsZnhkZGZyb3hseWN4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NTIwMDM5MCwiZXhwIjoyMDgwNzc2MzkwfQ.ervBHaedSRli3mkphPGSypsfuRaMll56bt4GNsK1xIk
SUPABASE_BUCKET_NAME=Docs
JWT_SECRET_KEY=OZrP1ApDGpllI527XGMYupgBXATfNLyYYRAGYwenYUg
METADATA_LLM_PROVIDER=gemini
RAG_LLM_PROVIDER=gemini
RERANKER_PROVIDER=gemini
```

7. **Click "Create Web Service"**

### Step 3: Deploy Frontend to Vercel

1. **Go to [vercel.com](https://vercel.com)**
2. **Sign up/Login** with GitHub
3. **Click "New Project"**
4. **Import your GitHub repository**
5. **Vercel will auto-detect settings** from `vercel.json`
6. **Add Environment Variable:**

```env
VITE_API_BASE_URL=https://your-render-app.onrender.com/api
```

_Replace `your-render-app` with your actual Render app name_

7. **Deploy!**

### Step 4: Setup UptimeRobot (Keep Render Awake)

1. **Go to [uptimerobot.com](https://uptimerobot.com)**
2. **Create free account**
3. **Add HTTP(s) monitor:**
   - **URL**: `https://your-render-app.onrender.com/health`
   - **Monitoring Interval**: 5 minutes
   - **Alert Contacts**: Your email

This prevents your Render app from sleeping on the free tier.

---

## 🎯 Expected Results

After successful deployment:

### Backend URLs

- **API Base**: `https://your-render-app.onrender.com`
- **API Docs**: `https://your-render-app.onrender.com/docs`
- **Health Check**: `https://your-render-app.onrender.com/health`
- **Quota Status**: `https://your-render-app.onrender.com/quota/status`

### Frontend URL

- **Web App**: `https://your-vercel-app.vercel.app`

---

## 🔧 Vercel Configuration Explained

### `vercel.json` Features:

- ✅ **SPA Routing**: All routes redirect to `index.html` (fixes 404s)
- ✅ **Security Headers**: XSS protection, content type sniffing prevention
- ✅ **Caching**: Static assets cached for 1 year
- ✅ **API Proxy**: Routes `/api/*` to your Render backend

### `_redirects` (Backup):

- ✅ **Fallback routing** for any missed routes
- ✅ **API proxying** as backup

---

## 📊 Testing Your Deployment

### 1. Test Backend Health

```bash
curl https://your-render-app.onrender.com/health
```

Expected response:

```json
{
  "status": "healthy",
  "database": "connected",
  "services": [
    "auth",
    "documents",
    "chat",
    "approvals",
    "data-sources",
    "insights"
  ]
}
```

### 2. Test Quota Status

```bash
curl https://your-render-app.onrender.com/quota/status
```

Expected response:

```json
{
  "status": "success",
  "quota_status": {
    "gemini_embeddings": {
      "daily": { "used": 0, "limit": 1500, "remaining": 1500 }
    },
    "gemini_chat": { "daily": { "used": 0, "limit": 1500, "remaining": 1500 } },
    "speech_to_text": {
      "monthly": { "used": 0, "limit": 60, "remaining": 60 }
    },
    "vision_ocr": { "monthly": { "used": 0, "limit": 1000, "remaining": 1000 } }
  }
}
```

### 3. Test Frontend

Visit your Vercel URL and verify:

- ✅ App loads correctly
- ✅ Navigation works (no 404s)
- ✅ API calls work
- ✅ Login/registration functions

---

## 💰 Cost Breakdown: $0/month

| Service           | Free Tier                  | Usage                   |
| ----------------- | -------------------------- | ----------------------- |
| **Render**        | 512MB RAM, 750 hours/month | Backend hosting         |
| **Vercel**        | 100GB bandwidth/month      | Frontend hosting        |
| **Supabase**      | 500MB DB, 1GB storage      | Database + file storage |
| **Google Gemini** | 1,500 requests/day         | AI embeddings + chat    |
| **Google Speech** | 60 minutes/month           | Voice queries           |
| **Google Vision** | 1,000 requests/month       | OCR processing          |
| **UptimeRobot**   | 50 monitors                | Keep app awake          |

**Total: $0/month** 🎉

---

## 🚨 Troubleshooting

### Backend Deployment Issues

**Build fails:**

- Check `requirements.txt` is in root directory
- Verify Python version compatibility
- Check Render build logs

**App crashes:**

- Verify all environment variables are set
- Check database connection
- Review Render logs

**Memory issues:**

- Ensure `CLOUD_ONLY_MODE=true`
- Verify no local AI models are loading

### Frontend Deployment Issues

**404 errors on routes:**

- Verify `vercel.json` is in root directory
- Check `_redirects` file in frontend folder
- Ensure SPA routing is configured

**API calls fail:**

- Verify `VITE_API_BASE_URL` points to correct Render URL
- Check CORS settings in backend
- Verify backend is running

### Quota Issues

**"Quota exceeded" errors:**

- Check `/quota/status` endpoint
- Wait for quota reset (daily/monthly)
- Verify quota limits in code

---

## 📈 Monitoring & Maintenance

### Daily Monitoring

- Check UptimeRobot status
- Monitor quota usage at `/quota/status`
- Review Render logs for errors

### Weekly Tasks

- Check Vercel deployment status
- Review quota usage patterns
- Monitor database storage usage

### Monthly Tasks

- Review quota limits and usage
- Check for any security updates
- Monitor performance metrics

---

## 🎉 Success Checklist

After deployment, verify:

- [ ] Backend health check returns 200
- [ ] Frontend loads without errors
- [ ] User registration/login works
- [ ] Document upload functions
- [ ] AI chat responds correctly
- [ ] Quota tracking is active
- [ ] UptimeRobot monitoring is active
- [ ] All routes work (no 404s)
- [ ] API documentation is accessible
- [ ] Mobile responsiveness works

---

## 🔗 Useful Links

- **Render Dashboard**: https://dashboard.render.com
- **Vercel Dashboard**: https://vercel.com/dashboard
- **Supabase Dashboard**: https://app.supabase.com
- **UptimeRobot Dashboard**: https://uptimerobot.com/dashboard
- **Google AI Studio**: https://ai.google.dev

---

## 🎯 Next Steps After Deployment

1. **Test all features** thoroughly
2. **Set up monitoring alerts**
3. **Document your deployment URLs**
4. **Share with stakeholders**
5. **Plan for scaling** when you outgrow free tiers

---

**🎉 Congratulations!** Your BEACON Platform is now deployed and running completely **FREE** in the cloud with automatic quota management!

The system will automatically prevent you from exceeding free tier limits while providing a smooth user experience.
