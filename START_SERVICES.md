# How to Start BEACON Services

## Prerequisites
1. Python 3.8+ installed
2. Node.js 16+ installed
3. All dependencies installed

## Step 1: Start Backend Server

Open a new terminal (Terminal 1) and run:

```bash
cd C:\Users\PARTH\Desktop\BEACON
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Step 2: Start Frontend Server

Open another terminal (Terminal 2) and run:

```bash
cd C:\Users\PARTH\Desktop\BEACON\frontend
npm run dev
```

You should see:
```
VITE v7.x.x  ready in xxx ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

## Step 3: Verify Services

### Check Backend
Open browser to: http://localhost:8000/health

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "services": ["auth", "documents", "chat", "approvals", "data-sources", "insights"]
}
```

### Check Frontend
Open browser to: http://localhost:3000

You should see the BEACON landing page.

### Check API Documentation
Open browser to: http://localhost:8000/docs

You should see the Swagger API documentation.

## Step 4: Test Login

1. Go to http://localhost:3000/login
2. Try logging in with your credentials
3. If you see a 404 error, the backend is not running
4. If you see CORS errors, check the backend CORS configuration

## Troubleshooting

### Backend won't start
- Check if port 8000 is already in use: `netstat -ano | findstr :8000`
- Kill existing processes: `taskkill /F /PID <PID>`
- Check database connection in .env file

### Frontend won't start
- Check if port 3000 is already in use: `netstat -ano | findstr :3000`
- Kill existing processes: `taskkill /F /PID <PID>`
- Run `npm install` if dependencies are missing

### 404 Errors on API Calls
- Backend is not running
- Check frontend .env file has: `VITE_API_URL=http://localhost:8000`
- Restart frontend after changing .env

### CORS Errors
- Backend CORS is configured for:
  - http://localhost:3000
  - http://localhost:5173
  - http://localhost:3001
- If using different port, update backend/main.py CORS configuration

### Connection Refused
- Backend is not running on port 8000
- Check firewall settings
- Try accessing http://127.0.0.1:8000/health instead

## Quick Test Script

Run this to test connectivity:
```bash
python test_frontend_backend_connectivity.py
```

## Environment Variables

### Backend (.env in root)
```env
DATABASE_HOSTNAME=aws-1-ap-southeast-2.pooler.supabase.com
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USERNAME=postgres.amgdpxmdpyaxxzxdszvz
DATABASE_PASSWORD=#suyashgandu6
JWT_SECRET_KEY=OZrP1ApDGpllI527XGMYupgBXATfNLyYYRAGYwenYUg
SUPABASE_URL=https://amgdpxmdpyaxxzxdszvz.supabase.co
FRONTEND_URL=http://localhost:3000
```

### Frontend (.env in frontend/)
```env
VITE_API_URL=http://localhost:8000
```

## Common Issues Fixed

✅ Created frontend/.env with VITE_API_URL
✅ Fixed WebScrapingPage.jsx API URL (was using VITE_API_BASE_URL)
✅ Fixed ScrapingLogs.jsx API URL
✅ Fixed DocumentChatPanel.jsx API URL
✅ Fixed LandingFooter.jsx hardcoded URL
✅ Verified CORS configuration in backend
✅ Verified all router registrations

## Service Status

- Backend: Port 8000
- Frontend: Port 3000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
