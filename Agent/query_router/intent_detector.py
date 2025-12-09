"""
Detect user intent from query to improve retrieval accuracy
Handles: "latest rule", "amendments", "what is the rule of...", etc.
"""
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class IntentDetector:
    """Detect what user is asking for and apply appropriate filters"""
    
    def __init__(self):
        # Intent patterns
        self.latest_keywords = ['latest', 'current', 'recent', 'new', 'newest', 'updated', 'present']
        self.amendment_keywords = ['amendment', 'change', 'update', 'revision', 'modified', 'amended']
        self.history_keywords = ['all versions', 'history', 'previous', 'old', 'past']
        self.rule_keywords = ['rule', 'regulation', 'policy', 'guideline', 'directive', 'circular']
        
        # Ministry/source detection
        self.ministry_patterns = {
            'moe': ['ministry of education', 'moe', 'education ministry'],
            'ugc': ['ugc', 'university grants commission'],
            'aicte': ['aicte', 'all india council for technical education', 'technical education']
        }
        
        # Category detection
        self.category_patterns = {
            'policy': ['policy', 'policies'],
            'circular': ['circular', 'circulars'],
            'notification': ['notification', 'notice'],
            'regulation': ['regulation', 'regulations'],
            'guideline': ['guideline', 'guidelines']
        }
    
    def detect_intent(self, query: str) -> Dict:
        """
        Detect user intent and extract filters
        
        Args:
            query: User query
        
        Returns:
            {
                "intent": "latest_version" | "amendments" | "all_versions" | "general",
                "filters": {
                    "is_latest_version": bool,
                    "ministry": str,
                    "category": str,
                    "version_filter": str
                },
                "query_type": "rule_query" | "general_query"
            }
        """
        query_lower = query.lower()
        
        result = {
            "intent": "general",
            "filters": {},
            "query_type": "general_query",
            "detected_keywords": []
        }
        
        # Detect query type
        if any(keyword in query_lower for keyword in self.rule_keywords):
            result["query_type"] = "rule_query"
            result["detected_keywords"].extend([k for k in self.rule_keywords if k in query_lower])
        
        # Detect intent
        if any(keyword in query_lower for keyword in self.latest_keywords):
            result["intent"] = "latest_version"
            result["filters"]["is_latest_version"] = True
            result["detected_keywords"].extend([k for k in self.latest_keywords if k in query_lower])
            logger.info(f"Detected intent: latest_version (keywords: {result['detected_keywords']})")
        
        elif any(keyword in query_lower for keyword in self.amendment_keywords):
            result["intent"] = "amendments"
            result["filters"]["version_filter"] = "amendments_only"
            result["detected_keywords"].extend([k for k in self.amendment_keywords if k in query_lower])
            logger.info(f"Detected intent: amendments (keywords: {result['detected_keywords']})")
        
        elif any(keyword in query_lower for keyword in self.history_keywords):
            result["intent"] = "all_versions"
            result["filters"]["version_filter"] = "all_versions"
            result["detected_keywords"].extend([k for k in self.history_keywords if k in query_lower])
            logger.info(f"Detected intent: all_versions (keywords: {result['detected_keywords']})")
        
        else:
            # Default: show latest versions only for rule queries
            if result["query_type"] == "rule_query":
                result["intent"] = "latest_version"
                result["filters"]["is_latest_version"] = True
                logger.info("Default intent for rule query: latest_version")
        
        # Detect ministry
        ministry = self._detect_ministry(query_lower)
        if ministry:
            result["filters"]["ministry"] = ministry
            logger.info(f"Detected ministry: {ministry}")
        
        # Detect category
        category = self._detect_category(query_lower)
        if category:
            result["filters"]["category"] = category
            logger.info(f"Detected category: {category}")
        
        # Extract years from query (for temporal filtering)
        years = self._extract_years(query)
        if years:
            result["filters"]["years"] = years
            logger.info(f"Detected years: {years}")
        
        return result
    
    def _extract_years(self, query: str) -> List[int]:
        """Extract years from query (2000-2099)"""
        import re
        years = re.findall(r'\b(20\d{2})\b', query)
        return [int(y) for y in years] if years else []
    
    def _detect_ministry(self, query: str) -> Optional[str]:
        """Detect which ministry/source is being asked about"""
        for ministry, patterns in self.ministry_patterns.items():
            if any(pattern in query for pattern in patterns):
                return ministry
        return None
    
    def _detect_category(self, query: str) -> Optional[str]:
        """Detect document category"""
        for category, patterns in self.category_patterns.items():
            if any(pattern in query for pattern in patterns):
                return category
        return None
    
    def expand_query_with_synonyms(self, query: str) -> List[str]:
        """
        Expand query with synonyms for better retrieval
        
        Args:
            query: Original query
        
        Returns:
            List of query variations
        """
        synonyms = {
            "rule": ["regulation", "guideline", "policy", "directive"],
            "latest": ["recent", "new", "current", "updated"],
            "amendment": ["modification", "change", "revision", "update"],
            "university": ["institution", "college", "educational institution"],
            "approval": ["permission", "authorization", "clearance", "sanction"],
        }
        
        queries = [query]
        query_lower = query.lower()
        
        # Add synonym variations
        for term, term_synonyms in synonyms.items():
            if term in query_lower:
                for synonym in term_synonyms[:2]:  # Limit to 2 synonyms per term
                    expanded = query_lower.replace(term, synonym)
                    if expanded not in queries:
                        queries.append(expanded)
        
        return queries[:5]  # Limit to 5 variations
    
    def should_prioritize_latest(self, query: str) -> bool:
        """
        Quick check if query should prioritize latest versions
        
        Args:
            query: User query
        
        Returns:
            True if should prioritize latest versions
        """
        query_lower = query.lower()
        
        # Explicit latest request
        if any(keyword in query_lower for keyword in self.latest_keywords):
            return True
        
        # Rule/regulation queries default to latest
        if any(keyword in query_lower for keyword in self.rule_keywords):
            return True
        
        return False
    
    def extract_topic(self, query: str) -> Optional[str]:
        """
        Extract main topic from query
        
        Examples:
            "What is the latest rule on PhD admissions?" -> "PhD admissions"
            "Show me UGC regulations for research" -> "research"
        """
        # Remove common question words
        query_clean = query.lower()
        for word in ['what', 'is', 'the', 'show', 'me', 'give', 'tell', 'about', 'on', 'for']:
            query_clean = query_clean.replace(f' {word} ', ' ')
        
        # Remove intent keywords
        for keyword in self.latest_keywords + self.rule_keywords:
            query_clean = query_clean.replace(keyword, '')
        
        # Clean up
        query_clean = ' '.join(query_clean.split())
        
        return query_clean if query_clean else None


# Singleton instance
_intent_detector = None

def get_intent_detector() -> IntentDetector:
    """Get singleton intent detector instance"""
    global _intent_detector
    if _intent_detector is None:
        _intent_detector = IntentDetector()
    return _intent_detector
