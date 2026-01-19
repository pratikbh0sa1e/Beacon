# Free-Tier Cloud Deployment Guide

## ✅ System Status

- **RAG Agent**: Fixed and working with quota management
- **OCR Service**: Updated to use Google Cloud Vision API
- **Reranker**: Configured to use OpenRouter (preserves Gemini quota)
- **Dependencies**: Optimized for 512MB RAM deployment
- **Quota Management**: Active for all Google Cloud services

## 🚀 Deployment Steps

### 1. Frontend Deployment (Vercel)

1. **Connect Repository to Vercel**

   ```bash
   # Push your code to GitHub first
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy on Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Set build settings:
     - **Framework**: Vite
     - **Root Directory**: `frontend`
     - **Build Command**: `npm run build`
     - **Output Directory**: `dist`

3. **Environment Variables** (Vercel Dashboard)
   ```
   VITE_API_URL=https://your-render-app.onrender.com
   ```

### 2. Backend Deployment (Render)

1. **Connect Repository to Render**
   - Go to [render.com](https://render.com)
   - Create new Web Service
   - Connect your GitHub repository

2. **Build Settings**

   ```
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Environment Variables** (Copy from render.env)

   ```bash
   # Core Configuration
   CLOUD_ONLY_MODE=true

   # Database (Supabase)
   DATABASE_HOSTNAME=aws-1-ap-south-1.pooler.supabase.com
   DATABASE_PORT=5432
   DATABASE_NAME=postgres
   DATABASE_USERNAME=postgres.ppqdbqzlfxddfroxlycx
   DATABASE_PASSWORD=suyashgandu

   # Google API (Free Tier with Quota Management)
   GOOGLE_API_KEY=AIzaSyBtrkvDpYbWLQZStyD8x8tOtnOHgme4jsE

   # OpenRouter (Free Models)
   OPENROUTER_API_KEY=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
   OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

   # LLM Providers (Optimized for Free Tier)
   METADATA_LLM_PROVIDER=gemini
   RAG_LLM_PROVIDER=gemini
   RERANKER_PROVIDER=openrouter

   # Supabase Storage
   SUPABASE_URL=https://ppqdbqzlfxddfroxlycx.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBwcWRicXpsZnhkZGZyb3hseWN4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NTIwMDM5MCwiZXhwIjoyMDgwNzc2MzkwfQ.ervBHaedSRli3mkphPGSypsfuRaMll56bt4GNsK1xIk
   SUPABASE_BUCKET_NAME=Docs

   # Security
   JWT_SECRET_KEY=OZrP1ApDGpllI527XGMYupgBXATfNLyYYRAGYwenYUg
   SECRET_KEY=mx7c1dF3CC51449E8674654DBbCC04211f1

   # Email (Gmail SMTP)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=beacon.system.67@gmail.com
   SMTP_PASSWORD=qzyawbepdaccunzh
   FROM_EMAIL=beacon.system.67@gmail.com
   FROM_NAME=BEACON System

   # Redis (Upstash)
   REDIS_URL=rediss://default:Aa1FAAIncDJmOWM1MjMzNTMxMGI0MTQ3YjVhYjg5OTUzMjZkNzg2MnAyNDQzNTc@included-krill-44357.upstash.io:6379
   ```

### 3. Database Setup (Supabase)

Your Supabase database is already configured. The connection details are in the environment variables above.

### 4. Monitoring Setup (UptimeRobot)

1. **Create UptimeRobot Account** (Free)
   - Go to [uptimerobot.com](https://uptimerobot.com)
   - Sign up for free account

2. **Add HTTP Monitor**
   - URL: `https://your-render-app.onrender.com/health`
   - Interval: 5 minutes
   - This keeps your Render app awake on free tier

## 📊 Free Tier Quotas

### Google Cloud APIs (with Quota Management)

- **Gemini Embeddings**: 1,500 requests/day
- **Gemini Chat**: 1,500 requests/day, 15/minute
- **Speech-to-Text**: 60 minutes/month
- **Vision OCR**: 1,000 requests/month

### OpenRouter (Free Models)

- **Llama 3.3 70B**: 200 requests/day
- **Gemini 2.0 Flash**: 200 requests/day

### Infrastructure

- **Vercel**: Unlimited static hosting
- **Render**: 750 hours/month (free tier)
- **Supabase**: 500MB database, 1GB bandwidth
- **Upstash Redis**: 10,000 requests/day

## 🔧 Quota Management Features

The system automatically:

- ✅ Tracks usage for all APIs
- ✅ Shows "quota exceeded" errors instead of charges
- ✅ Falls back to alternative services when possible
- ✅ Resets quotas daily/monthly as appropriate
- ✅ Provides quota status in admin dashboard

## 🚨 Important Notes

1. **Render Free Tier**: Apps sleep after 15 minutes of inactivity
   - **Solution**: UptimeRobot pings every 5 minutes to keep awake
   - **Limitation**: 750 hours/month total (about 25 days)

2. **Memory Limit**: 512MB RAM on Render free tier
   - **Solution**: Removed heavy dependencies (sentence-transformers, whisper, easyocr)
   - **Alternative**: Using cloud APIs instead of local models

3. **Cold Starts**: First request after sleep takes 30-60 seconds
   - **Solution**: UptimeRobot keeps app warm during business hours

## 🎯 Next Steps

1. **Deploy Frontend**: Push to Vercel
2. **Deploy Backend**: Push to Render with environment variables
3. **Setup Monitoring**: Configure UptimeRobot
4. **Test System**: Verify all features work in production
5. **Monitor Quotas**: Check usage in admin dashboard

## 📞 Support

If you encounter issues:

1. Check Render logs for backend errors
2. Check Vercel function logs for frontend issues
3. Verify all environment variables are set correctly
4. Monitor quota usage in the admin dashboard

Your system is now optimized for completely free deployment! 🎉
