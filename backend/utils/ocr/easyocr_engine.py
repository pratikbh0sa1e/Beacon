"""
Enhanced EasyOCR Engine with Confidence Scoring
"""

import easyocr
import numpy as np
from typing import Dict, List, Tuple
import io
from PIL import Image


class EasyOCREngine:
    """Enhanced EasyOCR wrapper with confidence scoring"""
    
    def __init__(self, languages=['en', 'hi']):
        """
        Initialize EasyOCR reader
        
        Args:
            languages: List of language codes (default: English + Hindi)
        """
        self.languages = languages
        self.reader = easyocr.Reader(languages, gpu=True)
        
    def extract_text(self, image_data, detail=True) -> Dict:
        """
        Extract text from image with confidence scores
        
        Args:
            image_data: bytes or PIL Image or numpy array
            detail: If True, return detailed results with bounding boxes
            
        Returns:
            dict: {
                'text': str,
                'confidence': float (0-1),
                'details': list of dicts with per-line info,
                'language_detected': str,
                'total_lines': int
            }
        """
        # Convert to numpy array if needed
        if isinstance(image_data, bytes):
            img = Image.open(io.BytesIO(image_data))
            img_array = np.array(img)
        elif isinstance(image_data, Image.Image):
            img_array = np.array(image_data)
        else:
            img_array = image_data
            
        # Run OCR with detail
        results = self.reader.readtext(img_array, detail=True)
        
        if not results:
            return {
                'text': '',
                'confidence': 0.0,
                'details': [],
                'language_detected': 'unknown',
                'total_lines': 0
            }
        
        # Extract text and confidence scores
        extracted_lines = []
        confidence_scores = []
        
        for (bbox, text, confidence) in results:
            extracted_lines.append(text)
            confidence_scores.append(confidence)
            
        # Combine text
        full_text = ' '.join(extracted_lines)
        
        # Calculate average confidence
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        
        # Detect primary language (simple heuristic)
        language_detected = self._detect_language(full_text)
        
        # Prepare detailed results
        details = []
        if detail:
            for (bbox, text, confidence) in results:
                details.append({
                    'text': text,
                    'confidence': float(confidence),
                    'bbox': bbox,
                    'needs_review': confidence < 0.8
                })
        
        return {
            'text': full_text,
            'confidence': float(avg_confidence),
            'details': details,
            'language_detected': language_detected,
            'total_lines': len(extracted_lines)
        }
    
    def extract_text_simple(self, image_data) -> Tuple[str, float]:
        """
        Simple extraction returning only text and confidence
        
        Returns:
            tuple: (text, confidence_score)
        """
        result = self.extract_text(image_data, detail=False)
        return result['text'], result['confidence']
    
    def _detect_language(self, text: str) -> str:
        """
        Detect primary language in text (simple heuristic)
        
        Args:
            text: Extracted text
            
        Returns:
            str: 'english', 'hindi', or 'mixed'
        """
        if not text:
            return 'unknown'
            
        # Count English characters (ASCII)
        english_chars = sum(1 for c in text if ord(c) < 128 and c.isalpha())
        
        # Count Hindi characters (Devanagari Unicode range)
        hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        
        total_chars = english_chars + hindi_chars
        
        if total_chars == 0:
            return 'unknown'
            
        english_ratio = english_chars / total_chars
        hindi_ratio = hindi_chars / total_chars
        
        if english_ratio > 0.7:
            return 'english'
        elif hindi_ratio > 0.7:
            return 'hindi'
        else:
            return 'mixed'
    
    def batch_extract(self, image_list: List) -> List[Dict]:
        """
        Extract text from multiple images
        
        Args:
            image_list: List of image data (bytes, PIL, or numpy)
            
        Returns:
            list: List of extraction results
        """
        results = []
        for image_data in image_list:
            result = self.extract_text(image_data)
            results.append(result)
        return results
