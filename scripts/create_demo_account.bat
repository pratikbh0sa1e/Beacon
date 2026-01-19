@echo off
REM Create Demo Account - Windows Batch Script
REM This script creates a demo account for testing BEACON platform

echo.
echo ========================================
echo   BEACON Demo Account Creator
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "backend\main.py" (
    echo ❌ Please run this script from the project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Load environment variables if .env exists
if exist ".env" (
    echo ✓ Loading environment variables from .env
) else (
    echo ⚠️  .env file not found - using default database settings
)

echo.
echo 🎯 Creating demo account...
echo.

REM Run the demo account creation script
python scripts\create_demo_account.py

if errorlevel 1 (
    echo.
    echo ❌ Failed to create demo account
    pause
    exit /b 1
)

echo.
echo ✅ Demo account created successfully!
echo.
echo You can now test the application with:
echo   Email: demo@beacon.system
echo   Password: demo123
echo.
pause