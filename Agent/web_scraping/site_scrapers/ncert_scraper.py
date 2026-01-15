"""
National Council of Educational Research and Training (NCERT) specific scraper
Hardcoded selectors and logic for NCERT websites
"""
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import re

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class NCERTScraper(BaseScraper):
    """Scraper specifically designed for NCERT websites"""
    
    def __init__(self):
        super().__init__()
        self.site_name = "National Council of Educational Research and Training"
        self.rate_limit_delay = 1.0  # NCERT sites are usually faster
        
        # NCERT-specific document extensions
        self.document_extensions = ['.pdf', '.docx', '.doc', '.pptx', '.xlsx', '.xls', '.zip']
        
        # NCERT-specific CSS selectors
        self.document_selectors = [
            # NCERT main document patterns
            'a[href$=".pdf"]',
            'a[href$=".docx"]',
            'a[href$=".doc"]',
            'a[href$=".zip"]',  # NCERT often has zip files
            # NCERT specific content areas
            '.content a[href*=".pdf"]',
            '.main-content a[href*=".pdf"]',
            '.textbook-section a',
            '.syllabus-section a',
            '.curriculum-section a',
            '.publication-section a',
            # NCERT table structures
            'table.textbook-table a',
            'table.publication-table a',
            'tbody tr td a[href$=".pdf"]',
            # NCERT list structures
            '.textbook-list a',
            '.publication-list a',
            '.syllabus-list a',
            'ul.books li a',
            'ul.publications li a',
            # NCERT specific divs
            'div.textbook-item a',
            'div.publication-item a',
            'div.book-item a',
            # NCERT download areas
            '.download-section a',
            '.downloads a[href$=".pdf"]',
            '.book-downloads a',
            # NCERT specific areas
            '.textbooks a',
            '.exemplar a',
            '.supplementary a',
            '.teacher-manual a'
        ]
        
        # NCERT-specific pagination selectors
        self.pagination_selectors = [
            '.pagination a',
            '.pager a',
            'a[rel="next"]',
            'a:contains("Next")',
            '.page-numbers a',
            # NCERT specific
            '.book-pagination a',
            '.publication-pagination a',
            'a[href*="page="]',
            'a[href*="pagenum="]'
        ]
        
        # NCERT-specific priority keywords
        self.priority_keywords = [
            'textbook', 'ncert', 'syllabus', 'curriculum', 'exemplar',
            'teacher manual', 'guide', 'class', 'standard', 'grade',
            'mathematics', 'science', 'social science', 'english', 'hindi',
            'environmental studies', 'evs', 'cbse', 'school education'
        ]
        
        # NCERT document categories
        self.ncert_categories = {
            'textbook': ['textbook', 'book', 'text book'],
            'exemplar': ['exemplar', 'problem', 'exercise'],
            'syllabus': ['syllabus', 'curriculum', 'course'],
            'teacher_manual': ['teacher', 'manual', 'guide', 'handbook'],
            'supplementary': ['supplementary', 'additional', 'extra'],
            'question_paper': ['question', 'paper', 'sample', 'model'],
            'report': ['report', 'annual', 'survey', 'study'],
            'policy': ['policy', 'framework', 'guideline']
        }
        
        # NCERT class/grade mapping
        self.class_patterns = [
            r'class\s*(\d+|[ivx]+)',
            r'standard\s*(\d+|[ivx]+)',
            r'grade\s*(\d+|[ivx]+)',
            r'std\s*(\d+|[ivx]+)',
            r'(\d+)(?:st|nd|rd|th)\s*class',
        ]
    
    def get_document_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract document links using NCERT-specific selectors"""
        documents = []
        found_urls = set()
        
        logger.debug(f"[NCERT] Starting document extraction from {base_url}")
        
        for selector in self.document_selectors:
            try:
                links = soup.select(selector)
                logger.debug(f"[NCERT] Selector '{selector}' found {len(links)} links")
                
                for link in links:
                    href = link.get('href')
                    if not href:
                        continue
                    
                    full_url = urljoin(base_url, href)
                    full_url = self._clean_url(full_url)
                    
                    if full_url in found_urls or not self._is_document_url(full_url):
                        continue
                    
                    found_urls.add(full_url)
                    
                    # Extract NCERT-specific document information
                    doc_info = self._extract_ncert_document_info(link, soup, base_url, selector)
                    
                    if doc_info and self.validate_document(doc_info):
                        documents.append(doc_info)
                        logger.debug(f"[NCERT] Found: {doc_info['title'][:50]}...")
                    
            except Exception as e:
                logger.warning(f"[NCERT] Error with selector '{selector}': {str(e)}")
                continue
        
        # Sort by priority and class
        documents.sort(key=lambda x: (
            not x['is_priority'],
            x['category'] != 'Textbook',
            x.get('class_number', 99),
            x['title']
        ))
        
        logger.info(f"[NCERT] Extracted {len(documents)} documents from {base_url}")
        return documents
    
    def get_pagination_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract pagination links using NCERT-specific patterns"""
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
                    full_url = self._clean_url(full_url)
                    
                    if full_url in found_links or full_url == base_url:
                        continue
                    
                    if self._is_ncert_pagination_link(link, href):
                        found_links.add(full_url)
                        pagination_links.append(full_url)
                        
            except Exception as e:
                logger.warning(f"[NCERT] Error with pagination selector '{selector}': {str(e)}")
                continue
        
        logger.debug(f"[NCERT] Found {len(pagination_links)} pagination links")
        return pagination_links[:8]  # NCERT usually has fewer pages
    
    def _extract_ncert_document_info(self, link, soup: BeautifulSoup, base_url: str, selector: str) -> Dict[str, Any]:
        """Extract comprehensive NCERT document information"""
        href = link.get('href')
        full_url = urljoin(base_url, href)
        full_url = self._clean_url(full_url)
        
        # Extract title using NCERT-specific strategies
        title = self._extract_ncert_title(link, soup)
        
        # Get context
        context = self._get_ncert_context(link)
        
        # Extract class/grade information
        class_info = self._extract_class_info(title, context)
        
        # Extract subject information
        subject_info = self._extract_subject_info(title, context)
        
        # Categorize document
        category = self._categorize_ncert_document(title, context)
        
        # Check priority
        is_priority = self._is_ncert_priority_document(title, context, category)
        
        return {
            'url': full_url,
            'title': title,
            'file_type': self._get_file_extension(full_url),
            'found_at': self._get_current_timestamp(),
            'source_page': base_url,
            'scraper_used': 'NCERTScraper',
            'selector_used': selector,
            'context': context,
            'category': category,
            'is_priority': is_priority,
            'ministry': 'National Council of Educational Research and Training',
            'class_number': class_info.get('number'),
            'class_text': class_info.get('text'),
            'subject': subject_info.get('subject'),
            'subject_category': subject_info.get('category'),
            'department': 'NCERT'
        }
    
    def _extract_ncert_title(self, link, soup: BeautifulSoup) -> str:
        """Extract title using NCERT-specific strategies"""
        # Strategy 1: Direct link text (often good for NCERT)
        title = link.get_text(strip=True)
        if title and len(title) > 5 and not title.lower().startswith(('download', 'click', 'view', 'pdf')):
            return self._clean_text(title)
        
        # Strategy 2: Title attribute
        title = link.get('title', '').strip()
        if title and len(title) > 5:
            return self._clean_text(title)
        
        # Strategy 3: Table cell content (common in NCERT textbook listings)
        td = link.find_parent('td')
        if td:
            tr = td.find_parent('tr')
            if tr:
                cells = tr.find_all('td')
                # Look for book title in adjacent cells
                for cell in cells:
                    if cell != td:
                        cell_text = cell.get_text(strip=True)
                        if cell_text and len(cell_text) > 5 and not cell_text.lower().startswith(('download', 'pdf')):
                            return self._clean_text(cell_text)
        
        # Strategy 4: Image alt text (NCERT often has book cover images)
        img = link.find('img')
        if img:
            alt_text = img.get('alt', '').strip()
            if alt_text and len(alt_text) > 5:
                return self._clean_text(alt_text)
        
        # Strategy 5: Parent div with book/textbook class
        parent_div = link.find_parent('div', class_=re.compile(r'(book|textbook|publication)'))
        if parent_div:
            # Look for heading tags
            for tag in ['h1', 'h2', 'h3', 'h4', 'h5']:
                heading = parent_div.find(tag)
                if heading:
                    heading_text = heading.get_text(strip=True)
                    if heading_text and len(heading_text) > 5:
                        return self._clean_text(heading_text)
        
        # Strategy 6: Previous/next sibling text
        for sibling in [link.previous_sibling, link.next_sibling]:
            if sibling and hasattr(sibling, 'get_text'):
                sibling_text = sibling.get_text(strip=True)
                if sibling_text and len(sibling_text) > 5 and len(sibling_text) < 100:
                    return self._clean_text(sibling_text)
        
        # Fallback: Clean filename
        href = link.get('href', '')
        filename = href.split('/')[-1]
        if filename and '.' in filename:
            name_without_ext = filename.rsplit('.', 1)[0]
            return self._clean_text(name_without_ext.replace('_', ' ').replace('-', ' '))
        
        return "NCERT Document"
    
    def _get_ncert_context(self, link) -> str:
        """Get NCERT-specific context information"""
        context_parts = []
        
        # Table row context
        tr = link.find_parent('tr')
        if tr:
            cells = tr.find_all(['td', 'th'])
            for cell in cells:
                cell_text = cell.get_text(strip=True)
                if cell_text and len(cell_text) < 100:
                    context_parts.append(cell_text)
        
        # List context
        li = link.find_parent('li')
        if li:
            li_text = li.get_text(strip=True)
            if li_text and li_text not in context_parts:
                context_parts.append(li_text)
        
        # Div context with NCERT-specific classes
        div = link.find_parent('div', class_=re.compile(r'(book|textbook|publication|class|subject)'))
        if div:
            div_text = div.get_text(strip=True)
            if div_text and len(div_text) < 200:
                context_parts.append(div_text)
        
        return ' | '.join(context_parts[:3])
    
    def _extract_class_info(self, title: str, context: str) -> Dict[str, Any]:
        """Extract class/grade information from NCERT documents"""
        text_to_search = f"{title} {context}".lower()
        
        for pattern in self.class_patterns:
            match = re.search(pattern, text_to_search, re.IGNORECASE)
            if match:
                class_text = match.group(1)
                
                # Convert Roman numerals to numbers
                roman_to_int = {
                    'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5,
                    'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10,
                    'xi': 11, 'xii': 12
                }
                
                if class_text.lower() in roman_to_int:
                    class_number = roman_to_int[class_text.lower()]
                elif class_text.isdigit():
                    class_number = int(class_text)
                else:
                    class_number = None
                
                return {
                    'text': class_text,
                    'number': class_number
                }
        
        return {'text': None, 'number': None}
    
    def _extract_subject_info(self, title: str, context: str) -> Dict[str, Any]:
        """Extract subject information from NCERT documents"""
        text_to_search = f"{title} {context}".lower()
        
        # NCERT subject mapping
        subjects = {
            'mathematics': ['mathematics', 'math', 'maths', 'गणित'],
            'science': ['science', 'विज्ञान'],
            'social_science': ['social science', 'social studies', 'सामाजिक विज्ञान'],
            'english': ['english', 'अंग्रेजी'],
            'hindi': ['hindi', 'हिंदी'],
            'environmental_studies': ['environmental studies', 'evs', 'पर्यावरण अध्ययन'],
            'physics': ['physics', 'भौतिकी'],
            'chemistry': ['chemistry', 'रसायन'],
            'biology': ['biology', 'जीव विज्ञान'],
            'history': ['history', 'इतिहास'],
            'geography': ['geography', 'भूगोल'],
            'economics': ['economics', 'अर्थशास्त्र'],
            'political_science': ['political science', 'राजनीति विज्ञान']
        }
        
        for subject, keywords in subjects.items():
            if any(keyword in text_to_search for keyword in keywords):
                # Determine subject category
                if subject in ['mathematics', 'science', 'physics', 'chemistry', 'biology']:
                    category = 'STEM'
                elif subject in ['english', 'hindi']:
                    category = 'Language'
                elif subject in ['history', 'geography', 'economics', 'political_science', 'social_science']:
                    category = 'Social Studies'
                else:
                    category = 'General'
                
                return {
                    'subject': subject.replace('_', ' ').title(),
                    'category': category
                }
        
        return {'subject': None, 'category': None}
    
    def _categorize_ncert_document(self, title: str, context: str) -> str:
        """Categorize NCERT document based on content"""
        text_to_check = f"{title} {context}".lower()
        
        for category, keywords in self.ncert_categories.items():
            if any(keyword in text_to_check for keyword in keywords):
                return category.replace('_', ' ').title()
        
        return 'General'
    
    def _is_ncert_priority_document(self, title: str, context: str, category: str) -> bool:
        """Check if document is high priority for NCERT"""
        text_to_check = f"{title} {context}".lower()
        
        # High priority categories
        if category.lower() in ['textbook', 'exemplar', 'syllabus']:
            return True
        
        # Check for priority keywords
        return any(keyword in text_to_check for keyword in self.priority_keywords)
    
    def _is_ncert_pagination_link(self, link, href: str) -> bool:
        """Check if link is NCERT pagination"""
        link_text = link.get_text(strip=True).lower()
        
        pagination_indicators = [
            'next', 'previous', 'prev', '>', '<', 'page', 'more'
        ]
        
        if any(indicator in link_text for indicator in pagination_indicators):
            return True
        
        if any(param in href.lower() for param in ['page=', 'pagenum=', 'start=']):
            return True
        
        if link_text.isdigit() and 1 <= int(link_text) <= 100:
            return True
        
        return False
    
    def _clean_url(self, url: str) -> str:
        """Clean and normalize URL"""
        if '#' in url:
            url = url.split('#')[0]
        url = url.replace(' ', '%20')
        return url
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def get_site_info(self) -> Dict[str, Any]:
        """Get NCERT-specific site information"""
        base_info = super().get_site_info()
        base_info.update({
            'document_selectors': len(self.document_selectors),
            'pagination_selectors': len(self.pagination_selectors),
            'priority_keywords': len(self.priority_keywords),
            'categories': list(self.ncert_categories.keys()),
            'class_patterns': len(self.class_patterns),
            'specialization': 'NCERT documents with textbook and class-wise categorization'
        })
        return base_info