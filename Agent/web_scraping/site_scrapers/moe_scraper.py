"""
Ministry of Education (MoE) specific scraper
Hardcoded selectors and logic for MoE websites
"""
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class MoEScraper(BaseScraper):
    """Scraper specifically designed for Ministry of Education websites"""
    
    def __init__(self):
        super().__init__()
        self.site_name = "Ministry of Education"
        self.rate_limit_delay = 1.5  # Be more respectful to government sites
        
        # MoE-specific document extensions (they often have additional formats)
        self.document_extensions = ['.pdf', '.docx', '.doc', '.pptx', '.xlsx', '.xls']
        
        # MoE-specific CSS selectors (hardcoded for reliability)
        self.document_selectors = [
            # Common MoE document link patterns
            'a[href$=".pdf"]',
            'a[href$=".docx"]', 
            'a[href$=".doc"]',
            '.document-list a',
            '.file-list a',
            '.download-links a',
            '.policy-documents a',
            '.circular-list a',
            '.notification-list a',
            # MoE specific content areas
            '.content-area a[href*=".pdf"]',
            '.main-content a[href*=".pdf"]',
            '#content a[href*=".pdf"]',
            # Table-based document listings (common in govt sites)
            'table a[href$=".pdf"]',
            'tbody a[href$=".pdf"]',
        ]
        
        # MoE-specific pagination selectors
        self.pagination_selectors = [
            '.pagination a',
            '.pager a', 
            'a[rel="next"]',
            'a:contains("Next")',
            'a:contains(">")',
            '.page-numbers a',
            # MoE specific pagination patterns
            '.page-nav a',
            '.document-pagination a',
            'a[href*="page="]',
            'a[href*="pageNo="]',
        ]
        
        # Keywords that indicate important MoE documents
        self.priority_keywords = [
            'policy', 'circular', 'notification', 'guidelines', 'scheme',
            'nep', 'national education policy', 'samagra shiksha', 
            'pm shri', 'digital india', 'skill development',
            'higher education', 'school education', 'technical education'
        ]
    
    def get_document_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Extract document links using MoE-specific selectors
        
        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for resolving relative links
            
        Returns:
            List of document dictionaries with MoE-specific metadata
        """
        documents = []
        found_urls = set()  # Avoid duplicates
        
        # Try each MoE-specific selector
        for selector in self.document_selectors:
            try:
                links = soup.select(selector)
                logger.debug(f"[MoE] Selector '{selector}' found {len(links)} links")
                
                for link in links:
                    href = link.get('href')
                    if not href:
                        continue
                    
                    full_url = urljoin(base_url, href)
                    
                    # Skip if already found
                    if full_url in found_urls:
                        continue
                    
                    # Validate it's a document
                    if not self._is_document_url(full_url):
                        continue
                    
                    found_urls.add(full_url)
                    
                    # Extract title with MoE-specific logic
                    title = self._extract_moe_title(link, soup)
                    
                    # Get document context (surrounding text for better categorization)
                    context = self._get_document_context(link)
                    
                    # Determine document category
                    category = self._categorize_moe_document(title, context)
                    
                    # Check if it's a priority document
                    is_priority = self._is_priority_document(title, context)
                    
                    doc_info = {
                        'url': full_url,
                        'title': title,
                        'file_type': self._get_file_extension(full_url),
                        'found_at': self._get_current_timestamp(),
                        'source_page': base_url,
                        'scraper_used': 'MoEScraper',
                        'selector_used': selector,
                        'context': context,
                        'category': category,
                        'is_priority': is_priority,
                        'ministry': 'Ministry of Education'
                    }
                    
                    # Validate before adding
                    if self.validate_document(doc_info):
                        documents.append(doc_info)
                        logger.debug(f"[MoE] Found document: {title[:50]}...")
                    
            except Exception as e:
                logger.warning(f"[MoE] Error with selector '{selector}': {str(e)}")
                continue
        
        # Sort by priority (priority documents first)
        documents.sort(key=lambda x: (not x['is_priority'], x['title']))
        
        logger.info(f"[MoE] Extracted {len(documents)} documents from {base_url}")
        return documents
    
    def get_pagination_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract pagination links using MoE-specific selectors
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of pagination URLs
        """
        pagination_links = []
        found_links = set()
        
        for selector in self.pagination_selectors:
            try:
                links = soup.select(selector)
                
                for link in links:
                    href = link.get('href')
                    if not href:
                        continue
                    
                    full_url = urljoin(base_url, href)
                    
                    # Skip if already found or same as current page
                    if full_url in found_links or full_url == base_url:
                        continue
                    
                    # Validate it looks like a pagination link
                    if self._is_pagination_link(link, href):
                        found_links.add(full_url)
                        pagination_links.append(full_url)
                        
            except Exception as e:
                logger.warning(f"[MoE] Error with pagination selector '{selector}': {str(e)}")
                continue
        
        logger.debug(f"[MoE] Found {len(pagination_links)} pagination links")
        return pagination_links[:10]  # Limit to prevent infinite loops
    
    def _extract_moe_title(self, link, soup: BeautifulSoup) -> str:
        """Extract title using MoE-specific logic"""
        # Try link text first
        title = link.get_text(strip=True)
        
        if title and len(title) > 5:
            return self._clean_text(title)
        
        # Try title attribute
        title = link.get('title', '').strip()
        if title and len(title) > 5:
            return self._clean_text(title)
        
        # Try parent element text (common in MoE sites)
        parent = link.parent
        if parent:
            parent_text = parent.get_text(strip=True)
            # Remove the link text to get surrounding context
            link_text = link.get_text(strip=True)
            if link_text in parent_text:
                title = parent_text.replace(link_text, '').strip()
                if title and len(title) > 5:
                    return self._clean_text(title)
        
        # Try adjacent text (sometimes title is in previous/next sibling)
        for sibling in [link.previous_sibling, link.next_sibling]:
            if sibling and hasattr(sibling, 'get_text'):
                sibling_text = sibling.get_text(strip=True)
                if sibling_text and len(sibling_text) > 5:
                    return self._clean_text(sibling_text)
        
        # Fallback to filename
        href = link.get('href', '')
        filename = href.split('/')[-1]
        if filename:
            # Remove extension and clean up
            name_without_ext = filename.rsplit('.', 1)[0]
            return self._clean_text(name_without_ext.replace('_', ' ').replace('-', ' '))
        
        return "Untitled Document"
    
    def _get_document_context(self, link) -> str:
        """Get surrounding context for better categorization"""
        context_parts = []
        
        # Get parent container text
        parent = link.parent
        if parent:
            parent_text = parent.get_text(strip=True)
            if parent_text and len(parent_text) < 500:  # Avoid huge blocks
                context_parts.append(parent_text)
        
        # Get table row context (common in govt document listings)
        tr = link.find_parent('tr')
        if tr:
            tr_text = tr.get_text(strip=True)
            if tr_text and tr_text not in context_parts:
                context_parts.append(tr_text)
        
        # Get list item context
        li = link.find_parent('li')
        if li:
            li_text = li.get_text(strip=True)
            if li_text and li_text not in context_parts:
                context_parts.append(li_text)
        
        return ' | '.join(context_parts[:3])  # Limit context size
    
    def _categorize_moe_document(self, title: str, context: str) -> str:
        """Categorize MoE document based on title and context"""
        text_to_check = f"{title} {context}".lower()
        
        # MoE-specific categories
        if any(word in text_to_check for word in ['policy', 'nep', 'national education']):
            return 'Policy'
        elif any(word in text_to_check for word in ['circular', 'notification', 'order']):
            return 'Circular/Notification'
        elif any(word in text_to_check for word in ['guideline', 'manual', 'handbook']):
            return 'Guidelines'
        elif any(word in text_to_check for word in ['scheme', 'samagra', 'pm shri']):
            return 'Scheme'
        elif any(word in text_to_check for word in ['report', 'annual', 'survey']):
            return 'Report'
        elif any(word in text_to_check for word in ['form', 'application', 'format']):
            return 'Form'
        else:
            return 'General'
    
    def _is_priority_document(self, title: str, context: str) -> bool:
        """Check if document is high priority based on MoE keywords"""
        text_to_check = f"{title} {context}".lower()
        
        return any(keyword in text_to_check for keyword in self.priority_keywords)
    
    def _is_pagination_link(self, link, href: str) -> bool:
        """Check if link is actually pagination"""
        link_text = link.get_text(strip=True).lower()
        
        # Common pagination indicators
        pagination_indicators = [
            'next', 'previous', 'prev', '>', '<', 'page',
            'more', 'continue', '»', '«', '→', '←'
        ]
        
        # Check link text
        if any(indicator in link_text for indicator in pagination_indicators):
            return True
        
        # Check if href contains pagination parameters
        pagination_params = ['page=', 'pageNo=', 'p=', 'offset=', 'start=']
        if any(param in href.lower() for param in pagination_params):
            return True
        
        # Check if it's a number (page number)
        if link_text.isdigit():
            return True
        
        return False
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def get_site_info(self) -> Dict[str, Any]:
        """Get MoE-specific site information"""
        base_info = super().get_site_info()
        base_info.update({
            'document_selectors': len(self.document_selectors),
            'pagination_selectors': len(self.pagination_selectors),
            'priority_keywords': len(self.priority_keywords),
            'specialization': 'Ministry of Education documents with policy categorization'
        })
        return base_info