"""
Institution domain management router
Allows admins to manage email domain whitelists for institutions
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from backend.database import get_db, User, Institution
from backend.routers.auth_router import get_current_user
from backend.utils.email_validator import INSTITUTION_DOMAINS, add_institution_domain

router = APIRouter(prefix="/institution-domains", tags=["institution-domains"])


class DomainRequest(BaseModel):
    institution_id: int
    domain: str


class DomainListResponse(BaseModel):
    role: str
    domains: List[str]


@router.get("/list")
async def list_domains(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of all configured institution domains
    Only accessible by developers and MoE admins
    """
    if current_user.role not in ["developer", "ministry_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return {
        "ministry_admin": INSTITUTION_DOMAINS.get("ministry_admin", []),
        "university_admin": INSTITUTION_DOMAINS.get("university_admin", [])
    }


@router.post("/add")
async def add_domain(
    request: DomainRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a domain to institution whitelist
    Only accessible by developers and MoE admins
    """
    if current_user.role not in ["developer", "ministry_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Verify institution exists
    institution = db.query(Institution).filter(Institution.id == request.institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    # Determine role based on institution type
    if institution.type == "ministry":
        role = "ministry_admin"
    elif institution.type in ["university", "college"]:
        role = "university_admin"
    else:
        raise HTTPException(status_code=400, detail="Invalid institution type")
    
    # Add domain
    domain = request.domain.lower().strip()
    add_institution_domain(role, domain)
    
    return {
        "status": "success",
        "message": f"Domain {domain} added for {institution.name}",
        "role": role,
        "domain": domain
    }


@router.get("/institution/{institution_id}")
async def get_institution_domains(
    institution_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get domains for a specific institution
    """
    if current_user.role not in ["developer", "ministry_admin", "university_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    # Determine role
    if institution.type == "ministry":
        role = "ministry_admin"
    elif institution.type in ["university", "college"]:
        role = "university_admin"
    else:
        return {"institution": institution.name, "domains": []}
    
    domains = INSTITUTION_DOMAINS.get(role, [])
    
    return {
        "institution": institution.name,
        "type": institution.type,
        "role": role,
        "domains": domains
    }


@router.post("/bulk-add")
async def bulk_add_domains(
    domains: List[DomainRequest],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add multiple domains at once
    Only accessible by developers
    """
    if current_user.role != "developer":
        raise HTTPException(status_code=403, detail="Only developers can bulk add domains")
    
    added = []
    errors = []
    
    for domain_req in domains:
        try:
            institution = db.query(Institution).filter(Institution.id == domain_req.institution_id).first()
            if not institution:
                errors.append(f"Institution {domain_req.institution_id} not found")
                continue
            
            if institution.type == "ministry":
                role = "ministry_admin"
            elif institution.type in ["university", "college"]:
                role = "university_admin"
            else:
                errors.append(f"Invalid type for institution {institution.name}")
                continue
            
            domain = domain_req.domain.lower().strip()
            add_institution_domain(role, domain)
            added.append({"institution": institution.name, "domain": domain, "role": role})
            
        except Exception as e:
            errors.append(f"Error adding {domain_req.domain}: {str(e)}")
    
    return {
        "status": "success",
        "added": added,
        "errors": errors,
        "total_added": len(added),
        "total_errors": len(errors)
    }
