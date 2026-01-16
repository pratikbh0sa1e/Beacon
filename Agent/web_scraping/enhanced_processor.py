"""Enhanced Web Scraping Processor with Document Family Integration"""
import logging
import hashlib
import os
import requests
from typing import List, Dict, Optional, Set
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time

from backend.database import SessionLocal, Document, DocumentMetadata, WebScrapingSource
from backend.utils.text_extractor import extract_text
from Agent.metadata.extractor import MetadataExtractor
from Agent.document_families.family_manager import process_scraped_document

# Import enhanced scraping components
from .enhanced_scraping_orchestrator import EnhancedScrapingOrchestrator

logger = logging.getLogger(__name__)


class EnhancedWebScrapingProcessor:
    """Enhanced web scraping with deduplication and family management"""
    
    def __init__(self):
        self.metadata_extractor = MetadataExtractor()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def scrape_source_enhanced(
        self,
        source_id: int,
        keywords: Optional[List[str]] = None,
        max_documents: int = 1500,
        pagination_enabled: bool = True,
        max_pages: int = 100,
        incremental: bool = True
    ) -> Dict:
        """
        Enhanced scraping with deduplication and family management
        
        Args:
            source_id: Web scraping source ID
            keywords: Keywords to filter documents
            max_documents: Maximum documents to scrape
            pagination_enabled: Whether to follow pagination
            max_pages: Maximum pages to scrape
            incremental: Whether to skip unchanged documents
        """
        db = SessionLocal()
        start_time = time.time()
        
        try:
            # Get source
            source = db.query(WebScrapingSource).filter(
                WebScrapingSource.id == source_id
            ).first()
            
            if not source:
                raise ValueError(f"Source {source_id} not found")
            
            logger.info(f"Starting enhanced scraping for {source.name}")
            
            # Initialize counters
            stats = {
                "documents_discovered": 0,
                "documents_new": 0,
                "documents_updated": 0,
                "documents_unchanged": 0,
                "documents_duplicate": 0,
                "documents_processed": 0,
                "families_created": 0,
                "families_updated": 0,
                "pages_scraped": 0,
                "errors": []
            }
            
            # Track processed URLs to avoid duplicates within same scrape
            processed_urls: Set[str] = set()
            
            # Start scraping
            pages_to_scrape = [source.url]
            
            while pages_to_scrape and stats["pages_scraped"] < max_pages:
                current_url = pages_to_scrape.pop(0)
                
                try:
                    logger.info(f"Scraping page: {current_url}")
                    
                    # Get page content
                    response = self.session.get(current_url, timeout=30)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    stats["pages_scraped"] += 1
                    
                    # Find document links
                    document_links = self._extract_document_links(soup, current_url)
                    stats["documents_discovered"] += len(document_links)
                    
                    logger.info(f"Found {len(document_links)} document links on page")
                    
                    # Process each document
                    for doc_info in document_links:
                        if stats["documents_processed"] >= max_documents:
                            break
                            
                        doc_url = doc_info["url"]
                        
                        # Skip if already processed in this scrape
                        if doc_url in processed_urls:
                            continue
                            
                        processed_urls.add(doc_url)
                        
                        try:
                            # Filter by keywords if provided
                            if keywords and not self._matches_keywords(doc_info, keywords):
                                continue
                            
                            # Process document with family management
                            result = self._process_document_enhanced(
                                doc_info, source, incremental, db
                            )
                            
                            # Update stats
                            if result["status"] == "new":
                                stats["documents_new"] += 1
                                if result.get("is_new_family"):
                                    stats["families_created"] += 1
                                else:
                                    stats["families_updated"] += 1
                            elif result["status"] == "updated":
                                stats["documents_updated"] += 1
                                stats["families_updated"] += 1
                            elif result["status"] == "unchanged":
                                stats["documents_unchanged"] += 1
                            elif result["status"] == "duplicate":
                                stats["documents_duplicate"] += 1
                            
                            stats["documents_processed"] += 1
                            
                            # Rate limiting
                            time.sleep(0.5)
                            
                        except Exception as e:
                            logger.error(f"Error processing document {doc_url}: {str(e)}")
                            stats["errors"].append(f"Document {doc_url}: {str(e)}")
                    
                    # Find pagination links if enabled
                    if pagination_enabled and len(pages_to_scrape) < max_pages:
                        pagination_links = self._find_pagination_links(soup, current_url)
                        for link in pagination_links:
                            if link not in processed_urls and link not in pages_to_scrape:
                                pages_to_scrape.append(link)
                    
                except Exception as e:
                    logger.error(f"Error scraping page {current_url}: {str(e)}")
                    stats["errors"].append(f"Page {current_url}: {str(e)}")
            
            # Update source statistics
            source.last_scraped_at = datetime.utcnow()
            source.last_scrape_status = "success" if not stats["errors"] else "partial"
            source.total_documents_scraped += stats["documents_new"] + stats["documents_updated"]
            
            db.commit()
            
            execution_time = time.time() - start_time
            
            logger.info(f"Enhanced scraping completed in {execution_time:.2f}s")
            logger.info(f"Stats: {stats}")
            
            return {
                "status": "success",
                "execution_time": execution_time,
                "source_name": source.name,
                **stats
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Enhanced scraping failed: {str(e)}")
            
            # Update source with error
            try:
                source = db.query(WebScrapingSource).filter(
                    WebScrapingSource.id == source_id
                ).first()
                if source:
                    source.last_scrape_status = "failed"
                    source.last_scrape_message = str(e)
                    db.commit()
            except:
                pass
            
            raise
        finally:
            db.close()
    
    def _extract_document_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract document links from page"""
        document_links = []
        
        # Common document extensions
        doc_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Check if it's a document link
            parsed_url = urlparse(full_url)
            path_lower = parsed_url.path.lower()
            
            is_document = any(path_lower.endswith(ext) for ext in doc_extensions)
            
            if is_document:
                # Extract title and metadata
                title = link.get_text(strip=True)
                if not title:
                    title = href.split('/')[-1]
                
                # Get file extension
                file_ext = None
                for ext in doc_extensions:
                    if path_lower.endswith(ext):
                        file_ext = ext[1:]  # Remove dot
                        break
                
                # Get surrounding context for better filtering
                context = ""
                parent = link.parent
                if parent:
                    context = parent.get_text(strip=True)[:200]
                
                document_links.append({
                    "url": full_url,
                    "title": title,
                    "file_type": file_ext,
                    "context": context,
                    "link_text": link.get_text(strip=True)
                })
        
        return document_links
    
    def _matches_keywords(self, doc_info: Dict, keywords: List[str]) -> bool:
        """Check if document matches any of the keywords"""
        if not keywords:
            return True
        
        # Combine all text for matching
        searchable_text = " ".join([
            doc_info.get("title", ""),
            doc_info.get("context", ""),
            doc_info.get("link_text", "")
        ]).lower()
        
        # Check if any keyword matches
        return any(keyword.lower() in searchable_text for keyword in keywords)
    
    def _process_document_enhanced(
        self,
        doc_info: Dict,
        source: WebScrapingSource,
        incremental: bool,
        db
    ) -> Dict:
        """Process document with enhanced family management"""
        doc_url = doc_info["url"]
        
        try:
            # Download document
            logger.info(f"Downloading document: {doc_url}")
            
            response = self.session.get(doc_url, timeout=60)
            response.raise_for_status()
            
            # Get last modified date from headers
            last_modified_str = response.headers.get('Last-Modified')
            last_modified_at_source = None
            if last_modified_str:
                try:
                    from email.utils import parsedate_to_datetime
                    last_modified_at_source = parsedate_to_datetime(last_modified_str)
                except:
                    pass
            
            # Extract text content
            content = ""
            if doc_info["file_type"] in ["pdf", "doc", "docx"]:
                # Save temporarily and extract
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix=f".{doc_info['file_type']}"
                ) as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                
                try:
                    content = extract_text(tmp_path, doc_info["file_type"])
                finally:
                    os.unlink(tmp_path)
            else:
                # For other types, use response text
                content = response.text
            
            if not content or len(content.strip()) < 100:
                return {
                    "status": "error",
                    "message": "Could not extract meaningful content"
                }
            
            # Check for updates if incremental
            if incremental:
                from Agent.document_families.family_manager import DocumentFamilyManager
                manager = DocumentFamilyManager()
                
                update_check = manager.check_for_updates(
                    doc_url, content, last_modified_at_source, db
                )
                
                if update_check["status"] == "unchanged":
                    return update_check
            
            # Create document record
            document = Document(
                filename=doc_info["title"][:255],
                file_type=doc_info["file_type"],
                extracted_text=content,
                scraped_from_url=doc_url,
                last_modified_at_source=last_modified_at_source,
                visibility_level="public",
                approval_status="approved",  # Auto-approve scraped docs
                uploaded_at=datetime.utcnow(),
                content_hash=hashlib.sha256(content.encode('utf-8')).hexdigest()
            )
            
            db.add(document)
            db.flush()  # Get document ID
            
            # Extract and save metadata
            try:
                metadata_dict = self.metadata_extractor.extract_metadata(
                    content, document.filename
                )
                
                doc_metadata = DocumentMetadata(
                    document_id=document.id,
                    title=metadata_dict.get('title', doc_info["title"])[:500],
                    department=metadata_dict.get('department'),
                    document_type=metadata_dict.get('document_type'),
                    summary=metadata_dict.get('summary'),
                    keywords=metadata_dict.get('keywords', []),
                    bm25_keywords=metadata_dict.get('bm25_keywords'),
                    text_length=len(content),
                    metadata_status='ready',
                    embedding_status='uploaded'
                )
                
                db.add(doc_metadata)
                
            except Exception as e:
                logger.error(f"Error extracting metadata: {str(e)}")
                # Create basic metadata
                doc_metadata = DocumentMetadata(
                    document_id=document.id,
                    title=doc_info["title"][:500],
                    text_length=len(content),
                    metadata_status='ready',
                    embedding_status='uploaded'
                )
                db.add(doc_metadata)
            
            db.commit()
            
            # Process through family management system
            family_result = process_scraped_document(
                document.id,
                doc_info["title"],
                content,
                doc_url,
                last_modified_at_source
            )
            
            if family_result["status"] == "duplicate":
                # Remove the document we just created since it's a duplicate
                db.delete(document)
                db.commit()
                return family_result
            
            logger.info(f"Successfully processed document {document.id} into family {family_result.get('family_id')}")
            
            return {
                "status": "new" if family_result["status"] == "added" else family_result["status"],
                "document_id": document.id,
                "family_id": family_result.get("family_id"),
                "version_number": family_result.get("version_number"),
                "is_new_family": family_result.get("is_new_family", False),
                "title": doc_info["title"]
            }
            
        except Exception as e:
            logger.error(f"Error processing document {doc_url}: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _find_pagination_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find pagination links on the page"""
        pagination_links = []
        
        # Common pagination patterns
        pagination_selectors = [
            'a[href*="page"]',
            'a[href*="next"]',
            '.pagination a',
            '.pager a',
            'a:contains("Next")',
            'a:contains(">")',
            'a[title*="next"]'
        ]
        
        for selector in pagination_selectors:
            try:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        if full_url not in pagination_links:
                            pagination_links.append(full_url)
            except:
                continue
        
        return pagination_links[:5]  # Limit to 5 pagination links per page


# Integration function for existing web scraping system
def enhanced_scrape_source(
    source_id: int,
    keywords: Optional[List[str]] = None,
    max_documents: int = 1500,
    pagination_enabled: bool = True,
    max_pages: int = 100,
    incremental: bool = True,
    stop_flag: Optional[callable] = None
) -> Dict:
    """
    Enhanced scraping function that saves documents to database
    Uses the new enhanced scraping orchestrator with database storage
    
    Args:
        stop_flag: Callable that returns True if scraping should stop
    """
    logger.info(f"Using enhanced scraping with database storage for source {source_id}")
    
    # Initialize metadata extractor
    metadata_extractor = MetadataExtractor()
    
    db = SessionLocal()
    start_time = time.time()
    
    try:
        # Get source
        source = db.query(WebScrapingSource).filter(
            WebScrapingSource.id == source_id
        ).first()
        
        if not source:
            raise ValueError(f"Source {source_id} not found")
        
        logger.info(f"Starting enhanced scraping for {source.name}")
        
        # Check stop flag before starting
        if stop_flag and stop_flag():
            logger.info("Scraping stopped before starting")
            return {
                "status": "stopped",
                "message": "Scraping was stopped",
                "documents_discovered": 0,
                "documents_new": 0
            }
        
        # Use site-specific scraper based on source URL
        from .site_scrapers import get_scraper_for_site
        
        # Detect scraper type from source URL
        source_url_lower = source.url.lower()
        if 'ugc.gov.in' in source_url_lower or 'ugc' in source.name.lower():
            scraper_type = "ugc"
            logger.info(f"Using UGC scraper for {source.name}")
        elif 'aicte' in source_url_lower or 'aicte' in source.name.lower():
            scraper_type = "aicte"
            logger.info(f"Using AICTE scraper for {source.name}")
        elif 'education.gov.in' in source_url_lower or 'moe' in source.name.lower() or 'ministry of education' in source.name.lower():
            scraper_type = "moe"
            logger.info(f"Using MoE scraper for {source.name}")
        elif 'ncert' in source_url_lower or 'ncert' in source.name.lower():
            scraper_type = "ncert"
            logger.info(f"Using NCERT scraper for {source.name}")
        else:
            scraper_type = "generic"
            logger.info(f"Using generic scraper for {source.name}")
        
        scraper = get_scraper_for_site(scraper_type)
        
        # Initialize stats
        stats = {
            "documents_discovered": 0,
            "documents_new": 0,
            "documents_updated": 0,
            "documents_unchanged": 0,
            "documents_duplicate": 0,
            "documents_processed": 0,
            "documents_failed_metadata": 0,  # NEW: Documents deleted due to metadata failure
            "pages_scraped": 0,
            "errors": []
        }
        
        # Scrape the source URL
        try:
            logger.info(f"Scraping page: {source.url}")
            
            # Get page content using site-specific scraper
            page_result = scraper.scrape_page(source.url)
            
            if page_result['status'] != 'success':
                raise Exception(f"Failed to scrape page: {page_result.get('error')}")
            
            stats["pages_scraped"] = 1
            
            # Extract document links
            documents = scraper.get_document_links(page_result['soup'], source.url)
            stats["documents_discovered"] = len(documents)
            
            logger.info(f"Found {len(documents)} document links on first page")
            
            # ✅ NEW: Add pagination support
            if pagination_enabled and len(documents) < max_documents:
                pagination_links = scraper.get_pagination_links(page_result['soup'], source.url)
                
                pages_scraped = 1
                for page_url in pagination_links:
                    # Check stop flag
                    if stop_flag and stop_flag():
                        logger.info(f"Scraping stopped by user during pagination after {pages_scraped} pages")
                        break
                    
                    if pages_scraped >= max_pages:
                        break
                    
                    if stats["documents_discovered"] >= max_documents:
                        break
                    
                    try:
                        logger.info(f"Scraping additional page {pages_scraped + 1}: {page_url}")
                        
                        page_result = scraper.scrape_page(page_url)
                        if page_result['status'] != 'success':
                            continue
                        
                        more_documents = scraper.get_document_links(page_result['soup'], page_url)
                        documents.extend(more_documents)
                        stats["documents_discovered"] += len(more_documents)
                        stats["pages_scraped"] += 1
                        pages_scraped += 1
                        
                        logger.info(f"Found {len(more_documents)} more documents on page {pages_scraped}")
                        
                        # Rate limiting between pages
                        time.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error scraping page {page_url}: {e}")
                        continue
            
            logger.info(f"Total documents discovered across {stats['pages_scraped']} pages: {stats['documents_discovered']}")
            
            # ✅ FIXED: Process all documents up to max_documents (removed 10-doc limit)
            processed_count = 0
            for doc_info in documents[:max_documents]:  # ✅ No more hard-coded limit!
                # Check stop flag
                if stop_flag and stop_flag():
                    logger.info(f"Scraping stopped by user after processing {processed_count} documents")
                    stats["status"] = "stopped"
                    break
                
                if processed_count >= max_documents:
                    break
                
                try:
                    # ✅ NEW: Progress logging every 50 documents
                    if processed_count > 0 and processed_count % 50 == 0:
                        logger.info(f"Progress: {processed_count}/{min(len(documents), max_documents)} documents processed")
                        logger.info(f"Stats: {stats['documents_new']} new, {stats['documents_unchanged']} unchanged")
                    
                    # Filter by keywords if provided
                    if keywords:
                        title_lower = doc_info.get('title', '').lower()
                        if not any(keyword.lower() in title_lower for keyword in keywords):
                            continue
                    
                    # Check if document already exists in database
                    existing_doc = db.query(Document).filter(
                        Document.source_url == doc_info['url']
                    ).first()
                    
                    if existing_doc:
                        stats["documents_unchanged"] += 1
                        logger.info(f"Document already exists: {doc_info['title']}")
                        continue
                    
                    # Download and extract text content (following normal workflow)
                    logger.info(f"Downloading and processing document: {doc_info['url']}")
                    
                    try:
                        # Download document
                        response = requests.get(doc_info['url'], timeout=30)
                        response.raise_for_status()
                        
                        # Save temporarily for text extraction and permanent storage
                        import tempfile
                        import re
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        # Better filename sanitization - remove ALL invalid characters
                        safe_filename = doc_info['title'][:100]
                        # Remove or replace invalid characters for Supabase storage
                        safe_filename = safe_filename.replace(':', '-')  # Colons to dashes
                        safe_filename = safe_filename.replace('"', '')   # Remove quotes
                        safe_filename = safe_filename.replace("'", '')   # Remove single quotes
                        safe_filename = safe_filename.replace('/', '_')  # Slashes to underscores
                        safe_filename = safe_filename.replace('\\', '_') # Backslashes to underscores
                        safe_filename = safe_filename.replace('?', '')   # Remove question marks
                        safe_filename = safe_filename.replace('*', '')   # Remove asterisks
                        safe_filename = safe_filename.replace('<', '')   # Remove less than
                        safe_filename = safe_filename.replace('>', '')   # Remove greater than
                        safe_filename = safe_filename.replace('|', '')   # Remove pipes
                        safe_filename = safe_filename.replace('\n', ' ') # Newlines to spaces
                        safe_filename = safe_filename.replace('\r', ' ') # Carriage returns to spaces
                        safe_filename = re.sub(r'\s+', ' ', safe_filename)  # Multiple spaces to single
                        safe_filename = safe_filename.strip()  # Remove leading/trailing spaces
                        
                        # Ensure filename is not empty
                        if not safe_filename:
                            safe_filename = f"document_{timestamp}"
                        
                        unique_filename = f"scraped_{timestamp}_{safe_filename}.{doc_info.get('file_type', 'pdf')}"
                        
                        # Create temp file for processing
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{doc_info.get('file_type', 'pdf')}") as tmp_file:
                            tmp_file.write(response.content)
                            tmp_path = tmp_file.name
                        
                        # Extract text using the same method as normal uploads
                        from backend.utils.text_extractor import extract_text_enhanced
                        extraction_result = extract_text_enhanced(tmp_path, doc_info.get('file_type', 'pdf'), use_ocr=False)
                        extracted_text = extraction_result['text']
                        is_scanned = extraction_result['is_scanned']
                        
                        # Upload to Supabase for permanent storage (same as normal uploads)
                        from backend.utils.supabase_storage import upload_to_supabase
                        s3_url = upload_to_supabase(tmp_path, unique_filename)
                        
                        # Clean up temp file
                        os.unlink(tmp_path)
                        
                        # Skip if no meaningful text extracted
                        if not extracted_text or len(extracted_text.strip()) < 50:
                            logger.warning(f"No meaningful text extracted from {doc_info['url']}")
                            continue
                            
                    except Exception as e:
                        logger.error(f"Error downloading/extracting {doc_info['url']}: {e}")
                        stats["errors"].append(f"Download error for {doc_info['url']}: {str(e)}")
                        continue
                    
                    # Create document record (following normal workflow)
                    document = Document(
                        filename=unique_filename,  # Use unique filename for storage
                        file_type=doc_info.get('file_type', 'pdf'),
                        file_path=None,  # No local path for scraped docs
                        s3_url=s3_url,  # Store in Supabase like normal uploads
                        extracted_text=extracted_text,
                        source_url=doc_info['url'],  # Use source_url field (correct field name)
                        visibility_level="public",
                        approval_status="approved",  # Auto-approve scraped docs
                        uploaded_at=datetime.utcnow(),
                        uploader_id=None,  # System upload
                        content_hash=hashlib.sha256(extracted_text.encode('utf-8')).hexdigest(),
                        is_scanned=is_scanned,
                        ocr_status='processing' if is_scanned else None,
                        download_allowed=True,  # Always allow downloads for scraped documents
                        version="1.0"
                    )
                    
                    db.add(document)
                    db.flush()  # Get document ID
                    
                    # ✅ NEW: Enhanced metadata extraction with quality check and fallback
                    metadata_extraction_success = False
                    used_fallback = False
                    
                    try:
                        logger.info(f"Running enhanced metadata extraction for document: {document.id}")
                        
                        # Extract metadata using MetadataExtractor (with Grok/Gemini fallback)
                        metadata_dict = metadata_extractor.extract_metadata(extracted_text, unique_filename)
                        
                        # Validate metadata quality
                        is_valid, reason = metadata_extractor.validate_metadata_quality(metadata_dict)
                        
                        if not is_valid:
                            logger.warning(f"Metadata quality check failed: {reason}")
                            
                            # Check if we should delete documents without metadata
                            delete_without_metadata = os.getenv("DELETE_DOCS_WITHOUT_METADATA", "true").lower() == "true"
                            
                            if delete_without_metadata:
                                logger.warning(f"Deleting document {document.id} due to failed metadata extraction")
                                
                                # Delete from Supabase storage
                                try:
                                    from backend.utils.supabase_storage import delete_from_supabase
                                    delete_from_supabase(unique_filename)
                                except Exception as e:
                                    logger.error(f"Error deleting from Supabase: {e}")
                                
                                # Delete from database
                                db.delete(document)
                                db.commit()
                                
                                stats["documents_failed_metadata"] += 1
                                continue  # Skip to next document
                            else:
                                logger.info("DELETE_DOCS_WITHOUT_METADATA=false, keeping document with poor metadata")
                        else:
                            metadata_extraction_success = True
                            logger.info(f"Metadata extraction successful: {metadata_dict.get('title', 'No title')}")
                        
                        # Create metadata record
                        doc_metadata = DocumentMetadata(
                            document_id=document.id,
                            title=metadata_dict.get('title', doc_info['title'])[:500] if metadata_dict.get('title') else doc_info['title'][:500],
                            department=metadata_dict.get('department', 'General'),
                            document_type=metadata_dict.get('document_type', 'Uncategorized'),
                            summary=metadata_dict.get('summary'),
                            keywords=metadata_dict.get('keywords', []),
                            key_topics=metadata_dict.get('key_topics', []),
                            entities=metadata_dict.get('entities'),
                            bm25_keywords=metadata_dict.get('bm25_keywords'),
                            text_length=len(extracted_text),
                            metadata_status='ready',
                            embedding_status='uploaded'
                        )
                        
                        db.add(doc_metadata)
                        db.commit()
                        
                        logger.info(f"Metadata saved for document {document.id}")
                        
                    except Exception as e:
                        logger.error(f"Error in metadata extraction for {document.id}: {e}")
                        
                        # Check if we should delete documents without metadata
                        delete_without_metadata = os.getenv("DELETE_DOCS_WITHOUT_METADATA", "true").lower() == "true"
                        
                        if delete_without_metadata:
                            logger.warning(f"Deleting document {document.id} due to metadata extraction error")
                            
                            # Delete from Supabase storage
                            try:
                                from backend.utils.supabase_storage import delete_from_supabase
                                delete_from_supabase(unique_filename)
                            except Exception as e:
                                logger.error(f"Error deleting from Supabase: {e}")
                            
                            # Delete from database
                            db.delete(document)
                            db.commit()
                            
                            stats["documents_failed_metadata"] += 1
                            continue  # Skip to next document
                        else:
                            # Create basic metadata as fallback
                            doc_metadata = DocumentMetadata(
                                document_id=document.id,
                                title=doc_info['title'][:500],
                                text_length=len(extracted_text),
                                metadata_status='ready',
                                embedding_status='uploaded'
                            )
                            db.add(doc_metadata)
                            db.commit()
                    
                    stats["documents_new"] += 1
                    processed_count += 1
                    
                    logger.info(f"Successfully processed document {document.id}: {doc_info['title']}")
                    
                    # ✅ FIXED: Faster rate limiting for large scrapes
                    time.sleep(0.2)  # Was missing, now added for rate limiting
                    
                except Exception as e:
                    logger.error(f"Error processing document {doc_info.get('url', 'unknown')}: {str(e)}")
                    stats["errors"].append(f"Document processing error: {str(e)}")
            
            stats["documents_processed"] = processed_count
            
            # Update source statistics
            source.total_documents_scraped += stats["documents_new"]
            source.last_scraped_at = datetime.utcnow()
            source.last_scrape_status = "success" if not stats["errors"] else "partial"
            
            db.commit()
            
            execution_time = time.time() - start_time
            
            logger.info(f"Enhanced scraping completed in {execution_time:.2f}s")
            logger.info(f"Stats: {stats}")
            
            return {
                "status": "success",
                "execution_time": execution_time,
                "source_name": source.name,
                "scraper_used": scraper.__class__.__name__,
                **stats
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced scraping: {str(e)}")
            stats["errors"].append(str(e))
            raise
        
    except Exception as e:
        db.rollback()
        logger.error(f"Enhanced scraping failed: {str(e)}")
        
        # Update source with error
        try:
            source = db.query(WebScrapingSource).filter(
                WebScrapingSource.id == source_id
            ).first()
            if source:
                source.last_scrape_status = "failed"
                db.commit()
        except:
            pass
        
        return {
            "status": "error",
            "error": str(e),
            "execution_time": time.time() - start_time,
            **stats
        }
    finally:
        db.close()