from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend.routers import document_router, chat_router, data_source_router
from Agent.data_ingestion.scheduler import start_scheduler
from dotenv import load_dotenv
import logging

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Government Policy Intelligence Platform",
    description="AI-powered document ingestion and policy analysis system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(document_router.router)
app.include_router(chat_router.router)
app.include_router(data_source_router.router)

@app.get("/")
async def root():
    return {
        "message": "Government Policy Intelligence Platform API",
        "status": "active",
        "endpoints": {
            "upload": "/documents/upload",
            "list": "/documents/list",
            "get": "/documents/{id}"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Start background scheduler on app startup"""
    logger.info("Starting sync scheduler...")
    start_scheduler(sync_time="02:00")  # Daily sync at 2 AM
    logger.info("Sync scheduler started")
