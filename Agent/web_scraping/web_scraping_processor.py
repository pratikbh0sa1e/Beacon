"""
Web Scraping Document Processor
Integrates web scraping with existing BEACON Agent pipeline
"""
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from Agent.web_scraping.web_source_manager import WebSourceManager
from backend.utils.text_extractor import extract_text
from backend.utils.supabase_storage import upload_to_supabase
from backend.database import Document, DocumentMetadata, SessionLocal
from Agent.metadata.extractor import MetadataExtractor
from Agent.lazy_rag.lazy_embedder import LazyEmbedder

logger = logging.getLogger(__name__)


class WebScrapingProcessor:
    """
    Process scraped documents through the complete BEACON pipeline:
    Scrape → Download → OCR → Metadata → Store → Lazy Embed → RAG Ready
    """
    
    def __init__(self):
        """Initialize processor with existing Agent components"""
        self.web_manager = WebSourceManager()
        self.metadata_extractor = MetadataExtractor()
        self.lazy_embedder = LazyEmbedder()
    
    def scrape_and_process(self,
                          url: str,
                          source_name: str,
                          keywords: Optional[List[str]] = None,
                          max_documents: int = 50,
                          uploader_id: int = 1,
                          institution_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Complete pipeline: Scrape → Process → Store → Ready for RAG
        
        Args:
            url: Website URL to scrape
            source_name: Name of the source
            keywords: Keywords to filter documents
            max_documents: Max documents to process
            uploader_id: User ID who initiated scraping
            institution_id: Institution ID for access control
        
        Returns:
            Processing result with statistics
        """
        logger.info(f"Starting scrape and process for {source_name}")
        
        # Step 1: Scrape and download documents
        scrape_result = self.web_manager.scrape_and_download(
            url=url,
            source_name=source_name,
            keywords=keywords,
            max_documents=max_documents
        )
        
        if scrape_result['status'] != 'success':
            return scrape_result
        
        # Step 2: Process each downloaded document
        processed_docs = []
        failed_docs = []
        
        for doc in scrape_result.get('downloaded_documents', []):
            try:
                result = self._process_single_document(
                    doc=doc,
                    source_name=source_name,
                    uploader_id=uploader_id,
                    institution_id=institution_id
                )
                
                if result['status'] == 'success':
                    processed_docs.append(result)
                else:
                    failed_docs.append(result)
            
            except Exception as e:
                logger.error(f"Error processing document {doc.get('text', 'unknown')}: {str(e)}")
                failed_docs.append({
                    'status': 'error',
                    'document': doc.get('text', 'unknown'),
                    'error': str(e)
                })
        
        return {
            'status': 'success',
            'source_name': source_name,
            'documents_scraped': scrape_result['documents_downloaded'],
            'documents_processed': len(processed_docs),
            'documents_failed': len(failed_docs),
            'processed_documents': processed_docs,
            'failed_documents': failed_docs,
            'scraped_at': scrape_result['scraped_at']
        }
    
    def _process_single_document(self,
                                doc: Dict[str, Any],
                                source_name: str,
                                uploader_id: int,
                                institution_id: Optional[int]) -> Dict[str, Any]:
        """
        Process a single scraped document through the pipeline
        
        Pipeline:
        1. Extract text (with OCR if needed)
        2. Upload to Supabase
        3. Extract metadata using Agent
        4. Store in database
        5. Mark for lazy embedding
        
        Args:
            doc: Document info from scraper
            source_name: Source name
            uploader_id: User ID
            institution_id: Institution ID
        
        Returns:
            Processing result
        """
        try:
            filepath = doc['download']['filepath']
            filename = doc['download']['filename']
            file_hash = doc['download']['file_hash']
            
            logger.info(f"Processing document: {filename}")
            
            # Step 1: Extract text (handles PDF, DOCX, images with OCR)
            extracted_text = extract_text(filepath)
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                logger.warning(f"No text extracted from {filename}")
                return {
                    'status': 'error',
                    'document': filename,
                    'error': 'No text could be extracted'
                }
            
            # Step 2: Upload to Supabase
            s3_url = upload_to_supabase(filepath, filename)
            
            # Step 3: Extract metadata using Agent
            metadata_result = self.metadata_extractor.extract_metadata(
                text=extracted_text,
                filename=filename
            )
            
            # Get matched keywords from document
            matched_keywords = doc.get('matched_keywords', [])
            if not matched_keywords and 'provenance' in doc:
                # Try to get from provenance metadata
                matched_keywords = doc['provenance'].get('metadata', {}).get('matched_keywords', [])
            
            # Step 4: Store in database
            db = SessionLocal()
            try:
                # Create document record
                document = Document(
                    filename=filename,
                    file_type=doc['type'],
                    file_path=filepath,
                    s3_url=s3_url,
                    extracted_text=extracted_text,
                    visibility_level='public',  # Default, can be changed
                    institution_id=institution_id,
                    uploader_id=uploader_id,
                    approval_status='approved',  # Auto-approve scraped docs
                    uploaded_at=datetime.utcnow()
                )
                
                db.add(document)
                db.flush()  # Get document ID
                
                # Combine AI-extracted tags with matched keywords
                all_tags = metadata_result.get('tags', [])
                # Add matched keywords as tags (with prefix for clarity)
                for keyword in matched_keywords:
                    tag = f"keyword:{keyword}"
                    if tag not in all_tags:
                        all_tags.append(tag)
                
                # Create metadata record
                doc_metadata = DocumentMetadata(
                    document_id=document.id,
                    title=metadata_result.get('title', filename),
                    description=metadata_result.get('description'),
                    category=metadata_result.get('category'),
                    tags=all_tags,  # Include matched keywords as tags
                    language=metadata_result.get('language', 'en'),
                    embedding_status='pending'  # Lazy embedding
                )
                
                db.add(doc_metadata)
                
                # Store provenance info
                from backend.database import ScrapedDocument
                scraped_doc = ScrapedDocument(
                    document_id=document.id,
                    source_url=doc['url'],
                    source_page=doc.get('source_page'),
                    source_domain=doc['provenance']['source_domain'],
                    credibility_score=doc['provenance']['credibility_score'],
                    scraped_at=datetime.fromisoformat(doc['provenance']['scraped_at']),
                    file_hash=file_hash,
                    provenance_metadata=doc['provenance']
                )
                
                db.add(scraped_doc)
                db.commit()
                
                logger.info(f"Successfully processed and stored: {filename} (ID: {document.id})")
                
                # Step 5: Document is now ready for lazy embedding
                # Embedding will happen on first query automatically
                
                return {
                    'status': 'success',
                    'document_id': document.id,
                    'filename': filename,
                    'title': metadata_result.get('title', filename),
                    'credibility_score': doc['provenance']['credibility_score'],
                    'matched_keywords': matched_keywords,  # NEW: Include matched keywords
                    'text_length': len(extracted_text),
                    'metadata': metadata_result
                }
            
            finally:
                db.close()
        
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return {
                'status': 'error',
                'document': doc.get('text', 'unknown'),
                'error': str(e)
            }
    
    def process_from_url_list(self,
                             urls: List[str],
                             source_name: str,
                             uploader_id: int,
                             institution_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Process documents from a list of direct URLs
        
        Args:
            urls: List of document URLs
            source_name: Source name
            uploader_id: User ID
            institution_id: Institution ID
        
        Returns:
            Processing result
        """
        logger.info(f"Processing {len(urls)} URLs from {source_name}")
        
        processed = []
        failed = []
        
        for url in urls:
            try:
                # Download document
                download_result = self.web_manager.downloader.download_document(url)
                
                if download_result['status'] != 'success':
                    failed.append({
                        'url': url,
                        'error': download_result.get('error')
                    })
                    continue
                
                # Create doc structure
                doc = {
                    'url': url,
                    'text': os.path.basename(url),
                    'type': self._get_file_type(url),
                    'download': download_result,
                    'provenance': self.web_manager.provenance.create_provenance_record(
                        url=url,
                        document_title=os.path.basename(url),
                        source_page=url
                    )
                }
                
                # Process through pipeline
                result = self._process_single_document(
                    doc=doc,
                    source_name=source_name,
                    uploader_id=uploader_id,
                    institution_id=institution_id
                )
                
                if result['status'] == 'success':
                    processed.append(result)
                else:
                    failed.append(result)
            
            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")
                failed.append({
                    'url': url,
                    'error': str(e)
                })
        
        return {
            'status': 'success',
            'source_name': source_name,
            'total_urls': len(urls),
            'processed': len(processed),
            'failed': len(failed),
            'processed_documents': processed,
            'failed_documents': failed
        }
    
    def _get_file_type(self, url: str) -> str:
        """Extract file type from URL"""
        url_lower = url.lower()
        if url_lower.endswith('.pdf'):
            return 'pdf'
        elif url_lower.endswith(('.docx', '.doc')):
            return 'docx'
        elif url_lower.endswith(('.pptx', '.ppt')):
            return 'pptx'
        else:
            return 'unknown'
    
    def get_processing_stats(self, db_session) -> Dict[str, Any]:
        """
        Get statistics about scraped and processed documents
        
        Args:
            db_session: Database session
        
        Returns:
            Statistics dictionary
        """
        from backend.database import ScrapedDocument, Document
        
        total_scraped = db_session.query(ScrapedDocument).count()
        
        # Get credibility distribution
        high_credibility = db_session.query(ScrapedDocument).filter(
            ScrapedDocument.credibility_score >= 9
        ).count()
        
        medium_credibility = db_session.query(ScrapedDocument).filter(
            ScrapedDocument.credibility_score >= 7,
            ScrapedDocument.credibility_score < 9
        ).count()
        
        low_credibility = db_session.query(ScrapedDocument).filter(
            ScrapedDocument.credibility_score < 7
        ).count()
        
        # Get source distribution
        from sqlalchemy import func
        source_stats = db_session.query(
            ScrapedDocument.source_domain,
            func.count(ScrapedDocument.id).label('count')
        ).group_by(ScrapedDocument.source_domain).all()
        
        return {
            'total_scraped_documents': total_scraped,
            'credibility_distribution': {
                'high': high_credibility,
                'medium': medium_credibility,
                'low': low_credibility
            },
            'source_distribution': [
                {'domain': domain, 'count': count}
                for domain, count in source_stats
            ]
        }
