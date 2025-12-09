"""
Web scraper for government policy documents
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import logging
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime

from .keyword_filter import KeywordFilter
from .retry_utils import retry_with_backoff, RetriableError

logger = logging.getLogger(__name__)


class WebScraper:
    """Scrape government websites for policy documents"""
    
    def __init__(self, user_agent: str = None):
        """
        Initialize web scraper
        
        Args:
            user_agent: Custom user agent string
        """
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def scrape_page(self, url: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Scrape a single page
        
        Args:
            url: URL to scrape
            timeout: Request timeout in seconds
        
        Returns:
            Dict with page content and metadata
        """
        try:
            logger.info(f"Scraping: {url}")
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            return {
                "status": "success",
                "url": url,
                "title": soup.title.string if soup.title else "No title",
                "content": soup.get_text(strip=True),
                "html": str(soup),
                "scraped_at": datetime.utcnow().isoformat(),
                "status_code": response.status_code
            }
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout scraping {url}")
            return {
                "status": "error",
                "url": url,
                "error": "Request timeout",
                "scraped_at": datetime.utcnow().isoformat()
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                "status": "error",
                "url": url,
                "error": str(e),
                "scraped_at": datetime.utcnow().isoformat()
            }
    
    def find_document_links(self, url: str, 
                           extensions: List[str] = None,
                           keywords: List[str] = None) -> List[Dict[str, str]]:
        """
        Find document links on a page with optional keyword filtering
        
        Args:
            url: Page URL to search
            extensions: File extensions to look for (default: pdf, docx, doc)
            keywords: Keywords to filter links (e.g., 'policy', 'circular')
        
        Returns:
            List of document links with metadata (only matching documents if keywords provided)
        """
        if extensions is None:
            extensions = ['.pdf', '.docx', '.doc', '.pptx']
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Initialize keyword filter
            keyword_filter = KeywordFilter(keywords)
            
            documents = []
            total_discovered = 0
            filtered_out = 0
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                
                # Check if link points to a document
                if any(absolute_url.lower().endswith(ext) for ext in extensions):
                    total_discovered += 1
                    link_text = link.get_text(strip=True)
                    
                    # Evaluate document against keyword filter
                    match_result = self._evaluate_document_match(link_text, keyword_filter)
                    
                    if match_result['matches']:
                        # Document matches filter - include it
                        documents.append({
                            "url": absolute_url,
                            "text": link_text,
                            "type": self._get_file_extension(absolute_url),
                            "source_page": url,
                            "found_at": datetime.utcnow().isoformat(),
                            "matched_keywords": match_result['matched_keywords']
                        })
                        logger.debug(f"Document matched: {link_text[:50]}... (keywords: {match_result['matched_keywords']})")
                    else:
                        # Document doesn't match filter - skip it
                        filtered_out += 1
                        logger.debug(f"Document filtered out: {link_text[:50]}...")
            
            # Log filtering statistics
            if keyword_filter.is_active():
                logger.info(f"Found {len(documents)} matching documents out of {total_discovered} discovered on {url} (filtered out: {filtered_out})")
            else:
                logger.info(f"Found {len(documents)} documents on {url} (no filtering)")
            
            return documents
        
        except Exception as e:
            logger.error(f"Error finding documents on {url}: {str(e)}")
            return []
    
    def scrape_documents_section(self, url: str,
                                section_selector: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Scrape documents from a specific section of a page
        
        Args:
            url: Page URL
            section_selector: CSS selector for the documents section
        
        Returns:
            List of document links
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find section if selector provided
            if section_selector:
                section = soup.select_one(section_selector)
                if not section:
                    logger.warning(f"Section '{section_selector}' not found on {url}")
                    return []
                soup = section
            
            documents = []
            
            # Find all document links
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                
                # Check if it's a document
                if self._is_document_url(absolute_url):
                    documents.append({
                        "url": absolute_url,
                        "title": link.get_text(strip=True),
                        "type": self._get_file_extension(absolute_url),
                        "source_page": url,
                        "found_at": datetime.utcnow().isoformat()
                    })
            
            return documents
        
        except Exception as e:
            logger.error(f"Error scraping documents section: {str(e)}")
            return []
    
    def scrape_with_pagination(self, base_url: str,
                              page_param: str = "page",
                              max_pages: int = 10) -> List[Dict[str, str]]:
        """
        Scrape documents from paginated pages
        
        Args:
            base_url: Base URL (e.g., https://example.com/documents)
            page_param: Query parameter for pagination
            max_pages: Maximum pages to scrape
        
        Returns:
            List of all documents found
        """
        all_documents = []
        
        for page_num in range(1, max_pages + 1):
            # Build paginated URL
            if '?' in base_url:
                page_url = f"{base_url}&{page_param}={page_num}"
            else:
                page_url = f"{base_url}?{page_param}={page_num}"
            
            logger.info(f"Scraping page {page_num}: {page_url}")
            
            documents = self.find_document_links(page_url)
            
            if not documents:
                logger.info(f"No documents found on page {page_num}, stopping pagination")
                break
            
            all_documents.extend(documents)
            
            # Be polite - wait between requests
            time.sleep(1)
        
        logger.info(f"Total documents found across {page_num} pages: {len(all_documents)}")
        return all_documents
    
    def _evaluate_document_match(self, link_text: str, keyword_filter: KeywordFilter) -> Dict[str, Any]:
        """
        Evaluate if a document link matches keyword criteria
        
        Args:
            link_text: The text of the document link
            keyword_filter: KeywordFilter instance to use for matching
        
        Returns:
            Dict with 'matches' (bool) and 'matched_keywords' (List[str])
        """
        return keyword_filter.evaluate(link_text)
    
    def _is_document_url(self, url: str) -> bool:
        """Check if URL points to a document"""
        doc_extensions = ['.pdf', '.docx', '.doc', '.pptx', '.xlsx', '.xls']
        return any(url.lower().endswith(ext) for ext in doc_extensions)
    
    def _get_file_extension(self, url: str) -> str:
        """Extract file extension from URL"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if path.endswith('.pdf'):
            return 'pdf'
        elif path.endswith('.docx') or path.endswith('.doc'):
            return 'docx'
        elif path.endswith('.pptx') or path.endswith('.ppt'):
            return 'pptx'
        elif path.endswith('.xlsx') or path.endswith('.xls'):
            return 'xlsx'
        else:
            return 'unknown'
    
    def get_page_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract metadata from a page
        
        Args:
            url: Page URL
        
        Returns:
            Dict with page metadata
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            metadata = {
                "url": url,
                "title": soup.title.string if soup.title else None,
                "description": None,
                "keywords": None,
                "author": None,
                "published_date": None
            }
            
            # Extract meta tags
            for meta in soup.find_all('meta'):
                name = meta.get('name', '').lower()
                property_attr = meta.get('property', '').lower()
                content = meta.get('content')
                
                if name == 'description' or property_attr == 'og:description':
                    metadata['description'] = content
                elif name == 'keywords':
                    metadata['keywords'] = content
                elif name == 'author':
                    metadata['author'] = content
                elif property_attr == 'article:published_time':
                    metadata['published_date'] = content
            
            return metadata
        
        except Exception as e:
            logger.error(f"Error extracting metadata from {url}: {str(e)}")
            return {"url": url, "error": str(e)}
    
    def detect_pagination_links(self, soup: BeautifulSoup) -> List[str]:
        """
        Detect pagination links on current page
        
        Args:
            soup: BeautifulSoup object of the page
        
        Returns:
            List of pagination link URLs
        """
        pagination_links = []
        
        # Common pagination selectors
        pagination_selectors = [
            '.pagination a',
            '.pager a',
            '.page-numbers a',
            '[class*="pagination"] a',
            'a[rel="next"]',
            'a[rel="prev"]'
        ]
        
        for selector in pagination_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    pagination_links.append(href)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in pagination_links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        logger.debug(f"Detected {len(unique_links)} pagination links")
        return unique_links
    
    def extract_total_pages(self, soup: BeautifulSoup) -> Optional[int]:
        """
        Try to extract total page count from pagination
        
        Args:
            soup: BeautifulSoup object of the page
        
        Returns:
            Total number of pages or None if not detectable
        """
        # Look for pagination elements
        pagination_selectors = [
            '.pagination', '#pagination',
            '.pager', '.page-numbers',
            '[class*="pagination"]'
        ]
        
        for selector in pagination_selectors:
            pagination = soup.select_one(selector)
            if pagination:
                # Find all page numbers
                page_numbers = []
                for link in pagination.find_all('a'):
                    text = link.get_text(strip=True)
                    if text.isdigit():
                        page_numbers.append(int(text))
                
                if page_numbers:
                    total = max(page_numbers)
                    logger.debug(f"Extracted total pages: {total}")
                    return total
        
        return None
    
    def scrape_with_retry(self, url: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Scrape with automatic retry and exponential backoff
        
        Args:
            url: URL to scrape
            max_retries: Maximum number of retry attempts
        
        Returns:
            Scraping result
        """
        def _scrape():
            try:
                result = self.scrape_page(url)
                
                # Check if result indicates an error
                if result.get('status') == 'error':
                    raise RetriableError(result.get('error', 'Unknown error'))
                
                return result
            
            except requests.exceptions.RequestException as e:
                raise RetriableError(str(e))
        
        try:
            return retry_with_backoff(_scrape, max_retries=max_retries)
        except Exception as e:
            logger.error(f"Failed to scrape {url} after {max_retries} retries: {str(e)}")
            return {
                "status": "error",
                "url": url,
                "error": f"Failed after {max_retries} retries: {str(e)}",
                "scraped_at": datetime.utcnow().isoformat()
            }
    
    def validate_document_content(self, document: Dict[str, str]) -> bool:
        """
        Validate that document content is not empty
        
        Args:
            document: Document dictionary
        
        Returns:
            True if document has valid content
        """
        # Check if document has required fields
        if not document.get('url'):
            logger.warning("Document missing URL")
            return False
        
        # Check if document has meaningful text
        text = document.get('text', '').strip()
        if not text or len(text) < 3:
            logger.warning(f"Document has empty or minimal content: {document.get('url')}")
            return False
        
        # Check if text is only whitespace
        if text.isspace():
            logger.warning(f"Document contains only whitespace: {document.get('url')}")
            return False
        
        return True
    
    def find_document_links_with_validation(self,
                                           url: str,
                                           extensions: List[str] = None,
                                           keywords: List[str] = None) -> List[Dict[str, str]]:
        """
        Find document links with content validation
        
        Args:
            url: Page URL to search
            extensions: File extensions to look for
            keywords: Keywords to filter links
        
        Returns:
            List of validated document links
        """
        documents = self.find_document_links(url, extensions, keywords)
        
        # Validate documents
        valid_documents = []
        for doc in documents:
            if self.validate_document_content(doc):
                valid_documents.append(doc)
            else:
                logger.debug(f"Filtered out invalid document: {doc.get('url')}")
        
        logger.info(f"Validated {len(valid_documents)}/{len(documents)} documents")
        
        return valid_documents
