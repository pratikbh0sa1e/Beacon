"""
University Grants Commission (UGC) specific scraper
Hardcoded selectors and logic for UGC websites
"""
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class UGCScraper(BaseScraper):
    """Scraper specifically designed for UGC websites"""
    
    def __init__(self):
        super().__init__()
        self.site_name = "University Grants Commission"
        self.rate_limit_delay = 1.5
        
        # UGC-specific document extensions
        self.document_extensions = ['.pdf', '.docx', '.doc', '.pptx', '.xlsx', '.xls']
        
        # UGC-specific CSS selectors
        self.document_selectors = [
            # UGC common patterns
            'a[href$=".pdf"]',
            'a[href$=".docx"]',
            'a[href$=".doc"]',
            '.regulations-list a',
            '.circular-list a',
            '.notification-list a',
            '.guidelines-list a',
            '.document-links a',
            # UGC specific content areas
            '.ugc-content a[href*=".pdf"]',
            '.main-wrapper a[href*=".pdf"]',
            '#main-content a[href*=".pdf"]',
            '.content-wrapper a[href*=".pdf"]',
            # Table-based listings (very common in UGC)
            'table.document-table a',
            'table a[href$=".pdf"]',
            '.data-table a',
            # UGC regulation specific
            '.regulation-documents a',
            '.policy-documents a',
        ]
        
        # UGC-specific pagination selectors
        self.pagination_selectors = [
            '.pagination a',
            '.pager a',
            'a[rel="next"]',
            'a:contains("Next")',
            'a:contains(">")',
            '.page-links a',
            # UGC specific
            '.document-pagination a',
            'a[href*="page="]',
            'a[href*="start="]',
        ]
        
        # UGC priority keywords
        self.priority_keywords = [
            'regulation', 'guidelines', 'circular', 'notification',
            'accreditation', 'naac', 'nirf', 'autonomy', 'graded autonomy',
            'academic reform', 'curriculum', 'examination reform',
            'research', 'phd', 'fellowship', 'scholarship',
            'quality assurance', 'academic bank of credits', 'abc'
        ]
    
    def get_document_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract document links using UGC-specific selectors"""
        documents = []
        found_urls = set()
        
        for selector in self.document_selectors:
            try:
                links = soup.select(selector)
                logger.debug(f"[UGC] Selector '{selector}' found {len(links)} links")
                
                for link in links:
                    href = link.get('href')
                    if not href:
                        continue
                    
                    full_url = urljoin(base_url, href)
                    
                    if full_url in found_urls or not self._is_document_url(full_url):
                        continue
                    
                    found_urls.add(full_url)
                    
                    # Extract UGC-specific metadata
                    title = self._extract_ugc_title(link, soup)
                    context = self._get_document_context(link)
                    category = self._categorize_ugc_document(title, context)
                    is_priority = self._is_priority_document(title, context)
                    
                    doc_info = {
                        'url': full_url,
                        'title': title,
                        'file_type': self._get_file_extension(full_url),
                        'found_at': self._get_current_timestamp(),
                        'source_page': base_url,
                        'scraper_used': 'UGCScraper',
                        'selector_used': selector,
                        'context': context,
                        'category': category,
                        'is_priority': is_priority,
                        'ministry': 'University Grants Commission'
                    }
                    
                    if self.validate_document(doc_info):
                        documents.append(doc_info)
                        logger.debug(f"[UGC] Found document: {title[:50]}...")
                    
            except Exception as e:
                logger.warning(f"[UGC] Error with selector '{selector}': {str(e)}")
                continue
        
        # Sort by priority and date
        documents.sort(key=lambda x: (not x['is_priority'], x['title']))
        
        logger.info(f"[UGC] Extracted {len(documents)} documents from {base_url}")
        return documents
    
    def get_pagination_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract pagination links using UGC-specific selectors"""
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
                    
                    if full_url in found_links or full_url == base_url:
                        continue
                    
                    if self._is_pagination_link(link, href):
                        found_links.add(full_url)
                        pagination_links.append(full_url)
                        
            except Exception as e:
                logger.warning(f"[UGC] Error with pagination selector '{selector}': {str(e)}")
                continue
        
        logger.debug(f"[UGC] Found {len(pagination_links)} pagination links")
        return pagination_links[:10]
    
    def _extract_ugc_title(self, link, soup: BeautifulSoup) -> str:
        """Extract title using UGC-specific logic"""
        # Try link text first
        title = link.get_text(strip=True)
        
        if title and len(title) > 5:
            return self._clean_text(title)
        
        # Try title attribute
        title = link.get('title', '').strip()
        if title and len(title) > 5:
            return self._clean_text(title)
        
        # UGC often has document titles in table cells
        td = link.find_parent('td')
        if td:
            # Look for title in same row, different column
            tr = td.find_parent('tr')
            if tr:
                cells = tr.find_all('td')
                for cell in cells:
                    if cell != td:  # Different cell
                        cell_text = cell.get_text(strip=True)
                        if cell_text and len(cell_text) > 5 and 'download' not in cell_text.lower():
                            return self._clean_text(cell_text)
        
        # Try parent element
        parent = link.parent
        if parent:
            parent_text = parent.get_text(strip=True)
            link_text = link.get_text(strip=True)
            if link_text in parent_text:
                title = parent_text.replace(link_text, '').strip()
                if title and len(title) > 5:
                    return self._clean_text(title)
        
        # Fallback to filename
        href = link.get('href', '')
        filename = href.split('/')[-1]
        if filename:
            name_without_ext = filename.rsplit('.', 1)[0]
            return self._clean_text(name_without_ext.replace('_', ' ').replace('-', ' '))
        
        return "UGC Document"
    
    def _get_document_context(self, link) -> str:
        """Get surrounding context for UGC documents"""
        context_parts = []
        
        # Table row context (very common in UGC)
        tr = link.find_parent('tr')
        if tr:
            tr_text = tr.get_text(strip=True)
            if tr_text and len(tr_text) < 500:
                context_parts.append(tr_text)
        
        # Parent container
        parent = link.parent
        if parent and parent.name != 'tr':  # Avoid duplicate with tr
            parent_text = parent.get_text(strip=True)
            if parent_text and len(parent_text) < 300:
                context_parts.append(parent_text)
        
        # List item context
        li = link.find_parent('li')
        if li:
            li_text = li.get_text(strip=True)
            if li_text and li_text not in context_parts:
                context_parts.append(li_text)
        
        return ' | '.join(context_parts[:3])
    
    def _categorize_ugc_document(self, title: str, context: str) -> str:
        """Categorize UGC document based on title and context"""
        text_to_check = f"{title} {context}".lower()
        
        if any(word in text_to_check for word in ['regulation', 'regulations']):
            return 'Regulation'
        elif any(word in text_to_check for word in ['guideline', 'guidelines']):
            return 'Guidelines'
        elif any(word in text_to_check for word in ['circular', 'notification']):
            return 'Circular/Notification'
        elif any(word in text_to_check for word in ['accreditation', 'naac', 'quality']):
            return 'Accreditation'
        elif any(word in text_to_check for word in ['research', 'phd', 'fellowship']):
            return 'Research'
        elif any(word in text_to_check for word in ['curriculum', 'academic', 'examination']):
            return 'Academic'
        elif any(word in text_to_check for word in ['scholarship', 'fellowship', 'grant']):
            return 'Scholarship/Grant'
        else:
            return 'General'
    
    def _is_priority_document(self, title: str, context: str) -> bool:
        """Check if document is high priority for UGC"""
        text_to_check = f"{title} {context}".lower()
        return any(keyword in text_to_check for keyword in self.priority_keywords)
    
    def _is_pagination_link(self, link, href: str) -> bool:
        """Check if link is pagination for UGC sites"""
        link_text = link.get_text(strip=True).lower()
        
        pagination_indicators = [
            'next', 'previous', 'prev', '>', '<', 'page',
            'more', 'continue', '»', '«', '→', '←'
        ]
        
        if any(indicator in link_text for indicator in pagination_indicators):
            return True
        
        pagination_params = ['page=', 'start=', 'p=', 'offset=']
        if any(param in href.lower() for param in pagination_params):
            return True
        
        if link_text.isdigit():
            return True
        
        return False
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def get_site_info(self) -> Dict[str, Any]:
        """Get UGC-specific site information"""
        base_info = super().get_site_info()
        base_info.update({
            'document_selectors': len(self.document_selectors),
            'pagination_selectors': len(self.pagination_selectors),
            'priority_keywords': len(self.priority_keywords),
            'specialization': 'UGC regulations and guidelines with academic categorization'
        })
        return base_info