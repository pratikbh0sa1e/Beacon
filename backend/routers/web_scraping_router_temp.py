"""
Web Scraping API - Temporary No-DB Version for Demo
This version works WITHOUT database until migration is complete
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime
import logging

from Agent.web_scraping.web_source_manager import WebSourceManager
from Agent.web_scraping.session_storage import SessionStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/web-scraping", tags=["Web Scraping"])

# Initialize web source manager and session storage
web_manager = WebSourceManager()
session_storage = SessionStorage()

# Load persisted data from disk
TEMP_SOURCES: List[Dict] = session_storage.load_sources()
TEMP_LOGS: List[Dict] = session_storage.load_logs()
TEMP_SCRAPED_DOCS: List[Dict] = session_storage.load_scraped_docs()

# Load counters from disk
_counters = session_storage.load_counters()
_source_id_counter = _counters.get("source_id", 1)
_log_id_counter = _counters.get("log_id", 1)


# ==================== Pydantic Models ====================

class WebSourceCreate(BaseModel):
    name: str
    url: HttpUrl
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    max_documents: Optional[int] = 50
    scraping_enabled: bool = True


class WebSourceResponse(BaseModel):
    id: int
    name: str
    url: str
    description: Optional[str]
    keywords: Optional[List[str]]
    max_documents: int
    scraping_enabled: bool
    last_scraped_at: Optional[str]
    last_scrape_status: Optional[str]
    total_documents_scraped: int
    created_at: str


class ScrapeRequest(BaseModel):
    source_id: Optional[int] = None
    url: Optional[HttpUrl] = None
    keywords: Optional[List[str]] = None
    max_documents: Optional[int] = 1500
    pagination_enabled: Optional[bool] = True
    max_pages: Optional[int] = 100
    incremental: Optional[bool] = False


# ==================== Endpoints ====================

@router.post("/sources", response_model=WebSourceResponse, status_code=201)
async def create_web_source(source: WebSourceCreate):
    """
    Create a new web scraping source
    """
    global _source_id_counter
    
    # Check if name already exists
    if any(s['name'] == source.name for s in TEMP_SOURCES):
        raise HTTPException(status_code=400, detail="Source name already exists")
    
    new_source = {
        "id": _source_id_counter,
        "name": source.name,
        "url": str(source.url),
        "description": source.description,
        "keywords": source.keywords,
        "max_documents": source.max_documents or 50,
        "scraping_enabled": source.scraping_enabled,
        "last_scraped_at": None,
        "last_scrape_status": None,
        "total_documents_scraped": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    
    TEMP_SOURCES.append(new_source)
    _source_id_counter += 1
    
    # Persist to disk
    session_storage.save_sources(TEMP_SOURCES)
    session_storage.save_counters(_source_id_counter, _log_id_counter)
    
    logger.info(f"Created web source: {source.name}")
    return new_source


@router.get("/sources", response_model=List[WebSourceResponse])
async def list_web_sources(enabled_only: bool = False):
    """
    List all web scraping sources
    """
    if enabled_only:
        return [s for s in TEMP_SOURCES if s['scraping_enabled']]
    return TEMP_SOURCES


@router.get("/sources/{source_id}", response_model=WebSourceResponse)
async def get_web_source(source_id: int):
    """
    Get a specific web source
    """
    source = next((s for s in TEMP_SOURCES if s['id'] == source_id), None)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.put("/sources/{source_id}", response_model=WebSourceResponse)
async def update_web_source(source_id: int, source_update: WebSourceCreate):
    """
    Update an existing web scraping source
    """
    global TEMP_SOURCES
    source = next((s for s in TEMP_SOURCES if s['id'] == source_id), None)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Update source fields
    source['name'] = source_update.name
    source['url'] = str(source_update.url)
    source['description'] = source_update.description
    source['keywords'] = source_update.keywords
    source['max_documents'] = source_update.max_documents or 50
    source['scraping_enabled'] = source_update.scraping_enabled
    
    # Persist to disk
    session_storage.save_sources(TEMP_SOURCES)
    
    logger.info(f"Updated web source: {source['name']} (keywords: {source['keywords']})")
    return source


@router.delete("/sources/{source_id}")
async def delete_web_source(source_id: int):
    """
    Delete a web scraping source
    """
    global TEMP_SOURCES
    source = next((s for s in TEMP_SOURCES if s['id'] == source_id), None)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    TEMP_SOURCES = [s for s in TEMP_SOURCES if s['id'] != source_id]
    
    # Persist to disk
    session_storage.save_sources(TEMP_SOURCES)
    
    logger.info(f"Deleted web source: {source['name']}")
    
    return {"message": "Source deleted successfully"}


@router.post("/scrape")
async def scrape_now(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Trigger immediate scraping
    Can scrape from:
    1. Existing source (by source_id)
    2. Ad-hoc URL (by url)
    """
    global _log_id_counter
    
    if request.source_id:
        # Scrape from existing source
        source = next((s for s in TEMP_SOURCES if s['id'] == request.source_id), None)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        url = source['url']
        name = source['name']
        # Ad-hoc keywords override source keywords (if provided)
        keywords = request.keywords if request.keywords else source.get('keywords')
        max_docs = request.max_documents if request.max_documents else source.get('max_documents')
        
        # Ensure keywords is a list or None (not empty list)
        if keywords is not None and len(keywords) == 0:
            keywords = None
        
        logger.info(f"Source keywords: {source.get('keywords')} (type: {type(source.get('keywords'))})")
        logger.info(f"Request keywords: {request.keywords} (type: {type(request.keywords)})")
        logger.info(f"Final keywords to use: {keywords} (type: {type(keywords)})")
    
    elif request.url:
        # Ad-hoc scraping
        url = str(request.url)
        name = f"Ad-hoc: {url}"
        keywords = request.keywords
        max_docs = request.max_documents
    
    else:
        raise HTTPException(status_code=400, detail="Either source_id or url must be provided")
    
    # Perform scraping
    try:
        logger.info(f"Starting scrape: {name}")
        logger.info(f"Keywords being used: {keywords} (type: {type(keywords)})")
        logger.info(f"Max documents: {max_docs}")
        logger.info(f"Pagination enabled: {request.pagination_enabled}")
        logger.info(f"Max pages: {request.max_pages}")
        
        # Use pagination-enabled scraping if source_id is provided
        if request.source_id:
            result = web_manager.scrape_source_with_pagination(
                source_id=request.source_id,
                url=url,
                source_name=name,
                keywords=keywords,
                pagination_enabled=request.pagination_enabled if request.pagination_enabled is not None else True,
                max_pages=request.max_pages or 100,
                incremental=request.incremental or False,
                max_documents=max_docs or 1500
            )
        else:
            # Ad-hoc scraping without pagination
            result = web_manager.scrape_source(
                url=url,
                source_name=name,
                keywords=keywords,
                max_documents=max_docs
            )
        
        # Create log entry with filtering statistics
        log_entry = {
            "id": _log_id_counter,
            "source_id": request.source_id,
            "source_name": name,
            "status": result['status'],
            "documents_found": result.get('documents_found', 0),
            "documents_discovered": result.get('documents_discovered', 0),  # NEW
            "documents_matched": result.get('documents_matched', 0),  # NEW
            "documents_skipped": result.get('documents_skipped', 0),  # NEW
            "keywords_used": result.get('keywords_used', []),  # NEW
            "documents_downloaded": 0,
            "documents_processed": 0,
            "error_message": result.get('error'),
            "started_at": result['scraped_at'],
            "completed_at": datetime.utcnow().isoformat()
        }
        
        TEMP_LOGS.append(log_entry)
        _log_id_counter += 1
        
        # Update source if it exists
        if request.source_id:
            source['last_scraped_at'] = datetime.utcnow().isoformat()
            source['last_scrape_status'] = result['status']
            if result['status'] == 'success':
                source['total_documents_scraped'] += result.get('documents_matched', result.get('documents_found', 0))
        
        # Store scraped documents info
        if result['status'] == 'success' and result.get('documents'):
            logger.info(f"Storing {len(result['documents'])} documents")
            for doc in result.get('documents', []):
                scraped_doc = {
                    "url": doc['url'],
                    "title": doc.get('text', 'Untitled'),
                    "type": doc.get('type', 'unknown'),
                    "source_url": url,
                    "source_name": name,
                    "provenance": doc.get('provenance', {}),
                    "matched_keywords": doc.get('matched_keywords', []),  # NEW
                    "scraped_at": doc.get('found_at', datetime.utcnow().isoformat())
                }
                TEMP_SCRAPED_DOCS.append(scraped_doc)
                # Safe logging for Unicode characters
                try:
                    logger.info(f"Stored document: {scraped_doc['title'][:50]}...")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    logger.info(f"Stored document: [Unicode title - {len(scraped_doc['title'])} chars]")
            
            logger.info(f"Total scraped docs now: {len(TEMP_SCRAPED_DOCS)}")
        
        # Persist all changes to disk
        session_storage.save_sources(TEMP_SOURCES)
        session_storage.save_logs(TEMP_LOGS)
        session_storage.save_scraped_docs(TEMP_SCRAPED_DOCS)
        session_storage.save_counters(_source_id_counter, _log_id_counter)
        
        # Build response with filtering statistics
        response_message = f"Scraping completed: {result.get('documents_matched', result.get('documents_found', 0))} documents found"
        if keywords:
            response_message += f" (filtered from {result.get('documents_discovered', 0)} total)"
        
        return {
            "status": "success",
            "message": response_message,
            "log_id": log_entry['id'],
            "filtering_stats": {  # NEW: Filtering statistics
                "keywords_used": result.get('keywords_used', []),
                "documents_discovered": result.get('documents_discovered', 0),
                "documents_matched": result.get('documents_matched', 0),
                "documents_skipped": result.get('documents_skipped', 0),
                "match_rate_percent": result.get('filter_match_rate', 100.0)
            },
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@router.post("/scrape-and-download")
async def scrape_and_download(request: ScrapeRequest):
    """
    Scrape and download documents with optional keyword filtering
    """
    if request.source_id:
        source = next((s for s in TEMP_SOURCES if s['id'] == request.source_id), None)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        url = source['url']
        name = source['name']
        # Ad-hoc keywords override source keywords (if provided)
        keywords = request.keywords if request.keywords else source.get('keywords')
        max_docs = request.max_documents if request.max_documents else source.get('max_documents')
    
    elif request.url:
        url = str(request.url)
        name = f"Ad-hoc: {url}"
        keywords = request.keywords
        max_docs = request.max_documents
    
    else:
        raise HTTPException(status_code=400, detail="Either source_id or url must be provided")
    
    try:
        result = web_manager.scrape_and_download(
            url=url,
            source_name=name,
            keywords=keywords,
            max_documents=max_docs
        )
        
        # Build response message
        message = f"Downloaded {result['documents_downloaded']} documents"
        if keywords:
            message += f" (matched {result.get('documents_matched', 0)} from {result.get('documents_discovered', 0)} discovered)"
        
        return {
            "status": "success",
            "message": message,
            "filtering_stats": {  # NEW: Filtering statistics
                "keywords_used": result.get('keywords_used', []),
                "documents_discovered": result.get('documents_discovered', 0),
                "documents_matched": result.get('documents_matched', 0),
                "match_rate_percent": result.get('filter_match_rate', 100.0)
            },
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Scrape and download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape-and-process")
async def scrape_and_process_full_pipeline(request: ScrapeRequest):
    """
    Complete pipeline: Scrape → Download → OCR → Metadata → Store → RAG Ready
    
    This endpoint integrates with the full BEACON Agent pipeline:
    1. Scrapes documents from website
    2. Downloads PDFs/documents
    3. Extracts text (with OCR for images)
    4. Extracts metadata using AI
    5. Stores in database
    6. Makes ready for RAG (lazy embedding)
    """
    from Agent.web_scraping.web_scraping_processor import WebScrapingProcessor
    
    if request.source_id:
        source = next((s for s in TEMP_SOURCES if s['id'] == request.source_id), None)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        url = source['url']
        name = source['name']
        # Ad-hoc keywords override source keywords (if provided)
        keywords = request.keywords if request.keywords else source.get('keywords')
        max_docs = request.max_documents if request.max_documents else source.get('max_documents')
    
    elif request.url:
        url = str(request.url)
        name = f"Ad-hoc: {url}"
        keywords = request.keywords
        max_docs = request.max_documents
    
    else:
        raise HTTPException(status_code=400, detail="Either source_id or url must be provided")
    
    try:
        processor = WebScrapingProcessor()
        
        result = processor.scrape_and_process(
            url=url,
            source_name=name,
            keywords=keywords,
            max_documents=max_docs,
            uploader_id=1,  # System user for scraped docs
            institution_id=None  # Public by default
        )
        
        # Build response message
        message = f"Processed {result['documents_processed']}/{result['documents_scraped']} documents through full pipeline"
        if keywords:
            message += f" (filtered by keywords: {', '.join(keywords)})"
        
        return {
            "status": "success",
            "message": message,
            "filtering_stats": {  # NEW: Filtering statistics (if available)
                "keywords_used": keywords if keywords else [],
                "documents_processed": result['documents_processed'],
                "documents_failed": result['documents_failed']
            },
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Full pipeline processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_scraping_logs(source_id: Optional[int] = None, limit: int = 50):
    """
    Get scraping logs
    """
    logs = TEMP_LOGS
    
    if source_id:
        logs = [log for log in logs if log.get('source_id') == source_id]
    
    # Sort by started_at descending
    logs = sorted(logs, key=lambda x: x['started_at'], reverse=True)
    
    return logs[:limit]


@router.get("/scraped-documents")
async def get_scraped_documents(limit: int = 100):
    """
    Get list of scraped documents
    """
    logger.info(f"Fetching scraped documents. Total available: {len(TEMP_SCRAPED_DOCS)}")
    
    # Return documents in reverse order (newest first)
    docs = list(reversed(TEMP_SCRAPED_DOCS))[:limit]
    
    logger.info(f"Returning {len(docs)} documents")
    return docs


@router.get("/debug/scraped-docs-count")
async def debug_scraped_docs_count():
    """
    Debug endpoint to check scraped documents count
    """
    return {
        "total_scraped_docs": len(TEMP_SCRAPED_DOCS),
        "sample": TEMP_SCRAPED_DOCS[:3] if TEMP_SCRAPED_DOCS else [],
        "all_docs": TEMP_SCRAPED_DOCS
    }


@router.get("/download-document")
async def download_scraped_document(url: str):
    """
    Download a specific document by URL
    This proxies the download through our server
    
    Note: Some government sites block downloads (403).
    Frontend will fallback to opening the original URL.
    """
    try:
        logger.info(f"Downloading document from: {url}")
        
        # Download the document
        download_result = web_manager.downloader.download_document(url)
        
        if download_result['status'] != 'success':
            error_msg = download_result.get('error', 'Unknown error')
            
            # If it's a 403 or access error, return specific error
            if '403' in error_msg or 'Forbidden' in error_msg:
                raise HTTPException(
                    status_code=403, 
                    detail="Source website blocks direct downloads. Please open the document URL directly."
                )
            
            raise HTTPException(status_code=404, detail=f"Failed to download: {error_msg}")
        
        # Return file for download
        from fastapi.responses import FileResponse
        import os
        
        filepath = download_result['filepath']
        filename = download_result['filename']
        
        # Determine media type
        if filename.lower().endswith('.pdf'):
            media_type = 'application/pdf'
        elif filename.lower().endswith(('.docx', '.doc')):
            media_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif filename.lower().endswith(('.pptx', '.ppt')):
            media_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        else:
            media_type = 'application/octet-stream'
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


class PreviewRequest(BaseModel):
    url: HttpUrl


@router.post("/preview")
async def preview_source(request: PreviewRequest):
    """
    Preview what documents would be scraped from a URL
    """
    try:
        preview = web_manager.get_source_preview(str(request.url))
        return preview
    except Exception as e:
        logger.error(f"Preview failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class ValidateRequest(BaseModel):
    url: HttpUrl


@router.post("/validate")
async def validate_source(request: ValidateRequest):
    """
    Validate if a URL is a valid scraping source
    """
    try:
        validation = web_manager.validate_source(str(request.url))
        return validation
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_scraping_stats():
    """
    Get overall scraping statistics including filtering effectiveness
    """
    total_sources = len(TEMP_SOURCES)
    enabled_sources = len([s for s in TEMP_SOURCES if s['scraping_enabled']])
    total_scrapes = len(TEMP_LOGS)
    successful_scrapes = len([log for log in TEMP_LOGS if log['status'] == 'success'])
    total_documents = sum(s['total_documents_scraped'] for s in TEMP_SOURCES)
    
    # Calculate filtering statistics
    scrapes_with_keywords = len([log for log in TEMP_LOGS if log.get('keywords_used')])
    total_discovered = sum(log.get('documents_discovered', 0) for log in TEMP_LOGS)
    total_matched = sum(log.get('documents_matched', 0) for log in TEMP_LOGS)
    total_skipped = sum(log.get('documents_skipped', 0) for log in TEMP_LOGS)
    
    # Calculate average match rate for filtered scrapes
    filtered_scrapes = [log for log in TEMP_LOGS if log.get('keywords_used')]
    avg_match_rate = 0.0
    if filtered_scrapes:
        match_rates = []
        for log in filtered_scrapes:
            discovered = log.get('documents_discovered', 0)
            matched = log.get('documents_matched', 0)
            if discovered > 0:
                match_rates.append((matched / discovered) * 100)
        if match_rates:
            avg_match_rate = sum(match_rates) / len(match_rates)
    
    return {
        "total_sources": total_sources,
        "enabled_sources": enabled_sources,
        "total_scrapes": total_scrapes,
        "successful_scrapes": successful_scrapes,
        "failed_scrapes": total_scrapes - successful_scrapes,
        "total_documents_scraped": total_documents,
        "scraped_documents_available": len(TEMP_SCRAPED_DOCS),
        "filtering_stats": {  # NEW: Filtering statistics
            "scrapes_with_keywords": scrapes_with_keywords,
            "scrapes_without_keywords": total_scrapes - scrapes_with_keywords,
            "total_documents_discovered": total_discovered,
            "total_documents_matched": total_matched,
            "total_documents_skipped": total_skipped,
            "average_match_rate_percent": round(avg_match_rate, 2)
        }
    }


# ==================== Quick Demo Endpoint ====================

@router.post("/demo/education-gov")
async def demo_education_gov():
    """
    Quick demo: Scrape UGC website (more reliable than education.gov.in)
    """
    try:
        # Use UGC website as it's more accessible
        url = "https://www.ugc.gov.in/"
        
        result = web_manager.scrape_source(
            url=url,
            source_name="UGC Official Website (Demo)",
            keywords=["policy", "circular", "notification"],
            max_documents=10
        )
        
        return {
            "status": "success",
            "message": f"Demo scrape complete: {result.get('documents_found', 0)} documents found from UGC",
            "url": url,
            "documents": result.get('documents', [])[:10]  # Return first 10
        }
    
    except Exception as e:
        logger.error(f"Demo scrape failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")


@router.post("/demo/ugc")
async def demo_ugc():
    """
    Demo: Scrape UGC website
    """
    try:
        url = "https://www.ugc.gov.in/"
        
        result = web_manager.scrape_source(
            url=url,
            source_name="UGC Official Website",
            keywords=["policy", "circular", "notification"],
            max_documents=10
        )
        
        return {
            "status": "success",
            "message": f"Found {result.get('documents_found', 0)} documents from UGC",
            "url": url,
            "documents": result.get('documents', [])
        }
    
    except Exception as e:
        logger.error(f"UGC demo failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demo/working-urls")
async def get_working_demo_urls():
    """
    Get list of working government URLs for demo
    """
    return {
        "working_urls": [
            {
                "name": "UGC (University Grants Commission)",
                "url": "https://www.ugc.gov.in/",
                "credibility": 9,
                "description": "Official UGC website with policies and circulars",
                "recommended": True
            },
            {
                "name": "AICTE",
                "url": "https://www.aicte-india.org/",
                "credibility": 9,
                "description": "All India Council for Technical Education",
                "recommended": True
            },
            {
                "name": "NCERT",
                "url": "https://ncert.nic.in/",
                "credibility": 9,
                "description": "National Council of Educational Research and Training",
                "recommended": False
            }
        ],
        "note": "These URLs have been tested and work reliably for demos"
    }


# ==================== Session Management ====================

@router.post("/clear-session")
async def clear_session():
    """
    Clear all session data (call on logout)
    """
    global TEMP_SOURCES, TEMP_LOGS, TEMP_SCRAPED_DOCS, _source_id_counter, _log_id_counter
    
    # Clear in-memory data
    TEMP_SOURCES.clear()
    TEMP_LOGS.clear()
    TEMP_SCRAPED_DOCS.clear()
    _source_id_counter = 1
    _log_id_counter = 1
    
    # Clear persisted data
    session_storage.clear_all()
    
    logger.info("Session data cleared")
    
    return {
        "message": "Session cleared successfully",
        "sources_cleared": True,
        "logs_cleared": True,
        "documents_cleared": True
    }


@router.get("/session-stats")
async def get_session_stats():
    """
    Get session storage statistics
    """
    return session_storage.get_stats()
