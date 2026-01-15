"""
Base scraper class for government websites
All site-specific scrapers inherit from this
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import logging
from urllib.parse import urljoin, urlparse
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base scraper with common functionality"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Site-specific configuration (override in subclasses)
        self.site_name = "Generic Government Site"
        self.document_extensions = ['.pdf', '.docx', '.doc', '.pptx', '.xlsx']
        self.rate_limit_delay = 1.0  # seconds between requests
        
    def get_document_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Extract document links from page (OVERRIDE IN SUBCLASSES)
        
        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for resolving relative links
            
        Returns:
            List of document dictionaries
        """
        # Generic implementation - subclasses should override with site-specific selectors
        documents = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Check if it's a document
            if self._is_document_url(full_url):
                documents.append({
                    'url': full_url,
                    'title': link.get_text(strip=True) or href.split('/')[-1],
                    'file_type': self._get_file_extension(full_url),
                    'found_at': datetime.utcnow().isoformat(),
                    'source_page': base_url,
                    'scraper_used': self.__class__.__name__
                })
        
        return documents
    
    def get_pagination_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract pagination links (OVERRIDE IN SUBCLASSES for site-specific pagination)
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of pagination URLs
        """
        # Generic pagination detection
        pagination_links = []
        
        # Common pagination patterns
        for selector in ['.pagination a', '.pager a', 'a[rel="next"]', 'a:contains("Next")']:
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
        
        return pagination_links
    
    def scrape_page(self, url: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Scrape a single page with error handling
        
        Args:
            url: URL to scrape
            timeout: Request timeout
            
        Returns:
            Scraping result
        """
        try:
            logger.info(f"[{self.site_name}] Scraping: {url}")
            
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            return {
                'status': 'success',
                'url': url,
                'soup': soup,
                'title': soup.title.string if soup.title else 'No title',
                'scraped_at': datetime.utcnow().isoformat(),
                'scraper': self.__class__.__name__
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"[{self.site_name}] Timeout scraping {url}")
            return {
                'status': 'error',
                'url': url,
                'error': 'Request timeout',
                'error_type': 'timeout'
            }
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"[{self.site_name}] HTTP error scraping {url}: {e}")
            return {
                'status': 'error',
                'url': url,
                'error': f'HTTP {e.response.status_code}',
                'error_type': 'http_error',
                'status_code': e.response.status_code
            }
            
        except Exception as e:
            logger.error(f"[{self.site_name}] Error scraping {url}: {str(e)}")
            return {
                'status': 'error',
                'url': url,
                'error': str(e),
                'error_type': 'general_error'
            }
    
    def scrape_with_sliding_window(self, base_url: str, window_size: int = 3, max_pages: int = 50) -> List[Dict[str, Any]]:
        """
        Scrape with sliding window re-scanning
        
        Args:
            base_url: Base URL to start scraping
            window_size: Number of recent pages to always re-scan
            max_pages: Maximum pages to scrape
            
        Returns:
            List of all documents found
        """
        logger.info(f"[{self.site_name}] Starting sliding window scrape (window_size={window_size})")
        
        all_documents = []
        pages_scraped = 0
        current_url = base_url
        
        # Track pages for sliding window
        recent_pages = []
        
        while current_url and pages_scraped < max_pages:
            # Scrape current page
            page_result = self.scrape_page(current_url)
            
            if page_result['status'] != 'success':
                logger.error(f"Failed to scrape page {current_url}: {page_result.get('error')}")
                break
            
            soup = page_result['soup']
            pages_scraped += 1
            
            # Extract documents from this page
            documents = self.get_document_links(soup, current_url)
            all_documents.extend(documents)
            
            logger.info(f"[{self.site_name}] Page {pages_scraped}: Found {len(documents)} documents")
            
            # Add to recent pages for sliding window
            recent_pages.append(current_url)
            if len(recent_pages) > window_size:
                recent_pages.pop(0)
            
            # Get next page
            pagination_links = self.get_pagination_links(soup, current_url)
            current_url = None
            
            for link in pagination_links:
                if link not in recent_pages:  # Avoid infinite loops
                    current_url = link
                    break
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
        
        # Re-scan sliding window pages for updates
        if len(recent_pages) > 1:
            logger.info(f"[{self.site_name}] Re-scanning {len(recent_pages)} recent pages for updates")
            
            for page_url in recent_pages:
                page_result = self.scrape_page(page_url)
                if page_result['status'] == 'success':
                    soup = page_result['soup']
                    documents = self.get_document_links(soup, page_url)
                    
                    # Add new documents (avoid duplicates by URL)
                    existing_urls = {doc['url'] for doc in all_documents}
                    new_documents = [doc for doc in documents if doc['url'] not in existing_urls]
                    all_documents.extend(new_documents)
                    
                    if new_documents:
                        logger.info(f"[{self.site_name}] Found {len(new_documents)} new documents in sliding window re-scan")
                
                time.sleep(self.rate_limit_delay)
        
        logger.info(f"[{self.site_name}] Sliding window scrape complete: {len(all_documents)} total documents")
        return all_documents
    
    def _is_document_url(self, url: str) -> bool:
        """Check if URL points to a document"""
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in self.document_extensions)
    
    def _get_file_extension(self, url: str) -> str:
        """Extract file extension from URL"""
        url_lower = url.lower()
        
        for ext in self.document_extensions:
            if url_lower.endswith(ext):
                return ext[1:]  # Remove the dot
        
        return 'unknown'
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common artifacts
        text = text.replace('\n', ' ').replace('\t', ' ')
        
        return text.strip()
    
    def validate_document(self, doc_info: Dict[str, Any]) -> bool:
        """
        Validate document information
        
        Args:
            doc_info: Document dictionary
            
        Returns:
            True if document is valid
        """
        # Check required fields
        if not doc_info.get('url'):
            return False
        
        # Check title length
        title = doc_info.get('title', '').strip()
        if not title or len(title) < 3:
            return False
        
        # Check if URL is accessible (basic validation)
        try:
            parsed = urlparse(doc_info['url'])
            if not parsed.scheme or not parsed.netloc:
                return False
        except:
            return False
        
        return True
    
    def get_site_info(self) -> Dict[str, Any]:
        """Get information about this scraper"""
        return {
            'site_name': self.site_name,
            'scraper_class': self.__class__.__name__,
            'supported_extensions': self.document_extensions,
            'rate_limit_delay': self.rate_limit_delay
        }