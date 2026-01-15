"""
Sliding Window Re-scanning Manager
Always re-scan first N pages to catch updates, then continue from where we left off
"""
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import hashlib

from backend.database import WebScrapingSource, ScrapedDocumentTracker
from .site_scrapers import get_scraper_for_site

logger = logging.getLogger(__name__)


class SlidingWindowManager:
    """Manage sliding window re-scanning for government websites"""
    
    def __init__(self, window_size: int = 3):
        """
        Initialize sliding window manager
        
        Args:
            window_size: Number of recent pages to always re-scan
        """
        self.window_size = window_size
        self.page_hashes = {}  # Cache for page content hashes
        
    def scrape_with_sliding_window(
        self,
        source_id: int,
        db: Session,
        max_pages: int = 50,
        force_full_scan: bool = False
    ) -> Dict[str, Any]:
        """
        Scrape source using sliding window approach
        
        Args:
            source_id: Web scraping source ID
            db: Database session
            max_pages: Maximum pages to scrape
            force_full_scan: Force full scan ignoring sliding window
            
        Returns:
            Scraping results with sliding window statistics
        """
        logger.info(f"Starting sliding window scrape for source {source_id} (window_size={self.window_size})")
        
        # Get source
        source = db.query(WebScrapingSource).filter(
            WebScrapingSource.id == source_id
        ).first()
        
        if not source:
            raise ValueError(f"Source {source_id} not found")
        
        # Get appropriate scraper
        scraper = get_scraper_for_site(source.source_type)
        
        # Initialize results
        results = {
            'source_id': source_id,
            'source_name': source.name,
            'window_size': self.window_size,
            'pages_in_window': 0,
            'pages_beyond_window': 0,
            'pages_unchanged': 0,
            'pages_changed': 0,
            'documents_found': 0,
            'documents_new': 0,
            'documents_updated': 0,
            'execution_time': 0,
            'status': 'success'
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Determine scraping strategy
            if force_full_scan or not source.last_scraped_at:
                # Full scan for new sources or forced scans
                documents = self._full_scan_with_window(source, scraper, max_pages, db)
            else:
                # Sliding window scan for existing sources
                documents = self._sliding_window_scan(source, scraper, max_pages, db)
            
            # Update results
            results['documents_found'] = len(documents)
            results['execution_time'] = (datetime.utcnow() - start_time).total_seconds()
            
            # Update source metadata
            source.last_scraped_at = datetime.utcnow()
            source.last_scrape_status = 'success'
            db.commit()
            
            logger.info(f"Sliding window scrape completed: {len(documents)} documents found")
            
            return results
            
        except Exception as e:
            logger.error(f"Sliding window scrape failed: {str(e)}")
            results['status'] = 'error'
            results['error'] = str(e)
            
            # Update source with error
            source.last_scrape_status = 'failed'
            source.last_scrape_message = str(e)
            db.commit()
            
            return results
    
    def _full_scan_with_window(
        self,
        source: WebScrapingSource,
        scraper,
        max_pages: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Perform full scan while building sliding window cache
        
        Args:
            source: Web scraping source
            scraper: Site-specific scraper
            max_pages: Maximum pages to scan
            db: Database session
            
        Returns:
            List of documents found
        """
        logger.info(f"Performing full scan for {source.name}")
        
        all_documents = []
        pages_scraped = 0
        current_url = source.url
        
        # Track recent pages for sliding window
        recent_pages = []
        
        while current_url and pages_scraped < max_pages:
            # Scrape page
            page_result = scraper.scrape_page(current_url)
            
            if page_result['status'] != 'success':
                logger.warning(f"Failed to scrape page {current_url}: {page_result.get('error')}")
                break
            
            soup = page_result['soup']
            pages_scraped += 1
            
            # Calculate and store page hash
            page_hash = self._calculate_page_hash(soup)
            self._store_page_hash(current_url, page_hash, db)
            
            # Extract documents
            documents = scraper.get_document_links(soup, current_url)
            all_documents.extend(documents)
            
            logger.info(f"Page {pages_scraped}: Found {len(documents)} documents")
            
            # Add to recent pages
            recent_pages.append(current_url)
            if len(recent_pages) > self.window_size:
                recent_pages.pop(0)
            
            # Get next page
            pagination_links = scraper.get_pagination_links(soup, current_url)
            current_url = self._get_next_page(pagination_links, recent_pages)
        
        return all_documents
    
    def _sliding_window_scan(
        self,
        source: WebScrapingSource,
        scraper,
        max_pages: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Perform sliding window scan (re-scan recent pages + continue from last position)
        
        Args:
            source: Web scraping source
            scraper: Site-specific scraper
            max_pages: Maximum pages to scan
            db: Database session
            
        Returns:
            List of documents found
        """
        logger.info(f"Performing sliding window scan for {source.name}")
        
        all_documents = []
        
        # Phase 1: Re-scan sliding window pages
        window_documents = self._rescan_sliding_window(source, scraper, db)
        all_documents.extend(window_documents)
        
        # Phase 2: Continue from where we left off
        new_documents = self._scan_new_pages(source, scraper, max_pages - self.window_size, db)
        all_documents.extend(new_documents)
        
        return all_documents
    
    def _rescan_sliding_window(
        self,
        source: WebScrapingSource,
        scraper,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Re-scan the first N pages (sliding window) for updates
        
        Args:
            source: Web scraping source
            scraper: Site-specific scraper
            db: Database session
            
        Returns:
            List of documents found in sliding window
        """
        logger.info(f"Re-scanning sliding window ({self.window_size} pages) for {source.name}")
        
        documents = []
        pages_scanned = 0
        current_url = source.url
        
        while current_url and pages_scanned < self.window_size:
            # Scrape page
            page_result = scraper.scrape_page(current_url)
            
            if page_result['status'] != 'success':
                logger.warning(f"Failed to re-scan page {current_url}: {page_result.get('error')}")
                break
            
            soup = page_result['soup']
            pages_scanned += 1
            
            # Check if page has changed
            page_hash = self._calculate_page_hash(soup)
            old_hash = self._get_stored_page_hash(current_url, db)
            
            if old_hash and old_hash == page_hash:
                logger.debug(f"Page unchanged, skipping: {current_url}")
                # Get next page for window scanning
                pagination_links = scraper.get_pagination_links(soup, current_url)
                current_url = self._get_next_page(pagination_links, [])
                continue
            
            # Page has changed or is new - process it
            logger.info(f"Page changed, processing: {current_url}")
            
            # Update stored hash
            self._store_page_hash(current_url, page_hash, db)
            
            # Extract documents
            page_documents = scraper.get_document_links(soup, current_url)
            documents.extend(page_documents)
            
            logger.info(f"Sliding window page {pages_scanned}: Found {len(page_documents)} documents")
            
            # Get next page
            pagination_links = scraper.get_pagination_links(soup, current_url)
            current_url = self._get_next_page(pagination_links, [])
        
        logger.info(f"Sliding window re-scan complete: {len(documents)} documents found")
        return documents
    
    def _scan_new_pages(
        self,
        source: WebScrapingSource,
        scraper,
        max_new_pages: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Scan new pages beyond the sliding window
        
        Args:
            source: Web scraping source
            scraper: Site-specific scraper
            max_new_pages: Maximum new pages to scan
            db: Database session
            
        Returns:
            List of documents found in new pages
        """
        if max_new_pages <= 0:
            return []
        
        logger.info(f"Scanning new pages beyond sliding window for {source.name}")
        
        documents = []
        
        # Find where to start scanning (after sliding window)
        start_page = self.window_size + 1
        current_url = self._get_page_url(source.url, start_page)
        
        pages_scanned = 0
        
        while current_url and pages_scanned < max_new_pages:
            # Check if we've seen this page before
            if self._page_exists_in_db(current_url, db):
                logger.debug(f"Page already processed, skipping: {current_url}")
                # Try next page
                current_url = self._get_page_url(source.url, start_page + pages_scanned + 1)
                pages_scanned += 1
                continue
            
            # Scrape new page
            page_result = scraper.scrape_page(current_url)
            
            if page_result['status'] != 'success':
                logger.warning(f"Failed to scan new page {current_url}: {page_result.get('error')}")
                break
            
            soup = page_result['soup']
            pages_scanned += 1
            
            # Store page hash
            page_hash = self._calculate_page_hash(soup)
            self._store_page_hash(current_url, page_hash, db)
            
            # Extract documents
            page_documents = scraper.get_document_links(soup, current_url)
            documents.extend(page_documents)
            
            logger.info(f"New page {start_page + pages_scanned - 1}: Found {len(page_documents)} documents")
            
            # Get next page
            pagination_links = scraper.get_pagination_links(soup, current_url)
            if pagination_links:
                current_url = pagination_links[0]
            else:
                # Try constructing next page URL
                current_url = self._get_page_url(source.url, start_page + pages_scanned)
        
        logger.info(f"New pages scan complete: {len(documents)} documents found")
        return documents
    
    def _calculate_page_hash(self, soup) -> str:
        """
        Calculate hash of meaningful page content (excluding scripts, styles, etc.)
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            SHA256 hash of cleaned content
        """
        # Remove scripts, styles, and other non-content elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Get text content
        content = soup.get_text(strip=True)
        
        # Normalize whitespace
        content = ' '.join(content.split())
        
        # Calculate hash
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _store_page_hash(self, url: str, page_hash: str, db: Session):
        """Store page hash in database"""
        try:
            # Check if entry exists
            tracker = db.query(ScrapedDocumentTracker).filter(
                ScrapedDocumentTracker.document_url == url
            ).first()
            
            if tracker:
                tracker.content_hash = page_hash
                tracker.last_seen_at = datetime.utcnow()
            else:
                tracker = ScrapedDocumentTracker(
                    document_url=url,
                    content_hash=page_hash,
                    first_scraped_at=datetime.utcnow(),
                    last_seen_at=datetime.utcnow()
                )
                db.add(tracker)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error storing page hash for {url}: {str(e)}")
            db.rollback()
    
    def _get_stored_page_hash(self, url: str, db: Session) -> Optional[str]:
        """Get stored page hash from database"""
        try:
            tracker = db.query(ScrapedDocumentTracker).filter(
                ScrapedDocumentTracker.document_url == url
            ).first()
            
            return tracker.content_hash if tracker else None
            
        except Exception as e:
            logger.error(f"Error getting stored hash for {url}: {str(e)}")
            return None
    
    def _page_exists_in_db(self, url: str, db: Session) -> bool:
        """Check if page has been processed before"""
        try:
            tracker = db.query(ScrapedDocumentTracker).filter(
                ScrapedDocumentTracker.document_url == url
            ).first()
            
            return tracker is not None
            
        except Exception as e:
            logger.error(f"Error checking page existence for {url}: {str(e)}")
            return False
    
    def _get_next_page(self, pagination_links: List[str], visited_pages: List[str]) -> Optional[str]:
        """Get next page URL avoiding already visited pages"""
        for link in pagination_links:
            if link not in visited_pages:
                return link
        return None
    
    def _get_page_url(self, base_url: str, page_num: int) -> str:
        """Construct page URL for given page number"""
        # Simple page URL construction - can be enhanced per site
        if '?' in base_url:
            return f"{base_url}&page={page_num}"
        else:
            return f"{base_url}?page={page_num}"
    
    def get_sliding_window_stats(self, source_id: int, db: Session) -> Dict[str, Any]:
        """Get sliding window statistics for a source"""
        try:
            source = db.query(WebScrapingSource).filter(
                WebScrapingSource.id == source_id
            ).first()
            
            if not source:
                return {'error': 'Source not found'}
            
            # Get page tracking stats
            page_count = db.query(ScrapedDocumentTracker).filter(
                ScrapedDocumentTracker.source_id == source_id
            ).count()
            
            # Get recent activity
            recent_threshold = datetime.utcnow() - timedelta(days=7)
            recent_pages = db.query(ScrapedDocumentTracker).filter(
                ScrapedDocumentTracker.source_id == source_id,
                ScrapedDocumentTracker.last_seen_at >= recent_threshold
            ).count()
            
            return {
                'source_id': source_id,
                'source_name': source.name,
                'window_size': self.window_size,
                'total_pages_tracked': page_count,
                'recent_pages_updated': recent_pages,
                'last_scraped_at': source.last_scraped_at.isoformat() if source.last_scraped_at else None,
                'last_scrape_status': source.last_scrape_status
            }
            
        except Exception as e:
            logger.error(f"Error getting sliding window stats: {str(e)}")
            return {'error': str(e)}