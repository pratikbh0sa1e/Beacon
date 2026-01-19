# 🚀 Deployment Checklist

## ✅ Pre-Deployment Steps

### 1. Code Preparation

- [x] Fixed RAG agent quota management error
- [x] Optimized reranker to use OpenRouter (preserves Gemini quota)
- [x] Updated requirements.txt for cloud deployment
- [x] Created production environment configuration
- [x] Added Vercel configuration for React routing

### 2. Environment Variables

- [x] Created `render.env` with production settings
- [x] Updated `.gitignore` to exclude sensitive files
- [x] Verified all API keys are working

### 3. Quota Management

- [x] Gemini Chat: 1,500/day + 15/min
- [x] Gemini Embeddings: 1,500/day
- [x] OpenRouter Reranker: 200/day
- [x] Google Cloud Speech: 60 min/month
- [x] Google Cloud Vision: 1,000/month

## 🔄 Git Commit & Push

### Safe to Commit:

```bash
git add .
git commit -m "feat: optimize system for free-tier deployment

- Fix RAG agent quota management error
- Switch reranker from Gemini to OpenRouter to preserve quota
- Add comprehensive quota tracking for all services
- Update requirements.txt for cloud deployment
- Add Vercel configuration for React routing
- Create deployment guides and scripts"

git push origin main
```

### Files Excluded from Git (Sensitive):

- `.env` (local development)
- `render.env` (production secrets)
- All environment files are in `.gitignore`

## 🌐 Render Deployment Steps

### 1. Create Render Web Service

1. Go to [render.com](https://render.com)
2. Connect your GitHub repository
3. Create new "Web Service"
4. Select your repository and branch (main)

### 2. Configure Build Settings

```
Build Command: pip install -r requirements.txt
Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

### 3. Add Environment Variables

Copy ALL variables from `render.env` to Render's environment variables section:

- Go to your service → Environment
- Add each variable from `render.env`
- **IMPORTANT**: Update `FRONTEND_URL` to your actual Vercel URL

### 4. Deploy

- Click "Create Web Service"
- Wait for deployment (5-10 minutes)
- Note your Render URL: `https://your-app-name.onrender.com`

## ⚡ Vercel Deployment Steps

### 1. Update API URLs

Before deploying frontend, update the Vercel config:

In `vercel.json`, replace:

```json
"dest": "https://your-render-app.onrender.com/api/$1"
```

With your actual Render URL.

### 2. Deploy to Vercel

```bash
cd frontend
npm install
npm run build  # Test build locally
```

Then either:

- **Option A**: Connect GitHub repo to Vercel dashboard
- **Option B**: Use Vercel CLI: `npx vercel --prod`

### 3. Update Environment Variables

In Render, update `FRONTEND_URL` to your Vercel URL:

```
FRONTEND_URL=https://your-app.vercel.app
```

## 🔍 Post-Deployment Verification

### 1. Backend Health Check

Visit: `https://your-render-app.onrender.com/health`
Should return: `{"status": "healthy"}`

### 2. Frontend Access

Visit: `https://your-app.vercel.app`
Should load the landing page

### 3. API Connection

Test login/registration to verify frontend-backend communication

### 4. Quota Monitoring

Check: `https://your-render-app.onrender.com/quota/status`
Should show all service quotas

## 🎯 UptimeRobot Setup (Keep Render Awake)

1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Create free account
3. Add monitor:
   - Type: HTTP(s)
   - URL: `https://your-render-app.onrender.com/health`
   - Interval: 5 minutes
4. This prevents Render free tier from sleeping

## 🚨 Important Notes

### Security

- ✅ All sensitive data excluded from git
- ✅ Environment variables properly configured
- ✅ API keys secured in Render environment

### Free Tier Limits

- ✅ Render: 512MB RAM, sleeps after 15min inactivity
- ✅ Vercel: 100GB bandwidth, unlimited requests
- ✅ Supabase: 500MB database, 2GB bandwidth
- ✅ All API quotas optimized for free tiers

### Monitoring

- Set up UptimeRobot to prevent Render sleeping
- Monitor quota usage via `/quota/status` endpoint
- Check logs in Render dashboard for issues

## 🎉 Success Criteria

- [ ] Backend deployed and accessible
- [ ] Frontend deployed and accessible
- [ ] API communication working
- [ ] User registration/login working
- [ ] Document upload working
- [ ] Chat functionality working
- [ ] Quota limits enforced
- [ ] UptimeRobot monitoring active

## 📞 Support

If you encounter issues:

1. Check Render logs for backend errors
2. Check browser console for frontend errors
3. Verify all environment variables are set
4. Test API endpoints individually
5. Check quota status if getting limit errors
