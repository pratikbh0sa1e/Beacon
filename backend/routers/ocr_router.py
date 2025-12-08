"""
OCR Router - Endpoints for OCR review and management
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from backend.database import get_db, OCRResult, Document, User
from backend.routers.auth_router import get_current_user

router = APIRouter(prefix="/ocr", tags=["ocr"])


# Pydantic models
class OCRReviewRequest(BaseModel):
    corrected_text: str
    notes: Optional[str] = None


class OCRResultResponse(BaseModel):
    id: int
    document_id: int
    document_filename: str
    engine_used: str
    confidence_score: Optional[float]
    extraction_time: Optional[float]
    language_detected: Optional[str]
    needs_review: bool
    quality_score: Optional[float]
    issues: Optional[List[str]]
    pages_with_ocr: Optional[List[int]]
    pages_with_text: Optional[List[int]]
    processed_result: Optional[str]
    reviewed_by: Optional[int]
    reviewed_at: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/pending-review", response_model=List[OCRResultResponse])
def get_pending_ocr_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all OCR results that need manual review
    Only accessible by admins and document officers
    """
    # Check permissions
    allowed_roles = ['developer', 'ministry_admin', 'university_admin', 'document_officer']
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Not authorized to review OCR results")
    
    # Query OCR results that need review
    query = db.query(OCRResult).filter(OCRResult.needs_review == True)
    
    # Filter by institution for university admins and document officers
    if current_user.role in ['university_admin', 'document_officer']:
        query = query.join(Document).filter(
            Document.institution_id == current_user.institution_id
        )
    
    ocr_results = query.order_by(OCRResult.created_at.desc()).all()
    
    # Format response
    response = []
    for ocr in ocr_results:
        document = db.query(Document).filter(Document.id == ocr.document_id).first()
        response.append({
            'id': ocr.id,
            'document_id': ocr.document_id,
            'document_filename': document.filename if document else 'Unknown',
            'engine_used': ocr.engine_used,
            'confidence_score': ocr.confidence_score,
            'extraction_time': ocr.extraction_time,
            'language_detected': ocr.language_detected,
            'needs_review': ocr.needs_review,
            'quality_score': ocr.quality_score,
            'issues': ocr.issues if ocr.issues else [],
            'pages_with_ocr': ocr.pages_with_ocr if ocr.pages_with_ocr else [],
            'pages_with_text': ocr.pages_with_text if ocr.pages_with_text else [],
            'processed_result': ocr.processed_result,
            'reviewed_by': ocr.reviewed_by,
            'reviewed_at': ocr.reviewed_at.isoformat() if ocr.reviewed_at else None,
            'created_at': ocr.created_at.isoformat()
        })
    
    return response


@router.get("/document/{document_id}", response_model=OCRResultResponse)
def get_ocr_result_by_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get OCR result for a specific document"""
    
    # Check if document exists and user has access
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check access permissions
    if current_user.role not in ['developer', 'ministry_admin']:
        if current_user.role in ['university_admin', 'document_officer', 'student']:
            if document.institution_id != current_user.institution_id:
                raise HTTPException(status_code=403, detail="Not authorized to access this document")
    
    # Get OCR result
    ocr_result = db.query(OCRResult).filter(OCRResult.document_id == document_id).first()
    if not ocr_result:
        raise HTTPException(status_code=404, detail="No OCR result found for this document")
    
    return {
        'id': ocr_result.id,
        'document_id': ocr_result.document_id,
        'document_filename': document.filename,
        'engine_used': ocr_result.engine_used,
        'confidence_score': ocr_result.confidence_score,
        'extraction_time': ocr_result.extraction_time,
        'language_detected': ocr_result.language_detected,
        'needs_review': ocr_result.needs_review,
        'quality_score': ocr_result.quality_score,
        'issues': ocr_result.issues if ocr_result.issues else [],
        'pages_with_ocr': ocr_result.pages_with_ocr if ocr_result.pages_with_ocr else [],
        'pages_with_text': ocr_result.pages_with_text if ocr_result.pages_with_text else [],
        'processed_result': ocr_result.processed_result,
        'reviewed_by': ocr_result.reviewed_by,
        'reviewed_at': ocr_result.reviewed_at.isoformat() if ocr_result.reviewed_at else None,
        'created_at': ocr_result.created_at.isoformat()
    }


@router.post("/review/{ocr_id}")
def review_ocr_result(
    ocr_id: int,
    review_data: OCRReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit manual review/correction for OCR result
    Updates the document's extracted text with corrected version
    """
    # Check permissions
    allowed_roles = ['developer', 'ministry_admin', 'university_admin', 'document_officer']
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Not authorized to review OCR results")
    
    # Get OCR result
    ocr_result = db.query(OCRResult).filter(OCRResult.id == ocr_id).first()
    if not ocr_result:
        raise HTTPException(status_code=404, detail="OCR result not found")
    
    # Get associated document
    document = db.query(Document).filter(Document.id == ocr_result.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Associated document not found")
    
    # Check institution access for non-admin roles
    if current_user.role in ['university_admin', 'document_officer']:
        if document.institution_id != current_user.institution_id:
            raise HTTPException(status_code=403, detail="Not authorized to review this document")
    
    # Update OCR result
    ocr_result.processed_result = review_data.corrected_text
    ocr_result.needs_review = False
    ocr_result.reviewed_by = current_user.id
    from datetime import datetime
    ocr_result.reviewed_at = datetime.utcnow()
    
    # Update document's extracted text
    document.extracted_text = review_data.corrected_text
    document.ocr_status = 'completed'
    
    # Commit changes
    db.commit()
    db.refresh(ocr_result)
    db.refresh(document)
    
    return {
        "message": "OCR result reviewed successfully",
        "ocr_id": ocr_id,
        "document_id": document.id,
        "reviewed_by": current_user.name
    }


@router.post("/reprocess/{document_id}")
def reprocess_document_ocr(
    document_id: int,
    preprocessing_level: str = Body('heavy', embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Re-run OCR extraction on a document with different settings
    Useful when initial extraction had low confidence
    """
    # Check permissions
    allowed_roles = ['developer', 'ministry_admin', 'university_admin', 'document_officer']
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Not authorized to reprocess documents")
    
    # Get document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check institution access
    if current_user.role in ['university_admin', 'document_officer']:
        if document.institution_id != current_user.institution_id:
            raise HTTPException(status_code=403, detail="Not authorized to reprocess this document")
    
    # Check if document is scanned
    if not document.is_scanned:
        raise HTTPException(status_code=400, detail="Document is not a scanned document")
    
    # Validate preprocessing level
    if preprocessing_level not in ['light', 'medium', 'heavy']:
        raise HTTPException(status_code=400, detail="Invalid preprocessing level. Must be 'light', 'medium', or 'heavy'")
    
    try:
        from backend.utils.ocr import OCRManager
        from datetime import datetime
        
        # Run OCR extraction
        ocr_manager = OCRManager(languages=['en', 'hi'])
        result = ocr_manager.extract_text(
            document.file_path,
            document.file_type,
            preprocessing_level=preprocessing_level
        )
        
        # Update or create OCR result
        ocr_result = db.query(OCRResult).filter(OCRResult.document_id == document_id).first()
        
        if ocr_result:
            # Update existing
            ocr_result.confidence_score = result.get('confidence')
            ocr_result.extraction_time = result.get('extraction_time')
            ocr_result.language_detected = result.get('language_detected')
            ocr_result.preprocessing_applied = result.get('preprocessing_applied') or result.get('ocr_details', {}).get('preprocessing_applied')
            ocr_result.processed_result = result['text']
            ocr_result.needs_review = result.get('needs_review', False)
            ocr_result.quality_score = result.get('quality_score')
            ocr_result.issues = result.get('issues', [])
            ocr_result.pages_with_ocr = result.get('pages_with_ocr')
            ocr_result.pages_with_text = result.get('pages_with_text')
        else:
            # Create new
            ocr_result = OCRResult(
                document_id=document_id,
                engine_used='easyocr',
                confidence_score=result.get('confidence'),
                extraction_time=result.get('extraction_time'),
                language_detected=result.get('language_detected'),
                preprocessing_applied=result.get('preprocessing_applied') or result.get('ocr_details', {}).get('preprocessing_applied'),
                processed_result=result['text'],
                needs_review=result.get('needs_review', False),
                quality_score=result.get('quality_score'),
                issues=result.get('issues', []),
                pages_with_ocr=result.get('pages_with_ocr'),
                pages_with_text=result.get('pages_with_text')
            )
            db.add(ocr_result)
        
        # Update document
        document.extracted_text = result['text']
        document.ocr_confidence = result.get('confidence')
        document.ocr_status = 'needs_review' if result.get('needs_review') else 'completed'
        
        db.commit()
        db.refresh(document)
        
        return {
            "message": "Document reprocessed successfully",
            "document_id": document_id,
            "confidence": result.get('confidence'),
            "needs_review": result.get('needs_review'),
            "preprocessing_level": preprocessing_level
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"OCR reprocessing failed: {str(e)}")


@router.get("/stats")
def get_ocr_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get OCR statistics"""
    
    # Only admins can view stats
    if current_user.role not in ['developer', 'ministry_admin', 'university_admin']:
        raise HTTPException(status_code=403, detail="Not authorized to view OCR statistics")
    
    # Base query
    query = db.query(OCRResult)
    
    # Filter by institution for university admins
    if current_user.role == 'university_admin':
        query = query.join(Document).filter(
            Document.institution_id == current_user.institution_id
        )
    
    # Calculate stats
    total_ocr_documents = query.count()
    needs_review_count = query.filter(OCRResult.needs_review == True).count()
    avg_confidence = db.query(db.func.avg(OCRResult.confidence_score)).scalar() or 0.0
    
    # Rotation stats
    rotation_corrections = query.filter(OCRResult.rotation_corrected != None).filter(OCRResult.rotation_corrected != 0).count()
    
    # Table stats
    documents_with_tables = query.filter(OCRResult.tables_extracted != None).count()
    
    # Language distribution
    language_stats = {}
    for ocr in query.all():
        lang = ocr.language_detected or 'unknown'
        language_stats[lang] = language_stats.get(lang, 0) + 1
    
    return {
        "total_ocr_documents": total_ocr_documents,
        "needs_review": needs_review_count,
        "average_confidence": round(float(avg_confidence), 2),
        "language_distribution": language_stats,
        "review_completion_rate": round((total_ocr_documents - needs_review_count) / total_ocr_documents * 100, 1) if total_ocr_documents > 0 else 0,
        "rotation_corrections": rotation_corrections,
        "documents_with_tables": documents_with_tables
    }


@router.get("/tables/{document_id}")
def get_document_tables(
    document_id: int,
    format: str = 'json',  # json, markdown, csv, html
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get extracted tables from a document
    
    Args:
        document_id: Document ID
        format: Output format (json, markdown, csv, html)
    """
    # Check if document exists and user has access
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check access permissions
    if current_user.role not in ['developer', 'ministry_admin']:
        if current_user.role in ['university_admin', 'document_officer', 'student']:
            if document.institution_id != current_user.institution_id:
                raise HTTPException(status_code=403, detail="Not authorized to access this document")
    
    # Get OCR result with tables
    ocr_result = db.query(OCRResult).filter(OCRResult.document_id == document_id).first()
    if not ocr_result or not ocr_result.tables_extracted:
        raise HTTPException(status_code=404, detail="No tables found for this document")
    
    tables = ocr_result.tables_extracted
    
    # Format tables based on requested format
    if format == 'json':
        return {
            "document_id": document_id,
            "document_filename": document.filename,
            "tables_count": len(tables),
            "tables": tables
        }
    elif format == 'markdown':
        from backend.utils.ocr import TableExtractor
        formatted_tables = []
        for idx, table in enumerate(tables, 1):
            if 'data' in table:
                formatted_tables.append({
                    'table_number': idx,
                    'page': table.get('page', 'Unknown'),
                    'markdown': TableExtractor.format_table_as_markdown(table['data'])
                })
        return {
            "document_id": document_id,
            "document_filename": document.filename,
            "format": "markdown",
            "tables": formatted_tables
        }
    elif format == 'csv':
        from backend.utils.ocr import TableExtractor
        formatted_tables = []
        for idx, table in enumerate(tables, 1):
            if 'data' in table:
                formatted_tables.append({
                    'table_number': idx,
                    'page': table.get('page', 'Unknown'),
                    'csv': TableExtractor.format_table_as_csv(table['data'])
                })
        return {
            "document_id": document_id,
            "document_filename": document.filename,
            "format": "csv",
            "tables": formatted_tables
        }
    elif format == 'html':
        from backend.utils.ocr import TableExtractor
        formatted_tables = []
        for idx, table in enumerate(tables, 1):
            if 'data' in table:
                formatted_tables.append({
                    'table_number': idx,
                    'page': table.get('page', 'Unknown'),
                    'html': TableExtractor.format_table_as_html(table['data'])
                })
        return {
            "document_id": document_id,
            "document_filename": document.filename,
            "format": "html",
            "tables": formatted_tables
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use: json, markdown, csv, or html")
