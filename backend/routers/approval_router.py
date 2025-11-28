"""Document approval workflow router"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from backend.database import get_db, Document, User, AuditLog
from backend.routers.auth_router import get_current_user

router = APIRouter()


class ApprovalRequest(BaseModel):
    notes: Optional[str] = None


def can_approve_document(user: User, document: Document) -> bool:
    """
    Check if user can approve a document based on visibility level
    
    - Public: Auto-approve OR University Admin
    - Institution-only: University Admin of that institution
    - Restricted: MoE Admin or Developer
    - Confidential: Developer only
    """
    if user.role == "developer":
        return True
    
    if document.visibility_level == "public":
        return user.role in ["university_admin", "moe_admin"]
    
    if document.visibility_level == "institution_only":
        return (user.role == "university_admin" and 
                user.institution_id == document.institution_id)
    
    if document.visibility_level == "restricted":
        return user.role in ["moe_admin", "developer"]
    
    if document.visibility_level == "confidential":
        return user.role == "developer"
    
    return False


@router.get("/documents/pending")
async def get_pending_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get documents pending approval based on user's role
    
    - Developer sees all pending documents
    - MoE Admin sees restricted and public documents
    - University Admin sees institution-only and public documents from their institution
    """
    if current_user.role not in ["developer", "moe_admin", "university_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Base query for pending documents
    query = db.query(Document).filter(Document.approval_status == "pending")
    
    # Filter based on role
    if current_user.role == "developer":
        # Developers see all pending documents
        pass
    elif current_user.role == "moe_admin":
        # MoE admins see restricted and public documents
        query = query.filter(Document.visibility_level.in_(["restricted", "public"]))
    elif current_user.role == "university_admin":
        # University admins see their institution's documents
        query = query.filter(
            Document.institution_id == current_user.institution_id,
            Document.visibility_level.in_(["institution_only", "public"])
        )
    
    documents = query.order_by(Document.uploaded_at.desc()).all()
    
    # Format response with uploader info
    result = []
    for doc in documents:
        uploader = db.query(User).filter(User.id == doc.uploader_id).first()
        result.append({
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "visibility_level": doc.visibility_level,
            "uploaded_at": doc.uploaded_at,
            "uploader": {
                "id": uploader.id if uploader else None,
                "name": uploader.name if uploader else "Unknown",
                "email": uploader.email if uploader else "Unknown"
            },
            "institution_id": doc.institution_id
        })
    
    return {"pending_documents": result}


@router.post("/documents/approve/{document_id}")
async def approve_document(
    document_id: int,
    request: ApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a pending document
    
    - Checks user has permission based on document visibility level
    - Updates document status to 'approved'
    - Logs the approval action
    """
    # Find document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if already approved
    if document.approval_status == "approved":
        raise HTTPException(status_code=400, detail="Document is already approved")
    
    # Check if rejected
    if document.approval_status == "rejected":
        raise HTTPException(status_code=400, detail="Cannot approve a rejected document")
    
    # Check permissions
    if not can_approve_document(current_user, document):
        raise HTTPException(
            status_code=403,
            detail=f"You don't have permission to approve {document.visibility_level} documents"
        )
    
    # Approve document
    document.approval_status = "approved"
    document.approved_by = current_user.id
    document.approved_at = datetime.utcnow()
    db.commit()
    
    # Log audit
    # audit = AuditLog(
    #     user_id=current_user.id,
    #     action="document_approved",
    #     metadata={
    #         "document_id": document_id,
    #         "filename": document.filename,
    #         "visibility_level": document.visibility_level,
    #         "notes": request.notes
    #     }
    # )
    audit = AuditLog(
        user_id=current_user.id,
        action="document_approved",
        action_metadata={  # ✅ Changed from 'metadata'
            "document_id": document_id,
            "filename": document.filename,
            "visibility_level": document.visibility_level,
            "notes": request.notes
        }
    )
    db.add(audit)
    db.commit()
    
    return {
        "status": "success",
        "message": f"Document '{document.filename}' has been approved",
        "document": {
            "id": document.id,
            "filename": document.filename,
            "approval_status": document.approval_status,
            "approved_by": current_user.name,
            "approved_at": document.approved_at
        }
    }


@router.post("/documents/reject/{document_id}")
async def reject_document(
    document_id: int,
    request: ApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a pending document
    
    - Same permissions as approval
    - Updates status to 'rejected'
    - Document becomes inaccessible for search
    """
    # Find document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if already processed
    if document.approval_status in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail=f"Document is already {document.approval_status}")
    
    # Check permissions
    if not can_approve_document(current_user, document):
        raise HTTPException(
            status_code=403,
            detail=f"You don't have permission to reject {document.visibility_level} documents"
        )
    
    # Reject document
    document.approval_status = "rejected"
    document.approved_by = current_user.id
    document.approved_at = datetime.utcnow()
    db.commit()
    
    # Log audit
    # audit = AuditLog(
    #     user_id=current_user.id,
    #     action="document_rejected",
    #     metadata={
    #         "document_id": document_id,
    #         "filename": document.filename,
    #         "visibility_level": document.visibility_level,
    #         "notes": request.notes
    #     }
    # )
    audit = AuditLog(
        user_id=current_user.id,
        action="document_rejected",
        action_metadata={  # ✅ Changed from 'metadata'
            "document_id": document_id,
            "filename": document.filename,
            "visibility_level": document.visibility_level,
            "notes": request.notes
        }
    )
    db.add(audit)
    db.commit()
    
    return {
        "status": "success",
        "message": f"Document '{document.filename}' has been rejected",
        "document": {
            "id": document.id,
            "filename": document.filename,
            "approval_status": document.approval_status
        }
    }


@router.get("/documents/history/{document_id}")
async def get_document_approval_history(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get approval history for a document"""
    # Find document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get approval/rejection logs
    logs = db.query(AuditLog).filter(
        AuditLog.metadata['document_id'].astext == str(document_id),
        AuditLog.action.in_(["document_approved", "document_rejected"])
    ).order_by(AuditLog.timestamp.desc()).all()
    
    # Get approver info if document is approved/rejected
    approver = None
    if document.approved_by:
        approver = db.query(User).filter(User.id == document.approved_by).first()
    
    return {
        "document": {
            "id": document.id,
            "filename": document.filename,
            "approval_status": document.approval_status,
            "approved_at": document.approved_at
        },
        "approver": {
            "id": approver.id if approver else None,
            "name": approver.name if approver else None,
            "role": approver.role if approver else None
        } if approver else None,
        "history": logs
    }