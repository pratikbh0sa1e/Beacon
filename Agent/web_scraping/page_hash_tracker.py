"""
Page Content Hashing System
Track page content changes to avoid reprocessing unchanged pages
"""
import hashlib
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup

from backend.database import ScrapedDocumentTracker

logger = logging.getLogger(__name__)


class PageHashTracker:
    """Track page content hashes to detect changes"""
    
    def __init__(self):
        """Initialize page hash tracker"""
        self.hash_cache = {}  # In-memory cache for current session
        
    def calculate_page_hash(self, soup: BeautifulSoup, url: str) -> str:
        """
        Calculate hash of meaningful page content
        
        Args:
            soup: BeautifulSoup object of the page
            url: Page URL for logging
            
        Returns:
            SHA256 hash of cleaned content
        """
        try:
            # Create a copy to avoid modifying original
            soup_copy = BeautifulSoup(str(soup), 'html.parser')
            
            # Remove non-content elements that change frequently
            elements_to_remove = [
                'script', 'style', 'nav', 'footer', 'header', 'aside',
                # Remove dynamic elements
                '.timestamp', '.last-updated', '.current-time',
                '.social-media', '.advertisement', '.ads',
                # Remove navigation that might change
                '.breadcrumb', '.pagination', '.page-nav',
                # Remove user-specific content
                '.user-info', '.login-status', '.session-info'
            ]
            
            for selector in elements_to_remove:
                if selector.startswith('.') or selector.startswith('#'):
                    # CSS selector
                    for element in soup_copy.select(selector):
                        element.decompose()
                else:
                    # Tag name
                    for element in soup_copy.find_all(selector):
                        element.decompose()
            
            # Remove attributes that change frequently
            for tag in soup_copy.find_all():
                # Remove dynamic attributes
                dynamic_attrs = ['data-timestamp', 'data-session', 'data-user', 'id', 'class']
                for attr in dynamic_attrs:
                    if tag.has_attr(attr):
                        del tag[attr]
            
            # Get meaningful text content
            content = soup_copy.get_text(strip=True)
            
            # Normalize whitespace and line breaks
            content = ' '.join(content.split())
            
            # Remove common dynamic text patterns
            import re
            
            # Remove timestamps and dates that might change
            content = re.sub(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', '', content)
            content = re.sub(r'\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM)?', '', content)
            
            # Remove "last updated" type text
            content = re.sub(r'last updated:?\s*\S+', '', content, flags=re.IGNORECASE)
            content = re.sub(r'updated on:?\s*\S+', '', content, flags=re.IGNORECASE)
            
            # Calculate hash
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            logger.debug(f"Calculated hash for {url}: {content_hash[:8]}...")
            return content_hash
            
        except Exception as e:
            logger.error(f"Error calculating page hash for {url}: {str(e)}")
            # Return a timestamp-based hash as fallback
            return hashlib.sha256(f"{url}_{datetime.utcnow().isoformat()}".encode()).hexdigest()
    
    def has_page_changed(self, url: str, current_hash: str, db: Session) -> Dict[str, Any]:
        """
        Check if page has changed since last scrape
        
        Args:
            url: Page URL
            current_hash: Current page hash
            db: Database session
            
        Returns:
            Dict with change status and metadata
        """
        try:
            # Check cache first
            if url in self.hash_cache:
                cached_hash = self.hash_cache[url]
                if cached_hash == current_hash:
                    return {
                        'changed': False,
                        'source': 'cache',
                        'previous_hash': cached_hash,
                        'current_hash': current_hash
                    }
            
            # Check database
            tracker = db.query(ScrapedDocumentTracker).filter(
                ScrapedDocumentTracker.document_url == url
            ).first()
            
            if not tracker:
                # New page
                self.hash_cache[url] = current_hash
                return {
                    'changed': True,
                    'source': 'new_page',
                    'previous_hash': None,
                    'current_hash': current_hash,
                    'is_new': True
                }
            
            previous_hash = tracker.content_hash
            
            if previous_hash == current_hash:
                # Page unchanged
                self.hash_cache[url] = current_hash
                return {
                    'changed': False,
                    'source': 'database',
                    'previous_hash': previous_hash,
                    'current_hash': current_hash,
                    'last_seen': tracker.last_seen_at.isoformat() if tracker.last_seen_at else None
                }
            else:
                # Page changed
                self.hash_cache[url] = current_hash
                return {
                    'changed': True,
                    'source': 'database',
                    'previous_hash': previous_hash,
                    'current_hash': current_hash,
                    'last_seen': tracker.last_seen_at.isoformat() if tracker.last_seen_at else None
                }
                
        except Exception as e:
            logger.error(f"Error checking page change for {url}: {str(e)}")
            # Assume changed on error to be safe
            return {
                'changed': True,
                'source': 'error',
                'error': str(e),
                'current_hash': current_hash
            }
    
    def update_page_hash(
        self,
        url: str,
        page_hash: str,
        source_id: Optional[int],
        db: Session
    ) -> bool:
        """
        Update page hash in database
        
        Args:
            url: Page URL
            page_hash: New page hash
            source_id: Source ID (optional)
            db: Database session
            
        Returns:
            True if successful
        """
        try:
            # Check if entry exists
            tracker = db.query(ScrapedDocumentTracker).filter(
                ScrapedDocumentTracker.document_url == url
            ).first()
            
            if tracker:
                # Update existing entry
                tracker.content_hash = page_hash
                tracker.last_seen_at = datetime.utcnow()
                if source_id:
                    tracker.source_id = source_id
            else:
                # Create new entry
                tracker = ScrapedDocumentTracker(
                    document_url=url,
                    content_hash=page_hash,
                    source_id=source_id,
                    first_scraped_at=datetime.utcnow(),
                    last_seen_at=datetime.utcnow()
                )
                db.add(tracker)
            
            db.commit()
            
            # Update cache
            self.hash_cache[url] = page_hash
            
            logger.debug(f"Updated page hash for {url}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating page hash for {url}: {str(e)}")
            db.rollback()
            return False
    
    def should_process_page(
        self,
        url: str,
        soup: BeautifulSoup,
        source_id: Optional[int],
        db: Session,
        force_process: bool = False
    ) -> Dict[str, Any]:
        """
        Determine if page should be processed based on content changes
        
        Args:
            url: Page URL
            soup: BeautifulSoup object
            source_id: Source ID
            db: Database session
            force_process: Force processing regardless of changes
            
        Returns:
            Dict with processing decision and metadata
        """
        if force_process:
            return {
                'should_process': True,
                'reason': 'forced',
                'changed': True
            }
        
        # Calculate current hash
        current_hash = self.calculate_page_hash(soup, url)
        
        # Check if changed
        change_result = self.has_page_changed(url, current_hash, db)
        
        should_process = change_result['changed']
        
        # Update hash if processing
        if should_process:
            self.update_page_hash(url, current_hash, source_id, db)
        
        return {
            'should_process': should_process,
            'reason': 'changed' if change_result['changed'] else 'unchanged',
            'hash_info': change_result,
            'current_hash': current_hash
        }
    
    def get_page_history(self, url: str, db: Session) -> Dict[str, Any]:
        """
        Get page tracking history
        
        Args:
            url: Page URL
            db: Database session
            
        Returns:
            Page history information
        """
        try:
            tracker = db.query(ScrapedDocumentTracker).filter(
                ScrapedDocumentTracker.document_url == url
            ).first()
            
            if not tracker:
                return {
                    'exists': False,
                    'url': url
                }
            
            return {
                'exists': True,
                'url': url,
                'content_hash': tracker.content_hash,
                'source_id': tracker.source_id,
                'first_scraped_at': tracker.first_scraped_at.isoformat() if tracker.first_scraped_at else None,
                'last_seen_at': tracker.last_seen_at.isoformat() if tracker.last_seen_at else None,
                'document_id': tracker.document_id
            }
            
        except Exception as e:
            logger.error(f"Error getting page history for {url}: {str(e)}")
            return {
                'exists': False,
                'url': url,
                'error': str(e)
            }
    
    def cleanup_old_hashes(self, db: Session, days_old: int = 90) -> int:
        """
        Clean up old page hashes to prevent database bloat
        
        Args:
            db: Database session
            days_old: Remove hashes older than this many days
            
        Returns:
            Number of records cleaned up
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Delete old tracking records
            deleted_count = db.query(ScrapedDocumentTracker).filter(
                ScrapedDocumentTracker.last_seen_at < cutoff_date,
                ScrapedDocumentTracker.document_id.is_(None)  # Only delete if no associated document
            ).delete()
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old page hash records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old hashes: {str(e)}")
            db.rollback()
            return 0
    
    def get_hash_statistics(self, source_id: Optional[int], db: Session) -> Dict[str, Any]:
        """
        Get hash tracking statistics
        
        Args:
            source_id: Source ID (optional, for source-specific stats)
            db: Database session
            
        Returns:
            Hash tracking statistics
        """
        try:
            query = db.query(ScrapedDocumentTracker)
            
            if source_id:
                query = query.filter(ScrapedDocumentTracker.source_id == source_id)
            
            total_pages = query.count()
            
            # Recent activity (last 7 days)
            recent_threshold = datetime.utcnow() - timedelta(days=7)
            recent_pages = query.filter(
                ScrapedDocumentTracker.last_seen_at >= recent_threshold
            ).count()
            
            # Pages with documents
            pages_with_docs = query.filter(
                ScrapedDocumentTracker.document_id.isnot(None)
            ).count()
            
            return {
                'source_id': source_id,
                'total_pages_tracked': total_pages,
                'recent_pages_updated': recent_pages,
                'pages_with_documents': pages_with_docs,
                'cache_size': len(self.hash_cache),
                'tracking_efficiency': round((pages_with_docs / total_pages * 100), 2) if total_pages > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting hash statistics: {str(e)}")
            return {
                'error': str(e)
            }
    
    def clear_cache(self):
        """Clear in-memory hash cache"""
        self.hash_cache.clear()
        logger.info("Page hash cache cleared")
    
    def preload_cache(self, source_id: int, db: Session, limit: int = 1000):
        """
        Preload recent page hashes into cache for faster access
        
        Args:
            source_id: Source ID
            db: Database session
            limit: Maximum number of hashes to preload
        """
        try:
            recent_threshold = datetime.utcnow() - timedelta(days=30)
            
            trackers = db.query(ScrapedDocumentTracker).filter(
                ScrapedDocumentTracker.source_id == source_id,
                ScrapedDocumentTracker.last_seen_at >= recent_threshold
            ).order_by(
                ScrapedDocumentTracker.last_seen_at.desc()
            ).limit(limit).all()
            
            for tracker in trackers:
                self.hash_cache[tracker.document_url] = tracker.content_hash
            
            logger.info(f"Preloaded {len(trackers)} page hashes into cache for source {source_id}")
            
        except Exception as e:
            logger.error(f"Error preloading cache: {str(e)}")