"""
OCR Module for Enhanced Text Extraction
Supports scanned documents with confidence scoring, preprocessing, rotation correction, and table extraction
"""

from .ocr_manager import OCRManager
from .easyocr_engine import EasyOCREngine
from .preprocessor import ImagePreprocessor
from .postprocessor import TextPostprocessor
from .table_extractor import TableExtractor

__all__ = [
    'OCRManager',
    'EasyOCREngine', 
    'ImagePreprocessor',
    'TextPostprocessor',
    'TableExtractor'
]
