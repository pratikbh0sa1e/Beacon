"""
Manager for web scraping sources and orchestration
"""
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from .scraper import WebScraper
from .pdf_downloader import PDFDownloader
from .provenance_tracker import ProvenanceTracker

logger = logging.getLogger(__name__)


class WebSourceManager:
    """Manage web scraping sources and orchestrate scraping operations"""
    
    def __init__(self):
        """Initialize web source manager"""
        self.scraper = WebScraper()
        self.downloader = PDFDownloader()
        self.provenance = ProvenanceTracker()
    
    def scrape_source(self,
                     url: str,
                     source_name: str,
                     keywords: Optional[List[str]] = None,
                     max_documents: Optional[int] = None) -> Dict[str, Any]:
        """
        Scrape a single web source with optional keyword filtering
        
        Args:
            url: Source URL to scrape
            source_name: Name of the source
            keywords: Keywords to filter documents
            max_documents: Maximum documents to scrape
        
        Returns:
            Scraping result with documents found and filtering statistics
        """
        logger.info(f"Starting scrape of {source_name}: {url}")
        if keywords:
            logger.info(f"Using keyword filter: {keywords}")
        start_time = datetime.utcnow()
        
        try:
            # Find document links on the page (with filtering if keywords provided)
            documents = self.scraper.find_document_links(url, keywords=keywords)
            
            # Track total discovered before max_documents limit
            total_discovered = len(documents)
            
            if max_documents:
                documents = documents[:max_documents]
            
            # Create provenance records for each document
            for doc in documents:
                # Include matched_keywords in provenance metadata
                additional_metadata = {
                    'matched_keywords': doc.get('matched_keywords', [])
                }
                
                provenance_record = self.provenance.create_provenance_record(
                    url=doc['url'],
                    document_title=doc['text'],
                    source_page=url,
                    scraped_at=doc['found_at'],
                    additional_metadata=additional_metadata
                )
                doc['provenance'] = provenance_record
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Calculate filtering statistics
            documents_matched = len(documents)
            filter_match_rate = (documents_matched / total_discovered * 100) if total_discovered > 0 else 0.0
            
            if keywords:
                logger.info(f"Scrape complete: Found {documents_matched} matching documents in {duration}s (filter match rate: {filter_match_rate:.1f}%)")
            else:
                logger.info(f"Scrape complete: Found {documents_matched} documents in {duration}s (no filtering)")
            
            return {
                "status": "success",
                "source_name": source_name,
                "source_url": url,
                "documents_found": documents_matched,  # For backward compatibility
                "documents_discovered": total_discovered,  # NEW: Total before filtering
                "documents_matched": documents_matched,    # NEW: Documents that passed filter
                "documents_skipped": 0,  # NEW: Filtered out (calculated in scraper)
                "filter_match_rate": round(filter_match_rate, 2),  # NEW: Match percentage
                "keywords_used": keywords if keywords else [],  # NEW: Keywords applied
                "documents": documents,
                "scraped_at": start_time.isoformat(),
                "duration_seconds": duration
            }
        
        except Exception as e:
            logger.error(f"Error scraping {source_name}: {str(e)}")
            return {
                "status": "error",
                "source_name": source_name,
                "source_url": url,
                "error": str(e),
                "scraped_at": start_time.isoformat()
            }
    
    def scrape_and_download(self,
                           url: str,
                           source_name: str,
                           keywords: Optional[List[str]] = None,
                           max_documents: Optional[int] = None) -> Dict[str, Any]:
        """
        Scrape source and download all matching documents
        
        Args:
            url: Source URL
            source_name: Name of source
            keywords: Keywords to filter
            max_documents: Max documents to download
        
        Returns:
            Result with downloaded documents and filtering statistics
        """
        # First scrape to find documents (with filtering if keywords provided)
        scrape_result = self.scrape_source(url, source_name, keywords, max_documents)
        
        if scrape_result['status'] != 'success':
            return scrape_result
        
        documents = scrape_result['documents']
        
        # Download each document
        downloaded = []
        failed = []
        
        for doc in documents:
            download_result = self.downloader.download_document(doc['url'])
            
            if download_result['status'] == 'success':
                # Merge download info with document info
                doc['download'] = download_result
                downloaded.append(doc)
            else:
                doc['download_error'] = download_result.get('error')
                failed.append(doc)
        
        return {
            "status": "success",
            "source_name": source_name,
            "source_url": url,
            "documents_found": len(documents),
            "documents_discovered": scrape_result.get('documents_discovered', len(documents)),  # NEW
            "documents_matched": scrape_result.get('documents_matched', len(documents)),  # NEW
            "filter_match_rate": scrape_result.get('filter_match_rate', 100.0),  # NEW
            "keywords_used": scrape_result.get('keywords_used', []),  # NEW
            "documents_downloaded": len(downloaded),
            "documents_failed": len(failed),
            "downloaded_documents": downloaded,
            "failed_documents": failed,
            "scraped_at": scrape_result['scraped_at']
        }
    
    def scrape_multiple_sources(self,
                                sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Scrape multiple sources
        
        Args:
            sources: List of source configs with 'url', 'name', 'keywords'
        
        Returns:
            Combined results from all sources
        """
        results = {
            "total_sources": len(sources),
            "successful": 0,
            "failed": 0,
            "total_documents": 0,
            "sources": []
        }
        
        for source in sources:
            result = self.scrape_source(
                url=source['url'],
                source_name=source['name'],
                keywords=source.get('keywords'),
                max_documents=source.get('max_documents')
            )
            
            results['sources'].append(result)
            
            if result['status'] == 'success':
                results['successful'] += 1
                results['total_documents'] += result['documents_found']
            else:
                results['failed'] += 1
        
        return results
    
    def get_source_preview(self, url: str) -> Dict[str, Any]:
        """
        Preview what documents would be scraped from a source
        
        Args:
            url: Source URL
        
        Returns:
            Preview of documents available
        """
        try:
            # Get page metadata
            metadata = self.scraper.get_page_metadata(url)
            
            # Find documents (limit to 10 for preview)
            documents = self.scraper.find_document_links(url)[:10]
            
            # Get source credibility
            domain = self.provenance._extract_domain(url)
            source_info = self.provenance.get_source_summary(domain)
            
            return {
                "status": "success",
                "url": url,
                "page_title": metadata.get('title'),
                "page_description": metadata.get('description'),
                "source_info": source_info,
                "sample_documents": len(documents),
                "documents": documents
            }
        
        except Exception as e:
            logger.error(f"Error previewing source {url}: {str(e)}")
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
    
    def validate_source(self, url: str) -> Dict[str, Any]:
        """
        Validate if a URL is a valid scraping source
        
        Args:
            url: URL to validate
        
        Returns:
            Validation result
        """
        try:
            # Try to scrape the page
            page_result = self.scraper.scrape_page(url)
            
            if page_result['status'] != 'success':
                return {
                    "valid": False,
                    "error": page_result.get('error'),
                    "message": "Failed to access URL"
                }
            
            # Check if any documents are found
            documents = self.scraper.find_document_links(url)
            
            # Get credibility
            domain = self.provenance._extract_domain(url)
            credibility = self.provenance._calculate_credibility(domain)
            
            return {
                "valid": True,
                "accessible": True,
                "documents_found": len(documents),
                "credibility_score": credibility,
                "message": f"Valid source with {len(documents)} documents found"
            }
        
        except Exception as e:
            logger.error(f"Error validating source {url}: {str(e)}")
            return {
                "valid": False,
                "error": str(e),
                "message": "Validation failed"
            }
