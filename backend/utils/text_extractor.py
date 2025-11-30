import fitz
import easyocr
from docx import Document as DocxDocument
from pptx import Presentation
from PIL import Image
import io
import os
from pptx import Presentation
reader = easyocr.Reader(['en', 'hi'])

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF (fitz)"""
    text = ""
    doc = fitz.open(file_path)
    
    for page in doc:
        text += page.get_text()
        
        # If no text found, try OCR on images
        if not text.strip():
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            ocr_result = reader.readtext(img_data, detail=0)
            text += " ".join(ocr_result)
    
    doc.close()
    return text.strip()

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX"""
    doc = DocxDocument(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text.strip()

def extract_text_from_image(file_path: str) -> str:
    """Extract text from image using EasyOCR"""
    result = reader.readtext(file_path, detail=0)
    return " ".join(result)

def extract_text_from_pptx(file_path: str) -> str:
    """Extract text from PPTX"""
    prs = Presentation(file_path)
    text_parts = []
    
    for slide_num, slide in enumerate(prs.slides, 1):
        slide_text = []
        
        # Extract text from shapes
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text:
                slide_text.append(shape.text)
            
            # Extract text from tables
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        if cell.text:
                            slide_text.append(cell.text)
        
        # Add slide separator
        if slide_text:
            text_parts.append(f"--- Slide {slide_num} ---\n" + "\n".join(slide_text))
    
    return "\n\n".join(text_parts).strip()


def extract_text(file_path: str, file_type: str) -> str:
    """Main extraction function"""
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "docx":
        return extract_text_from_docx(file_path)
    elif file_type == "pptx":
        return extract_text_from_pptx(file_path)
    elif file_type in ["jpeg", "jpg", "png"]:
        return extract_text_from_image(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
