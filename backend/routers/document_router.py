from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from typing import List,Optional
import os
import shutil
import re
import glob
from sqlalchemy import or_,and_
from datetime import datetime
from backend.routers.auth_router import get_current_user
from backend.database import get_db, Document, DocumentMetadata, User, AuditLog, Institution
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

# def extract_metadata_background(document_id: int, text: str, filename: str, db_session):
#     """Background task to extract metadata"""
#     try:
#         print(f"Extracting metadata for doc {document_id}...")
#         metadata = metadata_extractor.extract_metadata(text, filename)
        
#         # Create or update metadata record
#         doc_metadata = DocumentMetadata(
#             document_id=document_id,
#             title=metadata.get('title'),
#             department=metadata.get('department'),
#             document_type=metadata.get('document_type'),
#             date_published=metadata.get('date_published'),
#             keywords=metadata.get('keywords'),
#             summary=metadata.get('summary'),
#             key_topics=metadata.get('key_topics'),
#             entities=metadata.get('entities'),
#             bm25_keywords=metadata.get('bm25_keywords'),
#             text_length=metadata.get('text_length'),
#             embedding_status='uploaded',
#             metadata_status='ready'
#         )
        
#         db_session.add(doc_metadata)
#         db_session.commit()
#         print(f"Metadata extracted for doc {document_id}: {metadata.get('title')}")
        
#     except Exception as e:
#         print(f"Error extracting metadata for doc {document_id}: {str(e)}")
#         db_session.rollback()

def extract_metadata_background(document_id: int, text: str, filename: str, db_session):
    """
    Background task: SMART FILL Logic.
    - AI overwrites 'Generic' user inputs (like 'Uncategorized').
    - AI respects 'Specific' user inputs.
    - AI ALWAYS saves its own summary to the metadata table.
    """
    try:
        print(f"Starting AI extraction for doc {document_id}...")
        
        existing_meta = db_session.query(DocumentMetadata).filter(
            DocumentMetadata.document_id == document_id
        ).first()

        if not existing_meta:
            print("Metadata record not found, skipping AI.")
            return

        # 1. Run AI Extraction
        ai_metadata = metadata_extractor.extract_metadata(text, filename)
        
        # 2. SMART FILL: Title
        # Only overwrite if the current title is just the filename (user didn't type one)
        if not existing_meta.title or existing_meta.title == filename:
            if ai_metadata.get('title'): existing_meta.title = ai_metadata.get('title')

        # 3. SMART FILL: Department
        # Only overwrite if default "General"
        if not existing_meta.department or existing_meta.department == "General":
            if ai_metadata.get('department'): existing_meta.department = ai_metadata.get('department')
            
        # 4. SMART FILL: Category (Document Type)
        # Only overwrite if default "Uncategorized"
        if not existing_meta.document_type or existing_meta.document_type == "Uncategorized":
            if ai_metadata.get('document_type'): existing_meta.document_type = ai_metadata.get('document_type')

        # 5. AI SUMMARY: Always save to 'summary' column
        # We don't check for emptiness here because User Description lives in a different table now.
        # This ensures we always have the AI's version available.
        existing_meta.summary = ai_metadata.get('summary', 'No summary available')

        # 6. AI FIELDS: Always fill these (User never types them)
        existing_meta.keywords = ai_metadata.get('keywords', [])
        existing_meta.key_topics = ai_metadata.get('key_topics', [])
        existing_meta.entities = ai_metadata.get('entities', [])
        existing_meta.bm25_keywords = ai_metadata.get('bm25_keywords', {})
        existing_meta.metadata_status = 'ready'
        
        db_session.commit()
        print(f"Metadata enriched for doc {document_id}")
        
    except Exception as e:
        print(f"Error in background extraction for doc {document_id}: {str(e)}")
        db_session.rollback()


# @router.post("/upload")
# async def upload_documents(
#     # files: List[UploadFile] = File(...),
#     file: UploadFile = File(...),
#     background_tasks: BackgroundTasks = None,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
#     source_department: str = "Unknown"
# ):
#     """
#     Upload documents (PDF, DOCX, JPEG, PNG), extract text, 
#     store in Supabase S3 and save metadata to database
#     """
#     results = []
    
#     for file in files:
#         try:
#             # Validate file type
#             file_ext = file.filename.split(".")[-1].lower()
#             if file_ext not in ["pdf", "docx", "jpeg", "jpg", "png"]:
#                 results.append({
#                     "filename": file.filename,
#                     "status": "error",
#                     "message": f"Unsupported file type: {file_ext}"
#                 })
#                 continue
            
#             # Save file locally with sanitized filename
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             safe_filename = sanitize_filename(file.filename)
#             unique_filename = f"{timestamp}_{safe_filename}"
#             file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
#             with open(file_path, "wb") as buffer:
#                 shutil.copyfileobj(file.file, buffer)
            
#             # Extract text
#             extracted_text = extract_text(file_path, file_ext)
            
#             # Check text size (PostgreSQL text field limit is ~1GB, but let's be safe)
#             # If text is too large, we'll still store it but log a warning
#             text_size_mb = len(extracted_text.encode('utf-8')) / (1024 * 1024)
#             if text_size_mb > 10:  # Warn if over 10MB
#                 print(f"Warning: Large text extracted ({text_size_mb:.2f}MB) from {file.filename}")
            
#             # Upload to Supabase S3
#             s3_url = upload_to_supabase(file_path, unique_filename)
            
#             # Save to database with retry logic
#             try:
#                 doc = Document(
#                     filename=file.filename,
#                     file_type=file_ext,
#                     file_path=file_path,
#                     s3_url=s3_url,
#                     extracted_text=extracted_text,
#                     uploader_id=current_user.id, # <--- SAVE USER ID
#                     institution_id=current_user.institution_id, # <--- SAVE INSTITUTION
#                     visibility_level="public" # Default visibility
#                 )
#                 db.add(doc)
#                 db.commit()
#                 db.refresh(doc)
#             except Exception as db_error:
#                 db.rollback()
#                 # Retry once
#                 try:
#                     db.add(doc)
#                     db.commit()
#                     db.refresh(doc)
#                 except Exception as retry_error:
#                     raise Exception(f"Database error after retry: {str(retry_error)}")
            
#             # Trigger background metadata extraction
#             if background_tasks:
#                 # Create a new session for background task
#                 from backend.database import SessionLocal
#                 bg_db = SessionLocal()
#                 background_tasks.add_task(
#                     extract_metadata_background,
#                     doc.id,
#                     extracted_text,
#                     file.filename,
#                     bg_db
#                 )
            
#             results.append({
#                 "filename": file.filename,
#                 "status": "success",
#                 "document_id": doc.id,
#                 "s3_url": s3_url,
#                 "text_length": len(extracted_text),
#                 "metadata_status": "processing",
#                 "embedding_status": "not_embedded"
#             })
            
#         except Exception as e:
#             results.append({
#                 "filename": file.filename,
#                 "status": "error",
#                 "message": str(e)
#             })
    
#     return {"results": results}


# @router.post("/upload")
# async def upload_documents(
#     file: UploadFile = File(...),          # Single File
#     title: Optional[str] = Form(None),     # User Input
#     category: Optional[str] = Form("Uncategorized"),
#     department: Optional[str] = Form("General"),    
#     description: Optional[str] = Form(None), # ✅ User's Description
#     visibility: Optional[str] = Form("public"),
#     institution: Optional[str] = Form(None), 
#     year: Optional[str] = Form(None),      
#     version: Optional[str] = Form("1.0"),
#     download_allowed: bool = Form(False),  
#     background_tasks: BackgroundTasks = None,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Upload documents with optional metadata
#     If metadata is provided, skip AI extraction
#     """
#     results = []
    
#     for file in files:
#         try:
#             # Validate file type
#             file_ext = file.filename.split(".")[-1].lower()
#             if file_ext not in ["pdf", "docx", "jpeg", "jpg", "png"]:
#                 results.append({
#                     "filename": file.filename,
#                     "status": "error",
#                     "message": f"Unsupported file type: {file_ext}"
#                 })
#                 continue
            
#             # Save file locally
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             safe_filename = sanitize_filename(file.filename)
#             unique_filename = f"{timestamp}_{safe_filename}"
#             file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
#             with open(file_path, "wb") as buffer:
#                 shutil.copyfileobj(file.file, buffer)
            
#             # Extract text
#             extracted_text = extract_text(file_path, file_ext)
            
#             # Upload to Supabase
#             s3_url = upload_to_supabase(file_path, unique_filename)
            
#             # ✅ FIXED: Use institution from form or user
#             doc_institution_id = institution_id if institution_id else current_user.institution_id
            
#             # Create document
#             doc = Document(
#                 filename=file.filename,
#                 file_type=file_ext,
#                 file_path=file_path,
#                 s3_url=s3_url,
#                 extracted_text=extracted_text,
#                 uploader_id=current_user.id,
#                 institution_id=doc_institution_id,
#                 visibility_level=visibility or "public"
#             )
#             db.add(doc)
#             db.commit()
#             db.refresh(doc)
            
#             # ✅ FIXED: Only extract metadata if not provided
#             if title and category and department:
#                 # User provided metadata, use it directly
#                 doc_metadata = DocumentMetadata(
#                     document_id=doc.id,
#                     title=title,
#                     department=department,
#                     document_type=category,
#                     summary=description,
#                     text_length=len(extracted_text),
#                     embedding_status='uploaded',
#                     metadata_status='ready'
#                 )
#                 db.add(doc_metadata)
#                 db.commit()
                
#                 results.append({
#                     "filename": file.filename,
#                     "status": "success",
#                     "document_id": doc.id,
#                     "metadata_status": "ready",
#                     "metadata_source": "user_provided"
#                 })
#             else:
#                 # No metadata provided, trigger AI extraction
#                 if background_tasks:
#                     from backend.database import SessionLocal
#                     bg_db = SessionLocal()
#                     background_tasks.add_task(
#                         extract_metadata_background,
#                         doc.id,
#                         extracted_text,
#                         file.filename,
#                         bg_db
#                     )
                
    #             results.append({
    #                 "filename": file.filename,
    #                 "status": "success",
    #                 "document_id": doc.id,
    #                 "metadata_status": "processing",
    #                 "metadata_source": "ai_extraction"
    #             })
            
    #     except Exception as e:
    #         results.append({
    #             "filename": file.filename,
    #             "status": "error",
    #             "message": str(e)
    #         })
    
    # return {"results": results}

@router.post("/upload")
async def upload_documents(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form("Uncategorized"),
    department: Optional[str] = Form("General"),    
    description: Optional[str] = Form(None),
    visibility: Optional[str] = Form("public"),
    institution: Optional[str] = Form(None), 
    year: Optional[str] = Form(None),      
    version: Optional[str] = Form("1.0"),
    download_allowed: bool = Form(False),  
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = [] # ✅ Initialize results list for debugging output
    
    try:
        # 1. Validate file type
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in ["pdf", "docx", "jpeg", "jpg", "png", "txt"]:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # 2. Save file locally
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = sanitize_filename(file.filename)
        unique_filename = f"{timestamp}_{safe_filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 3. Extract text & Upload
        extracted_text = extract_text(file_path, file_ext)
        s3_url = upload_to_supabase(file_path, unique_filename)
        
        # 4. Handle Institution
        final_inst_id = current_user.institution_id
        if institution and institution.strip() and institution != "null":
             try: final_inst_id = int(institution)
             except ValueError: pass 
        
        # 5. Create Document
        doc = Document(
            filename=file.filename,
            file_type=file_ext,
            file_path=file_path,
            s3_url=s3_url,
            extracted_text=extracted_text,
            uploader_id=current_user.id,
            institution_id=final_inst_id,
            visibility_level=visibility or "public",
            approval_status="pending",
            download_allowed=download_allowed,
            version=version,
            user_description=description
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # 6. Create Metadata
        pub_date = None
        if year and year.isdigit():
            try: pub_date = datetime(int(year), 1, 1)
            except: pass

        doc_metadata = DocumentMetadata(
            document_id=doc.id,
            title=title if title and title.strip() else file.filename,
            department=department if department else "General",
            document_type=category if category else "Uncategorized",
            summary=None,
            date_published=pub_date,
            text_length=len(extracted_text),
            embedding_status='uploaded',
            metadata_status='processing'
        )
        db.add(doc_metadata)
        db.commit()

        # 7. Background Task
        if background_tasks:
            from backend.database import SessionLocal
            bg_db = SessionLocal()
            background_tasks.add_task(extract_metadata_background, doc.id, extracted_text, file.filename, bg_db)
        
        # ✅ SUCCESS: Append structured result
        results.append({
            "filename": file.filename,
            "status": "success",
            "document_id": doc.id,
            "metadata_status": "processing",
            # Determine source: if user typed something, it's user provided. Else AI.
            "metadata_source": "user_provided" if (title or description) else "ai_extraction"
        })
        
    except Exception as e:
        # ✅ ERROR: Append error details for debugging
        print(f"Upload Error: {str(e)}")
        # Clean up file if it exists but failed db save
        if 'file_path' in locals() and os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
            
        results.append({
            "filename": file.filename,
            "status": "error",
            "message": str(e)
        })
        # Note: We return 200 OK with error details so frontend can read 'results'
    
    return {"results": results}



# @router.get("/list")
# async def list_documents(category: Optional[str] = None, db: Session = Depends(get_db)):
#     # """List all uploaded documents"""
#     # documents = db.query(Document).all()
#     # return {"documents": documents}
#     """List documents with their metadata"""
#     # Join Document with Metadata so we get title, description, category
#     query = db.query(Document, DocumentMetadata).\
#         outerjoin(DocumentMetadata, Document.id == DocumentMetadata.document_id)
    
#     if category and category != "all":
#         query = query.filter(DocumentMetadata.document_type == category)

#     results = query.all()
    
#     # Format for Frontend
#     documents = []
#     for doc, meta in results:
#         documents.append({
#             "id": doc.id,
#             "title": meta.title if meta else doc.filename, # Fallback title
#             "description": meta.summary if meta else "",
#             "category": meta.document_type if meta else "Uncategorized",
#             "created_at": doc.uploaded_at, # Assuming field exists
#             "visibility": doc.visibility_level,
#             "department": meta.department if meta else "Unknown",
#             "year": meta.date_published.year if meta and meta.date_published else datetime.now().year,
#             "updated_at": doc.uploaded_at
#         })
    
#     return {"documents": documents}

@router.get("/list")
async def list_documents(
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # ✅ Security: Require Login
):
    """
    List documents with Pagination, Search, and Role-Based Security.
    """
    query = db.query(Document, DocumentMetadata).outerjoin(
        DocumentMetadata, Document.id == DocumentMetadata.document_id
    )
    
    # ==================================================================
    # 🔒 ROLE-BASED VISIBILITY LOGIC
    # ==================================================================
    
    # 1. DEVELOPER: God mode - sees everything.
    if current_user.role == "developer":
        pass 

    # 2. MINISTRY ADMIN: Sees almost everything across all institutions.
    elif current_user.role == "moe_admin":
        # Can see Public, Restricted, and ALL Institution docs.
        # Cannot see "Confidential" docs (unless uploaded by them, handled separately).
        query = query.filter(
            Document.visibility_level.in_(["public", "restricted", "institution_only"])
        )

    # 3. UNIVERSITY ADMIN: Sees specific docs for THEIR institution.
    elif current_user.role == "university_admin":
        # Sees:
        # A) Any Public document
        # B) Institution/Restricted docs belonging to THEIR Institution
        query = query.filter(
            or_(
                Document.visibility_level == "public",
                and_(
                    Document.visibility_level.in_(["institution_only", "restricted"]),
                    Document.institution_id == current_user.institution_id
                )
            )
        )

    # 4. STUDENT / PUBLIC VIEWER / OTHERS
    else:
        # Sees:
        # A) Public documents
        # B) "Institution Only" documents from THEIR Institution
        
        # Define what they can see
        visible_conditions = [Document.visibility_level == "public"]
        
        # If they belong to an institution (Students), add that access
        if current_user.institution_id:
            visible_conditions.append(
                and_(
                    Document.visibility_level == "institution_only",
                    Document.institution_id == current_user.institution_id
                )
            )
            
        # Apply the filter
        query = query.filter(or_(*visible_conditions))

    # ==================================================================
    # 🔍 FILTERS (Search & Category)
    # ==================================================================

    # Category Filter
    if category and category != "all":
        query = query.filter(DocumentMetadata.document_type == category)

    # Search Filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                DocumentMetadata.title.ilike(search_term),
                DocumentMetadata.summary.ilike(search_term),
                Document.filename.ilike(search_term)
            )
        )
    
    # ==================================================================
    # 📄 PAGINATION
    # ==================================================================
    total_count = query.count()
    query = query.order_by(Document.uploaded_at.desc())
    
    if limit > 0:
        query = query.limit(limit).offset(offset)
        
    results = query.all()
    
    # Format Response
    documents = []
    for doc, meta in results:
        # If user_description exists, use it. Otherwise, use AI summary.
        display_description = doc.user_description if doc.user_description else (meta.summary if meta else "")
        documents.append({
            "id": doc.id,
            "title": meta.title if meta else doc.filename,
            "description": display_description,
            "category": meta.document_type if meta else "Uncategorized",
            "visibility": doc.visibility_level,
            "download_allowed": doc.download_allowed,
            "department": meta.department if meta else "Unknown",
            "year": meta.date_published.year if meta and meta.date_published else datetime.now().year,
            "created_at": doc.uploaded_at,
            "updated_at": meta.updated_at if meta else doc.uploaded_at,
            "institution_id": doc.institution_id
        })
    
    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "documents": documents
    }

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

# @router.get("/{document_id}")
# async def get_document(document_id: int, db: Session = Depends(get_db)):
#     """Get document details by ID"""
#     doc = db.query(Document).filter(Document.id == document_id).first()
#     if not doc:
#         raise HTTPException(status_code=404, detail="Document not found")
#     return doc
@router.get("/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get full document details"""
    result = db.query(Document, DocumentMetadata, Institution).\
        outerjoin(DocumentMetadata, Document.id == DocumentMetadata.document_id).\
        outerjoin(Institution, Document.institution_id == Institution.id).\
        filter(Document.id == document_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc, meta, inst = result
    
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "s3_url": doc.s3_url,
        "title": meta.title if meta else doc.filename,
        
        # ✅ Return ALL description variations for Frontend to choose
        "description": doc.user_description or meta.summary,
        "user_description": doc.user_description,
        "ai_summary": meta.summary if meta else "",
        
        "category": meta.document_type if meta else "Uncategorized",
        "department": meta.department if meta else "Unknown",
        "keywords": meta.keywords if meta else [],
        "year": meta.date_published.year if meta and meta.date_published else None,
        "created_at": doc.uploaded_at,
        "updated_at": meta.updated_at if meta else doc.uploaded_at,
        "visibility": doc.visibility_level,
        "download_allowed": doc.download_allowed,
        "version": doc.version,
        "institution": {"id": inst.id, "name": inst.name, "type": inst.type} if inst else None
    }

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

# ✅ NEW: Add download endpoint
@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a document (if allowed)"""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 1. Security Check: Is download allowed?
    if not doc.download_allowed:
        # Extra check: Admins/Owners usually bypass this, but for now we enforce it strictly
        if current_user.role not in ["developer", "moe_admin"] and current_user.id != doc.uploader_id:
             raise HTTPException(status_code=403, detail="Download not allowed for this document")
    
    # 2. File Existence Check
    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    # 3. Log the Download (Audit Trail)
    audit = AuditLog(
        user_id=current_user.id,
        action="document_downloaded",
        action_metadata={
            "document_id": document_id,
            "filename": doc.filename,
            "user_role": current_user.role
        }
    )
    db.add(audit)
    db.commit()
    
    # 4. Serve the File
    return FileResponse(
        path=doc.file_path,
        filename=doc.filename,
        media_type="application/octet-stream"
    )

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
