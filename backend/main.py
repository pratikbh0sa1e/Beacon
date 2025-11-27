from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend.routers import document_router, chat_router
from dotenv import load_dotenv

load_dotenv()

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
