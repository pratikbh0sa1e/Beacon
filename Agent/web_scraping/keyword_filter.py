"""
Keyword filtering for web scraping
Filters documents based on user-provided keywords during the scraping process
"""
import re
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class KeywordFilter:
    """
    Filter documents based on keyword matching
    
    Provides case-insensitive substring matching with special character sanitization.
    Used to filter documents DURING scraping to improve efficiency.
    """
    
    def __init__(self, keywords: Optional[List[str]] = None):
        """
        Initialize keyword filter
        
        Args:
            keywords: Optional list of keywords to filter by
        """
        self.keywords = []
        logger.debug(f"KeywordFilter.__init__ called with keywords: {keywords} (type: {type(keywords)})")
        if keywords:
            self.set_keywords(keywords)
    
    def set_keywords(self, keywords: List[str]) -> None:
        """
        Set or update the keywords list
        
        Args:
            keywords: List of keywords to filter by
        """
        if not keywords:
            self.keywords = []
            return
        
        # Handle case where keywords might be a string instead of list
        if isinstance(keywords, str):
            logger.warning(f"Keywords passed as string instead of list: '{keywords}'. Converting to list.")
            keywords = [keywords]
        
        # Filter out empty strings and None values
        valid_keywords = [k for k in keywords if k and isinstance(k, str) and k.strip()]
        
        # Store keywords as-is (we do literal string matching, not regex)
        self.keywords = [k.strip() for k in valid_keywords]
        
        logger.debug(f"KeywordFilter initialized with {len(self.keywords)} keywords: {self.keywords}")
    
    def is_active(self) -> bool:
        """
        Check if filtering is active (keywords provided)
        
        Returns:
            True if keywords are set, False otherwise
        """
        return len(self.keywords) > 0
    
    def matches(self, text: str) -> bool:
        """
        Check if text matches any keyword
        
        Performs case-insensitive substring matching.
        
        Args:
            text: Text to check against keywords
        
        Returns:
            True if text contains at least one keyword, False otherwise
        """
        if not self.is_active():
            # No filtering - everything matches
            return True
        
        if not text or not isinstance(text, str):
            return False
        
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Check if any keyword appears in the text
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def get_matched_keywords(self, text: str) -> List[str]:
        """
        Get list of keywords that matched in the text
        
        Args:
            text: Text to check against keywords
        
        Returns:
            List of keywords that appear in the text (original case from keywords list)
        """
        if not self.is_active():
            return []
        
        if not text or not isinstance(text, str):
            return []
        
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        matched = []
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)
        
        return matched
    
    def evaluate(self, text: str) -> Dict[str, Any]:
        """
        Evaluate text against keywords and return detailed result
        
        Args:
            text: Text to evaluate
        
        Returns:
            Dict with 'matches' (bool) and 'matched_keywords' (List[str])
        """
        matched_keywords = self.get_matched_keywords(text)
        
        return {
            'matches': len(matched_keywords) > 0 if self.is_active() else True,
            'matched_keywords': matched_keywords,
            'text': text
        }
    
    def _sanitize_keyword(self, keyword: str) -> str:
        """
        Sanitize keyword for safe matching
        
        Since we use literal string matching (not regex), special characters
        are automatically treated as literals. This method is kept for future
        extensibility if regex matching is added.
        
        Args:
            keyword: Keyword to sanitize
        
        Returns:
            Sanitized keyword (currently just strips whitespace)
        """
        # For literal string matching, we just need to strip whitespace
        # Special characters are automatically safe since we're not using regex
        return keyword.strip()
    
    def get_filter_stats(self, total_items: int, matched_items: int) -> Dict[str, Any]:
        """
        Calculate filtering statistics
        
        Args:
            total_items: Total number of items evaluated
            matched_items: Number of items that matched
        
        Returns:
            Dict with filtering statistics
        """
        skipped_items = total_items - matched_items
        match_rate = (matched_items / total_items * 100) if total_items > 0 else 0.0
        
        return {
            'total_discovered': total_items,
            'matched': matched_items,
            'skipped': skipped_items,
            'match_rate_percent': round(match_rate, 2),
            'keywords_used': self.keywords.copy(),
            'filter_active': self.is_active()
        }
    
    def __repr__(self) -> str:
        """String representation of the filter"""
        if self.is_active():
            return f"KeywordFilter(keywords={self.keywords})"
        else:
            return "KeywordFilter(inactive)"
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        if self.is_active():
            return f"Keyword filter with {len(self.keywords)} keywords: {', '.join(self.keywords[:5])}" + \
                   (f" and {len(self.keywords) - 5} more" if len(self.keywords) > 5 else "")
        else:
            return "Keyword filter (inactive)"
