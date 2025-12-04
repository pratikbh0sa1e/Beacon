"""Institution management router"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from backend.database import get_db, Institution, User
from backend.routers.auth_router import get_current_user

router = APIRouter(tags=["institutions"])


class InstitutionCreate(BaseModel):
    name: str
    location: Optional[str] = None
    type: str  # university, ministry
    parent_ministry_id: Optional[int] = None  # Required for universities


class ParentMinistryInfo(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True


class InstitutionResponse(BaseModel):
    id: int
    name: str
    location: Optional[str]
    type: str
    user_count: int
    parent_ministry_id: Optional[int] = None  # For filtering in frontend
    parent_ministry: Optional[ParentMinistryInfo] = None
    child_universities_count: int = 0


class AssignUserRequest(BaseModel):
    institution_id: int


class DeleteInstitutionRequest(BaseModel):
    confirm: bool  # Must be True to proceed


@router.get("/public", response_model=List[InstitutionResponse])
async def list_institutions_public(
    type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Public endpoint to list all institutions (for registration)
    
    - No authentication required
    - Used during user registration to select institution
    """
    # Filter out deleted institutions
    query = db.query(Institution).filter(Institution.deleted_at == None)
    
    if type:
        query = query.filter(Institution.type == type)
    
    institutions = query.all()
    
    # Add user count and parent ministry info for each institution
    result = []
    for inst in institutions:
        user_count = db.query(User).filter(User.institution_id == inst.id).count()
        
        # Get child universities count if ministry
        child_count = 0
        if inst.type == "ministry":
            child_count = db.query(Institution).filter(Institution.parent_ministry_id == inst.id).count()
        
        result.append({
            "id": inst.id,
            "name": inst.name,
            "location": inst.location,
            "type": inst.type,
            "user_count": user_count,
            "parent_ministry_id": inst.parent_ministry_id,  # Add for filtering
            "parent_ministry": {
                "id": inst.parent_ministry.id,
                "name": inst.parent_ministry.name
            } if inst.parent_ministry else None,
            "child_universities_count": child_count
        })
    
    return result


@router.get("/list", response_model=List[InstitutionResponse])
async def list_institutions(
    type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List institutions based on user role
    
    - Developer: See all institutions
    - Ministry Admin: See their ministry + institutions under their ministry
    - University Admin: See their institution + parent ministry
    - Others: See all institutions (for registration/reference)
    """
    # Filter out deleted institutions
    query = db.query(Institution).filter(Institution.deleted_at == None)
    
    # Filter based on user role
    if current_user.role == "ministry_admin":
        # Ministry admin sees:
        # 1. Their own ministry
        # 2. All institutions under their ministry
        ministry_id = current_user.institution_id
        query = query.filter(
            (Institution.id == ministry_id) |  # Their ministry
            (Institution.parent_ministry_id == ministry_id)  # Institutions under their ministry
        )
    elif current_user.role == "university_admin":
        # University admin sees:
        # 1. Their own institution
        # 2. Their parent ministry
        user_institution = db.query(Institution).filter(Institution.id == current_user.institution_id).first()
        if user_institution:
            query = query.filter(
                (Institution.id == current_user.institution_id) |  # Their institution
                (Institution.id == user_institution.parent_ministry_id)  # Parent ministry
            )
    # Developer and other roles see all institutions
    
    # Apply type filter if provided
    if type:
        query = query.filter(Institution.type == type)
    
    institutions = query.all()
    
    # Add user count and parent ministry info for each institution
    result = []
    for inst in institutions:
        user_count = db.query(User).filter(User.institution_id == inst.id).count()
        
        # Get child universities count if ministry
        child_count = 0
        if inst.type == "ministry":
            child_count = db.query(Institution).filter(Institution.parent_ministry_id == inst.id).count()
        
        result.append({
            "id": inst.id,
            "name": inst.name,
            "location": inst.location,
            "type": inst.type,
            "user_count": user_count,
            "parent_ministry_id": inst.parent_ministry_id,  # Add for filtering
            "parent_ministry": {
                "id": inst.parent_ministry.id,
                "name": inst.parent_ministry.name
            } if inst.parent_ministry else None,
            "child_universities_count": child_count
        })
    
    return result


@router.post("/create", response_model=InstitutionResponse)
async def create_institution(
    request: InstitutionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new institution
    
    - Only developers can create ministries
    - Developers and ministry admins can create universities/departments
    """
    # Validate type first
    valid_types = ["university", "ministry"]
    if request.type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type. Must be one of: {valid_types}"
        )
    
    # Check permissions based on type
    if request.type == "ministry":
        # Only developer can create ministries
        if current_user.role != "developer":
            raise HTTPException(
                status_code=403, 
                detail="Only developers can create ministries"
            )
    elif request.type == "university":
        # Developer or ministry admin can create universities
        if current_user.role not in ["developer", "ministry_admin"]:
            raise HTTPException(
                status_code=403, 
                detail="Insufficient permissions to create institutions"
            )
    
    # Validate parent ministry for universities
    if request.type == "university":
        if not request.parent_ministry_id:
            raise HTTPException(
                status_code=400,
                detail="Universities must have a parent ministry"
            )
        # Verify parent is actually a ministry
        parent = db.query(Institution).filter(Institution.id == request.parent_ministry_id).first()
        if not parent or parent.type != "ministry":
            raise HTTPException(
                status_code=400,
                detail="Parent must be a ministry"
            )
    
    # Ministries should not have parent
    if request.type == "ministry" and request.parent_ministry_id:
        raise HTTPException(
            status_code=400,
            detail="Ministries cannot have a parent ministry"
        )
    
    # Check if institution already exists
    existing = db.query(Institution).filter(Institution.name == request.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Institution with this name already exists")
    
    # Create institution
    institution = Institution(
        name=request.name,
        location=request.location,
        type=request.type,
        parent_ministry_id=request.parent_ministry_id
    )
    
    db.add(institution)
    db.commit()
    db.refresh(institution)
    
    return {
        "id": institution.id,
        "name": institution.name,
        "location": institution.location,
        "type": institution.type,
        "user_count": 0,
        "parent_ministry": {
            "id": institution.parent_ministry.id,
            "name": institution.parent_ministry.name
        } if institution.parent_ministry else None,
        "child_universities_count": 0
    }


@router.patch("/assign-user/{user_id}")
async def assign_user_to_institution(
    user_id: int,
    request: AssignUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Assign a user to an institution
    
    - Only developers and MoE admins can assign users
    - Useful for transferring users between institutions
    """
    # Check permissions
    if current_user.role not in ["developer", "ministry_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find institution
    institution = db.query(Institution).filter(Institution.id == request.institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    # Update user's institution
    user.institution_id = request.institution_id
    db.commit()
    
    return {
        "status": "success",
        "message": f"User {user.email} assigned to {institution.name}",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "institution_id": user.institution_id
        }
    }


@router.get("/{institution_id}/users")
async def get_institution_users(
    institution_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all users in an institution
    
    - University admins can only see their own institution
    - MoE admins and developers can see any institution
    """
    # Check permissions
    if current_user.role == "university_admin":
        if current_user.institution_id != institution_id:
            raise HTTPException(status_code=403, detail="Can only view your own institution")
    elif current_user.role not in ["developer", "ministry_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Get institution
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    # Get users
    users = db.query(User).filter(User.institution_id == institution_id).all()
    
    return {
        "institution": {
            "id": institution.id,
            "name": institution.name,
            "type": institution.type
        },
        "users": users
    }



@router.delete("/{institution_id}")
async def delete_institution(
    institution_id: int,
    request: DeleteInstitutionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete an institution and convert users to public viewers
    
    - Only developers can delete ministries
    - Developers and ministry admins can delete institutions
    - All users converted to public viewers and notified
    """
    from datetime import datetime
    
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Confirmation required")
    
    # Get institution
    institution = db.query(Institution).filter(
        Institution.id == institution_id,
        Institution.deleted_at == None
    ).first()
    
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    # Check permissions
    if institution.type == "ministry":
        # Only developer can delete ministries
        if current_user.role != "developer":
            raise HTTPException(
                status_code=403, 
                detail="Only developers can delete ministries"
            )
        
        # Check for child institutions
        child_count = db.query(Institution).filter(
            Institution.parent_ministry_id == institution_id,
            Institution.deleted_at == None
        ).count()
        
        if child_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete ministry with {child_count} active institutions. Delete child institutions first."
            )
    
    elif institution.type == "university":
        # Developer or ministry admin can delete
        if current_user.role == "ministry_admin":
            # Must be under their ministry
            if institution.parent_ministry_id != current_user.institution_id:
                raise HTTPException(
                    status_code=403, 
                    detail="Can only delete institutions under your ministry"
                )
        elif current_user.role != "developer":
            raise HTTPException(
                status_code=403, 
                detail="Insufficient permissions"
            )
    
    # Get users in this institution
    users = db.query(User).filter(User.institution_id == institution_id).all()
    
    # Convert all users to public viewers
    for user in users:
        user.role = "public_viewer"
        user.institution_id = None
        user.approved = False  # Require re-approval
        
        # TODO: Send email notification
        # send_institution_closure_email(user, institution)
    
    # Soft delete institution
    institution.deleted_at = datetime.utcnow()
    institution.deleted_by = current_user.id
    
    db.commit()
    
    # TODO: Log action in audit_logs
    
    return {
        "status": "success",
        "message": f"Institution '{institution.name}' deleted successfully",
        "users_affected": len(users),
        "action": "All users converted to public viewers"
    }
