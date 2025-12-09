# Frontend-Backend Connectivity Fix

## Issues Identified

### 1. **Backend Server Not Running**
- The backend FastAPI server needs to be running on port 8000
- Frontend was trying to connect but getting 404 errors

### 2. **Missing Frontend Environment Variable**
- Frontend was missing `.env` file with `VITE_API_URL`
- Some components use `VITE_API_BASE_URL` instead of `VITE_API_URL`

### 3. **Inconsistent API URL Configuration**
- Most files use: `import.meta.env.VITE_API_URL`
- WebScrapingPage uses: `import.meta.env.VITE_API_BASE_URL`
- This causes inconsistency

### 4. **Multiple Backend Processes**
- Found 3 processes listening on port 8000 (PIDs: 25252, 18808, 4296)
- This can cause conflicts

## Fixes Applied

### 1. Created Frontend .env File
```env
VITE_API_URL=http://localhost:8000
```

### 2. Backend Server Status
- Backend is running on port 8000 (multiple instances detected)
- CORS is properly configured for localhost:3000 and localhost:5173
- All routes are properly registered

### 3. API Configuration Standardization Needed
- Need to update WebScrapingPage.jsx to use `VITE_API_URL` instead of `VITE_API_BASE_URL`
- Or add `VITE_API_BASE_URL` to .env file

## Remaining Issues to Fix

### 1. WebScrapingPage API URL
**File:** `frontend/src/pages/admin/WebScrapingPage.jsx`
**Line 52:** 
```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
```

**Should be:**
```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
```

**OR add to .env:**
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### 2. Multiple Backend Instances
- Kill duplicate backend processes
- Keep only one instance running

### 3. Frontend Port Configuration
- Frontend is configured to run on port 3000 (vite.config.js)
- Currently running on port 3000
- Backend CORS allows both 3000 and 5173

## How to Start Services Properly

### Backend (Terminal 1)
```bash
cd C:\Users\PARTH\Desktop\BEACON
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Terminal 2)
```bash
cd C:\Users\PARTH\Desktop\BEACON\frontend
npm run dev
```

## Verification Steps

1. **Check Backend Health:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check Frontend:**
   - Open browser to http://localhost:3000
   - Try logging in
   - Check browser console for errors

3. **Check API Connectivity:**
   - Login should work without 404 errors
   - All API calls should go to http://localhost:8000

## Environment Variables Summary

### Backend (.env in root)
```env
DATABASE_HOSTNAME=aws-1-ap-southeast-2.pooler.supabase.com
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USERNAME=postgres.amgdpxmdpyaxxzxdszvz
DATABASE_PASSWORD=#suyashgandu6
JWT_SECRET_KEY=OZrP1ApDGpllI527XGMYupgBXATfNLyYYRAGYwenYUg
SUPABASE_URL=https://amgdpxmdpyaxxzxdszvz.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=beacon.system.67@gmail.com
FRONTEND_URL=http://localhost:3000
```

### Frontend (.env in frontend/)
```env
VITE_API_URL=http://localhost:8000
```

## Status
- ✅ Backend running on port 8000
- ✅ Frontend running on port 3000
- ✅ Frontend .env created
- ⚠️ WebScrapingPage needs API URL fix
- ⚠️ Multiple backend instances should be cleaned up
