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
    type: str  # university, government_dept, ministry


class InstitutionResponse(BaseModel):
    id: int
    name: str
    location: Optional[str]
    type: str
    user_count: int


class AssignUserRequest(BaseModel):
    institution_id: int


@router.get("/list", response_model=List[InstitutionResponse])
async def list_institutions(
    type: Optional[str] = None,
    # current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all institutions
    
    - All authenticated users can view institutions
    - Optionally filter by type
    """
    query = db.query(Institution)
    
    if type:
        query = query.filter(Institution.type == type)
    
    institutions = query.all()
    
    # Add user count for each institution
    result = []
    for inst in institutions:
        user_count = db.query(User).filter(User.institution_id == inst.id).count()
        result.append({
            "id": inst.id,
            "name": inst.name,
            "location": inst.location,
            "type": inst.type,
            "user_count": user_count
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
    
    - Only developers and MoE admins can create institutions
    """
    # Check permissions
    if current_user.role not in ["developer", "moe_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Validate type
    valid_types = ["university", "government_dept", "ministry"]
    if request.type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type. Must be one of: {valid_types}"
        )
    
    # Check if institution already exists
    existing = db.query(Institution).filter(Institution.name == request.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Institution with this name already exists")
    
    # Create institution
    institution = Institution(
        name=request.name,
        location=request.location,
        type=request.type
    )
    
    db.add(institution)
    db.commit()
    db.refresh(institution)
    
    return {
        "id": institution.id,
        "name": institution.name,
        "location": institution.location,
        "type": institution.type,
        "user_count": 0
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
    if current_user.role not in ["developer", "moe_admin"]:
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
    elif current_user.role not in ["developer", "moe_admin"]:
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