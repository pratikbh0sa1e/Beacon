"""
Enhanced Scraping Orchestrator
Integrates all 4 architectural improvements:
1. Site-specific scrapers
2. Sliding window re-scanning
3. Page content hashing
4. Enhanced document identity
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.database import SessionLocal, WebScrapingSource
from .site_scrapers import get_scraper_for_site
from .sliding_window_manager import SlidingWindowManager
from .page_hash_tracker import PageHashTracker
from .document_identity_manager import DocumentIdentityManager

logger = logging.getLogger(__name__)


class EnhancedScrapingOrchestrator:
    """
    Orchestrate enhanced scraping with all architectural improvements
    """
    
    def __init__(self, window_size: int = 3):
        """
        Initialize enhanced scraping orchestrator
        
        Args:
            window_size: Sliding window size for re-scanning
        """
        self.sliding_window_manager = SlidingWindowManager(window_size)
        self.page_hash_tracker = PageHashTracker()
        self.document_identity_manager = DocumentIdentityManager()
        
    def scrape_source_enhanced(
        self,
        source_id: int,
        max_pages: int = 50,
        max_documents: int = 1000,
        force_full_scan: bool = False
    ) -> Dict[str, Any]:
        """
        Scrape source using all enhanced features
        
        Args:
            source_id: Web scraping source ID
            max_pages: Maximum pages to scrape
            max_documents: Maximum documents to process
            force_full_scan: Force full scan ignoring optimizations
            
        Returns:
            Enhanced scraping results
        """
        db = SessionLocal()
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting enhanced scraping for source {source_id}")
            
            # Get source
            source = db.query(WebScrapingSource).filter(
                WebScrapingSource.id == source_id
            ).first()
            
            if not source:
                raise ValueError(f"Source {source_id} not found")
            
            # Get site-specific scraper
            scraper = get_scraper_for_site(source.source_type)
            logger.info(f"Using scraper: {scraper.__class__.__name__} for {source.name}")
            
            # Preload caches for better performance
            self._preload_caches(source_id, db)
            
            # Initialize results
            results = {
                'source_id': source_id,
                'source_name': source.name,
                'scraper_used': scraper.__class__.__name__,
                'start_time': start_time.isoformat(),
                'pages_processed': 0,
                'pages_unchanged': 0,
                'pages_changed': 0,
                'documents_discovered': 0,
                'documents_new': 0,
                'documents_updated': 0,
                'documents_skipped': 0,
                'documents_duplicates': 0,
                'errors': [],
                'status': 'success'
            }
            
            # Phase 1: Sliding window scraping with page hashing
            pages_to_process = self._get_pages_to_process(source, scraper, max_pages, force_full_scan, db)
            
            # Phase 2: Process each page with enhanced logic
            documents_processed = 0
            
            for page_info in pages_to_process:
                if documents_processed >= max_documents:
                    logger.info(f"Reached document limit ({max_documents}), stopping")
                    break
                
                try:
                    page_result = self._process_page_enhanced(
                        page_info, source, scraper, db
                    )
                    
                    # Update results
                    results['pages_processed'] += 1
                    
                    if page_result['page_changed']:
                        results['pages_changed'] += 1
                    else:
                        results['pages_unchanged'] += 1
                    
                    results['documents_discovered'] += page_result['documents_found']
                    results['documents_new'] += page_result['documents_new']
                    results['documents_updated'] += page_result['documents_updated']
                    results['documents_skipped'] += page_result['documents_skipped']
                    results['documents_duplicates'] += page_result['documents_duplicates']
                    
                    documents_processed += page_result['documents_processed']
                    
                    if page_result.get('errors'):
                        results['errors'].extend(page_result['errors'])
                    
                except Exception as e:
                    logger.error(f"Error processing page {page_info.get('url', 'unknown')}: {str(e)}")
                    results['errors'].append(f"Page processing error: {str(e)}")
            
            # Update source metadata
            source.last_scraped_at = datetime.utcnow()
            source.last_scrape_status = 'success' if not results['errors'] else 'partial'
            source.total_documents_scraped += results['documents_new'] + results['documents_updated']
            
            db.commit()
            
            # Calculate execution time
            end_time = datetime.utcnow()
            results['end_time'] = end_time.isoformat()
            results['execution_time_seconds'] = (end_time - start_time).total_seconds()
            
            logger.info(f"Enhanced scraping completed for {source.name}")
            logger.info(f"Results: {results['documents_new']} new, {results['documents_updated']} updated, "
                       f"{results['documents_skipped']} skipped, {results['documents_duplicates']} duplicates")
            
            return results
            
        except Exception as e:
            logger.error(f"Enhanced scraping failed for source {source_id}: {str(e)}")
            
            # Update source with error
            try:
                source = db.query(WebScrapingSource).filter(
                    WebScrapingSource.id == source_id
                ).first()
                if source:
                    source.last_scrape_status = 'failed'
                    source.last_scrape_message = str(e)
                    db.commit()
            except:
                pass
            
            return {
                'source_id': source_id,
                'status': 'error',
                'error': str(e),
                'start_time': start_time.isoformat(),
                'end_time': datetime.utcnow().isoformat()
            }
            
        finally:
            db.close()
    
    def _preload_caches(self, source_id: int, db: Session):
        """Preload caches for better performance"""
        try:
            logger.debug(f"Preloading caches for source {source_id}")
            
            # Preload page hash cache
            self.page_hash_tracker.preload_cache(source_id, db)
            
            # Preload document identity cache
            self.document_identity_manager.preload_cache(source_id, db)
            
        except Exception as e:
            logger.warning(f"Error preloading caches: {str(e)}")
    
    def _get_pages_to_process(
        self,
        source: WebScrapingSource,
        scraper,
        max_pages: int,
        force_full_scan: bool,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Get list of pages to process using sliding window logic
        
        Args:
            source: Web scraping source
            scraper: Site-specific scraper
            max_pages: Maximum pages
            force_full_scan: Force full scan
            db: Database session
            
        Returns:
            List of page information dictionaries
        """
        pages_to_process = []
        
        try:
            if force_full_scan or not source.last_scraped_at:
                # Full scan - get all pages up to max_pages
                logger.info(f"Performing full scan for {source.name}")
                pages_to_process = self._discover_all_pages(source, scraper, max_pages, db)
            else:
                # Sliding window scan
                logger.info(f"Performing sliding window scan for {source.name}")
                
                # Get sliding window pages (first N pages)
                window_pages = self._get_sliding_window_pages(source, scraper, db)
                pages_to_process.extend(window_pages)
                
                # Get new pages beyond sliding window
                remaining_pages = max_pages - len(window_pages)
                if remaining_pages > 0:
                    new_pages = self._discover_new_pages(source, scraper, remaining_pages, db)
                    pages_to_process.extend(new_pages)
            
            logger.info(f"Found {len(pages_to_process)} pages to process")
            return pages_to_process
            
        except Exception as e:
            logger.error(f"Error getting pages to process: {str(e)}")
            return []
    
    def _discover_all_pages(
        self,
        source: WebScrapingSource,
        scraper,
        max_pages: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Discover all pages for full scan"""
        pages = []
        current_url = source.url
        pages_found = 0
        
        while current_url and pages_found < max_pages:
            pages.append({
                'url': current_url,
                'page_number': pages_found + 1,
                'scan_type': 'full'
            })
            
            pages_found += 1
            
            # Get next page (simplified - real implementation would use scraper)
            try:
                page_result = scraper.scrape_page(current_url)
                if page_result['status'] == 'success':
                    pagination_links = scraper.get_pagination_links(page_result['soup'], current_url)
                    current_url = pagination_links[0] if pagination_links else None
                else:
                    break
            except:
                break
        
        return pages
    
    def _get_sliding_window_pages(
        self,
        source: WebScrapingSource,
        scraper,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get sliding window pages (first N pages)"""
        pages = []
        current_url = source.url
        window_size = self.sliding_window_manager.window_size
        
        for i in range(window_size):
            if not current_url:
                break
            
            pages.append({
                'url': current_url,
                'page_number': i + 1,
                'scan_type': 'sliding_window'
            })
            
            # Get next page
            try:
                page_result = scraper.scrape_page(current_url)
                if page_result['status'] == 'success':
                    pagination_links = scraper.get_pagination_links(page_result['soup'], current_url)
                    current_url = pagination_links[0] if pagination_links else None
                else:
                    break
            except:
                break
        
        return pages
    
    def _discover_new_pages(
        self,
        source: WebScrapingSource,
        scraper,
        max_new_pages: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Discover new pages beyond sliding window"""
        pages = []
        
        # Start from page after sliding window
        start_page = self.sliding_window_manager.window_size + 1
        
        for i in range(max_new_pages):
            page_num = start_page + i
            
            # Construct page URL (simplified)
            if '?' in source.url:
                page_url = f"{source.url}&page={page_num}"
            else:
                page_url = f"{source.url}?page={page_num}"
            
            # Check if page exists in database
            if not self.page_hash_tracker._page_exists_in_db(page_url, db):
                pages.append({
                    'url': page_url,
                    'page_number': page_num,
                    'scan_type': 'new_page'
                })
        
        return pages
    
    def _process_page_enhanced(
        self,
        page_info: Dict[str, Any],
        source: WebScrapingSource,
        scraper,
        db: Session
    ) -> Dict[str, Any]:
        """
        Process single page with all enhancements
        
        Args:
            page_info: Page information
            source: Web scraping source
            scraper: Site-specific scraper
            db: Database session
            
        Returns:
            Page processing results
        """
        page_url = page_info['url']
        
        results = {
            'page_url': page_url,
            'page_changed': False,
            'documents_found': 0,
            'documents_processed': 0,
            'documents_new': 0,
            'documents_updated': 0,
            'documents_skipped': 0,
            'documents_duplicates': 0,
            'errors': []
        }
        
        try:
            # Step 1: Scrape page
            page_result = scraper.scrape_page(page_url)
            
            if page_result['status'] != 'success':
                results['errors'].append(f"Failed to scrape page: {page_result.get('error')}")
                return results
            
            soup = page_result['soup']
            
            # Step 2: Check if page has changed using content hashing
            hash_decision = self.page_hash_tracker.should_process_page(
                page_url, soup, source.id, db
            )
            
            results['page_changed'] = hash_decision['should_process']
            
            if not hash_decision['should_process']:
                logger.debug(f"Page unchanged, skipping: {page_url}")
                return results
            
            logger.info(f"Page changed, processing: {page_url}")
            
            # Step 3: Extract documents using site-specific scraper
            documents = scraper.get_document_links(soup, page_url)
            results['documents_found'] = len(documents)
            
            # Step 4: Process each document with enhanced identity checking
            for doc_info in documents:
                try:
                    doc_result = self._process_document_enhanced(doc_info, source, db)
                    
                    results['documents_processed'] += 1
                    
                    if doc_result['status'] == 'new':
                        results['documents_new'] += 1
                    elif doc_result['status'] == 'updated':
                        results['documents_updated'] += 1
                    elif doc_result['status'] == 'skipped':
                        results['documents_skipped'] += 1
                    elif doc_result['status'] == 'duplicate':
                        results['documents_duplicates'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing document {doc_info.get('url', 'unknown')}: {str(e)}")
                    results['errors'].append(f"Document processing error: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing page {page_url}: {str(e)}")
            results['errors'].append(f"Page processing error: {str(e)}")
            return results
    
    def _process_document_enhanced(
        self,
        doc_info: Dict[str, Any],
        source: WebScrapingSource,
        db: Session
    ) -> Dict[str, Any]:
        """
        Process document with enhanced identity checking
        
        Args:
            doc_info: Document information from scraper
            source: Web scraping source
            db: Database session
            
        Returns:
            Document processing result
        """
        doc_url = doc_info['url']
        doc_title = doc_info['title']
        
        try:
            # For this example, we'll simulate content extraction
            # In real implementation, you'd download and extract the document
            doc_content = f"Simulated content for {doc_title}"
            
            # Step 1: Check document identity
            identity_result = self.document_identity_manager.check_document_identity(
                doc_url, doc_content, doc_title, db
            )
            
            # Step 2: Process based on identity result
            process_result = self.document_identity_manager.process_document_identity(
                identity_result, doc_url, doc_content, doc_title, source.id, db
            )
            
            return process_result
            
        except Exception as e:
            logger.error(f"Error in enhanced document processing for {doc_url}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'url': doc_url
            }
    
    def get_orchestrator_statistics(self, source_id: Optional[int] = None) -> Dict[str, Any]:
        """Get comprehensive statistics from all components"""
        db = SessionLocal()
        
        try:
            stats = {
                'timestamp': datetime.utcnow().isoformat(),
                'source_id': source_id
            }
            
            # Sliding window stats
            if source_id:
                stats['sliding_window'] = self.sliding_window_manager.get_sliding_window_stats(source_id, db)
            
            # Page hash stats
            stats['page_hashing'] = self.page_hash_tracker.get_hash_statistics(source_id, db)
            
            # Document identity stats
            stats['document_identity'] = self.document_identity_manager.get_identity_statistics(source_id, db)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting orchestrator statistics: {str(e)}")
            return {'error': str(e)}
            
        finally:
            db.close()
    
    def clear_all_caches(self):
        """Clear all component caches"""
        self.page_hash_tracker.clear_cache()
        self.document_identity_manager.clear_cache()
        logger.info("All orchestrator caches cleared")


# Convenience function for external use
def scrape_source_with_enhancements(
    source_id: int,
    max_pages: int = 50,
    max_documents: int = 1000,
    window_size: int = 3,
    force_full_scan: bool = False
) -> Dict[str, Any]:
    """
    Scrape source with all enhancements - convenience function
    
    Args:
        source_id: Web scraping source ID
        max_pages: Maximum pages to scrape
        max_documents: Maximum documents to process
        window_size: Sliding window size
        force_full_scan: Force full scan
        
    Returns:
        Scraping results
    """
    orchestrator = EnhancedScrapingOrchestrator(window_size)
    return orchestrator.scrape_source_enhanced(
        source_id, max_pages, max_documents, force_full_scan
    )