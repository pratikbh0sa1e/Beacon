"""
Table Extractor for OCR
Extracts tables from both digital PDFs and scanned documents
"""

import cv2
import numpy as np
from PIL import Image
import io
import fitz  # PyMuPDF
from typing import List, Dict, Tuple
import pandas as pd


class TableExtractor:
    """Extract tables from documents with structure preservation"""
    
    @staticmethod
    def extract_tables_from_pdf(file_path: str) -> List[Dict]:
        """
        Extract tables from PDF (both digital and scanned)
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            list: List of tables with metadata
        """
        doc = fitz.open(file_path)
        all_tables = []
        
        for page_num, page in enumerate(doc, start=1):
            # Try to extract tables from digital PDF first
            digital_tables = TableExtractor._extract_digital_tables(page)
            
            if digital_tables:
                for table in digital_tables:
                    table['page'] = page_num
                    table['source'] = 'digital'
                    all_tables.append(table)
            else:
                # If no digital tables found, try OCR-based extraction
                pix = page.get_pixmap(dpi=300)
                img_data = pix.tobytes("png")
                
                scanned_tables = TableExtractor._extract_tables_from_image(img_data)
                for table in scanned_tables:
                    table['page'] = page_num
                    table['source'] = 'ocr'
                    all_tables.append(table)
        
        doc.close()
        return all_tables
    
    @staticmethod
    def _extract_digital_tables(page) -> List[Dict]:
        """Extract tables from digital PDF page using text positions"""
        tables = []
        
        # Get text with positions
        text_dict = page.get_text("dict")
        blocks = text_dict.get("blocks", [])
        
        # Simple heuristic: look for aligned text blocks (table-like structure)
        # This is a basic implementation - can be enhanced with ML models
        
        # Group text by vertical position (rows)
        rows = {}
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    y_pos = int(line["bbox"][1])  # Top y-coordinate
                    if y_pos not in rows:
                        rows[y_pos] = []
                    
                    # Extract text and x-position
                    for span in line["spans"]:
                        text = span["text"].strip()
                        x_pos = span["bbox"][0]
                        if text:
                            rows[y_pos].append({
                                'text': text,
                                'x': x_pos
                            })
        
        # Detect tables by finding consecutive rows with similar column structure
        if len(rows) > 2:  # At least 3 rows for a table
            sorted_rows = sorted(rows.items())
            
            # Simple table detection: if multiple rows have similar x-positions
            table_data = []
            for y_pos, cells in sorted_rows:
                # Sort cells by x-position
                sorted_cells = sorted(cells, key=lambda c: c['x'])
                row_data = [cell['text'] for cell in sorted_cells]
                
                if len(row_data) > 1:  # At least 2 columns
                    table_data.append(row_data)
            
            if len(table_data) > 2:
                # Convert to structured format
                tables.append({
                    'data': table_data,
                    'rows': len(table_data),
                    'columns': max(len(row) for row in table_data),
                    'format': 'list_of_lists'
                })
        
        return tables
    
    @staticmethod
    def _extract_tables_from_image(image_data) -> List[Dict]:
        """
        Extract tables from scanned image using computer vision
        
        Args:
            image_data: bytes or numpy array
            
        Returns:
            list: List of detected tables
        """
        # Convert to numpy array
        if isinstance(image_data, bytes):
            img = Image.open(io.BytesIO(image_data))
            img_array = np.array(img)
        else:
            img_array = image_data
        
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Threshold the image
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Detect horizontal and vertical lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        
        horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        
        # Combine lines to find table structure
        table_mask = cv2.add(horizontal_lines, vertical_lines)
        
        # Find contours (potential tables)
        contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        tables = []
        
        for contour in contours:
            # Filter small contours
            area = cv2.contourArea(contour)
            if area < 1000:  # Minimum table size
                continue
            
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Extract table region
            table_region = gray[y:y+h, x:x+w]
            
            # Detect cells within table
            cells = TableExtractor._detect_cells(table_region, horizontal_lines[y:y+h, x:x+w], vertical_lines[y:y+h, x:x+w])
            
            if cells:
                tables.append({
                    'bbox': (x, y, w, h),
                    'cells': cells,
                    'rows': len(set(cell['row'] for cell in cells)),
                    'columns': len(set(cell['col'] for cell in cells)),
                    'format': 'cell_based'
                })
        
        return tables
    
    @staticmethod
    def _detect_cells(table_region, h_lines, v_lines) -> List[Dict]:
        """Detect individual cells in a table"""
        cells = []
        
        # Find intersection points of horizontal and vertical lines
        # This gives us cell boundaries
        
        # Simplified approach: divide table into grid
        height, width = table_region.shape
        
        # Detect row boundaries (horizontal lines)
        h_projection = np.sum(h_lines, axis=1)
        row_boundaries = np.where(h_projection > width * 0.3)[0]
        
        # Detect column boundaries (vertical lines)
        v_projection = np.sum(v_lines, axis=0)
        col_boundaries = np.where(v_projection > height * 0.3)[0]
        
        # Create cells from boundaries
        if len(row_boundaries) > 1 and len(col_boundaries) > 1:
            for i in range(len(row_boundaries) - 1):
                for j in range(len(col_boundaries) - 1):
                    y1, y2 = row_boundaries[i], row_boundaries[i + 1]
                    x1, x2 = col_boundaries[j], col_boundaries[j + 1]
                    
                    cells.append({
                        'row': i,
                        'col': j,
                        'bbox': (x1, y1, x2 - x1, y2 - y1),
                        'image': table_region[y1:y2, x1:x2]
                    })
        
        return cells
    
    @staticmethod
    def extract_table_text_with_ocr(table_data: Dict, ocr_engine) -> Dict:
        """
        Extract text from table cells using OCR
        
        Args:
            table_data: Table structure from _extract_tables_from_image
            ocr_engine: EasyOCR engine instance
            
        Returns:
            dict: Table with text content
        """
        if table_data['format'] == 'cell_based':
            # Extract text from each cell
            table_with_text = []
            
            # Group cells by row
            rows = {}
            for cell in table_data['cells']:
                row_idx = cell['row']
                if row_idx not in rows:
                    rows[row_idx] = {}
                
                # OCR the cell image
                cell_img = cell['image']
                try:
                    result = ocr_engine.readtext(cell_img, detail=False)
                    cell_text = ' '.join(result) if result else ''
                except:
                    cell_text = ''
                
                rows[row_idx][cell['col']] = cell_text
            
            # Convert to list of lists
            for row_idx in sorted(rows.keys()):
                row_data = []
                for col_idx in sorted(rows[row_idx].keys()):
                    row_data.append(rows[row_idx][col_idx])
                table_with_text.append(row_data)
            
            return {
                'data': table_with_text,
                'rows': len(table_with_text),
                'columns': max(len(row) for row in table_with_text) if table_with_text else 0,
                'bbox': table_data['bbox']
            }
        
        return table_data
    
    @staticmethod
    def format_table_as_markdown(table_data: List[List[str]]) -> str:
        """
        Format table data as Markdown
        
        Args:
            table_data: List of lists representing table rows
            
        Returns:
            str: Markdown formatted table
        """
        if not table_data:
            return ""
        
        # Ensure all rows have same number of columns
        max_cols = max(len(row) for row in table_data)
        normalized_data = []
        for row in table_data:
            normalized_row = row + [''] * (max_cols - len(row))
            normalized_data.append(normalized_row)
        
        # Create markdown table
        markdown = []
        
        # Header row
        markdown.append('| ' + ' | '.join(normalized_data[0]) + ' |')
        
        # Separator
        markdown.append('| ' + ' | '.join(['---'] * max_cols) + ' |')
        
        # Data rows
        for row in normalized_data[1:]:
            markdown.append('| ' + ' | '.join(row) + ' |')
        
        return '\n'.join(markdown)
    
    @staticmethod
    def format_table_as_csv(table_data: List[List[str]]) -> str:
        """
        Format table data as CSV
        
        Args:
            table_data: List of lists representing table rows
            
        Returns:
            str: CSV formatted table
        """
        if not table_data:
            return ""
        
        # Use pandas for proper CSV formatting
        df = pd.DataFrame(table_data[1:], columns=table_data[0] if table_data else None)
        return df.to_csv(index=False)
    
    @staticmethod
    def format_table_as_html(table_data: List[List[str]]) -> str:
        """
        Format table data as HTML
        
        Args:
            table_data: List of lists representing table rows
            
        Returns:
            str: HTML formatted table
        """
        if not table_data:
            return ""
        
        html = ['<table border="1">']
        
        # Header row
        html.append('  <thead>')
        html.append('    <tr>')
        for cell in table_data[0]:
            html.append(f'      <th>{cell}</th>')
        html.append('    </tr>')
        html.append('  </thead>')
        
        # Data rows
        html.append('  <tbody>')
        for row in table_data[1:]:
            html.append('    <tr>')
            for cell in row:
                html.append(f'      <td>{cell}</td>')
            html.append('    </tr>')
        html.append('  </tbody>')
        
        html.append('</table>')
        
        return '\n'.join(html)
