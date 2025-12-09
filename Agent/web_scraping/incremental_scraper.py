"""
Incremental Scraper for tracking and scraping only new documents
"""
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class IncrementalScraper:
    """Track and scrape only new documents"""
    
    def __init__(self, storage):
        """
        Initialize incremental scraper
        
        Args:
            storage: LocalStorage instance for tracking documents
        """
        self.storage = storage
    
    def is_document_scraped(self, url: str) -> bool:
        """
        Check if document URL has been previously scraped
        
        Args:
            url: Document URL to check
        
        Returns:
            True if document has been scraped before
        """
        return self.storage.is_document_scraped(url)
    
    def get_document_hash(self, content: str) -> str:
        """
        Generate SHA-256 hash for document content
        
        Args:
            content: Document content (can be text or metadata)
        
        Returns:
            SHA-256 hash string
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def scrape_new_documents(self,
                            source_id: int,
                            all_documents: List[Dict[str, str]],
                            check_content_hash: bool = False) -> Dict[str, Any]:
        """
        Filter documents to only new ones
        
        Args:
            source_id: Source ID for tracking
            all_documents: List of all discovered documents
            check_content_hash: Whether to check content hash for changes
        
        Returns:
            Dict with:
                - new_documents: List of documents not seen before
                - skipped_documents: List of documents already scraped
                - changed_documents: List of documents with changed content (if check_content_hash=True)
                - statistics: Summary statistics
        """
        new_documents = []
        skipped_documents = []
        changed_documents = []
        
        logger.info(f"Filtering {len(all_documents)} discovered documents for source {source_id}")
        
        for doc in all_documents:
            url = doc.get('url')
            if not url:
                logger.warning(f"Document missing URL, skipping: {doc}")
                continue
            
            # Check if document has been scraped before
            if self.is_document_scraped(url):
                # Document exists in tracker
                if check_content_hash:
                    # Check if content has changed
                    stored_hash = self.storage.get_document_hash(url)
                    current_hash = self._generate_doc_hash(doc)
                    
                    if stored_hash != current_hash:
                        # Content has changed
                        logger.info(f"Document content changed: {url}")
                        doc['previous_hash'] = stored_hash
                        doc['current_hash'] = current_hash
                        changed_documents.append(doc)
                    else:
                        # Content unchanged, skip
                        skipped_documents.append(doc)
                else:
                    # Not checking content, just skip
                    skipped_documents.append(doc)
            else:
                # New document
                new_documents.append(doc)
        
        statistics = {
            'total_discovered': len(all_documents),
            'new_documents': len(new_documents),
            'skipped_documents': len(skipped_documents),
            'changed_documents': len(changed_documents),
            'source_id': source_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Incremental filtering complete: "
            f"{statistics['new_documents']} new, "
            f"{statistics['skipped_documents']} skipped, "
            f"{statistics['changed_documents']} changed"
        )
        
        return {
            'new_documents': new_documents,
            'skipped_documents': skipped_documents,
            'changed_documents': changed_documents,
            'statistics': statistics
        }
    
    def mark_documents_scraped(self, documents: List[Dict[str, str]], source_id: int):
        """
        Mark documents as scraped in tracking storage
        
        Args:
            documents: List of documents to mark as scraped
            source_id: Source ID for tracking
        """
        logger.info(f"Marking {len(documents)} documents as scraped for source {source_id}")
        
        for doc in documents:
            url = doc.get('url')
            if not url:
                logger.warning(f"Document missing URL, cannot track: {doc}")
                continue
            
            # Generate content hash
            content_hash = self._generate_doc_hash(doc)
            
            # Mark as scraped in storage
            self.storage.mark_document_scraped(url, content_hash, source_id)
        
        logger.info(f"Successfully marked {len(documents)} documents as scraped")
    
    def _generate_doc_hash(self, doc: Dict[str, str]) -> str:
        """
        Generate hash for a document based on its metadata
        
        Args:
            doc: Document dictionary
        
        Returns:
            SHA-256 hash of document metadata
        """
        # Create a stable string representation of document metadata
        # Use URL + text + type for hashing
        hash_content = f"{doc.get('url', '')}|{doc.get('text', '')}|{doc.get('type', '')}"
        return self.get_document_hash(hash_content)
    
    def get_scraping_statistics(self, source_id: int) -> Dict[str, Any]:
        """
        Get statistics about scraped documents for a source
        
        Args:
            source_id: Source ID
        
        Returns:
            Dict with statistics
        """
        tracked_docs = self.storage.get_tracked_documents_by_source(source_id)
        
        return {
            'source_id': source_id,
            'total_documents_tracked': len(tracked_docs),
            'first_scraped': min([d.get('first_scraped_at') for d in tracked_docs]) if tracked_docs else None,
            'last_scraped': max([d.get('last_seen_at') for d in tracked_docs]) if tracked_docs else None
        }
    
    def detect_content_changes(self, 
                              source_id: int,
                              current_documents: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Detect which documents have changed content since last scrape
        
        Args:
            source_id: Source ID
            current_documents: List of currently discovered documents
        
        Returns:
            List of documents with changed content
        """
        changed_docs = []
        
        for doc in current_documents:
            url = doc.get('url')
            if not url:
                continue
            
            if self.is_document_scraped(url):
                stored_hash = self.storage.get_document_hash(url)
                current_hash = self._generate_doc_hash(doc)
                
                if stored_hash and stored_hash != current_hash:
                    changed_docs.append({
                        'url': url,
                        'document': doc,
                        'previous_hash': stored_hash,
                        'current_hash': current_hash,
                        'detected_at': datetime.utcnow().isoformat()
                    })
        
        if changed_docs:
            logger.info(f"Detected {len(changed_docs)} documents with changed content")
        
        return changed_docs
    
    def force_rescrape(self, source_id: int):
        """
        Clear tracking data for a source to force full re-scrape
        
        Args:
            source_id: Source ID to clear tracking for
        """
        logger.warning(f"Forcing re-scrape for source {source_id} - clearing tracking data")
        
        # Get all tracked documents for this source
        tracked_docs = self.storage.get_tracked_documents_by_source(source_id)
        
        # Note: In a real implementation, we'd delete these from storage
        # For now, we'll just log the action
        logger.info(f"Would clear {len(tracked_docs)} tracked documents for source {source_id}")
        
        # TODO: Implement actual clearing in LocalStorage if needed
    
    def get_new_document_count(self, 
                              source_id: int,
                              discovered_documents: List[Dict[str, str]]) -> int:
        """
        Get count of new documents without full filtering
        
        Args:
            source_id: Source ID
            discovered_documents: List of discovered documents
        
        Returns:
            Count of new documents
        """
        new_count = 0
        
        for doc in discovered_documents:
            url = doc.get('url')
            if url and not self.is_document_scraped(url):
                new_count += 1
        
        return new_count
    
    def validate_incremental_accuracy(self, result: Dict[str, Any]) -> bool:
        """
        Validate that incremental scraping counts are accurate
        Property: new_documents + skipped_documents + changed_documents = total_discovered
        
        Args:
            result: Result from scrape_new_documents
        
        Returns:
            True if counts are accurate
        """
        stats = result['statistics']
        
        total = stats['new_documents'] + stats['skipped_documents'] + stats['changed_documents']
        expected = stats['total_discovered']
        
        if total != expected:
            logger.error(
                f"Incremental scraping count mismatch: "
                f"new({stats['new_documents']}) + "
                f"skipped({stats['skipped_documents']}) + "
                f"changed({stats['changed_documents']}) = {total}, "
                f"but expected {expected}"
            )
            return False
        
        return True
