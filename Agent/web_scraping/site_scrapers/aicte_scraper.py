"""
All India Council for Technical Education (AICTE) specific scraper
Hardcoded selectors and logic for AICTE websites
"""
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class AICTEScraper(BaseScraper):
    """Scraper specifically designed for AICTE websites"""
    
    def __init__(self):
        super().__init__()
        self.site_name = "All India Council for Technical Education"
        self.rate_limit_delay = 1.5
        
        # AICTE-specific document extensions
        self.document_extensions = ['.pdf', '.docx', '.doc', '.pptx', '.xlsx', '.xls']
        
        # AICTE-specific CSS selectors
        self.document_selectors = [
            # AICTE common patterns
            'a[href$=".pdf"]',
            'a[href$=".docx"]',
            'a[href$=".doc"]',
            '.approval-list a',
            '.handbook-list a',
            '.circular-list a',
            '.notification-list a',
            '.document-list a',
            # AICTE specific content areas
            '.aicte-content a[href*=".pdf"]',
            '.main-content a[href*=".pdf"]',
            '#content a[href*=".pdf"]',
            '.content-area a[href*=".pdf"]',
            # Table-based listings (common in AICTE)
            'table.approval-table a',
            'table a[href$=".pdf"]',
            '.data-grid a',
            # AICTE specific sections
            '.approval-documents a',
            '.handbook-documents a',
            '.policy-documents a',
            '.curriculum-documents a',
        ]
        
        # AICTE-specific pagination selectors
        self.pagination_selectors = [
            '.pagination a',
            '.pager a',
            'a[rel="next"]',
            'a:contains("Next")',
            'a:contains(">")',
            '.page-navigation a',
            # AICTE specific
            '.approval-pagination a',
            'a[href*="page="]',
            'a[href*="pageNo="]',
            'a[href*="start="]',
        ]
        
        # AICTE priority keywords
        self.priority_keywords = [
            'approval', 'handbook', 'curriculum', 'syllabus',
            'nba', 'accreditation', 'outcome based education', 'obe',
            'technical education', 'engineering', 'management', 'pharmacy',
            'architecture', 'hotel management', 'mca', 'mba',
            'internship', 'industry connect', 'skill development',
            'startup', 'innovation', 'research', 'faculty development'
        ]
    
    def get_document_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract document links using AICTE-specific selectors"""
        documents = []
        found_urls = set()
        
        for selector in self.document_selectors:
            try:
                links = soup.select(selector)
                logger.debug(f"[AICTE] Selector '{selector}' found {len(links)} links")
                
                for link in links:
                    href = link.get('href')
                    if not href:
                        continue
                    
                    full_url = urljoin(base_url, href)
                    
                    if full_url in found_urls or not self._is_document_url(full_url):
                        continue
                    
                    found_urls.add(full_url)
                    
                    # Extract AICTE-specific metadata
                    title = self._extract_aicte_title(link, soup)
                    context = self._get_document_context(link)
                    category = self._categorize_aicte_document(title, context)
                    is_priority = self._is_priority_document(title, context)
                    
                    doc_info = {
                        'url': full_url,
                        'title': title,
                        'file_type': self._get_file_extension(full_url),
                        'found_at': self._get_current_timestamp(),
                        'source_page': base_url,
                        'scraper_used': 'AICTEScraper',
                        'selector_used': selector,
                        'context': context,
                        'category': category,
                        'is_priority': is_priority,
                        'ministry': 'All India Council for Technical Education'
                    }
                    
                    if self.validate_document(doc_info):
                        documents.append(doc_info)
                        logger.debug(f"[AICTE] Found document: {title[:50]}...")
                    
            except Exception as e:
                logger.warning(f"[AICTE] Error with selector '{selector}': {str(e)}")
                continue
        
        # Sort by priority and category
        documents.sort(key=lambda x: (not x['is_priority'], x['category'], x['title']))
        
        logger.info(f"[AICTE] Extracted {len(documents)} documents from {base_url}")
        return documents
    
    def get_pagination_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract pagination links using AICTE-specific selectors"""
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
                logger.warning(f"[AICTE] Error with pagination selector '{selector}': {str(e)}")
                continue
        
        logger.debug(f"[AICTE] Found {len(pagination_links)} pagination links")
        return pagination_links[:10]
    
    def _extract_aicte_title(self, link, soup: BeautifulSoup) -> str:
        """Extract title using AICTE-specific logic"""
        # Try link text first
        title = link.get_text(strip=True)
        
        if title and len(title) > 5:
            return self._clean_text(title)
        
        # Try title attribute
        title = link.get('title', '').strip()
        if title and len(title) > 5:
            return self._clean_text(title)
        
        # AICTE often has document titles in table structure
        td = link.find_parent('td')
        if td:
            tr = td.find_parent('tr')
            if tr:
                cells = tr.find_all('td')
                # Look for title in first few columns
                for i, cell in enumerate(cells[:3]):
                    if cell != td:
                        cell_text = cell.get_text(strip=True)
                        if cell_text and len(cell_text) > 5 and 'download' not in cell_text.lower():
                            return self._clean_text(cell_text)
        
        # Try parent div or span
        for parent_tag in ['div', 'span', 'p']:
            parent = link.find_parent(parent_tag)
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
        
        return "AICTE Document"
    
    def _get_document_context(self, link) -> str:
        """Get surrounding context for AICTE documents"""
        context_parts = []
        
        # Table row context (very common in AICTE approval lists)
        tr = link.find_parent('tr')
        if tr:
            tr_text = tr.get_text(strip=True)
            if tr_text and len(tr_text) < 500:
                context_parts.append(tr_text)
        
        # Parent container
        for tag in ['div', 'section', 'article']:
            parent = link.find_parent(tag)
            if parent and parent.name != 'tr':
                parent_text = parent.get_text(strip=True)
                if parent_text and len(parent_text) < 300:
                    context_parts.append(parent_text)
                    break
        
        # List item context
        li = link.find_parent('li')
        if li:
            li_text = li.get_text(strip=True)
            if li_text and li_text not in context_parts:
                context_parts.append(li_text)
        
        return ' | '.join(context_parts[:3])
    
    def _categorize_aicte_document(self, title: str, context: str) -> str:
        """Categorize AICTE document based on title and context"""
        text_to_check = f"{title} {context}".lower()
        
        if any(word in text_to_check for word in ['approval', 'approved', 'approval process']):
            return 'Approval'
        elif any(word in text_to_check for word in ['handbook', 'manual', 'guide']):
            return 'Handbook'
        elif any(word in text_to_check for word in ['curriculum', 'syllabus', 'course']):
            return 'Curriculum'
        elif any(word in text_to_check for word in ['circular', 'notification', 'notice']):
            return 'Circular/Notification'
        elif any(word in text_to_check for word in ['nba', 'accreditation', 'quality']):
            return 'Accreditation'
        elif any(word in text_to_check for word in ['faculty', 'development', 'training']):
            return 'Faculty Development'
        elif any(word in text_to_check for word in ['internship', 'industry', 'placement']):
            return 'Industry Connect'
        elif any(word in text_to_check for word in ['startup', 'innovation', 'research']):
            return 'Innovation/Research'
        else:
            return 'General'
    
    def _is_priority_document(self, title: str, context: str) -> bool:
        """Check if document is high priority for AICTE"""
        text_to_check = f"{title} {context}".lower()
        return any(keyword in text_to_check for keyword in self.priority_keywords)
    
    def _is_pagination_link(self, link, href: str) -> bool:
        """Check if link is pagination for AICTE sites"""
        link_text = link.get_text(strip=True).lower()
        
        pagination_indicators = [
            'next', 'previous', 'prev', '>', '<', 'page',
            'more', 'continue', '»', '«', '→', '←'
        ]
        
        if any(indicator in link_text for indicator in pagination_indicators):
            return True
        
        pagination_params = ['page=', 'pageNo=', 'start=', 'p=', 'offset=']
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
        """Get AICTE-specific site information"""
        base_info = super().get_site_info()
        base_info.update({
            'document_selectors': len(self.document_selectors),
            'pagination_selectors': len(self.pagination_selectors),
            'priority_keywords': len(self.priority_keywords),
            'specialization': 'AICTE approvals and technical education documents'
        })
        return base_info