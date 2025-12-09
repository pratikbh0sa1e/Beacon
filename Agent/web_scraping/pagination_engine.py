"""
Pagination Engine for automatically detecting and following pagination links
"""
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import re
import time

from .config import ScrapingConfig

logger = logging.getLogger(__name__)


class PaginationEngine:
    """Automatically detect and follow pagination links"""
    
    def __init__(self, scraper):
        """
        Initialize pagination engine
        
        Args:
            scraper: WebScraper instance to use for fetching pages
        """
        self.scraper = scraper
    
    def detect_pagination(self, soup: BeautifulSoup, base_url: str) -> Optional[Dict[str, Any]]:
        """
        Detect pagination pattern on a page
        
        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL of the page
        
        Returns:
            Dict with pagination info or None if no pagination detected
            {
                'pattern': 'query_param' | 'path_segment' | 'next_button',
                'param_name': str (for query_param pattern),
                'next_url': str (if next page found),
                'total_pages': int (if detectable)
            }
        """
        # Try to detect different pagination patterns
        
        # Pattern 1: Query parameter pagination (?page=2, ?p=2, etc.)
        query_pattern = self._detect_query_param_pagination(soup, base_url)
        if query_pattern:
            logger.info(f"Detected query parameter pagination: {query_pattern}")
            return query_pattern
        
        # Pattern 2: Path segment pagination (/page/2/, /2/, etc.)
        path_pattern = self._detect_path_pagination(soup, base_url)
        if path_pattern:
            logger.info(f"Detected path segment pagination: {path_pattern}")
            return path_pattern
        
        # Pattern 3: Next button/link
        next_button = self._detect_next_button(soup, base_url)
        if next_button:
            logger.info(f"Detected next button pagination: {next_button}")
            return next_button
        
        logger.debug(f"No pagination detected on {base_url}")
        return None
    
    def _detect_query_param_pagination(self, soup: BeautifulSoup, base_url: str) -> Optional[Dict[str, Any]]:
        """Detect query parameter based pagination (?page=2)"""
        # Common pagination parameter names
        param_names = ['page', 'p', 'pg', 'pagenum', 'pagenumber']
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            parsed = urlparse(absolute_url)
            query_params = parse_qs(parsed.query)
            
            # Check if any pagination parameter exists
            for param_name in param_names:
                if param_name in query_params:
                    try:
                        page_num = int(query_params[param_name][0])
                        if page_num > 1:  # Found a page number > 1
                            # Try to find total pages
                            total_pages = self._extract_total_pages(soup)
                            
                            return {
                                'pattern': 'query_param',
                                'param_name': param_name,
                                'next_url': absolute_url if page_num == 2 else None,
                                'total_pages': total_pages,
                                'base_url': base_url
                            }
                    except (ValueError, IndexError):
                        continue
        
        return None
    
    def _detect_path_pagination(self, soup: BeautifulSoup, base_url: str) -> Optional[Dict[str, Any]]:
        """Detect path segment based pagination (/page/2/)"""
        # Common path patterns
        path_patterns = [
            r'/page/(\d+)/?$',
            r'/p/(\d+)/?$',
            r'/(\d+)/?$'
        ]
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            parsed = urlparse(absolute_url)
            
            for pattern in path_patterns:
                match = re.search(pattern, parsed.path)
                if match:
                    page_num = int(match.group(1))
                    if page_num > 1:
                        total_pages = self._extract_total_pages(soup)
                        
                        return {
                            'pattern': 'path_segment',
                            'path_pattern': pattern,
                            'next_url': absolute_url if page_num == 2 else None,
                            'total_pages': total_pages,
                            'base_url': base_url
                        }
        
        return None
    
    def _detect_next_button(self, soup: BeautifulSoup, base_url: str) -> Optional[Dict[str, Any]]:
        """Detect next button/link"""
        # Common next button text/attributes
        next_indicators = [
            'next', 'next page', 'next »', '»', '›', '→',
            'अगला', 'आगे'  # Hindi
        ]
        
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True).lower()
            link_class = ' '.join(link.get('class', [])).lower()
            link_id = link.get('id', '').lower()
            link_title = link.get('title', '').lower()
            
            # Check if link indicates "next"
            for indicator in next_indicators:
                if (indicator in link_text or 
                    indicator in link_class or 
                    indicator in link_id or
                    indicator in link_title):
                    
                    next_url = urljoin(base_url, link['href'])
                    total_pages = self._extract_total_pages(soup)
                    
                    return {
                        'pattern': 'next_button',
                        'next_url': next_url,
                        'total_pages': total_pages,
                        'base_url': base_url
                    }
        
        return None
    
    def _extract_total_pages(self, soup: BeautifulSoup) -> Optional[int]:
        """Try to extract total page count from pagination"""
        # Look for pagination elements
        pagination_selectors = [
            '.pagination', '#pagination', 
            '.pager', '.page-numbers',
            '[class*="pagination"]', '[class*="pager"]'
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
                    return max(page_numbers)
        
        return None
    
    def build_page_url(self, base_url: str, page_num: int, pattern_info: Dict[str, Any]) -> str:
        """
        Build URL for a specific page number
        
        Args:
            base_url: Base URL
            page_num: Page number to build URL for
            pattern_info: Pagination pattern info from detect_pagination
        
        Returns:
            URL for the specified page
        """
        pattern = pattern_info['pattern']
        
        if pattern == 'query_param':
            param_name = pattern_info['param_name']
            parsed = urlparse(base_url)
            query_params = parse_qs(parsed.query)
            query_params[param_name] = [str(page_num)]
            
            # Rebuild URL with new query params
            new_query = urlencode(query_params, doseq=True)
            new_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
            return new_url
        
        elif pattern == 'path_segment':
            path_pattern = pattern_info.get('path_pattern', r'/page/(\d+)/?$')
            parsed = urlparse(base_url)
            
            # Replace page number in path
            if '/page/' in path_pattern:
                new_path = re.sub(r'/page/\d+/?$', f'/page/{page_num}/', parsed.path)
            elif '/p/' in path_pattern:
                new_path = re.sub(r'/p/\d+/?$', f'/p/{page_num}/', parsed.path)
            else:
                new_path = re.sub(r'/\d+/?$', f'/{page_num}/', parsed.path)
            
            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                new_path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
        
        elif pattern == 'next_button':
            # For next button, we need to follow the next_url
            return pattern_info.get('next_url', base_url)
        
        return base_url
    
    def scrape_all_pages(self, 
                        base_url: str,
                        keywords: Optional[List[str]] = None,
                        max_pages: int = 10,
                        delay: float = 1.0,
                        max_documents: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Scrape all pages following pagination
        
        Args:
            base_url: Starting URL
            keywords: Keywords to filter documents
            max_pages: Maximum number of pages to scrape
            delay: Delay between page requests (seconds)
            max_documents: Maximum documents to collect (defaults to ScrapingConfig.MAX_DOCUMENTS_PER_SOURCE)
        
        Returns:
            List of all documents found across all pages (up to max_documents limit)
        """
        all_documents = []
        current_url = base_url
        pages_scraped = 0
        
        # Use config default if not specified
        if max_documents is None:
            max_documents = ScrapingConfig.get_max_documents()
        
        logger.info(f"Starting pagination scraping from {base_url} (max {max_pages} pages, max {max_documents} documents)")
        
        while pages_scraped < max_pages and len(all_documents) < max_documents:
            pages_scraped += 1
            logger.info(f"Scraping page {pages_scraped}: {current_url}")
            
            # Scrape current page
            try:
                response = self.scraper.session.get(current_url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                logger.error(f"Error fetching page {pages_scraped}: {str(e)}")
                break
            
            # Find documents on current page
            documents = self.scraper.find_document_links(current_url, keywords=keywords)
            
            # Early termination if no documents found
            if not documents:
                logger.info(f"No documents found on page {pages_scraped}, terminating pagination early")
                break
            
            # Add documents but respect the limit
            remaining_capacity = max_documents - len(all_documents)
            documents_to_add = documents[:remaining_capacity]
            all_documents.extend(documents_to_add)
            
            logger.info(f"Found {len(documents)} documents on page {pages_scraped}, added {len(documents_to_add)} (total: {len(all_documents)}/{max_documents})")
            
            # Check if we've reached the document limit
            if len(all_documents) >= max_documents:
                logger.info(f"Reached maximum document limit ({max_documents}), stopping pagination")
                break
            
            # Detect pagination for next page
            pagination_info = self.detect_pagination(soup, current_url)
            
            if not pagination_info:
                logger.info(f"No more pagination detected after page {pages_scraped}")
                break
            
            # Get next page URL
            if pagination_info['pattern'] == 'next_button':
                next_url = pagination_info.get('next_url')
                if not next_url or next_url == current_url:
                    logger.info(f"No next page available after page {pages_scraped}")
                    break
                current_url = next_url
            else:
                # Build URL for next page
                next_page_num = pages_scraped + 1
                current_url = self.build_page_url(base_url, next_page_num, pagination_info)
            
            # Check if we've reached the last page
            if pagination_info.get('total_pages'):
                if pages_scraped >= pagination_info['total_pages']:
                    logger.info(f"Reached last page ({pagination_info['total_pages']})")
                    break
            
            # Be polite - wait between requests
            if pages_scraped < max_pages:
                time.sleep(delay)
        
        logger.info(f"Pagination complete: scraped {pages_scraped} pages, found {len(all_documents)} documents")
        
        return all_documents
    
    def extract_total_pages(self, soup: BeautifulSoup) -> Optional[int]:
        """
        Public method to extract total page count
        
        Args:
            soup: BeautifulSoup object of the page
        
        Returns:
            Total number of pages or None if not detectable
        """
        return self._extract_total_pages(soup)
