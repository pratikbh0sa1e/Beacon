"""
Realtime scraper for on-demand document scraping
Integrates scraper, downloader, and document processing
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from .scraper import WebScraper
from .pdf_downloader import PDFDownloader
from backend.database import SessionLocal, Document, WebScrapingSource, ScrapedDocumentTracker
from backend.utils.text_extractor import extract_text

logger = logging.getLogger(__name__)


class RealtimeScraper:
    """Scrape documents on-demand for RAG queries"""
    
    def __init__(self):
        self.scraper = WebScraper()
        self.downloader = PDFDownloader()
    
    def scrape_for_query(
        self,
        user_query: str,
        user_id: int,
        source_name: str = "MoE",
        keywords: Optional[List[str]] = None,
        max_documents: int = 50,
        enable_pagination: bool = True,
        max_pages: int = 5,
        auto_expand_on_duplicates: bool = True,
        target_new_documents: int = 30
    ) -> Dict[str, Any]:
        """
        Scrape documents for a user query
        
        Args:
            user_query: User's search query
            user_id: User ID for tracking
            source_name: Source to scrape (MoE, UGC, AICTE)
            keywords: Keywords to filter documents
            max_documents: Maximum documents to scrape
            enable_pagination: Enable pagination
            max_pages: Maximum pages to scrape
            auto_expand_on_duplicates: Continue searching if duplicates found
            target_new_documents: Target number of new documents
        
        Returns:
            Dict with scraping results
        """
        logger.info(f"Starting realtime scrape for query: '{user_query}'")
        
        db = SessionLocal()
        
        try:
            # Get source
            source = db.query(WebScrapingSource).filter(
                WebScrapingSource.name == source_name
            ).first()
            
            if not source:
                return {
                    "status": "error",
                    "error": f"Source '{source_name}' not found"
                }
            
            # Step 1: Find document links
            logger.info(f"Scraping {source.url} for documents...")
            
            if enable_pagination:
                documents = self.scraper.scrape_with_smart_pagination(
                    base_url=source.url,
                    max_pages=max_pages,
                    keywords=keywords
                )
            else:
                documents = self.scraper.find_document_links(
                    url=source.url,
                    keywords=keywords
                )
            
            logger.info(f"Found {len(documents)} document links")
            
            # Step 2: Filter duplicates
            new_docs, skipped = self._filter_duplicates(db, documents)
            
            logger.info(f"After duplicate check: {len(new_docs)} new, {skipped} duplicates")
            
            # Step 3: Download and process documents
            processed = 0
            added = 0
            
            for doc_info in new_docs[:max_documents]:
                try:
                    # Download document
                    download_result = self.downloader.download_document_with_retry(
                        url=doc_info['url'],
                        max_retries=3
                    )
                    
                    if download_result['status'] != 'success':
                        logger.warning(f"Failed to download: {doc_info['url']}")
                        continue
                    
                    # Extract text
                    text = extract_text(
                        download_result['filepath'],
                        download_result['filename'].split('.')[-1]
                    )
                    
                    # Create document
                    document = Document(
                        filename=doc_info['text'][:500] or download_result['filename'],
                        file_path=download_result['filepath'],
                        file_type=doc_info['type'],
                        scraped_from_url=doc_info['url'],
                        file_hash=download_result['file_hash'],
                        extracted_text=text,
                        uploader_id=user_id,
                        visibility_level='public',
                        approval_status='approved',
                        download_allowed=True,
                        is_latest_version=True
                    )
                    
                    db.add(document)
                    db.commit()
                    db.refresh(document)
                    
                    # Track in scraper
                    tracker = ScrapedDocumentTracker(
                        document_url=doc_info['url'],
                        content_hash=download_result['file_hash'],
                        source_id=source.id,
                        document_id=document.id,
                        first_scraped_at=datetime.utcnow(),
                        last_seen_at=datetime.utcnow(),
                        scrape_count=1,
                        status='tracked'
                    )
                    
                    db.add(tracker)
                    db.commit()
                    
                    added += 1
                    processed += 1
                    
                    logger.info(f"Added document {document.id}: {document.filename[:50]}")
                    
                except Exception as e:
                    logger.error(f"Error processing document: {str(e)}")
                    continue
            
            return {
                "status": "success",
                "documents_discovered": len(documents),
                "documents_new": len(new_docs),
                "documents_skipped": skipped,
                "documents_added": added,
                "documents_processed": processed,
                "execution_time": 0
            }
            
        except Exception as e:
            logger.error(f"Error in realtime scrape: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
        
        finally:
            db.close()
    
    def _filter_duplicates(self, db, documents: List[Dict]) -> tuple:
        """Filter out duplicate documents"""
        if not documents:
            return [], 0
        
        urls = [doc['url'] for doc in documents]
        
        # Check which URLs are already tracked
        existing = db.query(ScrapedDocumentTracker).filter(
            ScrapedDocumentTracker.document_url.in_(urls)
        ).all()
        
        existing_urls = {tracker.document_url for tracker in existing}
        
        # Update last_seen for existing
        for tracker in existing:
            tracker.last_seen_at = datetime.utcnow()
            tracker.scrape_count += 1
        db.commit()
        
        # Filter new documents
        new_docs = [doc for doc in documents if doc['url'] not in existing_urls]
        
        return new_docs, len(existing_urls)
