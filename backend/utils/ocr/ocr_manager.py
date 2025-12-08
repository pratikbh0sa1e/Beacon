"""
OCR Manager - Orchestrates the entire OCR pipeline
"""

import fitz  # PyMuPDF
from PIL import Image
import io
from typing import Dict, List, Tuple
import time

from .easyocr_engine import EasyOCREngine
from .preprocessor import ImagePreprocessor
from .postprocessor import TextPostprocessor
from .table_extractor import TableExtractor


class OCRManager:
    """Manages the complete OCR extraction pipeline"""
    
    def __init__(self, languages=['en', 'hi']):
        """
        Initialize OCR Manager
        
        Args:
            languages: List of language codes for OCR
        """
        self.ocr_engine = EasyOCREngine(languages=languages)
        self.preprocessor = ImagePreprocessor()
        self.postprocessor = TextPostprocessor()
        self.table_extractor = TableExtractor()
        
    def extract_from_pdf(self, file_path: str, preprocessing_level='medium', extract_tables=True) -> Dict:
        """
        Extract text from PDF with per-page OCR detection
        Handles mixed documents (text pages + scanned pages)
        Includes rotation correction and table extraction
        
        Args:
            file_path: Path to PDF file
            preprocessing_level: 'light', 'medium', 'heavy'
            extract_tables: Whether to extract tables separately
            
        Returns:
            dict: {
                'text': str,
                'confidence': float,
                'pages_processed': int,
                'pages_with_ocr': list,
                'pages_with_text': list,
                'extraction_time': float,
                'needs_review': bool,
                'ocr_details': dict,
                'tables': list (if extract_tables=True)
            }
        """
        start_time = time.time()
        
        doc = fitz.open(file_path)
        all_text = []
        pages_with_ocr = []
        pages_with_text = []
        confidence_scores = []
        ocr_details = {
            'total_pages': len(doc),
            'scanned_pages': 0,
            'text_pages': 0,
            'preprocessing_applied': [],
            'rotation_corrections': []
        }
        
        # Extract tables later (after doc is closed) to avoid conflicts
        tables = []
        
        for page_num, page in enumerate(doc, start=1):
            # Try to extract text directly
            page_text = page.get_text().strip()
            
            if page_text:
                # Page has digital text
                all_text.append(page_text)
                pages_with_text.append(page_num)
                ocr_details['text_pages'] += 1
                confidence_scores.append(1.0)  # Digital text = 100% confidence
            else:
                # Page is scanned - apply OCR with rotation correction
                print(f"Page {page_num} is scanned, applying OCR...")
                
                # Convert page to image
                pix = page.get_pixmap(dpi=300)  # Higher DPI for better OCR
                img_data = pix.tobytes("png")
                
                # Step 1: Detect and correct rotation
                try:
                    corrected_img, rotation_angle = self.preprocessor.detect_and_correct_rotation(img_data)
                    if rotation_angle != 0:
                        print(f"  → Corrected rotation: {rotation_angle}°")
                        ocr_details['rotation_corrections'].append({
                            'page': page_num,
                            'angle': rotation_angle
                        })
                    img_data = corrected_img
                except Exception as e:
                    print(f"  → Rotation correction failed: {str(e)}")
                
                # Step 2: Preprocess image
                processed_img, preprocessing_applied = self.preprocessor.preprocess(
                    img_data, 
                    preprocessing_level=preprocessing_level
                )
                
                # Step 3: Extract text with OCR
                ocr_result = self.ocr_engine.extract_text(processed_img, detail=True)
                
                if ocr_result['text']:
                    all_text.append(ocr_result['text'])
                    confidence_scores.append(ocr_result['confidence'])
                    pages_with_ocr.append(page_num)
                    ocr_details['scanned_pages'] += 1
                    ocr_details['preprocessing_applied'].append({
                        'page': page_num,
                        'methods': preprocessing_applied
                    })
                else:
                    # No text found even with OCR
                    all_text.append(f"[Page {page_num}: No text detected]")
                    confidence_scores.append(0.0)
                    pages_with_ocr.append(page_num)
                    ocr_details['scanned_pages'] += 1
        
        total_pages = len(doc)
        doc.close()
        
        # Extract tables AFTER closing the document to avoid conflicts
        if extract_tables:
            try:
                tables = self.table_extractor.extract_tables_from_pdf(file_path)
                ocr_details['tables_found'] = len(tables)
            except Exception as e:
                print(f"Table extraction failed: {str(e)}")
                ocr_details['tables_found'] = 0
        
        # Combine all text
        combined_text = "\n\n".join(all_text)
        
        # Clean up text
        cleaned_text = self.postprocessor.clean_text(combined_text)
        
        # Calculate overall confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Calculate quality and determine if review needed
        quality_metrics = self.postprocessor.calculate_text_quality(cleaned_text, avg_confidence)
        
        extraction_time = time.time() - start_time
        
        result = {
            'text': cleaned_text,
            'confidence': avg_confidence,
            'pages_processed': total_pages,
            'pages_with_ocr': pages_with_ocr,
            'pages_with_text': pages_with_text,
            'extraction_time': extraction_time,
            'needs_review': quality_metrics['needs_review'],
            'quality_score': quality_metrics['quality_score'],
            'issues': quality_metrics['issues'],
            'ocr_details': ocr_details
        }
        
        # Add tables if extracted
        if extract_tables and tables:
            result['tables'] = tables
            # Format tables as markdown and append to text
            table_text = "\n\n## Extracted Tables\n\n"
            for idx, table in enumerate(tables, 1):
                table_text += f"\n### Table {idx} (Page {table.get('page', 'Unknown')})\n\n"
                if 'data' in table:
                    table_text += self.table_extractor.format_table_as_markdown(table['data'])
                table_text += "\n"
            result['text'] += table_text
        
        return result
    
    def extract_from_image(self, file_path: str, preprocessing_level='medium', extract_tables=True) -> Dict:
        """
        Extract text from image file with rotation correction and table extraction
        
        Args:
            file_path: Path to image file
            preprocessing_level: 'light', 'medium', 'heavy'
            extract_tables: Whether to extract tables separately
            
        Returns:
            dict: Extraction results with confidence and metadata
        """
        start_time = time.time()
        
        # Load image
        with open(file_path, 'rb') as f:
            img_data = f.read()
        
        # Step 1: Detect and correct rotation
        rotation_angle = 0
        try:
            corrected_img, rotation_angle = self.preprocessor.detect_and_correct_rotation(img_data)
            if rotation_angle != 0:
                print(f"Corrected rotation: {rotation_angle}°")
            img_data = corrected_img
        except Exception as e:
            print(f"Rotation correction failed: {str(e)}")
        
        # Step 2: Preprocess image
        processed_img, preprocessing_applied = self.preprocessor.preprocess(
            img_data,
            preprocessing_level=preprocessing_level
        )
        
        # Step 3: Extract tables if requested
        tables = []
        if extract_tables:
            try:
                tables = self.table_extractor._extract_tables_from_image(img_data)
                # Extract text from table cells
                for table in tables:
                    table_with_text = self.table_extractor.extract_table_text_with_ocr(
                        table,
                        self.ocr_engine.reader
                    )
                    table.update(table_with_text)
            except Exception as e:
                print(f"Table extraction failed: {str(e)}")
        
        # Step 4: Extract text with OCR
        ocr_result = self.ocr_engine.extract_text(processed_img, detail=True)
        
        # Clean text
        cleaned_text = self.postprocessor.clean_text(ocr_result['text'])
        
        # Calculate quality
        quality_metrics = self.postprocessor.calculate_text_quality(
            cleaned_text,
            ocr_result['confidence']
        )
        
        extraction_time = time.time() - start_time
        
        result = {
            'text': cleaned_text,
            'confidence': ocr_result['confidence'],
            'language_detected': ocr_result['language_detected'],
            'total_lines': ocr_result['total_lines'],
            'extraction_time': extraction_time,
            'needs_review': quality_metrics['needs_review'],
            'quality_score': quality_metrics['quality_score'],
            'issues': quality_metrics['issues'],
            'preprocessing_applied': preprocessing_applied,
            'rotation_corrected': rotation_angle,
            'details': ocr_result['details']
        }
        
        # Add tables if extracted
        if extract_tables and tables:
            result['tables'] = tables
            # Format tables as markdown and append to text
            table_text = "\n\n## Extracted Tables\n\n"
            for idx, table in enumerate(tables, 1):
                table_text += f"\n### Table {idx}\n\n"
                if 'data' in table:
                    table_text += self.table_extractor.format_table_as_markdown(table['data'])
                table_text += "\n"
            result['text'] += table_text
        
        return result
    
    def extract_text(self, file_path: str, file_type: str, preprocessing_level='medium') -> Dict:
        """
        Main extraction method - routes to appropriate handler
        
        Args:
            file_path: Path to file
            file_type: File extension (pdf, jpg, png, etc.)
            preprocessing_level: 'light', 'medium', 'heavy'
            
        Returns:
            dict: Extraction results
        """
        file_type = file_type.lower()
        
        if file_type == 'pdf':
            return self.extract_from_pdf(file_path, preprocessing_level)
        elif file_type in ['jpg', 'jpeg', 'png', 'tiff', 'bmp']:
            return self.extract_from_image(file_path, preprocessing_level)
        else:
            raise ValueError(f"Unsupported file type for OCR: {file_type}")
