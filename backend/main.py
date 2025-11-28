from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend.routers import (
    auth_router,
    user_router,
    institution_router,
    document_router,
    approval_router,
    chat_router,
    audit_router
)
from backend.init_developer import initialize_developer_account
from dotenv import load_dotenv

load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize developer account on first run
initialize_developer_account()

app = FastAPI(
    title="BEACON - Government Policy Intelligence Platform",
    description="AI-powered document management and policy analysis system with role-based access control",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3000",
        "http://127.0.0.1:3000",],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with consistent /api prefix removed (handled by frontend)
app.include_router(auth_router.router, prefix="/auth", tags=["authentication"])
app.include_router(user_router.router, prefix="/users", tags=["user-management"])
app.include_router(institution_router.router, prefix="/institutions", tags=["institutions"])
app.include_router(document_router.router, prefix="/documents", tags=["documents"])
app.include_router(approval_router.router, prefix="/approvals", tags=["approvals"])
app.include_router(chat_router.router, prefix="/chat", tags=["chat"])
app.include_router(audit_router.router, prefix="/audit", tags=["audit"])

@app.get("/")
async def root():
    return {
        "name": "BEACON Platform",
        "version": "2.0.0",
        "status": "active",
        "endpoints": {
            "authentication": "/auth",
            "users": "/users",
            "institutions": "/institutions",
            "documents": "/documents",
            "approvals": "/approvals",
            "chat": "/chat",
            "audit": "/audit"
        },
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "services": ["auth", "documents", "chat", "approvals"]
    }