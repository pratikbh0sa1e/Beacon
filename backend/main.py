from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from backend.database import engine, Base
from backend.routers import (
    auth_router,
    user_router,
    institution_router,
    institution_domain_router,
    document_router,
    bookmark_router,
    approval_router,
    chat_router,
    chat_history_router,
    audit_router,
    data_source_router,
    notification_router,    
    voice_router,
    insights_router,
    document_chat_router,
    notes_router,
    # ocr_router  # Temporarily disabled - uses EasyOCR dependencies
)
# Temporary: Use no-DB version until migration is complete
from backend.routers import web_scraping_router_temp as web_scraping_router
from backend.routers import document_analysis_router
from backend.routers import scraping_logs
from backend.routers.enhanced_web_scraping_router import router as enhanced_scraping_router
from backend.init_developer import initialize_developer_account
from Agent.data_ingestion.scheduler import start_scheduler
from backend.utils.quota_manager import get_quota_manager
from dotenv import load_dotenv
import logging
import time

load_dotenv()

# Setup logging with UTF-8 encoding for Windows
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
# Force UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize developer account on first run
initialize_developer_account()

# Initialize demo account for testing
from backend.init_developer import initialize_demo_account
initialize_demo_account()

app = FastAPI(
    title="BEACON - Government Policy Intelligence Platform",
    description="AI-powered document management and policy analysis system with role-based access control",
    version="2.0.0"
)

# Performance monitoring middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 3))
    
    # Log slow requests for monitoring
    if process_time > 1.0:
        logger.warning(f"SLOW REQUEST: {request.method} {request.url.path} took {process_time:.2f}s")
    
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://beacon-67.vercel.app",  # Production Vercel deployment
        "https://*.vercel.app",  # Allow other Vercel deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression middleware for faster response times
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(auth_router.router, prefix="/auth", tags=["authentication"])
app.include_router(user_router.router, prefix="/users", tags=["user-management"])
app.include_router(bookmark_router.router, prefix="/bookmark")
app.include_router(institution_router.router, prefix="/institutions", tags=["institutions"])
app.include_router(institution_domain_router.router, tags=["institution-domains"])
app.include_router(document_router.router, prefix="/documents", tags=["documents"])
app.include_router(approval_router.router, prefix="/approvals", tags=["approvals"])
app.include_router(chat_router.router, prefix="/chat", tags=["chat"])
app.include_router(chat_history_router.router, prefix="/chat", tags=["chat-history"])
app.include_router(voice_router.router, tags=["voice"])  # Voice query support
app.include_router(audit_router.router, prefix="/audit", tags=["audit"])
app.include_router(data_source_router.router, prefix="/data-sources", tags=["data-sources"])
app.include_router(notification_router.router, prefix="/notifications", tags=["notifications"])
app.include_router(insights_router.router, tags=["insights"])
app.include_router(document_chat_router.router, tags=["document-chat"])
app.include_router(notes_router.router, tags=["notes"])
app.include_router(web_scraping_router.router, tags=["web-scraping"])  # Web scraping endpoints
app.include_router(enhanced_scraping_router, tags=["enhanced-web-scraping"])  # Enhanced web scraping with families
app.include_router(document_analysis_router.router, tags=["document-analysis"])  # Document analysis with AI
app.include_router(scraping_logs.router, tags=["scraping-logs"])  # Scraping logs
# app.include_router(ocr_router.router, prefix="/ocr", tags=["ocr"])  # Temporarily disabled - uses EasyOCR

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
            "audit": "/audit",
            "data_sources": "/data-sources",
            "notifications": "/notifications",
            "insights": "/insights"
        },
        "documentation": "/docs"
    }

@app.get("/health")
@app.head("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "services": ["auth", "documents", "chat", "approvals", "data-sources", "insights"]
    }

@app.get("/quota/status")
async def get_quota_status():
    """Get current quota status for all cloud services"""
    try:
        quota_manager = get_quota_manager()
        status = quota_manager.get_quota_status()
        
        return {
            "status": "success",
            "quota_status": status,
            "cloud_only_mode": True,  # Always true for deployment
            "message": "Quota status retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting quota status: {e}")
        return {
            "status": "error",
            "message": f"Failed to get quota status: {str(e)}"
        }

@app.get("/quota/status/{service}")
async def get_service_quota_status(service: str):
    """Get quota status for a specific service"""
    try:
        quota_manager = get_quota_manager()
        
        # Validate service name
        valid_services = ["gemini_embeddings", "gemini_chat", "speech_to_text", "vision_ocr"]
        if service not in valid_services:
            return {
                "status": "error",
                "message": f"Invalid service. Valid services: {', '.join(valid_services)}"
            }
        
        status = quota_manager.get_quota_status(service)
        
        return {
            "status": "success",
            "service": service,
            "quota_status": status,
            "message": f"Quota status for {service} retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting quota status for {service}: {e}")
        return {
            "status": "error",
            "message": f"Failed to get quota status for {service}: {str(e)}"
        }

@app.on_event("startup")
async def startup_event():
    """Start background scheduler and initialize cache on app startup"""
    logger.info("Starting BEACON Platform...")
    
    # Initialize cache (Redis if available, fallback to in-memory)
    try:
        from fastapi_cache import FastAPICache
        import os
        
        # Try Redis first (better for production)
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            from redis import asyncio as aioredis
            from fastapi_cache.backends.redis import RedisBackend
            
            # Check if it's Upstash or other cloud Redis (requires SSL)
            is_cloud_redis = "upstash.io" in redis_url or "redislabs.com" in redis_url
            
            if is_cloud_redis:
                # Upstash requires rediss:// (Redis with SSL)
                # Convert redis:// to rediss:// for SSL
                if redis_url.startswith("redis://"):
                    redis_url = redis_url.replace("redis://", "rediss://", 1)
                
                redis = await aioredis.from_url(
                    redis_url,
                    encoding="utf8",
                    decode_responses=True
                )
            else:
                # Local Redis doesn't need SSL
                redis = await aioredis.from_url(
                    redis_url,
                    encoding="utf8",
                    decode_responses=True
                )
            
            # Test connection
            await redis.ping()
            FastAPICache.init(RedisBackend(redis), prefix="beacon-cache:")
            cache_type = "Upstash Redis" if is_cloud_redis else "Redis"
            logger.info(f"Cache initialized ({cache_type})")
        except (ImportError, Exception) as redis_error:
            # Fallback to in-memory cache
            from fastapi_cache.backends.inmemory import InMemoryBackend
            FastAPICache.init(InMemoryBackend(), prefix="beacon-cache:")
            logger.info("Cache initialized (in-memory) - Redis connection failed")
            logger.debug(f"Redis error: {redis_error}")
    except ImportError:
        logger.warning("fastapi-cache2 not installed. Install with: pip install fastapi-cache2")
    except Exception as e:
        logger.warning(f"Cache initialization failed: {str(e)}")
    
    # Start scheduler
    logger.info("Starting sync scheduler...")
    start_scheduler(sync_time="02:00")  # Daily sync at 2 AM
    logger.info("Sync scheduler started")
    logger.info("BEACON Platform ready!")