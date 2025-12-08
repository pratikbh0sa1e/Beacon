"""
API endpoints for web scraping functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime

from backend.database import SessionLocal, WebScrapingSource, WebScrapingLog, ScrapedDocument, User
from backend.routers.auth_router import get_current_user
from Agent.web_scraping.web_source_manager import WebSourceManager
from Agent.web_scraping.web_scraping_processor import WebScrapingProcessor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/web-scraping", tags=["Web Scraping"])


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic models
class WebSourceCreate(BaseModel):
    name: str
    url: HttpUrl
    description: Optional[str] = None
    source_type: str = "government"
    keywords: Optional[List[str]] = None
    max_documents_per_scrape: Optional[int] = 50
    scraping_frequency: str = "daily"
    institution_id: Optional[int] = None


class WebSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    description: Optional[str] = None
    scraping_enabled: Optional[bool] = None
    keywords: Optional[List[str]] = None
    max_documents_per_scrape: Optional[int] = None
    scraping_frequency: Optional[str] = None


class WebSourceResponse(BaseModel):
    id: int
    name: str
    url: str
    description: Optional[str]
    source_type: str
    credibility_score: int
    scraping_enabled: bool
    scraping_frequency: str
    keywords: Optional[List[str]]
    max_documents_per_scrape: Optional[int]
    last_scraped_at: Optional[datetime]
    last_scrape_status: Optional[str]
    last_scrape_message: Optional[str]
    total_documents_scraped: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ScrapeRequest(BaseModel):
    max_documents: Optional[int] = None


# Helper function to check admin permissions
def require_admin(current_user: User):
    """Require user to be admin (developer or ministry_admin)"""
    if current_user.role not in ["developer", "ministry_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage web scraping sources"
        )


@router.post("/sources", response_model=WebSourceResponse, status_code=status.HTTP_201_CREATED)
def create_web_source(
    source: WebSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new web scraping source (Admin only)"""
    require_admin(current_user)
    
    # Check if source with same name exists
    existing = db.query(WebScrapingSource).filter(
        WebScrapingSource.name == source.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Web source with name '{source.name}' already exists"
        )
    
    # Calculate credibility score based on domain
    from Agent.web_scraping.provenance_tracker import ProvenanceTracker
    tracker = ProvenanceTracker()
    domain = tracker._extract_domain(str(source.url))
    credibility = tracker._calculate_credibility(domain)
    
    # Create source
    new_source = WebScrapingSource(
        name=source.name,
        url=str(source.url),
        description=source.description,
        source_type=source.source_type,
        credibility_score=credibility,
        keywords=source.keywords,
        max_documents_per_scrape=source.max_documents_per_scrape,
        scraping_frequency=source.scraping_frequency,
        institution_id=source.institution_id,
        created_by_user_id=current_user.id
    )
    
    db.add(new_source)
    db.commit()
    db.refresh(new_source)
    
    logger.info(f"Created web scraping source: {source.name} by user {current_user.id}")
    
    return new_source


@router.get("/sources", response_model=List[WebSourceResponse])
def list_web_sources(
    enabled_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all web scraping sources"""
    query = db.query(WebScrapingSource)
    
    if enabled_only:
        query = query.filter(WebScrapingSource.scraping_enabled == True)
    
    # Filter by institution for non-admin users
    if current_user.role not in ["developer", "ministry_admin"]:
        query = query.filter(WebScrapingSource.institution_id == current_user.institution_id)
    
    sources = query.order_by(WebScrapingSource.created_at.desc()).all()
    return sources


@router.get("/sources/{source_id}", response_model=WebSourceResponse)
def get_web_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific web scraping source"""
    source = db.query(WebScrapingSource).filter(WebScrapingSource.id == source_id).first()
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Web scraping source not found"
        )
    
    # Check permissions
    if current_user.role not in ["developer", "ministry_admin"]:
        if source.institution_id != current_user.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this source"
            )
    
    return source


@router.patch("/sources/{source_id}", response_model=WebSourceResponse)
def update_web_source(
    source_id: int,
    updates: WebSourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a web scraping source (Admin only)"""
    require_admin(current_user)
    
    source = db.query(WebScrapingSource).filter(WebScrapingSource.id == source_id).first()
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Web scraping source not found"
        )
    
    # Update fields
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "url" and value:
            value = str(value)
        setattr(source, field, value)
    
    source.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(source)
    
    logger.info(f"Updated web scraping source {source_id} by user {current_user.id}")
    
    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_web_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a web scraping source (Admin only)"""
    require_admin(current_user)
    
    source = db.query(WebScrapingSource).filter(WebScrapingSource.id == source_id).first()
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Web scraping source not found"
        )
    
    db.delete(source)
    db.commit()
    
    logger.info(f"Deleted web scraping source {source_id} by user {current_user.id}")
    
    return None


@router.post("/sources/{source_id}/scrape")
def trigger_scrape(
    source_id: int,
    request: Optional[ScrapeRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger scraping for a specific source (Admin only)"""
    require_admin(current_user)
    
    source = db.query(WebScrapingSource).filter(WebScrapingSource.id == source_id).first()
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Web scraping source not found"
        )
    
    # Trigger scraping
    processor = WebScrapingProcessor()
    max_docs = request.max_documents if request else None
    
    result = processor.scrape_and_process_source(source_id, db, max_documents=max_docs)
    
    return result


@router.post("/scrape-all")
def trigger_scrape_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger scraping for all enabled sources (Admin only)"""
    require_admin(current_user)
    
    processor = WebScrapingProcessor()
    result = processor.scrape_all_enabled_sources(db)
    
    return result


@router.get("/sources/{source_id}/logs")
def get_scrape_logs(
    source_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get scraping logs for a specific source"""
    source = db.query(WebScrapingSource).filter(WebScrapingSource.id == source_id).first()
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Web scraping source not found"
        )
    
    logs = db.query(WebScrapingLog).filter(
        WebScrapingLog.source_id == source_id
    ).order_by(WebScrapingLog.started_at.desc()).limit(limit).all()
    
    return logs


@router.get("/logs/recent")
def get_recent_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent scraping logs across all sources (Admin only)"""
    require_admin(current_user)
    
    logs = db.query(WebScrapingLog).order_by(
        WebScrapingLog.started_at.desc()
    ).limit(limit).all()
    
    return logs


@router.post("/sources/validate")
def validate_source(
    url: HttpUrl,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate a URL as a potential scraping source"""
    require_admin(current_user)
    
    manager = WebSourceManager()
    result = manager.validate_source(str(url))
    
    return result


@router.post("/sources/preview")
def preview_source(
    url: HttpUrl,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Preview documents available from a source"""
    require_admin(current_user)
    
    manager = WebSourceManager()
    result = manager.get_source_preview(str(url))
    
    return result


@router.get("/scraped-documents")
def list_scraped_documents(
    source_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List documents that were scraped from web sources"""
    query = db.query(ScrapedDocument)
    
    if source_id:
        query = query.filter(ScrapedDocument.source_id == source_id)
    
    scraped_docs = query.order_by(ScrapedDocument.scraped_at.desc()).limit(limit).all()
    
    return scraped_docs


@router.get("/stats")
def get_scraping_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall web scraping statistics (Admin only)"""
    require_admin(current_user)
    
    total_sources = db.query(WebScrapingSource).count()
    enabled_sources = db.query(WebScrapingSource).filter(
        WebScrapingSource.scraping_enabled == True
    ).count()
    total_scraped = db.query(ScrapedDocument).count()
    
    recent_logs = db.query(WebScrapingLog).order_by(
        WebScrapingLog.started_at.desc()
    ).limit(10).all()
    
    return {
        "total_sources": total_sources,
        "enabled_sources": enabled_sources,
        "total_documents_scraped": total_scraped,
        "recent_activity": recent_logs
    }
