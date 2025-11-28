from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List,Optional
import os
import shutil
import re
import glob
from datetime import datetime
from backend.routers.auth_router import get_current_user
from backend.database import get_db, Document, DocumentMetadata, User
from backend.utils.text_extractor import extract_text
from backend.utils.supabase_storage import upload_to_supabase
from Agent.metadata.extractor import MetadataExtractor

router = APIRouter(tags=["documents"])

UPLOAD_DIR = "backend/files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize metadata extractor
metadata_extractor = MetadataExtractor()

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for Supabase storage"""
    # Remove or replace characters that Supabase doesn't allow
    # Keep only alphanumeric, dots, hyphens, and underscores
    name, ext = os.path.splitext(filename)
    # Replace spaces and special chars with underscores
    safe_name = re.sub(r'[^\w\-.]', '_', name)
    # Remove consecutive underscores
    safe_name = re.sub(r'_+', '_', safe_name)
    return f"{safe_name}{ext}"

def extract_metadata_background(document_id: int, text: str, filename: str, db_session):
    """Background task to extract metadata"""
    try:
        print(f"Extracting metadata for doc {document_id}...")
        metadata = metadata_extractor.extract_metadata(text, filename)
        
        # Create or update metadata record
        doc_metadata = DocumentMetadata(
            document_id=document_id,
            title=metadata.get('title'),
            department=metadata.get('department'),
            document_type=metadata.get('document_type'),
            date_published=metadata.get('date_published'),
            keywords=metadata.get('keywords'),
            summary=metadata.get('summary'),
            key_topics=metadata.get('key_topics'),
            entities=metadata.get('entities'),
            bm25_keywords=metadata.get('bm25_keywords'),
            text_length=metadata.get('text_length'),
            embedding_status='uploaded',
            metadata_status='ready'
        )
        
        db_session.add(doc_metadata)
        db_session.commit()
        print(f"Metadata extracted for doc {document_id}: {metadata.get('title')}")
        
    except Exception as e:
        print(f"Error extracting metadata for doc {document_id}: {str(e)}")
        db_session.rollback()


@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    source_department: str = "Unknown"
):
    """
    Upload documents (PDF, DOCX, JPEG, PNG), extract text, 
    store in Supabase S3 and save metadata to database
    """
    results = []
    
    for file in files:
        try:
            # Validate file type
            file_ext = file.filename.split(".")[-1].lower()
            if file_ext not in ["pdf", "docx", "jpeg", "jpg", "png"]:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"Unsupported file type: {file_ext}"
                })
                continue
            
            # Save file locally with sanitized filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = sanitize_filename(file.filename)
            unique_filename = f"{timestamp}_{safe_filename}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Extract text
            extracted_text = extract_text(file_path, file_ext)
            
            # Check text size (PostgreSQL text field limit is ~1GB, but let's be safe)
            # If text is too large, we'll still store it but log a warning
            text_size_mb = len(extracted_text.encode('utf-8')) / (1024 * 1024)
            if text_size_mb > 10:  # Warn if over 10MB
                print(f"Warning: Large text extracted ({text_size_mb:.2f}MB) from {file.filename}")
            
            # Upload to Supabase S3
            s3_url = upload_to_supabase(file_path, unique_filename)
            
            # Save to database with retry logic
            try:
                doc = Document(
                    filename=file.filename,
                    file_type=file_ext,
                    file_path=file_path,
                    s3_url=s3_url,
                    extracted_text=extracted_text,
                    uploader_id=current_user.id, # <--- SAVE USER ID
                    institution_id=current_user.institution_id, # <--- SAVE INSTITUTION
                    visibility_level="public" # Default visibility
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)
            except Exception as db_error:
                db.rollback()
                # Retry once
                try:
                    db.add(doc)
                    db.commit()
                    db.refresh(doc)
                except Exception as retry_error:
                    raise Exception(f"Database error after retry: {str(retry_error)}")
            
            # Trigger background metadata extraction
            if background_tasks:
                # Create a new session for background task
                from backend.database import SessionLocal
                bg_db = SessionLocal()
                background_tasks.add_task(
                    extract_metadata_background,
                    doc.id,
                    extracted_text,
                    file.filename,
                    bg_db
                )
            
            results.append({
                "filename": file.filename,
                "status": "success",
                "document_id": doc.id,
                "s3_url": s3_url,
                "text_length": len(extracted_text),
                "metadata_status": "processing",
                "embedding_status": "not_embedded"
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })
    
    return {"results": results}

@router.get("/list")
async def list_documents(category: Optional[str] = None, db: Session = Depends(get_db)):
    # """List all uploaded documents"""
    # documents = db.query(Document).all()
    # return {"documents": documents}
    """List documents with their metadata"""
    # Join Document with Metadata so we get title, description, category
    query = db.query(Document, DocumentMetadata).\
        outerjoin(DocumentMetadata, Document.id == DocumentMetadata.document_id)
    
    if category and category != "all":
        query = query.filter(DocumentMetadata.document_type == category)

    results = query.all()
    
    # Format for Frontend
    documents = []
    for doc, meta in results:
        documents.append({
            "id": doc.id,
            "title": meta.title if meta else doc.filename, # Fallback title
            "description": meta.summary if meta else "",
            "category": meta.document_type if meta else "Uncategorized",
            "created_at": doc.uploaded_at, # Assuming field exists
            "visibility": doc.visibility_level,
            "department": meta.department if meta else "Unknown",
            "year": meta.date_published.year if meta and meta.date_published else datetime.now().year,
            "updated_at": doc.uploaded_at
        })
    
    return {"documents": documents}

@router.get("/vector-stats")
async def get_vector_stats():
    """Get overall vector store statistics"""
    try:
        # Count all document folders
        import glob
        doc_folders = glob.glob("Agent/vector_store/documents/*/")
        total_docs = len(doc_folders)
        
        return {
            "status": "success",
            "total_documents": total_docs,
            "storage_mode": "separate_indexes",
            "storage_location": "Agent/vector_store/documents/{doc_id}/",
            "document_folders": [os.path.basename(os.path.dirname(f)) for f in doc_folders]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/vector-stats/{document_id}")
async def get_document_vector_stats(document_id: int):
    """Get vector store statistics for a specific document"""
    try:
        from Agent.vector_store.faiss_store import FAISSVectorStore
        index_path = f"Agent/vector_store/documents/{document_id}/faiss_index"
        
        if not os.path.exists(f"{index_path}.index"):
            raise HTTPException(status_code=404, detail="Vector index not found for this document")
        
        vector_store = FAISSVectorStore(index_path=index_path)
        stats = vector_store.get_stats()
        
        return {
            "status": "success",
            "document_id": document_id,
            "stats": stats,
            "index_path": index_path
        }
    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document details by ID"""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/{document_id}/status")
async def get_document_status(document_id: int, db: Session = Depends(get_db)):
    """Get document processing status"""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get metadata if exists
    metadata = db.query(DocumentMetadata).filter(DocumentMetadata.document_id == document_id).first()
    
    if not metadata:
        return {
            "doc_id": document_id,
            "status": "uploaded",
            "metadata_extracted": False,
            "embedding_status": "not_embedded",
            "estimated_wait": 3  # seconds for metadata extraction
        }
    
    return {
        "doc_id": document_id,
        "status": metadata.metadata_status,
        "metadata_extracted": metadata.metadata_status == "ready",
        "embedding_status": metadata.embedding_status,
        "title": metadata.title,
        "department": metadata.department,
        "document_type": metadata.document_type,
        "estimated_wait": 0 if metadata.metadata_status == "ready" else 2
    }

@router.get("/browse/metadata")
async def browse_documents(
    department: str = None,
    document_type: str = None,
    year: int = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Browse documents by metadata filters"""
    query = db.query(DocumentMetadata).join(Document)
    
    # Apply filters
    if department:
        query = query.filter(DocumentMetadata.department.ilike(f"%{department}%"))
    if document_type:
        query = query.filter(DocumentMetadata.document_type == document_type)
    if year:
        from sqlalchemy import extract
        query = query.filter(extract('year', DocumentMetadata.date_published) == year)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    results = query.offset(offset).limit(limit).all()
    
    # Format response
    documents = []
    for metadata in results:
        documents.append({
            "doc_id": metadata.document_id,
            "title": metadata.title,
            "department": metadata.department,
            "document_type": metadata.document_type,
            "date_published": str(metadata.date_published) if metadata.date_published else None,
            "summary": metadata.summary,
            "keywords": metadata.keywords[:5] if metadata.keywords else [],
            "embedding_status": metadata.embedding_status,
            "filename": metadata.document.filename
        })
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "documents": documents
    }

@router.post("/embed")
async def embed_documents(
    doc_ids: List[int],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Manually trigger embedding for specific documents"""
    from Agent.lazy_rag.lazy_embedder import LazyEmbedder
    
    # Validate documents exist
    docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
    if len(docs) != len(doc_ids):
        raise HTTPException(status_code=404, detail="One or more documents not found")
    
    # Trigger embedding in background
    def embed_batch():
        embedder = LazyEmbedder()
        documents_to_embed = [
            {"id": doc.id, "text": doc.extracted_text, "filename": doc.filename}
            for doc in docs
        ]
        results = embedder.embed_documents_batch(documents_to_embed)
        
        # Update metadata status
        from backend.database import SessionLocal
        bg_db = SessionLocal()
        for result in results:
            if result['status'] == 'success':
                metadata = bg_db.query(DocumentMetadata).filter(
                    DocumentMetadata.document_id == result['doc_id']
                ).first()
                if metadata:
                    metadata.embedding_status = 'embedded'
                    bg_db.commit()
        bg_db.close()
    
    background_tasks.add_task(embed_batch)
    
    return {
        "status": "embedding_started",
        "doc_ids": doc_ids,
        "estimated_time": len(doc_ids) * 2  # ~2 seconds per document
    }
