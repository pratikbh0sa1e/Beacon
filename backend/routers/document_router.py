from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from datetime import datetime

from backend.database import get_db, Document
from backend.utils.text_extractor import extract_text
from backend.utils.supabase_storage import upload_to_supabase
from Agent.vector_store.embedding_pipeline import EmbeddingPipeline

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "backend/files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize embedding pipeline
embedding_pipeline = EmbeddingPipeline()

def process_embeddings_background(document_id: int, text: str, metadata: dict):
    """Background task to process embeddings"""
    try:
        result = embedding_pipeline.process_document(text, metadata)
        print(f"Embedding result for doc {document_id}: {result}")
    except Exception as e:
        print(f"Error processing embeddings for doc {document_id}: {str(e)}")


@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
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
            
            # Save file locally
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Extract text
            extracted_text = extract_text(file_path, file_ext)
            
            # Upload to Supabase S3
            s3_url = upload_to_supabase(file_path, unique_filename)
            
            # Save to database
            doc = Document(
                filename=file.filename,
                file_type=file_ext,
                file_path=file_path,
                s3_url=s3_url,
                extracted_text=extracted_text
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            # Trigger background embedding task
            embedding_metadata = {
                "document_id": doc.id,
                "filename": file.filename,
                "file_type": file_ext,
                "source_department": source_department
            }
            
            if background_tasks:
                background_tasks.add_task(
                    process_embeddings_background,
                    doc.id,
                    extracted_text,
                    embedding_metadata
                )
            
            results.append({
                "filename": file.filename,
                "status": "success",
                "document_id": doc.id,
                "s3_url": s3_url,
                "text_length": len(extracted_text),
                "embedding_status": "processing"
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })
    
    return {"results": results}

@router.get("/list")
async def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents"""
    documents = db.query(Document).all()
    return {"documents": documents}

@router.get("/vector-stats")
async def get_vector_stats():
    """Get vector store statistics"""
    try:
        stats = embedding_pipeline.vector_store.get_stats()
        return {
            "status": "success",
            "stats": stats,
            "storage_location": "Agent/vector_store/faiss_index.*"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "stats": {
                "total_vectors": 0,
                "total_documents": 0,
                "dimension": 384
            }
        }

@router.get("/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document details by ID"""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.post("/reprocess-embeddings/{document_id}")
async def reprocess_embeddings(
    document_id: int,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    source_department: str = "Unknown"
):
    """Manually trigger embedding reprocessing for a document"""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    embedding_metadata = {
        "document_id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "source_department": source_department
    }
    
    background_tasks.add_task(
        process_embeddings_background,
        doc.id,
        doc.extracted_text,
        embedding_metadata
    )
    
    return {
        "status": "success",
        "message": "Embedding reprocessing triggered",
        "document_id": document_id
    }
