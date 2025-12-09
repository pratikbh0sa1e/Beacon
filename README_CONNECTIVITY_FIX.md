# 🔧 BEACON Frontend-Backend Connectivity - FIXED ✅

## 🎯 Quick Start

### Option 1: Using Batch Scripts (Windows)
1. **Start Backend:** Double-click `start-backend.bat`
2. **Start Frontend:** Double-click `start-frontend.bat`
3. **Open Browser:** Go to http://localhost:3000

### Option 2: Manual Start
**Terminal 1 (Backend):**
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

## 🐛 What Was Wrong?

### 1. Missing Environment Configuration
- Frontend had no `.env` file
- API URL was undefined, causing 404 errors

### 2. Inconsistent API URL Variables
- Some files used `VITE_API_URL`
- Others used `VITE_API_BASE_URL`
- This caused connection failures

### 3. Multiple Backend Processes
- 3 uvicorn processes running simultaneously
- Caused port conflicts and timeouts

## ✅ What Was Fixed?

### 1. Created Frontend Environment File
**File:** `frontend/.env`
```env
VITE_API_URL=http://localhost:8000
```

### 2. Standardized API URL Configuration
Fixed 4 files to use consistent `VITE_API_URL`:
- ✅ `WebScrapingPage.jsx`
- ✅ `ScrapingLogs.jsx`
- ✅ `DocumentChatPanel.jsx`
- ✅ `LandingFooter.jsx`

### 3. Cleaned Up Backend Processes
- Killed duplicate processes
- Ensured single backend instance

### 4. Verified CORS Configuration
- Backend allows: localhost:3000, localhost:5173, localhost:3001
- All origins properly configured

## 📋 Files Created

1. **`frontend/.env`** - Frontend environment variables
2. **`start-backend.bat`** - Easy backend startup script
3. **`start-frontend.bat`** - Easy frontend startup script
4. **`test_frontend_backend_connectivity.py`** - Connectivity test script
5. **`START_SERVICES.md`** - Detailed startup guide
6. **`CONNECTIVITY_FIXES_COMPLETE.md`** - Complete fix documentation
7. **`FRONTEND_BACKEND_CONNECTIVITY_FIX.md`** - Technical details

## 🧪 Test Your Setup

Run the connectivity test:
```bash
python test_frontend_backend_connectivity.py
```

This will verify:
- ✅ Backend is running
- ✅ All API endpoints are accessible
- ✅ Health check passes
- ✅ Web scraping endpoints work

## 🌐 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Main application |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger documentation |
| Health Check | http://localhost:8000/health | Backend status |

## 🔍 Verify Everything Works

### 1. Check Backend
```bash
curl http://localhost:8000/health
```
Should return:
```json
{"status": "healthy", "database": "connected", ...}
```

### 2. Check Frontend
Open browser to: http://localhost:3000
- Should see BEACON landing page
- No console errors

### 3. Test Login
1. Go to http://localhost:3000/login
2. Enter credentials
3. Should login successfully (no 404 errors)

### 4. Test Web Scraping
1. Login as admin/developer
2. Go to http://localhost:3000/admin/web-scraping
3. Should see scraping dashboard
4. Stats should load without errors

## 🚨 Troubleshooting

### "Cannot connect to server" Error
**Problem:** Backend not running
**Solution:** 
```bash
# Check if backend is running
netstat -ano | findstr :8000

# If not running, start it
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### "404 Not Found" on API Calls
**Problem:** Wrong API URL or backend not running
**Solution:**
1. Check `frontend/.env` exists and has: `VITE_API_URL=http://localhost:8000`
2. Restart frontend after changing .env
3. Verify backend is running

### CORS Errors
**Problem:** Frontend port not allowed
**Solution:** Backend CORS is configured for ports 3000, 5173, 3001. If using different port, update `backend/main.py`

### Port Already in Use
**Problem:** Port 8000 or 3000 already taken
**Solution:**
```bash
# Find process using port
netstat -ano | findstr :8000

# Kill process
taskkill /F /PID <PID>
```

## 📊 API Endpoints Reference

### Authentication
- `POST /auth/login` - Login
- `POST /auth/register` - Register
- `GET /auth/me` - Current user
- `POST /auth/logout` - Logout

### Web Scraping
- `GET /api/web-scraping/stats` - Statistics
- `GET /api/web-scraping/sources` - List sources
- `POST /api/web-scraping/sources` - Create source
- `POST /api/web-scraping/sources/{id}/scrape` - Trigger scrape
- `GET /api/web-scraping/logs` - Scraping logs
- `GET /api/web-scraping/scraped-documents` - Documents

### Documents
- `GET /documents/list` - List documents
- `POST /documents/upload` - Upload
- `GET /documents/{id}` - Get document

### System
- `GET /health` - Health check
- `GET /` - Root info
- `GET /docs` - API documentation

## 🎉 Success Indicators

You'll know everything is working when:
- ✅ Backend starts without errors
- ✅ Frontend starts without errors
- ✅ Login works (no 404)
- ✅ Web scraping page loads data
- ✅ No CORS errors in console
- ✅ API calls succeed
- ✅ Health check returns "healthy"

## 📝 Environment Variables

### Backend (`.env` in root)
```env
DATABASE_HOSTNAME=aws-1-ap-southeast-2.pooler.supabase.com
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USERNAME=postgres.amgdpxmdpyaxxzxdszvz
DATABASE_PASSWORD=#suyashgandu6
JWT_SECRET_KEY=OZrP1ApDGpllI527XGMYupgBXATfNLyYYRAGYwenYUg
SUPABASE_URL=https://amgdpxmdpyaxxzxdszvz.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
FRONTEND_URL=http://localhost:3000
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=beacon.system.67@gmail.com
```

### Frontend (`frontend/.env`)
```env
VITE_API_URL=http://localhost:8000
```

## 🔄 After Making Changes

### If you modify backend code:
- Backend auto-reloads (--reload flag)
- No restart needed

### If you modify frontend code:
- Frontend auto-reloads (Vite HMR)
- No restart needed

### If you modify .env files:
- **Backend:** Restart backend server
- **Frontend:** Restart frontend server

## 📚 Additional Documentation

- **`START_SERVICES.md`** - Detailed startup instructions
- **`CONNECTIVITY_FIXES_COMPLETE.md`** - Complete fix documentation
- **`FRONTEND_BACKEND_CONNECTIVITY_FIX.md`** - Technical details
- **`test_frontend_backend_connectivity.py`** - Test script

## ✨ Summary

All frontend-backend connectivity issues have been resolved:
- ✅ Environment variables configured
- ✅ API URLs standardized
- ✅ CORS properly set up
- ✅ All endpoints accessible
- ✅ Easy startup scripts created
- ✅ Test script provided

**The application is now ready to use!** 🚀

---

**Need Help?**
1. Run the test script: `python test_frontend_backend_connectivity.py`
2. Check the logs in both terminal windows
3. Verify environment variables are correct
4. Ensure no firewall is blocking ports 3000 or 8000
