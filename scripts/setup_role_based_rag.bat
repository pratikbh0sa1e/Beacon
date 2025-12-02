@echo off
echo 🚀 Setting up Role-Based RAG with PGVector
echo ==========================================
echo.

echo 📦 Installing pgvector Python package...
pip install pgvector==0.3.6

echo.
echo 🗄️  Enabling pgvector extension in PostgreSQL...
python scripts\enable_pgvector.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Setup complete!
    echo.
    echo Next steps:
    echo 1. Restart your FastAPI server
    echo 2. Documents will be automatically embedded on first query ^(lazy embedding^)
    echo 3. Check ROLE_BASED_RAG_IMPLEMENTATION.md for details
    echo.
    echo To manually embed all documents, run:
    echo   python scripts\batch_embed_documents.py
) else (
    echo.
    echo ❌ Setup failed. Please check the error messages above.
    echo.
    echo Common issues:
    echo - pgvector extension not installed in PostgreSQL
    echo - Database connection issues ^(check .env file^)
    echo - Insufficient permissions
    exit /b 1
)

pause
