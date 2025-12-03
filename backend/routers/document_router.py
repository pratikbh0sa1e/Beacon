from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks, Body
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from typing import List,Optional
from pydantic import BaseModel
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

# Pydantic models for request bodies
class RejectRequest(BaseModel):
    reason: str

class ChangesRequest(BaseModel):
    changes_requested: str

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
        if file_ext not in ["pdf", "docx", "pptx", "jpeg", "jpg", "png", "txt"]:
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
        # MoE Admin and Developer don't need approval - their uploads are auto-approved
        initial_status = "approved" if current_user.role in ["moe_admin", "developer"] else "draft"
        
        doc = Document(
            filename=file.filename,
            file_type=file_ext,
            file_path=file_path,
            s3_url=s3_url,
            extracted_text=extracted_text,
            uploader_id=current_user.id,
            institution_id=final_inst_id,
            visibility_level=visibility or "public",
            approval_status=initial_status,  # MoE/Developer: approved, Others: draft
            download_allowed=download_allowed,
            version=version,
            user_description=description,
            approved_by=current_user.id if current_user.role in ["moe_admin", "developer"] else None,
            approved_at=datetime.utcnow() if current_user.role in ["moe_admin", "developer"] else None
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

        # 7. Background Task: Extract metadata (which will then trigger embedding)
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
    sort_by: Optional[str] = "recent",
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # ✅ Security: Require Login
):
    """
    List documents with Pagination, Search, Sorting, and Role-Based Security.
    
    Sort options:
    - recent: Most recent first (default)
    - oldest: Oldest first
    - title-asc: Title A-Z
    - title-desc: Title Z-A
    - department: By department name
    """
    # query = db.query(Document, DocumentMetadata).outerjoin(
    #     DocumentMetadata, Document.id == DocumentMetadata.document_id
    # )
    query = db.query(Document, DocumentMetadata, User).outerjoin(
        DocumentMetadata, Document.id == DocumentMetadata.document_id
    ).outerjoin(
        User, Document.uploader_id == User.id
    )
    
    # ==================================================================
    # 🔒 ROLE-BASED VISIBILITY LOGIC (Security through Obscurity + Access Control)
    # ==================================================================
    
    # 1. DEVELOPER: Full access to everything
    if current_user.role == "developer":
        pass  # No filters - sees all documents

    # 2. MOE ADMIN: Respects institutional autonomy
    elif current_user.role == "moe_admin":
        # MOE Admin can ONLY see:
        # a) Public documents (everyone can see)
        # b) Documents pending approval (requires_moe_approval)
        # c) Documents from MOE institution (if MOE has an institution_id)
        # d) Documents they uploaded
        query = query.filter(
            or_(
                # Public documents
                Document.visibility_level == "public",
                # Documents pending approval (universities requesting MOE approval)
                Document.approval_status == "pending",
                # Documents from MOE's own institution (if applicable)
                Document.institution_id == current_user.institution_id,
                # Documents uploaded by this MOE admin
                Document.uploader_id == current_user.id
            )
        )

    # 3. UNIVERSITY ADMIN: Sees docs from their institution + public
    elif current_user.role == "university_admin":
        query = query.filter(
            or_(
                # Public documents (everyone can see)
                Document.visibility_level == "public",
                # Confidential, Restricted, Institution-only from THEIR institution
                and_(
                    Document.visibility_level.in_(["confidential", "restricted", "institution_only"]),
                    Document.institution_id == current_user.institution_id
                ),
                # OR documents they uploaded (ownership)
                Document.uploader_id == current_user.id
            )
        )

    # 4. DOCUMENT OFFICER: Sees restricted/institution docs from their institution + public
    elif current_user.role == "document_officer":
        query = query.filter(
            or_(
                # Public documents
                Document.visibility_level == "public",
                # Restricted and Institution-only from THEIR institution
                and_(
                    Document.visibility_level.in_(["restricted", "institution_only"]),
                    Document.institution_id == current_user.institution_id
                ),
                # OR documents they uploaded
                Document.uploader_id == current_user.id
            )
        )

    # 5. STUDENT: Sees public + institution-only from their institution
    elif current_user.role == "student":
        visible_conditions = [Document.visibility_level == "public"]
        
        if current_user.institution_id:
            visible_conditions.append(
                and_(
                    Document.visibility_level == "institution_only",
                    Document.institution_id == current_user.institution_id
                )
            )
        
        query = query.filter(or_(*visible_conditions))

    # 6. PUBLIC VIEWER / OTHERS: Only public documents
    else:
        query = query.filter(Document.visibility_level == "public")

    # ==================================================================
    # ✅ APPROVAL STATUS FILTER
    # ==================================================================
    # Draft documents: Only visible to uploader and admins from same institution
    # Approved documents: Visible to everyone (based on visibility level)
    # Pending/Under Review: Visible to admins
    # Other statuses: Visible to admins and uploader
    
    if current_user.role == "developer":
        # Developer sees everything
        pass
    elif current_user.role in ["moe_admin", "university_admin"]:
        # Admins see: approved, pending, under_review, changes_requested, rejected, and their own drafts
        query = query.filter(
            or_(
                Document.approval_status.in_(["approved", "pending", "under_review", "changes_requested", "rejected", "archived", "flagged"]),
                Document.uploader_id == current_user.id  # Their own drafts
            )
        )
    elif current_user.role == "document_officer":
        # Doc officers see: approved documents and their own drafts
        query = query.filter(
            or_(
                Document.approval_status == "approved",
                Document.uploader_id == current_user.id  # Their own drafts
            )
        )
    else:
        # Students and public: Only approved documents
        query = query.filter(Document.approval_status == "approved")
    
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
    # 📄 SORTING
    # ==================================================================
    if sort_by == "recent":
        query = query.order_by(Document.uploaded_at.desc())
    elif sort_by == "oldest":
        query = query.order_by(Document.uploaded_at.asc())
    elif sort_by == "title-asc":
        query = query.order_by(DocumentMetadata.title.asc())
    elif sort_by == "title-desc":
        query = query.order_by(DocumentMetadata.title.desc())
    elif sort_by == "department":
        query = query.order_by(DocumentMetadata.department.asc())
    else:
        # Default to recent
        query = query.order_by(Document.uploaded_at.desc())
    
    # ==================================================================
    # 📄 PAGINATION
    # ==================================================================
    total_count = query.count()
    
    if limit > 0:
        query = query.limit(limit).offset(offset)
        
    results = query.all()
    
    # Format Response
    documents = []
    for doc, meta, user in results:
        # If user_description exists, use it. Otherwise, use AI summary.
        display_description = doc.user_description if doc.user_description else (meta.summary if meta else "")
        documents.append({
            "id": doc.id,
            "title": meta.title if meta else doc.filename,
            "description": display_description,
            "category": meta.document_type if meta else "Uncategorized",
            "visibility": doc.visibility_level,
            "download_allowed": doc.download_allowed,
            "approval_status": doc.approval_status,
            "department": meta.department if meta else "Unknown",
            "year": meta.date_published.year if meta and meta.date_published else datetime.now().year,
            "created_at": doc.uploaded_at,
            "updated_at": meta.updated_at if meta else doc.uploaded_at,
            "institution_id": doc.institution_id,
            "uploader": {
                "name": user.name if user else "Unknown",
                "role": user.role if user else "Unknown"
            }

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
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full document details with access control"""
    result = db.query(Document, DocumentMetadata, Institution).\
        outerjoin(DocumentMetadata, Document.id == DocumentMetadata.document_id).\
        outerjoin(Institution, Document.institution_id == Institution.id).\
        filter(Document.id == document_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc, meta, inst = result
    
    # ==================================================================
    # 🔒 ACCESS CONTROL CHECK
    # ==================================================================
    def check_access():
        """Check if current user can access this document - Respects institutional autonomy"""
        visibility = doc.visibility_level
        user_role = current_user.role
        user_institution = current_user.institution_id
        doc_institution = doc.institution_id
        is_uploader = doc.uploader_id == current_user.id
        approval_status = doc.approval_status
        
        # Developer: Full access
        if user_role == "developer":
            return True
        
        # Public documents: Everyone can access
        if visibility == "public":
            return True
        
        # Uploader: Always has access to their own documents
        if is_uploader:
            return True
        
        # MOE Admin: Institutional autonomy rules
        if user_role == "moe_admin":
            # Can access if:
            # a) Document is pending approval (university requesting MOE review)
            if approval_status == "pending":
                return True
            # b) Document is from MOE's own institution
            if user_institution and user_institution == doc_institution:
                return True
            # c) Document is public (already handled above)
            # Otherwise, NO ACCESS to university documents
            return False
        
        # Confidential documents
        if visibility == "confidential":
            # Only: Developer, University Admin (same institution), Uploader
            if user_role == "university_admin" and user_institution == doc_institution:
                return True
            return False
        
        # Restricted documents
        if visibility == "restricted":
            # Only: Developer, University Admin (same inst), Document Officer (same inst)
            if user_role in ["university_admin", "document_officer"] and user_institution == doc_institution:
                return True
            return False
        
        # Institution-only documents
        if visibility == "institution_only":
            # Only: Developer, University Admin (same inst), Document Officer (same inst), Students (same inst)
            if user_role in ["university_admin", "document_officer", "student"] and user_institution == doc_institution:
                return True
            return False
        
        return False
    
    # Check access
    if not check_access():
        visibility = doc.visibility_level
        # Return appropriate error message based on visibility level
        if visibility == "confidential":
            raise HTTPException(
                status_code=403,
                detail="Access Denied — This document requires elevated clearance."
            )
        elif visibility == "restricted":
            raise HTTPException(
                status_code=403,
                detail="This document has limited access permissions."
            )
        elif visibility == "institution_only":
            raise HTTPException(
                status_code=403,
                detail="Access restricted to institution members."
            )
        else:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get uploader info
    uploader = db.query(User).filter(User.id == doc.uploader_id).first()
    
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
        "approval_status": doc.approval_status,
        "requires_moe_approval": doc.requires_moe_approval,
        "rejection_reason": doc.rejection_reason,
        "institution": {"id": inst.id, "name": inst.name, "type": inst.type} if inst else None,
        "uploader": {"id": uploader.id, "name": uploader.name, "role": uploader.role} if uploader else None
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
    
    # ==================================================================
    # 🔒 ACCESS CONTROL CHECK (Same as get_document)
    # ==================================================================
    def check_access():
        """Check if current user can access this document - Respects institutional autonomy"""
        visibility = doc.visibility_level
        user_role = current_user.role
        user_institution = current_user.institution_id
        doc_institution = doc.institution_id
        is_uploader = doc.uploader_id == current_user.id
        approval_status = doc.approval_status
        
        if user_role == "developer":
            return True
        if visibility == "public":
            return True
        if is_uploader:
            return True
        
        # MOE Admin: Institutional autonomy
        if user_role == "moe_admin":
            if approval_status == "pending":
                return True
            if user_institution and user_institution == doc_institution:
                return True
            return False
        
        if visibility == "confidential":
            if user_role == "university_admin" and user_institution == doc_institution:
                return True
            return False
        
        if visibility == "restricted":
            if user_role in ["university_admin", "document_officer"] and user_institution == doc_institution:
                return True
            return False
        
        if visibility == "institution_only":
            if user_role in ["university_admin", "document_officer", "student"] and user_institution == doc_institution:
                return True
            return False
        
        return False
    
    # Check access first
    if not check_access():
        visibility = doc.visibility_level
        if visibility == "confidential":
            raise HTTPException(status_code=403, detail="Access Denied — This document requires elevated clearance.")
        elif visibility == "restricted":
            raise HTTPException(status_code=403, detail="This document has limited access permissions.")
        elif visibility == "institution_only":
            raise HTTPException(status_code=403, detail="Access restricted to institution members.")
        else:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # 1. Security Check: Is download allowed?
    if not doc.download_allowed:
        # Extra check: Admins/Owners usually bypass this, but for now we enforce it strictly
        if current_user.role not in ["developer", "moe_admin"] and current_user.id != doc.uploader_id:
             raise HTTPException(status_code=403, detail="Download not allowed for this document")
    
    # 2. Check if file is stored in S3/Supabase or locally
    if doc.s3_url:
        # File is stored in Supabase Storage - stream it with proper headers
        import httpx
        import mimetypes
        from fastapi.responses import StreamingResponse
        
        try:
            # Download file from S3
            async with httpx.AsyncClient() as client:
                response = await client.get(doc.s3_url)
                response.raise_for_status()
                
                # Determine MIME type
                mime_type, _ = mimetypes.guess_type(doc.filename)
                if not mime_type:
                    mime_type = "application/octet-stream"
                
                # Log the Download (Audit Trail)
                audit = AuditLog(
                    user_id=current_user.id,
                    action="document_downloaded",
                    action_metadata={
                        "document_id": document_id,
                        "filename": doc.filename,
                        "user_role": current_user.role,
                        "storage": "supabase"
                    }
                )
                db.add(audit)
                db.commit()
                
                # Stream the file with proper headers
                return StreamingResponse(
                    iter([response.content]),
                    media_type=mime_type,
                    headers={
                        "Content-Disposition": f'attachment; filename="{doc.filename}"'
                    }
                )
                
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to download file from Supabase: {str(e)}"
            )
    
    # 3. File stored locally - check existence
    if not doc.file_path:
        raise HTTPException(
            status_code=404, 
            detail=f"No file path or S3 URL set for document {document_id}. Document may not have been uploaded correctly."
        )
    
    if not os.path.exists(doc.file_path):
        raise HTTPException(
            status_code=404, 
            detail=f"File not found at path: {doc.file_path}. The file may have been moved or deleted."
        )
    
    # 4. Log the Download (Audit Trail)
    audit = AuditLog(
        user_id=current_user.id,
        action="document_downloaded",
        action_metadata={
            "document_id": document_id,
            "filename": doc.filename,
            "user_role": current_user.role,
            "storage": "local"
        }
    )
    db.add(audit)
    db.commit()
    
    # 5. Serve the File with correct MIME type
    import mimetypes
    mime_type, _ = mimetypes.guess_type(doc.filename)
    
    # Default to octet-stream if type cannot be determined
    if not mime_type:
        mime_type = "application/octet-stream"
    
    return FileResponse(
        path=doc.file_path,
        filename=doc.filename,
        media_type=mime_type
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

# ==================================================================
# 📋 DOCUMENT WORKFLOW ENDPOINTS (Option 2 Compliance)
# ==================================================================

@router.post("/{document_id}/submit-for-review")
async def submit_document_for_review(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit document for MoE review (University Admin only)
    Changes status from 'draft' to 'pending' and sets escalation flag
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Only University Admin or uploader can submit for review
    if current_user.role not in ["university_admin", "developer"] and current_user.id != doc.uploader_id:
        raise HTTPException(status_code=403, detail="Only University Admin can submit documents for review")
    
    # Must be from same institution
    if current_user.role == "university_admin" and current_user.institution_id != doc.institution_id:
        raise HTTPException(status_code=403, detail="Can only submit documents from your institution")
    
    # Update document status
    doc.approval_status = "pending"
    doc.requires_moe_approval = True
    doc.escalated_at = datetime.utcnow()
    db.commit()
    
    # Create notification for MoE Admin
    from backend.database import Notification
    moe_admins = db.query(User).filter(User.role == "moe_admin").all()
    
    for moe_admin in moe_admins:
        notification = Notification(
            user_id=moe_admin.id,
            type="document_approval",
            title="New Document Pending Review",
            message=f"Document '{doc.filename}' has been submitted for MoE approval by {current_user.name}",
            priority="high",
            action_url=f"/approvals/{document_id}",
            action_metadata={
                "document_id": document_id,
                "submitter_id": current_user.id,
                "institution_id": doc.institution_id
            }
        )
        db.add(notification)
    
    # Notify Developer (copy)
    developers = db.query(User).filter(User.role == "developer").all()
    for dev in developers:
        notification = Notification(
            user_id=dev.id,
            type="document_approval",
            title="Document Submitted for Review",
            message=f"Document '{doc.filename}' submitted for MoE approval",
            priority="medium",
            action_url=f"/approvals/{document_id}",
            action_metadata={"document_id": document_id}
        )
        db.add(notification)
    
    db.commit()
    
    return {
        "status": "success",
        "message": "Document submitted for MoE review",
        "document_id": document_id,
        "approval_status": "pending"
    }


@router.post("/{document_id}/approve")
async def approve_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a document (MoE Admin or University Admin)
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check permissions
    can_approve = False
    
    if current_user.role == "developer":
        can_approve = True
    elif current_user.role == "moe_admin" and doc.requires_moe_approval:
        can_approve = True
    elif current_user.role == "university_admin" and current_user.institution_id == doc.institution_id:
        can_approve = True
    
    if not can_approve:
        raise HTTPException(status_code=403, detail="You don't have permission to approve this document")
    
    # Update document
    doc.approval_status = "approved"
    doc.approved_by = current_user.id
    doc.approved_at = datetime.utcnow()
    db.commit()
    
    # Notify uploader
    from backend.database import Notification
    notification = Notification(
        user_id=doc.uploader_id,
        type="document_approved",
        title="Document Approved",
        message=f"Your document '{doc.filename}' has been approved by {current_user.name}",
        priority="high",
        action_url=f"/documents/{document_id}",
        action_metadata={"document_id": document_id, "approved_by": current_user.id}
    )
    db.add(notification)
    db.commit()
    
    return {
        "status": "success",
        "message": "Document approved",
        "document_id": document_id,
        "approved_by": current_user.name
    }


@router.post("/{document_id}/reject")
async def reject_document(
    document_id: int,
    request: RejectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a document with reason (MoE Admin or University Admin)
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check permissions
    can_reject = False
    
    if current_user.role == "developer":
        can_reject = True
    elif current_user.role == "moe_admin" and doc.requires_moe_approval:
        can_reject = True
    elif current_user.role == "university_admin" and current_user.institution_id == doc.institution_id:
        can_reject = True
    
    if not can_reject:
        raise HTTPException(status_code=403, detail="You don't have permission to reject this document")
    
    # Update document
    doc.approval_status = "rejected"
    doc.rejection_reason = request.reason
    doc.approved_by = current_user.id
    doc.approved_at = datetime.utcnow()
    db.commit()
    
    # Notify uploader
    from backend.database import Notification
    notification = Notification(
        user_id=doc.uploader_id,
        type="document_rejected",
        title="Document Rejected",
        message=f"Your document '{doc.filename}' has been rejected. Reason: {request.reason}",
        priority="high",
        action_url=f"/documents/{document_id}",
        action_metadata={"document_id": document_id, "rejected_by": current_user.id, "reason": request.reason}
    )
    db.add(notification)
    db.commit()
    
    return {
        "status": "success",
        "message": "Document rejected",
        "document_id": document_id,
        "reason": request.reason
    }


@router.post("/{document_id}/request-changes")
async def request_changes(
    document_id: int,
    request: ChangesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request changes to a document (MoE Admin or University Admin)
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check permissions
    can_request = False
    
    if current_user.role == "developer":
        can_request = True
    elif current_user.role == "moe_admin" and doc.requires_moe_approval:
        can_request = True
    elif current_user.role == "university_admin" and current_user.institution_id == doc.institution_id:
        can_request = True
    
    if not can_request:
        raise HTTPException(status_code=403, detail="You don't have permission to request changes")
    
    # Update document
    doc.approval_status = "changes_requested"
    doc.rejection_reason = request.changes_requested
    db.commit()
    
    # Notify uploader
    from backend.database import Notification
    notification = Notification(
        user_id=doc.uploader_id,
        type="changes_requested",
        title="Changes Requested",
        message=f"Changes requested for '{doc.filename}': {request.changes_requested}",
        priority="high",
        action_url=f"/documents/{document_id}",
        action_metadata={"document_id": document_id, "requested_by": current_user.id}
    )
    db.add(notification)
    db.commit()
    
    return {
        "status": "success",
        "message": "Changes requested",
        "document_id": document_id
    }


@router.get("/approvals/pending")
async def get_pending_approvals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of documents pending approval (for MoE Admin and University Admin)
    """
    query = db.query(Document, DocumentMetadata, Institution, User).outerjoin(
        DocumentMetadata, Document.id == DocumentMetadata.document_id
    ).outerjoin(
        Institution, Document.institution_id == Institution.id
    ).outerjoin(
        User, Document.uploader_id == User.id
    )
    
    # Filter based on role
    if current_user.role == "moe_admin":
        # MoE sees documents that require MoE approval
        query = query.filter(
            Document.approval_status == "pending",
            Document.requires_moe_approval == True
        )
    elif current_user.role == "university_admin":
        # University Admin sees pending docs from their institution
        query = query.filter(
            Document.approval_status == "pending",
            Document.institution_id == current_user.institution_id
        )
    elif current_user.role == "developer":
        # Developer sees all pending
        query = query.filter(Document.approval_status == "pending")
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    results = query.order_by(Document.escalated_at.desc()).all()
    
    documents = []
    for doc, meta, inst, uploader in results:
        documents.append({
            "id": doc.id,
            "filename": doc.filename,
            "title": meta.title if meta else doc.filename,
            "description": doc.user_description or (meta.summary if meta else ""),
            "category": meta.document_type if meta else "Uncategorized",
            "visibility": doc.visibility_level,
            "institution": {"id": inst.id, "name": inst.name} if inst else None,
            "uploader": {"id": uploader.id, "name": uploader.name} if uploader else None,
            "submitted_at": doc.escalated_at,
            "requires_moe_approval": doc.requires_moe_approval
        })
    
    return {"total": len(documents), "documents": documents}


@router.post("/{document_id}/update-status")
async def update_document_status(
    document_id: int,
    new_status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update document status (for admins)
    Valid statuses: draft, pending, under_review, changes_requested, approved, 
                    restricted_approved, archived, rejected, flagged, expired
    """
    valid_statuses = [
        "draft", "pending", "under_review", "changes_requested", 
        "approved", "restricted_approved", "archived", "rejected", "flagged", "expired"
    ]
    
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check permissions
    if current_user.role not in ["developer", "moe_admin", "university_admin"]:
        raise HTTPException(status_code=403, detail="Only admins can update document status")
    
    if current_user.role == "university_admin" and current_user.institution_id != doc.institution_id:
        raise HTTPException(status_code=403, detail="Can only update documents from your institution")
    
    # Update status
    old_status = doc.approval_status
    doc.approval_status = new_status
    
    if new_status in ["approved", "restricted_approved"]:
        doc.approved_by = current_user.id
        doc.approved_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "status": "success",
        "message": f"Status updated from '{old_status}' to '{new_status}'",
        "document_id": document_id,
        "new_status": new_status
    }



# ==================================================================
# POLICY COMPARISON ENDPOINT
# ==================================================================

class CompareRequest(BaseModel):
    document_ids: List[int]
    comparison_aspects: Optional[List[str]] = None


@router.post("/compare")
async def compare_documents(
    request: CompareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compare multiple policy documents using LLM analysis
    
    Args:
        document_ids: List of 2-5 document IDs to compare
        comparison_aspects: Optional list of aspects to compare
    
    Returns:
        Structured comparison matrix with extracted information
    
    Role-based access:
    - Users can only compare documents they have access to
    - Students/Public: Only approved public documents
    - University Admin: Public + their institution documents
    - MoE Admin/Developer: All documents
    """
    try:
        # Validate input
        if not request.document_ids or len(request.document_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 documents required for comparison"
            )
        
        if len(request.document_ids) > 5:
            raise HTTPException(
                status_code=400,
                detail="Maximum 5 documents can be compared at once"
            )
        
        # Fetch documents with role-based filtering
        documents = []
        for doc_id in request.document_ids:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            
            if not doc:
                raise HTTPException(
                    status_code=404,
                    detail=f"Document {doc_id} not found"
                )
            
            # Role-based access control
            has_access = False
            
            if current_user.role in ["developer", "moe_admin"]:
                # Full access
                has_access = True
            
            elif current_user.role == "university_admin":
                # Access to public + their institution
                if doc.visibility_level == "public":
                    has_access = True
                elif doc.institution_id == current_user.institution_id:
                    has_access = True
            
            elif current_user.role in ["document_officer", "student", "public_viewer"]:
                # Access to approved public documents only
                if doc.approval_status == "approved" and doc.visibility_level == "public":
                    has_access = True
                # Students can also see their institution's approved institution_only docs
                elif (current_user.role == "student" and 
                      doc.approval_status == "approved" and
                      doc.visibility_level == "institution_only" and
                      doc.institution_id == current_user.institution_id):
                    has_access = True
            
            if not has_access:
                raise HTTPException(
                    status_code=403,
                    detail=f"You don't have access to document {doc_id}"
                )
            
            # Get metadata
            metadata = db.query(DocumentMetadata).filter(
                DocumentMetadata.document_id == doc_id
            ).first()
            
            # Prepare document data
            doc_data = {
                "id": doc.id,
                "title": metadata.title if metadata and metadata.title else doc.filename,
                "filename": doc.filename,
                "text": doc.extracted_text or "",
                "approval_status": doc.approval_status,
                "visibility_level": doc.visibility_level,
                "metadata": {
                    "summary": metadata.summary if metadata else None,
                    "department": metadata.department if metadata else None,
                    "document_type": metadata.document_type if metadata else None,
                    "date_published": metadata.date_published.isoformat() if metadata and metadata.date_published else None
                }
            }
            
            documents.append(doc_data)
        
        # Import comparison tool
        from Agent.tools.comparison_tools import create_comparison_tool
        import os
        
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise HTTPException(
                status_code=500,
                detail="Google API key not configured"
            )
        
        # Create comparison tool
        comparison_tool = create_comparison_tool(google_api_key)
        
        # Perform comparison
        result = comparison_tool.compare_policies(
            documents,
            request.comparison_aspects
        )
        
        # Log audit trail
        audit_log = AuditLog(
            user_id=current_user.id,
            action="compare_documents",
            action_metadata={
                "document_ids": request.document_ids,
                "comparison_aspects": request.comparison_aspects,
                "status": result.get("status", "unknown")
            }
        )
        db.add(audit_log)
        db.commit()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {str(e)}"
        )


@router.post("/compare/conflicts")
async def detect_conflicts(
    request: CompareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Detect conflicts between policy documents
    
    Args:
        document_ids: List of 2-5 document IDs to analyze
    
    Returns:
        List of potential conflicts and contradictions
    
    Role-based access: Same as compare endpoint
    """
    try:
        # Validate input
        if not request.document_ids or len(request.document_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 documents required for conflict detection"
            )
        
        # Fetch documents with role-based filtering (same logic as compare)
        documents = []
        for doc_id in request.document_ids:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            
            if not doc:
                raise HTTPException(
                    status_code=404,
                    detail=f"Document {doc_id} not found"
                )
            
            # Role-based access control
            has_access = False
            
            if current_user.role in ["developer", "moe_admin"]:
                has_access = True
            elif current_user.role == "university_admin":
                if doc.visibility_level == "public" or doc.institution_id == current_user.institution_id:
                    has_access = True
            elif current_user.role in ["document_officer", "student", "public_viewer"]:
                if doc.approval_status == "approved" and doc.visibility_level == "public":
                    has_access = True
                elif (current_user.role == "student" and 
                      doc.approval_status == "approved" and
                      doc.visibility_level == "institution_only" and
                      doc.institution_id == current_user.institution_id):
                    has_access = True
            
            if not has_access:
                raise HTTPException(
                    status_code=403,
                    detail=f"You don't have access to document {doc_id}"
                )
            
            # Prepare document data
            doc_data = {
                "id": doc.id,
                "title": doc.filename,
                "text": doc.extracted_text or ""
            }
            
            documents.append(doc_data)
        
        # Import comparison tool
        from Agent.tools.comparison_tools import create_comparison_tool
        import os
        
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise HTTPException(
                status_code=500,
                detail="Google API key not configured"
            )
        
        # Create comparison tool
        comparison_tool = create_comparison_tool(google_api_key)
        
        # Detect conflicts
        result = comparison_tool.find_conflicts(documents)
        
        # Log audit trail
        audit_log = AuditLog(
            user_id=current_user.id,
            action="detect_conflicts",
            action_metadata={
                "document_ids": request.document_ids,
                "conflicts_found": len(result.get("conflicts", [])),
                "status": result.get("status", "unknown")
            }
        )
        db.add(audit_log)
        db.commit()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Conflict detection failed: {str(e)}"
        )
