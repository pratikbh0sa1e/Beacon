"""
Enhanced Document Identity Manager
Improved logic for document identity checking using URL-first approach
"""
import hashlib
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from urllib.parse import urlparse, parse_qs

from backend.database import Document, ScrapedDocument, DocumentMetadata

logger = logging.getLogger(__name__)


class DocumentIdentityManager:
    """Manage document identity checking and deduplication"""
    
    def __init__(self):
        """Initialize document identity manager"""
        self.url_cache = {}  # Cache for URL-based lookups
        self.hash_cache = {}  # Cache for content hash lookups
        
    def check_document_identity(
        self,
        url: str,
        content: str,
        title: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Check document identity using URL-first approach
        
        Args:
            url: Document source URL (primary identifier)
            content: Document content for hashing
            title: Document title
            db: Database session
            
        Returns:
            Identity check result with action recommendation
        """
        try:
            # Calculate content hash
            content_hash = self._calculate_content_hash(content)
            
            # Step 1: Check by source URL (primary identifier)
            url_result = self._check_by_source_url(url, content_hash, db)
            
            if url_result['found']:
                return url_result
            
            # Step 2: Check by content hash (for duplicates across sources)
            hash_result = self._check_by_content_hash(content_hash, url, db)
            
            if hash_result['found']:
                return hash_result
            
            # Step 3: Check by normalized URL (handle URL variations)
            normalized_url_result = self._check_by_normalized_url(url, content_hash, db)
            
            if normalized_url_result['found']:
                return normalized_url_result
            
            # Step 4: New document
            return {
                'action': 'create_new',
                'reason': 'new_document',
                'found': False,
                'url': url,
                'content_hash': content_hash,
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error checking document identity for {url}: {str(e)}")
            return {
                'action': 'error',
                'reason': 'identity_check_failed',
                'error': str(e),
                'url': url
            }
    
    def _check_by_source_url(self, url: str, content_hash: str, db: Session) -> Dict[str, Any]:
        """
        Check for existing document by source URL
        
        Args:
            url: Source URL
            content_hash: Content hash
            db: Database session
            
        Returns:
            Check result
        """
        try:
            # Check cache first
            if url in self.url_cache:
                cached_doc = self.url_cache[url]
                if cached_doc['content_hash'] == content_hash:
                    return {
                        'action': 'skip_unchanged',
                        'reason': 'same_url_same_content',
                        'found': True,
                        'document_id': cached_doc['document_id'],
                        'source': 'cache'
                    }
                else:
                    return {
                        'action': 'update_version',
                        'reason': 'same_url_different_content',
                        'found': True,
                        'document_id': cached_doc['document_id'],
                        'old_hash': cached_doc['content_hash'],
                        'new_hash': content_hash,
                        'source': 'cache'
                    }
            
            # Check database
            existing_doc = db.query(Document).filter(
                Document.source_url == url
            ).first()
            
            if not existing_doc:
                return {'found': False}
            
            # Cache the result
            self.url_cache[url] = {
                'document_id': existing_doc.id,
                'content_hash': existing_doc.content_hash
            }
            
            if existing_doc.content_hash == content_hash:
                # Same URL, same content - no changes
                return {
                    'action': 'skip_unchanged',
                    'reason': 'same_url_same_content',
                    'found': True,
                    'document_id': existing_doc.id,
                    'last_modified': existing_doc.last_modified_at_source.isoformat() if existing_doc.last_modified_at_source else None
                }
            else:
                # Same URL, different content - new version
                return {
                    'action': 'update_version',
                    'reason': 'same_url_different_content',
                    'found': True,
                    'document_id': existing_doc.id,
                    'old_hash': existing_doc.content_hash,
                    'new_hash': content_hash,
                    'family_id': existing_doc.document_family_id
                }
                
        except Exception as e:
            logger.error(f"Error checking by source URL {url}: {str(e)}")
            return {'found': False, 'error': str(e)}
    
    def _check_by_content_hash(self, content_hash: str, url: str, db: Session) -> Dict[str, Any]:
        """
        Check for existing document by content hash (duplicate detection)
        
        Args:
            content_hash: Content hash
            url: Current URL
            db: Database session
            
        Returns:
            Check result
        """
        try:
            # Check cache first
            if content_hash in self.hash_cache:
                cached_info = self.hash_cache[content_hash]
                return {
                    'action': 'link_duplicate',
                    'reason': 'same_content_different_url',
                    'found': True,
                    'document_id': cached_info['document_id'],
                    'existing_url': cached_info['url'],
                    'new_url': url,
                    'source': 'cache'
                }
            
            # Check database
            existing_doc = db.query(Document).filter(
                Document.content_hash == content_hash,
                Document.source_url != url  # Different URL
            ).first()
            
            if not existing_doc:
                return {'found': False}
            
            # Cache the result
            self.hash_cache[content_hash] = {
                'document_id': existing_doc.id,
                'url': existing_doc.source_url
            }
            
            return {
                'action': 'link_duplicate',
                'reason': 'same_content_different_url',
                'found': True,
                'document_id': existing_doc.id,
                'existing_url': existing_doc.source_url,
                'new_url': url,
                'family_id': existing_doc.document_family_id
            }
            
        except Exception as e:
            logger.error(f"Error checking by content hash {content_hash[:8]}: {str(e)}")
            return {'found': False, 'error': str(e)}
    
    def _check_by_normalized_url(self, url: str, content_hash: str, db: Session) -> Dict[str, Any]:
        """
        Check for existing document by normalized URL (handle URL variations)
        
        Args:
            url: Original URL
            content_hash: Content hash
            db: Database session
            
        Returns:
            Check result
        """
        try:
            # Normalize URL (remove query parameters, fragments, etc.)
            normalized_url = self._normalize_url(url)
            
            # Find similar URLs
            similar_docs = db.query(Document).filter(
                Document.source_url.like(f"{normalized_url}%")
            ).all()
            
            for doc in similar_docs:
                if self._urls_are_equivalent(url, doc.source_url):
                    if doc.content_hash == content_hash:
                        return {
                            'action': 'skip_unchanged',
                            'reason': 'equivalent_url_same_content',
                            'found': True,
                            'document_id': doc.id,
                            'original_url': doc.source_url,
                            'new_url': url
                        }
                    else:
                        return {
                            'action': 'update_version',
                            'reason': 'equivalent_url_different_content',
                            'found': True,
                            'document_id': doc.id,
                            'original_url': doc.source_url,
                            'new_url': url,
                            'old_hash': doc.content_hash,
                            'new_hash': content_hash
                        }
            
            return {'found': False}
            
        except Exception as e:
            logger.error(f"Error checking by normalized URL {url}: {str(e)}")
            return {'found': False, 'error': str(e)}
    
    def process_document_identity(
        self,
        identity_result: Dict[str, Any],
        url: str,
        content: str,
        title: str,
        source_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Process document based on identity check result
        
        Args:
            identity_result: Result from check_document_identity
            url: Document URL
            content: Document content
            title: Document title
            source_id: Source ID
            db: Database session
            
        Returns:
            Processing result
        """
        action = identity_result['action']
        
        try:
            if action == 'skip_unchanged':
                return self._handle_skip_unchanged(identity_result, url, db)
            
            elif action == 'update_version':
                return self._handle_update_version(identity_result, url, content, title, db)
            
            elif action == 'link_duplicate':
                return self._handle_link_duplicate(identity_result, url, source_id, db)
            
            elif action == 'create_new':
                return self._handle_create_new(identity_result, url, content, title, source_id, db)
            
            else:
                return {
                    'status': 'error',
                    'message': f"Unknown action: {action}",
                    'action': action
                }
                
        except Exception as e:
            logger.error(f"Error processing document identity: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'action': action
            }
    
    def _handle_skip_unchanged(self, identity_result: Dict, url: str, db: Session) -> Dict[str, Any]:
        """Handle unchanged document (skip processing)"""
        document_id = identity_result['document_id']
        
        # Update last seen timestamp
        try:
            scraped_doc = db.query(ScrapedDocument).filter(
                ScrapedDocument.document_id == document_id
            ).first()
            
            if scraped_doc:
                scraped_doc.scraped_at = datetime.utcnow()
                db.commit()
        except:
            pass  # Non-critical
        
        return {
            'status': 'skipped',
            'message': 'Document unchanged, skipped processing',
            'document_id': document_id,
            'action': 'skip_unchanged'
        }
    
    def _handle_update_version(
        self,
        identity_result: Dict,
        url: str,
        content: str,
        title: str,
        db: Session
    ) -> Dict[str, Any]:
        """Handle document version update"""
        document_id = identity_result['document_id']
        new_hash = identity_result['new_hash']
        
        # Update existing document
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if document:
            # Update document content and hash
            document.extracted_text = content
            document.content_hash = new_hash
            document.last_modified_at_source = datetime.utcnow()
            
            # Update metadata if title changed
            if document.filename != title:
                document.filename = title
                
                # Update document metadata
                doc_metadata = db.query(DocumentMetadata).filter(
                    DocumentMetadata.document_id == document_id
                ).first()
                
                if doc_metadata:
                    doc_metadata.title = title
                    doc_metadata.updated_at = datetime.utcnow()
            
            db.commit()
            
            # Update cache
            self.url_cache[url] = {
                'document_id': document_id,
                'content_hash': new_hash
            }
            
            return {
                'status': 'updated',
                'message': 'Document version updated',
                'document_id': document_id,
                'action': 'update_version'
            }
        
        return {
            'status': 'error',
            'message': 'Document not found for update',
            'document_id': document_id
        }
    
    def _handle_link_duplicate(
        self,
        identity_result: Dict,
        url: str,
        source_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Handle duplicate document (link to existing)"""
        document_id = identity_result['document_id']
        existing_url = identity_result['existing_url']
        
        # Check if scraped document entry exists
        scraped_doc = db.query(ScrapedDocument).filter(
            ScrapedDocument.document_id == document_id
        ).first()
        
        if scraped_doc:
            # Update provenance to include new source URL
            if scraped_doc.provenance_metadata:
                metadata = scraped_doc.provenance_metadata
                if 'source_urls' not in metadata:
                    metadata['source_urls'] = [existing_url]
                
                if url not in metadata['source_urls']:
                    metadata['source_urls'].append(url)
                    
                scraped_doc.provenance_metadata = metadata
            else:
                scraped_doc.provenance_metadata = {
                    'source_urls': [existing_url, url],
                    'duplicate_detected_at': datetime.utcnow().isoformat()
                }
            
            scraped_doc.scraped_at = datetime.utcnow()
            db.commit()
        
        return {
            'status': 'duplicate',
            'message': f'Duplicate content found, linked to existing document',
            'document_id': document_id,
            'existing_url': existing_url,
            'new_url': url,
            'action': 'link_duplicate'
        }
    
    def _handle_create_new(
        self,
        identity_result: Dict,
        url: str,
        content: str,
        title: str,
        source_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Handle new document creation"""
        content_hash = identity_result['content_hash']
        
        # This will be handled by the calling function
        # We just return the information needed for creation
        return {
            'status': 'new',
            'message': 'New document ready for creation',
            'url': url,
            'content': content,
            'title': title,
            'content_hash': content_hash,
            'source_id': source_id,
            'action': 'create_new'
        }
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate SHA256 hash of document content"""
        # Normalize content for consistent hashing
        normalized_content = ' '.join(content.split())
        return hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing query parameters and fragments"""
        try:
            parsed = urlparse(url)
            # Keep scheme, netloc, and path only
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            return normalized.rstrip('/')
        except:
            return url
    
    def _urls_are_equivalent(self, url1: str, url2: str) -> bool:
        """Check if two URLs are equivalent (ignoring minor differences)"""
        try:
            parsed1 = urlparse(url1)
            parsed2 = urlparse(url2)
            
            # Same domain and path
            if parsed1.netloc != parsed2.netloc or parsed1.path != parsed2.path:
                return False
            
            # Check query parameters (ignore order and minor differences)
            params1 = parse_qs(parsed1.query)
            params2 = parse_qs(parsed2.query)
            
            # Remove common tracking parameters
            tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'ref', 'source']
            
            for param in tracking_params:
                params1.pop(param, None)
                params2.pop(param, None)
            
            return params1 == params2
            
        except:
            return url1 == url2
    
    def get_identity_statistics(self, source_id: Optional[int], db: Session) -> Dict[str, Any]:
        """Get document identity statistics"""
        try:
            query = db.query(Document)
            
            if source_id:
                # Filter by source through scraped_documents
                query = query.join(ScrapedDocument).filter(
                    ScrapedDocument.source_id == source_id
                )
            
            total_docs = query.count()
            
            # Documents with duplicates (same content hash)
            duplicate_hashes = db.query(Document.content_hash).group_by(
                Document.content_hash
            ).having(db.func.count(Document.id) > 1).all()
            
            duplicate_count = len(duplicate_hashes)
            
            # Documents with multiple source URLs
            multi_source_docs = db.query(ScrapedDocument).filter(
                ScrapedDocument.provenance_metadata.contains({'source_urls'})
            ).count()
            
            return {
                'source_id': source_id,
                'total_documents': total_docs,
                'duplicate_content_groups': duplicate_count,
                'multi_source_documents': multi_source_docs,
                'cache_size_urls': len(self.url_cache),
                'cache_size_hashes': len(self.hash_cache),
                'deduplication_rate': round((duplicate_count / total_docs * 100), 2) if total_docs > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting identity statistics: {str(e)}")
            return {'error': str(e)}
    
    def clear_cache(self):
        """Clear identity caches"""
        self.url_cache.clear()
        self.hash_cache.clear()
        logger.info("Document identity caches cleared")
    
    def preload_cache(self, source_id: int, db: Session, limit: int = 1000):
        """Preload recent documents into cache"""
        try:
            recent_docs = db.query(Document).join(ScrapedDocument).filter(
                ScrapedDocument.source_id == source_id
            ).order_by(
                Document.uploaded_at.desc()
            ).limit(limit).all()
            
            for doc in recent_docs:
                if doc.source_url:
                    self.url_cache[doc.source_url] = {
                        'document_id': doc.id,
                        'content_hash': doc.content_hash
                    }
                
                if doc.content_hash:
                    self.hash_cache[doc.content_hash] = {
                        'document_id': doc.id,
                        'url': doc.source_url
                    }
            
            logger.info(f"Preloaded {len(recent_docs)} documents into identity cache for source {source_id}")
            
        except Exception as e:
            logger.error(f"Error preloading identity cache: {str(e)}")