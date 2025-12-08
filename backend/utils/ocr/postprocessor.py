"""
Text Post-processor for OCR Results
Cleans up and formats extracted text
"""

import re
from typing import Dict


class TextPostprocessor:
    """Post-process OCR extracted text"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean up OCR extracted text
        
        Args:
            text: Raw OCR text
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
            
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove spaces before punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        # Add space after punctuation if missing
        text = re.sub(r'([.,!?;:])([A-Za-z])', r'\1 \2', text)
        
        # Fix common OCR mistakes
        text = TextPostprocessor._fix_common_mistakes(text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def _fix_common_mistakes(text: str) -> str:
        """Fix common OCR recognition mistakes"""
        
        # Common character confusions
        replacements = {
            r'\b0\b': 'O',  # Zero to letter O in words
            r'\bl\b': 'I',  # lowercase L to uppercase I in words
            r'\|': 'I',     # Pipe to I
            r'rn': 'm',     # rn often misread as m
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)
            
        return text
    
    @staticmethod
    def format_text(text: str, preserve_structure=True) -> str:
        """
        Format text with proper paragraphs and structure
        
        Args:
            text: Cleaned text
            preserve_structure: Try to preserve document structure
            
        Returns:
            str: Formatted text
        """
        if not text:
            return ""
            
        # Split into sentences
        sentences = re.split(r'([.!?]+\s+)', text)
        
        # Reconstruct with proper spacing
        formatted = ""
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i].strip()
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
            
            if sentence:
                formatted += sentence + punctuation
                
        return formatted.strip()
    
    @staticmethod
    def extract_metadata_from_text(text: str) -> Dict:
        """
        Extract metadata hints from text (dates, emails, phones, etc.)
        
        Args:
            text: Extracted text
            
        Returns:
            dict: Metadata found in text
        """
        metadata = {
            'emails': [],
            'phones': [],
            'dates': [],
            'urls': []
        }
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        metadata['emails'] = re.findall(email_pattern, text)
        
        # Extract phone numbers (Indian format)
        phone_pattern = r'\b(?:\+91|0)?[6-9]\d{9}\b'
        metadata['phones'] = re.findall(phone_pattern, text)
        
        # Extract dates (various formats)
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # DD/MM/YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY-MM-DD
        ]
        for pattern in date_patterns:
            metadata['dates'].extend(re.findall(pattern, text))
            
        # Extract URLs
        url_pattern = r'https?://[^\s]+'
        metadata['urls'] = re.findall(url_pattern, text)
        
        return metadata
    
    @staticmethod
    def calculate_text_quality(text: str, confidence: float) -> Dict:
        """
        Calculate quality metrics for extracted text
        
        Args:
            text: Extracted text
            confidence: OCR confidence score
            
        Returns:
            dict: Quality metrics
        """
        if not text:
            return {
                'quality_score': 0.0,
                'needs_review': True,
                'issues': ['No text extracted']
            }
            
        issues = []
        quality_score = confidence  # Start with OCR confidence
        
        # Check text length
        if len(text) < 50:
            issues.append('Very short text')
            quality_score *= 0.9
            
        # Check for excessive special characters (sign of poor OCR)
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
        if special_char_ratio > 0.3:
            issues.append('Too many special characters')
            quality_score *= 0.8
            
        # Check for repeated characters (OCR artifact)
        if re.search(r'(.)\1{4,}', text):
            issues.append('Repeated characters detected')
            quality_score *= 0.9
            
        # Determine if needs review
        needs_review = quality_score < 0.8 or len(issues) > 0
        
        return {
            'quality_score': float(quality_score),
            'needs_review': needs_review,
            'issues': issues
        }
