"""
Intent Classification Module

Classifies user queries into intent types to determine appropriate response format.
Supports: comparison, count, list, and standard Q&A intents.
"""

import logging
import re
from typing import Dict, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IntentResult:
    """Result of intent classification"""
    intent: str  # "comparison" | "count" | "list" | "qa"
    confidence: float  # 0.0 to 1.0
    extracted_params: Dict[str, any]  # Extracted parameters (language, type, etc.)


class IntentClassifier:
    """
    Classifies user query intent using keyword matching and pattern recognition.
    
    Intent Types:
    - comparison: User wants to compare documents/policies
    - count: User wants to know how many documents exist
    - list: User wants to see a list of documents
    - qa: Standard question-answering (default)
    """
    
    # Intent detection patterns
    COMPARISON_KEYWORDS = [
        "compare", "comparison", "difference", "differences", "vs", "versus",
        "contrast", "between", "distinguish", "differentiate"
    ]
    
    COUNT_KEYWORDS = [
        "how many", "count", "number of", "total", "how much",
        "quantity", "amount of"
    ]
    
    LIST_KEYWORDS = [
        "show all", "list all", "fetch all", "get all", "find all",
        "display all", "give me all", "show me all", "retrieve all"
    ]
    
    # Language names for list queries
    LANGUAGES = [
        "hindi", "english", "tamil", "telugu", "bengali", "marathi",
        "gujarati", "kannada", "malayalam", "punjabi", "urdu", "odia"
    ]
    
    # Document types
    DOCUMENT_TYPES = [
        "policy", "policies", "guideline", "guidelines", "regulation",
        "regulations", "circular", "circulars", "notification",
        "notifications", "document", "documents", "report", "reports"
    ]
    
    def __init__(self):
        """Initialize the intent classifier"""
        logger.info("Intent classifier initialized")
    
    def classify(self, query: str) -> IntentResult:
        """
        Classify the intent of a user query.
        
        Args:
            query: User's question
            
        Returns:
            IntentResult with intent type, confidence, and extracted parameters
        """
        if not query or not query.strip():
            return IntentResult(
                intent="qa",
                confidence=0.5,
                extracted_params={}
            )
        
        query_lower = query.lower().strip()
        
        # Try each intent type in priority order
        
        # 1. Check for comparison intent (highest priority for explicit comparisons)
        comparison_result = self._check_comparison(query_lower)
        if comparison_result:
            return comparison_result
        
        # 2. Check for count intent
        count_result = self._check_count(query_lower)
        if count_result:
            return count_result
        
        # 3. Check for list intent
        list_result = self._check_list(query_lower)
        if list_result:
            return list_result
        
        # 4. Default to Q&A
        return IntentResult(
            intent="qa",
            confidence=0.80,
            extracted_params={}
        )
    
    def _check_comparison(self, query: str) -> Optional[IntentResult]:
        """Check if query is a comparison intent"""
        # Check for comparison keywords
        has_comparison_keyword = any(
            keyword in query for keyword in self.COMPARISON_KEYWORDS
        )
        
        if not has_comparison_keyword:
            return None
        
        # Extract potential document identifiers (years, names)
        extracted_params = {}
        
        # Extract years (e.g., "2018 vs 2021")
        years = re.findall(r'\b(19|20)\d{2}\b', query)
        if len(years) >= 2:
            extracted_params["years"] = years[:2]  # Take first two years
        
        # Extract document types
        doc_types = [dt for dt in self.DOCUMENT_TYPES if dt in query]
        if doc_types:
            extracted_params["document_types"] = doc_types
        
        logger.info(f"Classified as comparison intent with params: {extracted_params}")
        
        return IntentResult(
            intent="comparison",
            confidence=0.95,
            extracted_params=extracted_params
        )
    
    def _check_count(self, query: str) -> Optional[IntentResult]:
        """Check if query is a count intent"""
        # Check for count keywords
        has_count_keyword = any(
            keyword in query for keyword in self.COUNT_KEYWORDS
        )
        
        if not has_count_keyword:
            return None
        
        # Extract filters
        extracted_params = self._extract_filters(query)
        
        logger.info(f"Classified as count intent with params: {extracted_params}")
        
        return IntentResult(
            intent="count",
            confidence=0.95,
            extracted_params=extracted_params
        )
    
    def _check_list(self, query: str) -> Optional[IntentResult]:
        """Check if query is a list intent"""
        # Check for list keywords
        has_list_keyword = any(
            keyword in query for keyword in self.LIST_KEYWORDS
        )
        
        # Check for language mentions (strong indicator of list intent)
        has_language = any(
            lang in query for lang in self.LANGUAGES
        )
        
        # Check for "all" + document type pattern
        has_all_pattern = "all" in query and any(
            dt in query for dt in self.DOCUMENT_TYPES
        )
        
        if not (has_list_keyword or has_language or has_all_pattern):
            return None
        
        # Extract filters
        extracted_params = self._extract_filters(query)
        
        # Determine confidence based on signal strength
        confidence = 0.90
        if has_list_keyword and (has_language or has_all_pattern):
            confidence = 0.95
        
        logger.info(f"Classified as list intent with params: {extracted_params}")
        
        return IntentResult(
            intent="list",
            confidence=confidence,
            extracted_params=extracted_params
        )
    
    def _extract_filters(self, query: str) -> Dict[str, any]:
        """
        Extract filter parameters from query.
        
        Extracts:
        - language: Language name if mentioned
        - document_type: Type of document if mentioned
        - years: Year range if mentioned
        """
        filters = {}
        
        # Extract language
        for lang in self.LANGUAGES:
            if lang in query:
                filters["language"] = lang.capitalize()
                break
        
        # Extract document type
        for doc_type in self.DOCUMENT_TYPES:
            if doc_type in query:
                # Normalize to singular form
                normalized = doc_type.rstrip('s')
                filters["document_type"] = normalized.capitalize()
                break
        
        # Extract years
        years = re.findall(r'\b(19|20)\d{2}\b', query)
        if years:
            if len(years) == 1:
                filters["year"] = years[0]
            elif len(years) >= 2:
                filters["year_from"] = min(years)
                filters["year_to"] = max(years)
        
        return filters


# Global classifier instance
_classifier = None


def get_classifier() -> IntentClassifier:
    """Get or create the global intent classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier()
    return _classifier


def classify_intent(query: str) -> IntentResult:
    """
    Convenience function to classify query intent.
    
    Args:
        query: User's question
        
    Returns:
        IntentResult with intent type, confidence, and extracted parameters
    """
    classifier = get_classifier()
    return classifier.classify(query)
