@echo off
echo ========================================
echo Starting BEACON Backend Server
echo ========================================
echo.
echo Backend will run on: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo Health Check: http://localhost:8000/health
echo.
echo Press CTRL+C to stop the server
echo ========================================
echo.

python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
