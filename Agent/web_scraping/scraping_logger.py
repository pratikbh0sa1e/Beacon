"""
Scraping Logger - Stores scraping logs in database for frontend display
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from .local_storage import LocalStorage

logger = logging.getLogger(__name__)


class ScrapingLogger:
    """Log scraping activities to database for frontend display"""
    
    def __init__(self, storage: Optional[LocalStorage] = None):
        """
        Initialize scraping logger
        
        Args:
            storage: LocalStorage instance
        """
        self.storage = storage or LocalStorage()
    
    def log_scraping_start(self, 
                          source_id: int,
                          source_name: str,
                          source_url: str,
                          max_documents: int,
                          max_pages: int) -> int:
        """
        Log the start of a scraping job
        
        Args:
            source_id: Source ID
            source_name: Source name
            source_url: Source URL
            max_documents: Maximum documents to scrape
            max_pages: Maximum pages to scrape
        
        Returns:
            log_id: ID of the created log entry
        """
        log_entry = {
            'source_id': source_id,
            'source_name': source_name,
            'source_url': source_url,
            'status': 'running',
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': None,
            'max_documents': max_documents,
            'max_pages': max_pages,
            'documents_found': 0,
            'pages_scraped': 0,
            'current_page': 0,
            'errors': [],
            'messages': [f"Started scraping {source_name}"]
        }
        
        log_id = self.storage.create_scraping_log(log_entry)
        logger.info(f"Created scraping log {log_id} for {source_name}")
        
        return log_id
    
    def log_page_scraped(self,
                        log_id: int,
                        page_num: int,
                        documents_on_page: int):
        """
        Log that a page was scraped
        
        Args:
            log_id: Log entry ID
            page_num: Page number scraped
            documents_on_page: Documents found on this page
        """
        log_entry = self.storage.get_scraping_log(log_id)
        if not log_entry:
            return
        
        log_entry['current_page'] = page_num
        log_entry['pages_scraped'] = page_num
        log_entry['documents_found'] += documents_on_page
        log_entry['messages'].append(
            f"Page {page_num}: Found {documents_on_page} documents "
            f"(total: {log_entry['documents_found']})"
        )
        
        self.storage.update_scraping_log(log_id, log_entry)
    
    def log_document_limit_reached(self, log_id: int, total_documents: int):
        """
        Log that document limit was reached
        
        Args:
            log_id: Log entry ID
            total_documents: Total documents collected
        """
        log_entry = self.storage.get_scraping_log(log_id)
        if not log_entry:
            return
        
        log_entry['messages'].append(
            f"⚠️ Document limit reached: {total_documents} documents collected"
        )
        
        self.storage.update_scraping_log(log_id, log_entry)
    
    def log_error(self, log_id: int, error_message: str):
        """
        Log an error during scraping
        
        Args:
            log_id: Log entry ID
            error_message: Error message
        """
        log_entry = self.storage.get_scraping_log(log_id)
        if not log_entry:
            return
        
        error_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'message': error_message
        }
        
        log_entry['errors'].append(error_entry)
        log_entry['messages'].append(f"❌ Error: {error_message}")
        
        self.storage.update_scraping_log(log_id, log_entry)
        logger.error(f"Scraping error in log {log_id}: {error_message}")
    
    def log_scraping_complete(self,
                             log_id: int,
                             status: str,
                             documents_found: int,
                             pages_scraped: int,
                             execution_time: float):
        """
        Log completion of scraping job
        
        Args:
            log_id: Log entry ID
            status: Final status (success/error)
            documents_found: Total documents found
            pages_scraped: Total pages scraped
            execution_time: Execution time in seconds
        """
        log_entry = self.storage.get_scraping_log(log_id)
        if not log_entry:
            return
        
        log_entry['status'] = status
        log_entry['completed_at'] = datetime.utcnow().isoformat()
        log_entry['documents_found'] = documents_found
        log_entry['pages_scraped'] = pages_scraped
        log_entry['execution_time'] = execution_time
        
        if status == 'success':
            log_entry['messages'].append(
                f"✅ Scraping complete: {documents_found} documents in {execution_time:.1f}s"
            )
        else:
            log_entry['messages'].append(
                f"❌ Scraping failed after {execution_time:.1f}s"
            )
        
        self.storage.update_scraping_log(log_id, log_entry)
        logger.info(f"Scraping log {log_id} completed with status: {status}")
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent scraping logs
        
        Args:
            limit: Maximum number of logs to return
        
        Returns:
            List of log entries
        """
        return self.storage.get_recent_scraping_logs(limit)
    
    def get_log(self, log_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific scraping log
        
        Args:
            log_id: Log entry ID
        
        Returns:
            Log entry or None
        """
        return self.storage.get_scraping_log(log_id)
    
    def get_logs_for_source(self, source_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get scraping logs for a specific source
        
        Args:
            source_id: Source ID
            limit: Maximum number of logs to return
        
        Returns:
            List of log entries for the source
        """
        return self.storage.get_scraping_logs_for_source(source_id, limit)
    
    def clear_old_logs(self, days: int = 30):
        """
        Clear logs older than specified days
        
        Args:
            days: Number of days to keep logs
        """
        self.storage.clear_old_scraping_logs(days)
        logger.info(f"Cleared scraping logs older than {days} days")
