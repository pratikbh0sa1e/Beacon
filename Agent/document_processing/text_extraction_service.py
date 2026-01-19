"""
Text Extraction Service with Intelligent OCR Detection

This service handles text extraction from PDFs with automatic quality assessment
and OCR fallback for image-based documents.
"""
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import fitz  # PyMuPDF
from PIL import Image
import io
import re

logger = logging.getLogger(__name__)

# Lazy load EasyOCR to avoid startup overhead
_ocr_reader = None


def get_ocr_reader():
    """Get cloud OCR service for text extraction"""
    try:
        from backend.utils.cloud_ocr_service import get_ocr_service
        return get_ocr_service()
    except ImportError as e:
        logger.error(f"Failed to import cloud OCR service: {str(e)}")
        return None


class TextExtractionService:
    """
    Handles text extraction from PDFs with intelligent OCR fallback
    
    Features:
    - Standard text extraction using PyMuPDF
    - Quality assessment based on text length and character distribution
    - Automatic OCR fallback for low-quality extractions
    - Support for English and Hindi languages
    """
    
    def __init__(
        self,
        quality_threshold: int = 100,  # min chars per page
        char_ratio_threshold: float = 0.7,  # min alphanumeric ratio
        max_pages_for_ocr: int = 50,  # limit OCR to first N pages
        enable_ocr: bool = True
    ):
        """
        Initialize text extraction service
        
        Args:
            quality_threshold: Minimum characters per page for acceptable quality
            char_ratio_threshold: Minimum ratio of alphanumeric characters
            max_pages_for_ocr: Maximum pages to process with OCR
            enable_ocr: Whether to enable OCR fallback
        """
        self.quality_threshold = quality_threshold
        self.char_ratio_threshold = char_ratio_threshold
        self.max_pages_for_ocr = max_pages_for_ocr
        self.enable_ocr = enable_ocr
        
        logger.info(
            f"TextExtractionService initialized: "
            f"quality_threshold={quality_threshold}, "
            f"char_ratio_threshold={char_ratio_threshold}, "
            f"max_pages_for_ocr={max_pages_for_ocr}, "
            f"enable_ocr={enable_ocr}"
        )
    
    def extract_text(self, pdf_path: str, progress_callback=None) -> Dict[str, Any]:
        """
        Extract text from PDF with automatic quality assessment and OCR fallback
        
        Args:
            pdf_path: Path to PDF file
            progress_callback: Optional callback function(stage, message) for progress updates
        
        Returns:
            Dict containing:
                - text: Extracted text
                - quality_score: Quality assessment score
                - extraction_method: 'standard' | 'ocr' | 'hybrid'
                - pages_processed: Number of pages processed
                - chars_per_page: Average characters per page
                - alphanumeric_ratio: Ratio of alphanumeric characters
                - ocr_triggered: Whether OCR was used
                - processing_time_ms: Processing time in milliseconds
        """
        start_time = datetime.utcnow()
        
        try:
            if progress_callback:
                progress_callback('extraction', f'Opening PDF: {os.path.basename(pdf_path)}')
            
            # Step 1: Try standard text extraction
            logger.info(f"Starting standard text extraction for: {pdf_path}")
            standard_result = self._extract_standard(pdf_path, progress_callback)
            
            # Step 2: Assess quality
            if progress_callback:
                progress_callback('assessment', 'Assessing text quality...')
            
            quality = self.assess_quality(
                standard_result['text'],
                standard_result['pages_processed']
            )
            
            logger.info(
                f"Quality assessment: score={quality['score']:.2f}, "
                f"chars_per_page={quality['chars_per_page']:.1f}, "
                f"alphanumeric_ratio={quality['alphanumeric_ratio']:.2f}, "
                f"is_acceptable={quality['is_acceptable']}"
            )
            
            # Step 3: Decide if OCR is needed
            if quality['is_acceptable'] or not self.enable_ocr:
                # Quality is good, use standard extraction
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                return {
                    'text': standard_result['text'],
                    'quality_score': quality['score'],
                    'extraction_method': 'standard',
                    'pages_processed': standard_result['pages_processed'],
                    'chars_per_page': quality['chars_per_page'],
                    'alphanumeric_ratio': quality['alphanumeric_ratio'],
                    'ocr_triggered': False,
                    'processing_time_ms': int(processing_time)
                }
            
            # Step 4: Quality is low, try OCR
            logger.info(f"Quality below threshold, triggering OCR for: {pdf_path}")
            
            if progress_callback:
                progress_callback('ocr', f'Applying OCR to improve text quality...')
            
            ocr_result = self._extract_with_ocr(pdf_path, progress_callback)
            
            # Assess OCR quality
            ocr_quality = self.assess_quality(
                ocr_result['text'],
                ocr_result['pages_processed']
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                f"OCR extraction complete: "
                f"chars_per_page={ocr_quality['chars_per_page']:.1f}, "
                f"processing_time={processing_time:.0f}ms"
            )
            
            return {
                'text': ocr_result['text'],
                'quality_score': ocr_quality['score'],
                'extraction_method': 'ocr',
                'pages_processed': ocr_result['pages_processed'],
                'chars_per_page': ocr_quality['chars_per_page'],
                'alphanumeric_ratio': ocr_quality['alphanumeric_ratio'],
                'ocr_triggered': True,
                'processing_time_ms': int(processing_time)
            }
            
        except Exception as e:
            logger.error(f"Text extraction failed for {pdf_path}: {str(e)}")
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                'text': '',
                'quality_score': 0.0,
                'extraction_method': 'failed',
                'pages_processed': 0,
                'chars_per_page': 0.0,
                'alphanumeric_ratio': 0.0,
                'ocr_triggered': False,
                'processing_time_ms': int(processing_time),
                'error': str(e)
            }
    
    def _extract_standard(self, pdf_path: str, progress_callback=None) -> Dict[str, Any]:
        """
        Extract text using standard PyMuPDF extraction
        
        Args:
            pdf_path: Path to PDF file
            progress_callback: Optional callback for progress updates
        
        Returns:
            Dict with 'text' and 'pages_processed'
        """
        text_parts = []
        pages_processed = 0
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            for page_num in range(total_pages):
                page = doc[page_num]
                page_text = page.get_text()
                text_parts.append(page_text)
                pages_processed += 1
                
                if progress_callback and page_num % 5 == 0:
                    progress_callback(
                        'extraction',
                        f'Extracting text: page {page_num + 1}/{total_pages}'
                    )
            
            doc.close()
            
            full_text = '\n'.join(text_parts)
            
            return {
                'text': full_text,
                'pages_processed': pages_processed
            }
            
        except Exception as e:
            logger.error(f"Standard extraction failed: {str(e)}")
            raise
    
    def _extract_with_ocr(self, pdf_path: str, progress_callback=None) -> Dict[str, Any]:
        """
        Extract text using EasyOCR
        
        Args:
            pdf_path: Path to PDF file
            progress_callback: Optional callback for progress updates
        
        Returns:
            Dict with 'text' and 'pages_processed'
        """
        try:
            # Get OCR reader (lazy initialization)
            reader = get_ocr_reader()
            
            # Convert PDF pages to images
            doc = fitz.open(pdf_path)
            total_pages = min(len(doc), self.max_pages_for_ocr)
            
            text_parts = []
            pages_processed = 0
            
            for page_num in range(total_pages):
                if progress_callback:
                    progress_callback(
                        'ocr',
                        f'OCR processing: page {page_num + 1}/{total_pages}'
                    )
                
                # Convert page to image
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                img_data = pix.tobytes("png")
                
                # Use cloud OCR service
                try:
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                        temp_file.write(img_data)
                        temp_file.flush()
                        
                        ocr_result = reader.extract_text_from_image(temp_file.name)
                        page_text = ocr_result.get("text", "")
                        text_parts.append(page_text)
                        pages_processed += 1
                        
                        os.unlink(temp_file.name)
                except Exception as e:
                    logger.error(f"OCR failed for page {page_num + 1}: {e}")
                    # Continue with next page
            
            doc.close()
            
            full_text = '\n'.join(text_parts)
            
            return {
                'text': full_text,
                'pages_processed': pages_processed
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            raise
    
    def assess_quality(self, text: str, page_count: int) -> Dict[str, Any]:
        """
        Assess the quality of extracted text
        
        Args:
            text: Extracted text
            page_count: Number of pages processed
        
        Returns:
            Dict containing:
                - score: Overall quality score (0-100)
                - chars_per_page: Average characters per page
                - alphanumeric_ratio: Ratio of alphanumeric characters
                - is_acceptable: Whether quality meets threshold
        """
        if not text or page_count == 0:
            return {
                'score': 0.0,
                'chars_per_page': 0.0,
                'alphanumeric_ratio': 0.0,
                'is_acceptable': False
            }
        
        # Calculate characters per page
        total_chars = len(text)
        chars_per_page = total_chars / page_count
        
        # Calculate alphanumeric ratio
        alphanumeric_chars = sum(1 for c in text if c.isalnum())
        alphanumeric_ratio = alphanumeric_chars / total_chars if total_chars > 0 else 0.0
        
        # Determine if quality is acceptable
        is_acceptable = (
            chars_per_page >= self.quality_threshold and
            alphanumeric_ratio >= self.char_ratio_threshold
        )
        
        # Calculate overall score (0-100)
        # Weight: 60% chars_per_page, 40% alphanumeric_ratio
        chars_score = min(100, (chars_per_page / self.quality_threshold) * 60)
        ratio_score = (alphanumeric_ratio / self.char_ratio_threshold) * 40
        overall_score = chars_score + ratio_score
        
        return {
            'score': round(overall_score, 2),
            'chars_per_page': round(chars_per_page, 2),
            'alphanumeric_ratio': round(alphanumeric_ratio, 3),
            'is_acceptable': is_acceptable
        }
    
    def convert_pdf_to_images(self, pdf_path: str, max_pages: Optional[int] = None) -> List[Image.Image]:
        """
        Convert PDF pages to PIL Images
        
        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to convert (None for all)
        
        Returns:
            List of PIL Image objects
        """
        images = []
        
        try:
            doc = fitz.open(pdf_path)
            page_limit = min(len(doc), max_pages) if max_pages else len(doc)
            
            for page_num in range(page_limit):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
            
            doc.close()
            
            return images
            
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {str(e)}")
            raise
