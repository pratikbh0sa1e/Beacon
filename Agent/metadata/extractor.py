"""Metadata extraction service for Lazy RAG"""
import logging
import re
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# Setup logging
log_dir = Path("Agent/agent_logs")
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "metadata.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract metadata from documents without full embedding"""
    
    def __init__(self, google_api_key: Optional[str] = None):
        """
        Initialize metadata extractor
        
        Args:
            google_api_key: Google API key for LLM-based extraction
        """
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.llm = None
        
        if self.google_api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=self.google_api_key,
                temperature=0.1
            )
            logger.info("Metadata extractor initialized with LLM support")
        else:
            logger.warning("No Google API key provided - LLM extraction disabled")
    
    def extract_metadata(self, text: str, filename: str) -> Dict:
        """
        Extract comprehensive metadata from document
        
        Args:
            text: Full document text
            filename: Original filename
        
        Returns:
            Dictionary with extracted metadata
        """
        logger.info(f"Extracting metadata for: {filename}")
        
        metadata = {
            "title": None,
            "department": None,
            "document_type": None,
            "date_published": None,
            "keywords": [],
            "summary": None,
            "key_topics": [],
            "entities": {},
            "bm25_keywords": None,
            "text_length": len(text)
        }
        
        # Step 1: Parse filename
        filename_metadata = self._parse_filename(filename)
        metadata.update(filename_metadata)
        
        # Step 2: Extract from first page
        first_page = text[:3000]  # First ~3000 chars
        first_page_metadata = self._extract_from_first_page(first_page)
        metadata.update({k: v for k, v in first_page_metadata.items() if v})
        
        # Step 3: Extract TF-IDF keywords
        keywords = self._extract_tfidf_keywords(text, top_n=20)
        metadata["keywords"] = keywords
        metadata["bm25_keywords"] = " ".join(keywords)
        
        # Step 4: LLM-based extraction (if available)
        if self.llm:
            llm_metadata = self._llm_extract_metadata(first_page, filename)
            metadata.update({k: v for k, v in llm_metadata.items() if v})
        
        logger.info(f"Metadata extracted: title={metadata.get('title')}, dept={metadata.get('department')}")
        return metadata
    
    def _parse_filename(self, filename: str) -> Dict:
        """Extract metadata from filename"""
        metadata = {}
        
        # Remove extension
        name = Path(filename).stem
        
        # Try to extract year (4 digits)
        year_match = re.search(r'(19|20)\d{2}', name)
        if year_match:
            try:
                year = int(year_match.group())
                metadata["date_published"] = datetime(year, 1, 1).date()
            except:
                pass
        
        # Try to extract department (common patterns)
        dept_patterns = [
            r'MoE|Ministry of Education',
            r'MoH|Ministry of Health',
            r'MoF|Ministry of Finance',
            r'MoD|Ministry of Defence',
            r'MHA|Ministry of Home Affairs'
        ]
        for pattern in dept_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                metadata["department"] = re.search(pattern, name, re.IGNORECASE).group()
                break
        
        # Use filename as fallback title
        metadata["title"] = name.replace('_', ' ').replace('-', ' ')
        
        return metadata
    
    def _extract_from_first_page(self, text: str) -> Dict:
        """Extract metadata from first page text"""
        metadata = {}
        
        # Look for title (usually first line or in caps)
        lines = text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                # Likely a title
                if line.isupper() or line.istitle():
                    metadata["title"] = line
                    break
        
        # Look for date patterns
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) == 3:
                        if match.group(1).isdigit() and len(match.group(1)) == 4:
                            year = int(match.group(1))
                            metadata["date_published"] = datetime(year, 1, 1).date()
                        break
                except:
                    pass
        
        # Look for document type keywords
        doc_types = {
            "policy": ["policy", "policies"],
            "report": ["report", "annual report"],
            "memo": ["memorandum", "memo"],
            "guideline": ["guideline", "guidelines"],
            "regulation": ["regulation", "regulations"],
            "act": ["act", "legislation"]
        }
        
        text_lower = text.lower()
        for doc_type, keywords in doc_types.items():
            if any(kw in text_lower for kw in keywords):
                metadata["document_type"] = doc_type
                break
        
        return metadata
    
    def _extract_tfidf_keywords(self, text: str, top_n: int = 20) -> List[str]:
        """Extract top keywords using TF-IDF"""
        try:
            vectorizer = TfidfVectorizer(
                max_features=top_n,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.8
            )
            
            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            top_indices = scores.argsort()[-top_n:][::-1]
            keywords = [feature_names[i] for i in top_indices if scores[i] > 0]
            
            logger.info(f"Extracted {len(keywords)} TF-IDF keywords")
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting TF-IDF keywords: {str(e)}")
            return []
    
    def _llm_extract_metadata(self, text: str, filename: str) -> Dict:
        """Use LLM to extract rich metadata"""
        try:
            prompt = f"""Analyze this document and extract metadata in JSON format.

Document: {filename}
Text: {text[:2000]}

Extract and return ONLY valid JSON:
{{
    "title": "document title",
    "department": "ministry name",
    "document_type": "policy/report/memo/guideline",
    "summary": "2-3 sentence summary",
    "key_topics": ["topic1", "topic2", "topic3"],
    "entities": {{"departments": [], "locations": [], "people": []}}
}}"""

            logger.info("Calling LLM for metadata extraction...")
            response = self.llm.invoke(prompt)
            
            import json
            response_text = response.content.strip()
            
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            metadata = json.loads(response_text)
            logger.info("LLM metadata extraction successful")
            return metadata
            
        except Exception as e:
            logger.error(f"Error in LLM metadata extraction: {str(e)}")
            return {}
