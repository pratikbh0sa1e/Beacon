"""User management router - handles user approval, role changes, and listing"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.database import get_db, User, AuditLog
from backend.routers.auth_router import get_current_user

router = APIRouter(prefix="/users", tags=["user-management"])


class UserListResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    institution_id: Optional[int]
    approved: bool
    created_at: datetime


class ApprovalRequest(BaseModel):
    notes: Optional[str] = None


class RoleChangeRequest(BaseModel):
    new_role: str
    notes: Optional[str] = None


def check_admin_permission(current_user: User, target_user: User) -> bool:
    """
    Check if current user has permission to manage target user
    
    - Developer can manage MoE admins
    - MoE admin can manage University admins
    - University admin can manage Document Officers and Students in their institution
    """
    # Developer can manage everyone
    if current_user.role == "developer":
        return True
    
    # MoE admin can manage university admins
    if current_user.role == "moe_admin" and target_user.role == "university_admin":
        return True
    
    # University admin can manage doc officers and students in their institution
    if current_user.role == "university_admin":
        if target_user.role in ["document_officer", "student"]:
            if current_user.institution_id == target_user.institution_id:
                return True
    
    return False


def log_audit(db: Session, user_id: int, action: str, metadata: dict):
    """Create audit log entry"""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        # metadata=metadata
        action_metadata=metadata  # ✅ Changed from 'metadata=metadata'

    )
    db.add(audit)
    db.commit()


@router.get("/list", response_model=List[UserListResponse])
async def list_users(
    role: Optional[str] = Query(None, description="Filter by role"),
    approved: Optional[bool] = Query(None, description="Filter by approval status"),
    institution_id: Optional[int] = Query(None, description="Filter by institution"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List users based on current user's permissions
    
    - Developer sees all users
    - MoE admin sees all users nationwide
    - University admin sees only users in their institution
    - Others cannot list users
    """
    # Check permissions
    if current_user.role not in ["developer", "moe_admin", "university_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Build query
    query = db.query(User)
    
    # Apply institution filter for university admin
    if current_user.role == "university_admin":
        query = query.filter(User.institution_id == current_user.institution_id)
    
    # Apply filters
    if role:
        query = query.filter(User.role == role)
    if approved is not None:
        query = query.filter(User.approved == approved)
    if institution_id and current_user.role in ["developer", "moe_admin"]:
        query = query.filter(User.institution_id == institution_id)
    
    users = query.order_by(User.created_at.desc()).all()
    return users


@router.post("/approve/{user_id}")
async def approve_user(
    user_id: int,
    request: ApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a pending user
    
    - Developer approves MoE admins
    - MoE admin approves University admins
    - University admin approves Document Officers and Students
    """
    # Find target user
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already approved
    if target_user.approved:
        raise HTTPException(status_code=400, detail="User is already approved")
    
    # Check permissions
    if not check_admin_permission(current_user, target_user):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to approve this user"
        )
    
    # Approve user
    target_user.approved = True
    db.commit()
    
    # Log audit
    log_audit(db, current_user.id, "user_approved", {
        "target_user_id": user_id,
        "target_email": target_user.email,
        "target_role": target_user.role,
        "notes": request.notes
    })
    
    return {
        "status": "success",
        "message": f"User {target_user.email} has been approved",
        "user": {
            "id": target_user.id,
            "name": target_user.name,
            "email": target_user.email,
            "role": target_user.role,
            "approved": target_user.approved
        }
    }


@router.post("/reject/{user_id}")
async def reject_user(
    user_id: int,
    request: ApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a pending user (deletes the user account)
    """
    # Find target user
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check permissions
    if not check_admin_permission(current_user, target_user):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to reject this user"
        )
    
    # Log audit before deletion
    log_audit(db, current_user.id, "user_rejected", {
        "target_user_id": user_id,
        "target_email": target_user.email,
        "target_role": target_user.role,
        "notes": request.notes
    })
    
    # Delete user
    db.delete(target_user)
    db.commit()
    
    return {
        "status": "success",
        "message": f"User {target_user.email} has been rejected and removed"
    }


@router.patch("/change-role/{user_id}")
async def change_user_role(
    user_id: int,
    request: RoleChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change a user's role (admin only)
    
    - Must have appropriate permissions
    - Cannot demote yourself
    - Logs the change in audit trail
    """
    # Find target user
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Cannot change your own role
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    # Validate new role
    valid_roles = ["student", "document_officer", "university_admin", "moe_admin", "developer"]
    if request.new_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    # Check permissions (only developer can change roles)
    if current_user.role != "developer":
        raise HTTPException(status_code=403, detail="Only developers can change user roles")
    
    # Store old role for audit
    old_role = target_user.role
    
    # Change role
    target_user.role = request.new_role
    db.commit()
    
    # Log audit
    log_audit(db, current_user.id, "role_changed", {
        "target_user_id": user_id,
        "target_email": target_user.email,
        "old_role": old_role,
        "new_role": request.new_role,
        "notes": request.notes
    })
    
    return {
        "status": "success",
        "message": f"User role changed from {old_role} to {request.new_role}",
        "user": {
            "id": target_user.id,
            "name": target_user.name,
            "email": target_user.email,
            "role": target_user.role
        }
    }


@router.get("/pending")
async def get_pending_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of users pending approval based on current user's role"""
    if current_user.role not in ["developer", "moe_admin", "university_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    query = db.query(User).filter(User.approved == False)
    
    # Filter based on role
    if current_user.role == "developer":
        # Developers see MoE admin requests
        query = query.filter(User.role == "moe_admin")
    elif current_user.role == "moe_admin":
        # MoE admins see university admin requests
        query = query.filter(User.role == "university_admin")
    elif current_user.role == "university_admin":
        # University admins see doc officers and students in their institution
        query = query.filter(
            User.role.in_(["document_officer", "student"]),
            User.institution_id == current_user.institution_id
        )
    
    pending_users = query.order_by(User.created_at.desc()).all()
    return pending_users