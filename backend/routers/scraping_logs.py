"""
API endpoints for scraping logs
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from Agent.web_scraping.local_storage import LocalStorage
from Agent.web_scraping.scraping_logger import ScrapingLogger

router = APIRouter(prefix="/api/scraping-logs", tags=["scraping-logs"])

# Initialize storage and logger
storage = LocalStorage()
scraping_logger = ScrapingLogger(storage)


class ScrapingLogResponse(BaseModel):
    """Scraping log response model"""
    id: int
    source_id: int
    source_name: str
    source_url: str
    status: str
    started_at: str
    completed_at: Optional[str]
    max_documents: int
    max_pages: int
    documents_found: int
    pages_scraped: int
    current_page: int
    execution_time: Optional[float]
    errors: List[dict]
    messages: List[str]


@router.get("/recent", response_model=List[ScrapingLogResponse])
async def get_recent_logs(limit: int = 50):
    """
    Get recent scraping logs
    
    Args:
        limit: Maximum number of logs to return (default: 50)
    
    Returns:
        List of recent scraping logs
    """
    try:
        logs = scraping_logger.get_recent_logs(limit)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{log_id}", response_model=ScrapingLogResponse)
async def get_log(log_id: int):
    """
    Get a specific scraping log
    
    Args:
        log_id: Log entry ID
    
    Returns:
        Scraping log details
    """
    try:
        log = scraping_logger.get_log(log_id)
        
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")
        
        return log
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/source/{source_id}", response_model=List[ScrapingLogResponse])
async def get_logs_for_source(source_id: int, limit: int = 20):
    """
    Get scraping logs for a specific source
    
    Args:
        source_id: Source ID
        limit: Maximum number of logs to return (default: 20)
    
    Returns:
        List of scraping logs for the source
    """
    try:
        logs = scraping_logger.get_logs_for_source(source_id, limit)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/old")
async def clear_old_logs(days: int = 30):
    """
    Clear logs older than specified days
    
    Args:
        days: Number of days to keep logs (default: 30)
    
    Returns:
        Success message
    """
    try:
        scraping_logger.clear_old_logs(days)
        return {"message": f"Cleared logs older than {days} days"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_logs_summary():
    """
    Get summary statistics of scraping logs
    
    Returns:
        Summary statistics
    """
    try:
        logs = scraping_logger.get_recent_logs(100)
        
        total_logs = len(logs)
        running_logs = len([log for log in logs if log['status'] == 'running'])
        successful_logs = len([log for log in logs if log['status'] == 'success'])
        failed_logs = len([log for log in logs if log['status'] == 'error'])
        
        total_documents = sum(log.get('documents_found', 0) for log in logs)
        total_pages = sum(log.get('pages_scraped', 0) for log in logs)
        
        return {
            "total_logs": total_logs,
            "running": running_logs,
            "successful": successful_logs,
            "failed": failed_logs,
            "total_documents_scraped": total_documents,
            "total_pages_scraped": total_pages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
