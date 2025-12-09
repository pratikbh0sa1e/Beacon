"""
Document Processing Module

Handles text extraction, OCR, and document analysis
"""
from .text_extraction_service import TextExtractionService, get_ocr_reader

__all__ = ['TextExtractionService', 'get_ocr_reader']
