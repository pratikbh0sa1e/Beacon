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

# Try to import caching decorator
try:
    from fastapi_cache.decorator import cache
    CACHE_AVAILABLE = True
except ImportError:
    # Fallback no-op decorator if cache not installed
    def cache(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    CACHE_AVAILABLE = False

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
        initial_status = "approved" if current_user.role in ["ministry_admin", "developer"] else "draft"
        
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
            approved_by=current_user.id if current_user.role in ["ministry_admin", "developer"] else None,
            approved_at=datetime.utcnow() if current_user.role in ["ministry_admin", "developer"] else None
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


@router.get("/list")
@cache(expire=30)  # Cache for 30 seconds (adjust based on your needs)
async def list_documents(
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "recent",
    limit: int = 20,  # Reduced from 100 for better performance
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # ✅ Security: Require Login
):
    """
    List documents with Pagination, Search, Sorting, and Role-Based Security.
    ⚡ Optimized with caching, eager loading, and reduced default limit.
    
    Sort options:
    - recent: Most recent first (default)
    - oldest: Oldest first
    - title-asc: Title A-Z
    - title-desc: Title Z-A
    - department: By department name
    """
    from sqlalchemy.orm import joinedload, contains_eager
    
    # ✅ OPTIMIZED: Start with base query
    # We'll add eager loading after filters to avoid conflicts
    query = db.query(Document)
    
    # ==================================================================
    # 🔒 ROLE-BASED VISIBILITY LOGIC (Security through Obscurity + Access Control)
    # ==================================================================
    
    # 1. DEVELOPER: Full access to everything
    if current_user.role == "developer":
        pass  # No filters - sees all documents

    # 2. MOE ADMIN: Respects institutional autonomy
    elif current_user.role == "ministry_admin":
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
    elif current_user.role == "ministry_admin":
        # Ministry Admin: Only see documents from institutions under their ministry
        child_institution_ids = db.query(Institution.id).filter(
            Institution.parent_ministry_id == current_user.institution_id,
            Institution.deleted_at == None
        ).all()
        child_institution_ids = [inst_id[0] for inst_id in child_institution_ids]
        
        query = query.filter(
            or_(
                # Public approved documents (everyone sees)
                and_(
                    Document.approval_status == "approved",
                    Document.visibility_level == "public"
                ),
                # Documents from their institutions (any status)
                and_(
                    Document.institution_id.in_(child_institution_ids),
                    Document.approval_status.in_(["pending", "under_review", "changes_requested", "rejected", "approved", "draft"])
                ),
                # Their own uploads
                Document.uploader_id == current_user.id
            )
        )
    
    elif current_user.role == "university_admin":
        # University Admin: Only see documents from their institution
        query = query.filter(
            or_(
                # Public approved documents
                and_(
                    Document.approval_status == "approved",
                    Document.visibility_level == "public"
                ),
                # Documents from their institution (any status)
                Document.institution_id == current_user.institution_id,
                # Their own uploads
                Document.uploader_id == current_user.id
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

    # Category Filter - join metadata for filtering
    if category and category != "all":
        query = query.join(DocumentMetadata).filter(DocumentMetadata.document_type == category)

    # Search Filter - join metadata for searching
    if search:
        search_term = f"%{search}%"
        if not category or category == "all":
            query = query.outerjoin(DocumentMetadata)
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
    # Join metadata if needed for sorting
    if sort_by in ["title-asc", "title-desc", "department"]:
        if not category and not search:
            query = query.outerjoin(DocumentMetadata)
    
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
    
    # ✅ Add eager loading AFTER all filters to prevent N+1 queries
    query = query.options(
        joinedload(Document.doc_metadata_rel),
        joinedload(Document.uploader),
        joinedload(Document.institution)
    )
    
    if limit > 0:
        query = query.limit(limit).offset(offset)
        
    results = query.all()
    
    # Format Response - data is already loaded via eager loading
    documents = []
    for doc in results:
        meta = doc.doc_metadata_rel
        user = doc.uploader
        inst = doc.institution
        
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
async def get_document_vector_stats(document_id: int, db: Session = Depends(get_db)):
    """Get vector store statistics for a specific document using pgvector"""
    try:
        from Agent.vector_store.pgvector_store import PGVectorStore
        from backend.database import DocumentEmbedding
        
        # Check if document exists
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get embedding count from pgvector
        embedding_count = db.query(DocumentEmbedding).filter(
            DocumentEmbedding.document_id == document_id
        ).count()
        
        if embedding_count == 0:
            raise HTTPException(status_code=404, detail="No embeddings found for this document")
        
        return {
            "status": "success",
            "document_id": document_id,
            "stats": {
                "total_vectors": embedding_count,
                "dimension": 1024,
                "storage": "pgvector"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

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
        if user_role == "ministry_admin":
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
        if user_role == "ministry_admin":
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
        if current_user.role not in ["developer", "ministry_admin"] and current_user.id != doc.uploader_id:
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
    
    # Create notification for Ministry Admin of the parent ministry
    from backend.database import Notification
    
    # Get the institution to find its parent ministry
    institution = db.query(Institution).filter(Institution.id == doc.institution_id).first()
    
    if institution and institution.parent_ministry_id:
        # Get ministry admins of the parent ministry only
        ministry_admins = db.query(User).filter(
            User.role == "ministry_admin",
            User.institution_id == institution.parent_ministry_id
        ).all()
        
        for ministry_admin in ministry_admins:
            notification = Notification(
                user_id=ministry_admin.id,
                type="document_approval",
                title="New Document Pending Review",
                message=f"Document '{doc.filename}' has been submitted for approval by {current_user.name} from {institution.name}",
                priority="high",
                action_url=f"/approvals/{document_id}",
                action_metadata={
                    "document_id": document_id,
                    "submitter_id": current_user.id,
                    "institution_id": doc.institution_id,
                    "parent_ministry_id": institution.parent_ministry_id
                }
            )
            db.add(notification)
    else:
        # Fallback: If no parent ministry, notify all ministry admins (shouldn't happen)
        ministry_admins = db.query(User).filter(User.role == "ministry_admin").all()
        for ministry_admin in ministry_admins:
            notification = Notification(
                user_id=ministry_admin.id,
                type="document_approval",
                title="New Document Pending Review",
                message=f"Document '{doc.filename}' has been submitted for approval by {current_user.name}",
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
    elif current_user.role == "ministry_admin" and doc.requires_moe_approval:
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
    elif current_user.role == "ministry_admin" and doc.requires_moe_approval:
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
    elif current_user.role == "ministry_admin" and doc.requires_moe_approval:
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
    if current_user.role == "ministry_admin":
        # Ministry Admin sees documents from institutions under their ministry only
        # Get all institutions under this ministry
        child_institution_ids = db.query(Institution.id).filter(
            Institution.parent_ministry_id == current_user.institution_id,
            Institution.deleted_at == None
        ).all()
        child_institution_ids = [inst_id[0] for inst_id in child_institution_ids]
        
        query = query.filter(
            Document.approval_status == "pending",
            Document.requires_moe_approval == True,
            Document.institution_id.in_(child_institution_ids)  # Only from their institutions
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
    if current_user.role not in ["developer", "ministry_admin", "university_admin"]:
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
    
    Role-based access (respects institutional autonomy):
    - Developer: All documents
    - MoE Admin: Public + pending approval + their institution + their uploads
    - University Admin: Public + their institution
    - Document Officer: Public + their institution
    - Student: Approved public + their institution's approved institution_only
    - Public Viewer: Only approved public documents
    
    Users can only compare documents they have access to.
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
            
            # Role-based access control (matching existing document access rules)
            has_access = False
            
            # 1. DEVELOPER: Full access to everything
            if current_user.role == "developer":
                has_access = True
            
            # 2. MOE ADMIN: Respects institutional autonomy
            elif current_user.role == "ministry_admin":
                # MOE Admin can ONLY see:
                # a) Public documents
                # b) Documents pending approval (requires_moe_approval)
                # c) Documents from MOE institution (if MOE has institution_id)
                # d) Documents they uploaded
                if (doc.visibility_level == "public" or
                    doc.approval_status == "pending" or
                    doc.institution_id == current_user.institution_id or
                    doc.uploader_id == current_user.id):
                    has_access = True
            
            # 3. UNIVERSITY ADMIN: Public + their institution
            elif current_user.role == "university_admin":
                if (doc.visibility_level == "public" or
                    doc.institution_id == current_user.institution_id):
                    has_access = True
            
            # 4. DOCUMENT OFFICER: Public + their institution
            elif current_user.role == "document_officer":
                if (doc.visibility_level == "public" or
                    doc.institution_id == current_user.institution_id):
                    has_access = True
            
            # 5. STUDENT: Approved public + their institution's approved institution_only
            elif current_user.role == "student":
                if (doc.approval_status == "approved" and doc.visibility_level == "public"):
                    has_access = True
                elif (doc.approval_status == "approved" and
                      doc.visibility_level == "institution_only" and
                      doc.institution_id == current_user.institution_id):
                    has_access = True
            
            # 6. PUBLIC VIEWER: Only approved public documents
            elif current_user.role == "public_viewer":
                if (doc.approval_status == "approved" and doc.visibility_level == "public"):
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
            
            # Role-based access control (matching existing document access rules)
            has_access = False
            
            # 1. DEVELOPER: Full access
            if current_user.role == "developer":
                has_access = True
            
            # 2. MOE ADMIN: Limited access (respects institutional autonomy)
            elif current_user.role == "ministry_admin":
                if (doc.visibility_level == "public" or
                    doc.approval_status == "pending" or
                    doc.institution_id == current_user.institution_id or
                    doc.uploader_id == current_user.id):
                    has_access = True
            
            # 3. UNIVERSITY ADMIN: Public + their institution
            elif current_user.role == "university_admin":
                if (doc.visibility_level == "public" or
                    doc.institution_id == current_user.institution_id):
                    has_access = True
            
            # 4. DOCUMENT OFFICER: Public + their institution
            elif current_user.role == "document_officer":
                if (doc.visibility_level == "public" or
                    doc.institution_id == current_user.institution_id):
                    has_access = True
            
            # 5. STUDENT: Approved public + their institution's approved institution_only
            elif current_user.role == "student":
                if (doc.approval_status == "approved" and doc.visibility_level == "public"):
                    has_access = True
                elif (doc.approval_status == "approved" and
                      doc.visibility_level == "institution_only" and
                      doc.institution_id == current_user.institution_id):
                    has_access = True
            
            # 6. PUBLIC VIEWER: Only approved public documents
            elif current_user.role == "public_viewer":
                if (doc.approval_status == "approved" and doc.visibility_level == "public"):
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



# ==================================================================
# COMPLIANCE CHECKING ENDPOINT
# ==================================================================

class ComplianceRequest(BaseModel):
    checklist: List[str]
    strict_mode: Optional[bool] = False


@router.post("/{document_id}/check-compliance")
async def check_document_compliance(
    document_id: int,
    request: ComplianceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if document complies with given criteria
    
    Args:
        document_id: ID of document to check
        checklist: List of compliance criteria (max 20)
        strict_mode: If true, requires explicit evidence
    
    Returns:
        Compliance report with pass/fail for each criterion and evidence
    
    Role-based access (respects institutional autonomy):
    - Developer: Can check any document
    - MoE Admin: Can check public + pending + their institution + their uploads
    - University Admin: Can check public + their institution
    - Document Officer: Can check public + their institution
    - Student: Can check approved public + their institution's approved institution_only
    - Public Viewer: Can check approved public documents only
    
    Users can only check compliance of documents they have access to.
    """
    try:
        # Validate input
        if not request.checklist:
            raise HTTPException(
                status_code=400,
                detail="Checklist cannot be empty"
            )
        
        if len(request.checklist) > 20:
            raise HTTPException(
                status_code=400,
                detail="Maximum 20 checklist items allowed"
            )
        
        # Fetch document
        doc = db.query(Document).filter(Document.id == document_id).first()
        
        if not doc:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
        
        # Role-based access control (matching existing document access rules)
        has_access = False
        
        # 1. DEVELOPER: Full access
        if current_user.role == "developer":
            has_access = True
        
        # 2. MOE ADMIN: Limited access (respects institutional autonomy)
        elif current_user.role == "ministry_admin":
            if (doc.visibility_level == "public" or
                doc.approval_status == "pending" or
                doc.institution_id == current_user.institution_id or
                doc.uploader_id == current_user.id):
                has_access = True
        
        # 3. UNIVERSITY ADMIN: Public + their institution
        elif current_user.role == "university_admin":
            if (doc.visibility_level == "public" or
                doc.institution_id == current_user.institution_id):
                has_access = True
        
        # 4. DOCUMENT OFFICER: Public + their institution
        elif current_user.role == "document_officer":
            if (doc.visibility_level == "public" or
                doc.institution_id == current_user.institution_id):
                has_access = True
        
        # 5. STUDENT: Approved public + their institution's approved institution_only
        elif current_user.role == "student":
            if (doc.approval_status == "approved" and doc.visibility_level == "public"):
                has_access = True
            elif (doc.approval_status == "approved" and
                  doc.visibility_level == "institution_only" and
                  doc.institution_id == current_user.institution_id):
                has_access = True
        
        # 6. PUBLIC VIEWER: Only approved public documents
        elif current_user.role == "public_viewer":
            if (doc.approval_status == "approved" and doc.visibility_level == "public"):
                has_access = True
        
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail=f"You don't have access to document {document_id}"
            )
        
        # Get metadata
        metadata = db.query(DocumentMetadata).filter(
            DocumentMetadata.document_id == document_id
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
        
        # Import compliance checker
        from Agent.tools.compliance_tools import create_compliance_checker
        import os
        
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise HTTPException(
                status_code=500,
                detail="Google API key not configured"
            )
        
        # Create compliance checker
        compliance_checker = create_compliance_checker(google_api_key)
        
        # Perform compliance check
        result = compliance_checker.check_compliance(
            doc_data,
            request.checklist,
            request.strict_mode
        )
        
        # Log audit trail
        audit_log = AuditLog(
            user_id=current_user.id,
            action="check_compliance",
            action_metadata={
                "document_id": document_id,
                "checklist_items": len(request.checklist),
                "strict_mode": request.strict_mode,
                "status": result.get("status", "unknown"),
                "compliance_status": result.get("overall_compliance", {}).get("status", "unknown")
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
            detail=f"Compliance check failed: {str(e)}"
        )


@router.post("/{document_id}/compliance-report")
async def generate_compliance_report(
    document_id: int,
    request: ComplianceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate detailed compliance report with recommendations
    
    Args:
        document_id: ID of document to analyze
        checklist: List of compliance criteria
        strict_mode: If true, requires explicit evidence
    
    Returns:
        Detailed compliance report with actionable recommendations
    
    Role-based access: Same as check-compliance endpoint
    """
    try:
        # Validate input
        if not request.checklist:
            raise HTTPException(
                status_code=400,
                detail="Checklist cannot be empty"
            )
        
        # Fetch document with role-based access control
        doc = db.query(Document).filter(Document.id == document_id).first()
        
        if not doc:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
        
        # Role-based access control (same as check-compliance)
        has_access = False
        
        if current_user.role == "developer":
            has_access = True
        elif current_user.role == "ministry_admin":
            if (doc.visibility_level == "public" or
                doc.approval_status == "pending" or
                doc.institution_id == current_user.institution_id or
                doc.uploader_id == current_user.id):
                has_access = True
        elif current_user.role == "university_admin":
            if (doc.visibility_level == "public" or
                doc.institution_id == current_user.institution_id):
                has_access = True
        elif current_user.role == "document_officer":
            if (doc.visibility_level == "public" or
                doc.institution_id == current_user.institution_id):
                has_access = True
        elif current_user.role == "student":
            if (doc.approval_status == "approved" and doc.visibility_level == "public"):
                has_access = True
            elif (doc.approval_status == "approved" and
                  doc.visibility_level == "institution_only" and
                  doc.institution_id == current_user.institution_id):
                has_access = True
        elif current_user.role == "public_viewer":
            if (doc.approval_status == "approved" and doc.visibility_level == "public"):
                has_access = True
        
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail=f"You don't have access to document {document_id}"
            )
        
        # Get metadata
        metadata = db.query(DocumentMetadata).filter(
            DocumentMetadata.document_id == document_id
        ).first()
        
        # Prepare document data
        doc_data = {
            "id": doc.id,
            "title": metadata.title if metadata and metadata.title else doc.filename,
            "filename": doc.filename,
            "text": doc.extracted_text or "",
            "metadata": {
                "summary": metadata.summary if metadata else None,
                "department": metadata.department if metadata else None,
                "document_type": metadata.document_type if metadata else None
            }
        }
        
        # Import compliance checker
        from Agent.tools.compliance_tools import create_compliance_checker
        import os
        
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise HTTPException(
                status_code=500,
                detail="Google API key not configured"
            )
        
        # Create compliance checker
        compliance_checker = create_compliance_checker(google_api_key)
        
        # Generate detailed report
        result = compliance_checker.generate_compliance_report(
            doc_data,
            request.checklist
        )
        
        # Log audit trail
        audit_log = AuditLog(
            user_id=current_user.id,
            action="generate_compliance_report",
            action_metadata={
                "document_id": document_id,
                "checklist_items": len(request.checklist),
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
            detail=f"Report generation failed: {str(e)}"
        )



# ==================================================================
# CONFLICT DETECTION ENDPOINT
# ==================================================================

@router.get("/{document_id}/conflicts")
async def detect_document_conflicts(
    document_id: int,
    max_candidates: int = 3,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Detect conflicts between this document and other documents
    
    Uses lazy embedding strategy:
    1. Search by metadata to find potentially related documents
    2. Embed only top 3 candidates (if not already embedded)
    3. Use semantic search + LLM to detect actual conflicts
    
    Args:
        document_id: ID of document to check for conflicts
        max_candidates: Maximum number of documents to check (default: 3, max: 10)
    
    Returns:
        List of potential conflicts with severity and recommendations
    
    Role-based access (respects institutional autonomy):
    - Developer: Can check any document
    - MoE Admin: Can check public + pending + their institution + their uploads
    - University Admin: Can check public + their institution
    - Document Officer: Can check public + their institution
    - Student: Can check approved public + their institution's approved institution_only
    - Public Viewer: Can check approved public documents only
    
    Users can only check conflicts for documents they have access to.
    """
    try:
        # Validate input
        if max_candidates > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 candidates allowed"
            )
        
        # Fetch document
        doc = db.query(Document).filter(Document.id == document_id).first()
        
        if not doc:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
        
        # Role-based access control (matching existing document access rules)
        has_access = False
        
        # 1. DEVELOPER: Full access
        if current_user.role == "developer":
            has_access = True
        
        # 2. MOE ADMIN: Limited access (respects institutional autonomy)
        elif current_user.role == "ministry_admin":
            if (doc.visibility_level == "public" or
                doc.approval_status == "pending" or
                doc.institution_id == current_user.institution_id or
                doc.uploader_id == current_user.id):
                has_access = True
        
        # 3. UNIVERSITY ADMIN: Public + their institution
        elif current_user.role == "university_admin":
            if (doc.visibility_level == "public" or
                doc.institution_id == current_user.institution_id):
                has_access = True
        
        # 4. DOCUMENT OFFICER: Public + their institution
        elif current_user.role == "document_officer":
            if (doc.visibility_level == "public" or
                doc.institution_id == current_user.institution_id):
                has_access = True
        
        # 5. STUDENT: Approved public + their institution's approved institution_only
        elif current_user.role == "student":
            if (doc.approval_status == "approved" and doc.visibility_level == "public"):
                has_access = True
            elif (doc.approval_status == "approved" and
                  doc.visibility_level == "institution_only" and
                  doc.institution_id == current_user.institution_id):
                has_access = True
        
        # 6. PUBLIC VIEWER: Only approved public documents
        elif current_user.role == "public_viewer":
            if (doc.approval_status == "approved" and doc.visibility_level == "public"):
                has_access = True
        
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail=f"You don't have access to document {document_id}"
            )
        
        # Get metadata
        metadata = db.query(DocumentMetadata).filter(
            DocumentMetadata.document_id == document_id
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
                "keywords": metadata.keywords if metadata else [],
                "date_published": metadata.date_published.isoformat() if metadata and metadata.date_published else None
            }
        }
        
        # Import conflict detector
        from Agent.tools.conflict_detection import create_conflict_detector
        import os
        
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise HTTPException(
                status_code=500,
                detail="Google API key not configured"
            )
        
        # Create conflict detector
        conflict_detector = create_conflict_detector(google_api_key)
        
        # Detect conflicts
        result = conflict_detector.detect_conflicts(
            doc_data,
            db,
            current_user.role,
            current_user.institution_id,
            max_candidates
        )
        
        # Log audit trail
        audit_log = AuditLog(
            user_id=current_user.id,
            action="detect_conflicts",
            action_metadata={
                "document_id": document_id,
                "max_candidates": max_candidates,
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
