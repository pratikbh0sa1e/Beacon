"""Audit log router - view system activity logs"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from backend.database import get_db, AuditLog, User
from backend.routers.auth_router import get_current_user

router = APIRouter()


@router.get("/logs")
async def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(100, description="Maximum number of logs to return"),
    offset: int = Query(0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit logs
    
    - Developer sees all logs
    - MoE Admin sees logs for their scope
    - University Admin sees logs for their institution
    - Others cannot access audit logs
    """
    # Check permissions
    if current_user.role not in ["developer", "moe_admin", "university_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions to view audit logs")
    
    # Calculate date threshold
    date_threshold = datetime.utcnow() - timedelta(days=days)
    
    # Build query
    query = db.query(AuditLog).filter(AuditLog.timestamp >= date_threshold)
    
    # Apply filters
    if action:
        query = query.filter(AuditLog.action == action)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    # Role-based filtering
    if current_user.role == "university_admin":
        # University admins only see logs from users in their institution
        institution_user_ids = db.query(User.id).filter(
            User.institution_id == current_user.institution_id
        ).all()
        user_ids = [uid[0] for uid in institution_user_ids]
        query = query.filter(AuditLog.user_id.in_(user_ids))
    
    # Get total count
    total = query.count()
    
    # Apply pagination and order
    logs = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    # Enrich with user information
    result = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first()
        # result.append({
        #     "id": log.id,
        #     "action": log.action,
        #     "timestamp": log.timestamp,
        #     "user": {
        #         "id": user.id if user else None,
        #         "name": user.name if user else "Unknown",
        #         "email": user.email if user else "Unknown",
        #         "role": user.role if user else "Unknown"
        #     },
        #     "metadata": log.metadata
        # })
        result.append({
            "id": log.id,
            "action": log.action,
            "timestamp": log.timestamp,
            "user": {
                "id": user.id if user else None,
                "name": user.name if user else "Unknown",
                "email": user.email if user else "Unknown",
                "role": user.role if user else "Unknown"
            },
            "metadata": log.action_metadata  # ✅ Changed from log.metadata
        })
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "days": days,
        "logs": result
    }


@router.get("/actions")
async def get_action_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of all action types in the system"""
    if current_user.role not in ["developer", "moe_admin", "university_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Get distinct action types
    actions = db.query(AuditLog.action).distinct().all()
    action_list = [action[0] for action in actions]
    
    return {
        "actions": sorted(action_list),
        "description": {
            "login": "User logged in",
            "logout": "User logged out",
            "upload_document": "Document uploaded",
            "user_approved": "User registration approved",
            "user_rejected": "User registration rejected",
            "document_approved": "Document approved for access",
            "document_rejected": "Document rejected",
            "role_changed": "User role modified",
            "search_query": "AI search performed"
        }
    }


@router.get("/user/{user_id}/activity")
async def get_user_activity(
    user_id: int,
    days: int = Query(30, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get activity logs for a specific user
    
    - Admins can view activity for users in their scope
    - Users can view their own activity
    """
    # Check permissions
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Allow users to see their own logs
    if current_user.id != user_id:
        # Otherwise check admin permissions
        if current_user.role == "university_admin":
            if target_user.institution_id != current_user.institution_id:
                raise HTTPException(status_code=403, detail="Can only view activity for users in your institution")
        elif current_user.role not in ["developer", "moe_admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Calculate date threshold
    date_threshold = datetime.utcnow() - timedelta(days=days)
    
    # Get logs
    logs = db.query(AuditLog).filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= date_threshold
    ).order_by(AuditLog.timestamp.desc()).all()
    
    # Calculate statistics
    action_counts = {}
    for log in logs:
        action_counts[log.action] = action_counts.get(log.action, 0) + 1
    
    return {
        "user": {
            "id": target_user.id,
            "name": target_user.name,
            "email": target_user.email,
            "role": target_user.role
        },
        "period_days": days,
        "total_actions": len(logs),
        "action_counts": action_counts,
        "recent_activity": logs[:20]  # Last 20 activities
    }


@router.get("/summary")
async def get_audit_summary(
    days: int = Query(7, description="Number of days to summarize"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics of system activity
    
    - Only available to admins
    """
    if current_user.role not in ["developer", "moe_admin", "university_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Calculate date threshold
    date_threshold = datetime.utcnow() - timedelta(days=days)
    
    # Base query
    query = db.query(AuditLog).filter(AuditLog.timestamp >= date_threshold)
    
    # Role-based filtering
    if current_user.role == "university_admin":
        institution_user_ids = db.query(User.id).filter(
            User.institution_id == current_user.institution_id
        ).all()
        user_ids = [uid[0] for uid in institution_user_ids]
        query = query.filter(AuditLog.user_id.in_(user_ids))
    
    # Get all logs
    logs = query.all()
    
    # Calculate statistics
    total_actions = len(logs)
    unique_users = len(set(log.user_id for log in logs))
    
    action_counts = {}
    for log in logs:
        action_counts[log.action] = action_counts.get(log.action, 0) + 1
    
    # Most active users
    user_activity = {}
    for log in logs:
        user_activity[log.user_id] = user_activity.get(log.user_id, 0) + 1
    
    most_active = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:5]
    most_active_users = []
    for user_id, count in most_active:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            most_active_users.append({
                "user_id": user_id,
                "name": user.name,
                "email": user.email,
                "action_count": count
            })
    
    return {
        "period_days": days,
        "total_actions": total_actions,
        "unique_users": unique_users,
        "action_breakdown": action_counts,
        "most_active_users": most_active_users,
        "scope": current_user.role
    }