from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend.routers import document_router, chat_router
from backend.routers import auth_router, user_router, institution_router, approval_router, audit_router
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
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(institution_router.router)
app.include_router(document_router.router)
app.include_router(approval_router.router)
app.include_router(chat_router.router)
app.include_router(audit_router.router)

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