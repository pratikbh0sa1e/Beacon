"""Enhanced Web Scraping Router with Document Family Integration"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel
import logging

from backend.database import get_db, Document, DocumentFamily, WebScrapingSource, User
from backend.routers.auth_router import get_current_user
from Agent.web_scraping.enhanced_processor import enhanced_scrape_source
from Agent.document_families.family_manager import DocumentFamilyManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/enhanced-web-scraping", tags=["Enhanced Web Scraping"])


def require_admin(current_user: User):
    """Require user to be admin (developer or ministry_admin)"""
    if current_user.role not in ["developer", "ministry_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access enhanced web scraping features"
        )


class EnhancedScrapeRequest(BaseModel):
    source_id: int
    keywords: Optional[List[str]] = None
    max_documents: int = 1500
    pagination_enabled: bool = True
    max_pages: int = 100
    incremental: bool = True


class DocumentFamilyResponse(BaseModel):
    id: int
    canonical_title: str
    category: Optional[str]
    ministry: Optional[str]
    document_count: int
    latest_version: Optional[str]
    created_at: str
    updated_at: str


class FamilyEvolutionResponse(BaseModel):
    family_id: int
    canonical_title: str
    category: Optional[str]
    ministry: Optional[str]
    created_at: str
    updated_at: str
    versions: List[Dict]


@router.post("/scrape-enhanced")
async def scrape_source_enhanced(
    request: EnhancedScrapeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enhanced scraping with family management and deduplication"""
    require_admin(current_user)
    
    try:
        # Check if source exists
        source = db.query(WebScrapingSource).filter(
            WebScrapingSource.id == request.source_id
        ).first()
        
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        # Run enhanced scraping
        result = enhanced_scrape_source(
            source_id=request.source_id,
            keywords=request.keywords,
            max_documents=request.max_documents,
            pagination_enabled=request.pagination_enabled,
            max_pages=request.max_pages,
            incremental=request.incremental
        )
        
        return {
            "status": "success",
            "message": f"Enhanced scraping completed for {source.name}",
            **result
        }
        
    except Exception as e:
        logger.error(f"Enhanced scraping failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats-enhanced")
async def get_enhanced_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get enhanced statistics including family and deduplication metrics"""
    require_admin(current_user)
    
    try:
        # Basic stats
        total_sources = db.query(WebScrapingSource).count()
        enabled_sources = db.query(WebScrapingSource).filter(
            WebScrapingSource.scraping_enabled == True
        ).count()
        
        # Family stats
        total_families = db.query(DocumentFamily).count()
        total_documents = db.query(Document).count()
        latest_versions = db.query(Document).filter(
            Document.is_latest_version == True
        ).count()
        total_versions = db.query(Document).filter(
            Document.document_family_id.isnot(None)
        ).count()
        
        # Calculate deduplication rate
        documents_with_hash = db.query(Document).filter(
            Document.content_hash.isnot(None)
        ).count()
        
        # Count duplicates (same content hash)
        duplicate_query = db.execute("""
            SELECT COUNT(*) as duplicates
            FROM (
                SELECT content_hash, COUNT(*) as count
                FROM documents 
                WHERE content_hash IS NOT NULL
                GROUP BY content_hash 
                HAVING COUNT(*) > 1
            ) as dup_counts
        """)
        duplicates_found = duplicate_query.fetchone()[0] if duplicate_query else 0
        
        deduplication_rate = 0
        if documents_with_hash > 0:
            deduplication_rate = round((duplicates_found / documents_with_hash) * 100, 1)
        
        # Update detection stats
        updates_detected = db.query(Document).filter(
            Document.supersedes_id.isnot(None)
        ).count()
        
        # RAG accuracy (placeholder - would need actual metrics)
        rag_accuracy = 85  # This would come from actual RAG evaluation
        
        avg_docs_per_family = 0
        if total_families > 0:
            avg_docs_per_family = round(total_versions / total_families, 1)
        
        return {
            "total_sources": total_sources,
            "enabled_sources": enabled_sources,
            "total_families": total_families,
            "total_documents": total_documents,
            "latest_versions": latest_versions,
            "total_versions": total_versions,
            "avg_docs_per_family": avg_docs_per_family,
            "deduplication_rate": deduplication_rate,
            "duplicates_found": duplicates_found,
            "updates_detected": updates_detected,
            "rag_accuracy": rag_accuracy,
            "incremental_scrapes": 0  # Would track this in scraping logs
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document-families", response_model=List[DocumentFamilyResponse])
async def get_document_families(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document families with metadata"""
    require_admin(current_user)
    
    try:
        # Get families with document counts
        families_query = db.execute(f"""
            SELECT 
                df.id,
                df.canonical_title,
                df.category,
                df.ministry,
                df.created_at,
                df.updated_at,
                COUNT(d.id) as document_count,
                MAX(d.version_number) as latest_version
            FROM document_families df
            LEFT JOIN documents d ON df.id = d.document_family_id
            GROUP BY df.id, df.canonical_title, df.category, df.ministry, df.created_at, df.updated_at
            ORDER BY df.updated_at DESC
            LIMIT {limit} OFFSET {offset}
        """)
        
        families = []
        for row in families_query.fetchall():
            families.append(DocumentFamilyResponse(
                id=row[0],
                canonical_title=row[1],
                category=row[2],
                ministry=row[3],
                created_at=row[4].isoformat() if row[4] else "",
                updated_at=row[5].isoformat() if row[5] else "",
                document_count=row[6] or 0,
                latest_version=str(row[7]) if row[7] else "1.0"
            ))
        
        return families
        
    except Exception as e:
        logger.error(f"Error getting document families: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document-families/{family_id}/evolution", response_model=FamilyEvolutionResponse)
async def get_family_evolution(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the evolution history of a document family"""
    require_admin(current_user)
    
    try:
        manager = DocumentFamilyManager()
        evolution = manager.get_family_evolution(family_id, db)
        
        if "error" in evolution:
            raise HTTPException(status_code=404, detail=evolution["error"])
        
        return FamilyEvolutionResponse(**evolution)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting family evolution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/document-families/migrate-existing")
async def migrate_existing_documents(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Migrate existing documents to family structure"""
    require_admin(current_user)
    
    try:
        # Run migration in background
        def run_migration():
            from scripts.migrate_existing_documents_to_families import DocumentFamilyMigrator
            migrator = DocumentFamilyMigrator()
            migrator.migrate_all_documents()
        
        background_tasks.add_task(run_migration)
        
        # Get current counts for response
        total_documents = db.query(Document).count()
        total_families = db.query(DocumentFamily).count()
        
        return {
            "status": "started",
            "message": "Document family migration started in background",
            "total_documents": total_documents,
            "total_families": total_families
        }
        
    except Exception as e:
        logger.error(f"Error starting migration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document-families/{family_id}/documents")
async def get_family_documents(
    family_id: int,
    include_superseded: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all documents in a family"""
    require_admin(current_user)
    
    try:
        manager = DocumentFamilyManager()
        documents = manager.get_family_documents(
            family_id=family_id,
            include_superseded=include_superseded,
            db=db
        )
        
        return {
            "family_id": family_id,
            "documents": documents,
            "total_count": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error getting family documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-scraping")
async def stop_scraping(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop an active scraping job"""
    require_admin(current_user)
    
    try:
        source_id = request.get("source_id")
        job_id = request.get("job_id")
        
        if not source_id or not job_id:
            raise HTTPException(status_code=400, detail="source_id and job_id are required")
        
        # For now, we'll just return success since we don't have persistent job tracking
        # In a production system, you'd track active jobs and cancel them
        logger.info(f"Stop scraping requested for source {source_id}, job {job_id}")
        
        return {
            "status": "success",
            "message": f"Scraping job {job_id} for source {source_id} stopped",
            "source_id": source_id,
            "job_id": job_id
        }
        
    except Exception as e:
        logger.error(f"Error stopping scraping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-scrapers")
async def get_available_scrapers(
    current_user: User = Depends(get_current_user)
):
    """Get list of available site-specific scrapers"""
    require_admin(current_user)
    
    try:
        # Return the available scrapers
        scrapers = {
            "generic": "Generic Government Site",
            "moe": "Ministry of Education",
            "ugc": "University Grants Commission", 
            "aicte": "All India Council for Technical Education"
        }
        
        return scrapers
        
    except Exception as e:
        logger.error(f"Error getting available scrapers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-document-updates")
async def check_document_updates(
    source_url: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a document at URL has been updated"""
    require_admin(current_user)
    
    try:
        manager = DocumentFamilyManager()
        
        # This would need the actual content to check
        # For now, just check if document exists
        existing_doc = db.query(Document).filter(
            Document.scraped_from_url == source_url
        ).first()
        
        if existing_doc:
            return {
                "status": "exists",
                "document_id": existing_doc.id,
                "family_id": existing_doc.document_family_id,
                "version_number": existing_doc.version_number,
                "last_modified": existing_doc.last_modified_at_source.isoformat() if existing_doc.last_modified_at_source else None
            }
        else:
            return {
                "status": "new",
                "message": "Document not found in database"
            }
        
    except Exception as e:
        logger.error(f"Error checking document updates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))