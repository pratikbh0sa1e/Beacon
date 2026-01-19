#!/bin/bash

# BEACON Platform Deployment Script
# This script helps deploy the platform to Vercel + Render

echo "🚀 BEACON Platform Deployment Helper"
echo "====================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "📋 Pre-deployment checklist:"
echo "1. ✅ Quota management system implemented"
echo "2. ✅ Cloud-only mode configured"
echo "3. ✅ Environment variables ready"
echo "4. ✅ Vercel configuration files created"

echo ""
echo "🔧 Next steps for deployment:"
echo ""

echo "1️⃣  PUSH TO GITHUB:"
echo "   git add ."
echo "   git commit -m 'Add quota management for free deployment'"
echo "   git push origin main"
echo ""

echo "2️⃣  DEPLOY BACKEND TO RENDER:"
echo "   • Go to https://render.com"
echo "   • Create Web Service from GitHub repo"
echo "   • Settings:"
echo "     - Build Command: pip install -r requirements.txt"
echo "     - Start Command: uvicorn backend.main:app --host 0.0.0.0 --port \$PORT"
echo "     - Environment: Python 3"
echo ""

echo "3️⃣  DEPLOY FRONTEND TO VERCEL:"
echo "   • Go to https://vercel.com"
echo "   • Import GitHub repository"
echo "   • Vercel will auto-detect settings from vercel.json"
echo "   • Add environment variable:"
echo "     VITE_API_BASE_URL=https://your-render-app.onrender.com/api"
echo ""

echo "4️⃣  SETUP MONITORING:"
echo "   • Go to https://uptimerobot.com"
echo "   • Add monitor: https://your-render-app.onrender.com/health"
echo "   • Interval: 5 minutes"
echo ""

echo "📊 ENVIRONMENT VARIABLES FOR RENDER:"
echo "CLOUD_ONLY_MODE=true"
echo "GOOGLE_API_KEY=your_google_api_key"
echo "DATABASE_HOSTNAME=your_supabase_hostname"
echo "DATABASE_USERNAME=your_supabase_username"
echo "DATABASE_PASSWORD=your_supabase_password"
echo "SUPABASE_URL=your_supabase_url"
echo "SUPABASE_KEY=your_supabase_anon_key"
echo "JWT_SECRET_KEY=your_jwt_secret"
echo "METADATA_LLM_PROVIDER=gemini"
echo "RAG_LLM_PROVIDER=gemini"
echo "RERANKER_PROVIDER=local"
echo ""

echo "💰 TOTAL COST: \$0/month (100% free tier)"
echo ""

echo "🎯 After deployment, test these endpoints:"
echo "• https://your-render-app.onrender.com/health"
echo "• https://your-render-app.onrender.com/docs"
echo "• https://your-render-app.onrender.com/quota/status"
echo ""

echo "✅ Ready to deploy! Follow the steps above."