"""Insights router for document analytics and intelligence"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, extract
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from collections import Counter
import json

from backend.database import (
    get_db, 
    Document, 
    DocumentMetadata, 
    AuditLog, 
    User,
    Institution
)
from backend.routers.auth_router import get_current_user

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/document-stats")
async def get_document_stats(
    category: Optional[str] = None,
    department: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive document statistics
    
    Returns:
    - Total documents
    - Documents by category
    - Documents by department
    - Documents by approval status
    - Documents by visibility level
    - Upload trends over time
    """
    try:
        # Base query with role-based filtering
        query = db.query(Document)
        
        # Apply role-based access control (respects institutional autonomy)
        if current_user.role == "developer":
            # Developer: Full access to all documents
            pass  # No filters
        
        elif current_user.role == "moe_admin":
            # MoE Admin: LIMITED access (respects institutional autonomy)
            query = query.filter(
                or_(
                    Document.visibility_level == "public",
                    Document.approval_status == "pending",
                    Document.institution_id == current_user.institution_id,
                    Document.uploader_id == current_user.id
                )
            )
        
        elif current_user.role == "university_admin":
            # University Admin: Public + their institution
            query = query.filter(
                or_(
                    Document.visibility_level == "public",
                    Document.institution_id == current_user.institution_id
                )
            )
        
        elif current_user.role == "document_officer":
            # Document Officer: Public + their institution
            query = query.filter(
                or_(
                    Document.visibility_level == "public",
                    Document.institution_id == current_user.institution_id
                )
            )
        
        elif current_user.role == "student":
            # Student: Approved public + their institution's approved institution_only
            query = query.filter(
                and_(
                    Document.approval_status == "approved",
                    or_(
                        Document.visibility_level == "public",
                        and_(
                            Document.visibility_level == "institution_only",
                            Document.institution_id == current_user.institution_id
                        )
                    )
                )
            )
        
        elif current_user.role == "public_viewer":
            # Public Viewer: Only approved public documents
            query = query.filter(
                and_(
                    Document.approval_status == "approved",
                    Document.visibility_level == "public"
                )
            )
        
        # Apply filters
        if category:
            query = query.join(DocumentMetadata).filter(
                DocumentMetadata.document_type == category
            )
        
        if department:
            query = query.join(DocumentMetadata).filter(
                DocumentMetadata.department == department
            )
        
        if date_from:
            date_from_obj = datetime.fromisoformat(date_from)
            query = query.filter(Document.uploaded_at >= date_from_obj)
        
        if date_to:
            date_to_obj = datetime.fromisoformat(date_to)
            query = query.filter(Document.uploaded_at <= date_to_obj)
        
        # Total documents
        total_documents = query.count()
        
        # Documents by category (document_type)
        category_stats = db.query(
            DocumentMetadata.document_type,
            func.count(Document.id).label('count')
        ).join(Document).filter(
            Document.id.in_([d.id for d in query.all()])
        ).group_by(DocumentMetadata.document_type).all()
        
        documents_by_category = {
            cat or "Uncategorized": count 
            for cat, count in category_stats
        }
        
        # Documents by department
        department_stats = db.query(
            DocumentMetadata.department,
            func.count(Document.id).label('count')
        ).join(Document).filter(
            Document.id.in_([d.id for d in query.all()])
        ).group_by(DocumentMetadata.department).all()
        
        documents_by_department = {
            dept or "Unknown": count 
            for dept, count in department_stats
        }
        
        # Documents by approval status
        status_stats = query.with_entities(
            Document.approval_status,
            func.count(Document.id).label('count')
        ).group_by(Document.approval_status).all()
        
        documents_by_status = {
            status: count 
            for status, count in status_stats
        }
        
        # Documents by visibility level
        visibility_stats = query.with_entities(
            Document.visibility_level,
            func.count(Document.id).label('count')
        ).group_by(Document.visibility_level).all()
        
        documents_by_visibility = {
            visibility: count 
            for visibility, count in visibility_stats
        }
        
        # Upload trends (last 30 days, grouped by day)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        upload_trends = db.query(
            func.date(Document.uploaded_at).label('date'),
            func.count(Document.id).label('count')
        ).filter(
            Document.uploaded_at >= thirty_days_ago
        ).group_by(func.date(Document.uploaded_at)).order_by('date').all()
        
        upload_timeline = [
            {
                "date": date.isoformat(),
                "count": count
            }
            for date, count in upload_trends
        ]
        
        # Recent uploads (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_uploads = query.filter(
            Document.uploaded_at >= seven_days_ago
        ).count()
        
        return {
            "total_documents": total_documents,
            "recent_uploads_7d": recent_uploads,
            "documents_by_category": documents_by_category,
            "documents_by_department": documents_by_department,
            "documents_by_status": documents_by_status,
            "documents_by_visibility": documents_by_visibility,
            "upload_timeline": upload_timeline,
            "filters_applied": {
                "category": category,
                "department": department,
                "date_from": date_from,
                "date_to": date_to
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching document stats: {str(e)}")


@router.get("/trending-topics")
async def get_trending_topics(
    limit: int = Query(20, ge=5, le=100),
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get trending topics from document keywords
    
    Returns:
    - Top keywords across all documents
    - Keyword frequency
    - Recent trending topics
    """
    try:
        # Get documents from last N days
        date_threshold = datetime.utcnow() - timedelta(days=days)
        
        # Base query with role-based filtering
        query = db.query(DocumentMetadata).join(Document).filter(
            Document.uploaded_at >= date_threshold
        )
        
        # Apply role-based access control (respects institutional autonomy)
        if current_user.role == "developer":
            pass  # Full access
        
        elif current_user.role == "moe_admin":
            # MoE Admin: LIMITED access
            query = query.filter(
                or_(
                    Document.visibility_level == "public",
                    Document.approval_status == "pending",
                    Document.institution_id == current_user.institution_id,
                    Document.uploader_id == current_user.id
                )
            )
        
        elif current_user.role == "university_admin":
            query = query.filter(
                or_(
                    Document.visibility_level == "public",
                    Document.institution_id == current_user.institution_id
                )
            )
        
        elif current_user.role == "document_officer":
            query = query.filter(
                or_(
                    Document.visibility_level == "public",
                    Document.institution_id == current_user.institution_id
                )
            )
        
        elif current_user.role == "student":
            query = query.filter(
                and_(
                    Document.approval_status == "approved",
                    or_(
                        Document.visibility_level == "public",
                        and_(
                            Document.visibility_level == "institution_only",
                            Document.institution_id == current_user.institution_id
                        )
                    )
                )
            )
        
        elif current_user.role == "public_viewer":
            query = query.filter(
                and_(
                    Document.approval_status == "approved",
                    Document.visibility_level == "public"
                )
            )
        
        # Get all keywords
        metadata_records = query.all()
        
        all_keywords = []
        all_topics = []
        
        for record in metadata_records:
            if record.keywords:
                all_keywords.extend(record.keywords)
            if record.key_topics:
                all_topics.extend(record.key_topics)
        
        # Count keyword frequencies
        keyword_counter = Counter(all_keywords)
        topic_counter = Counter(all_topics)
        
        # Get top keywords
        top_keywords = [
            {
                "keyword": keyword,
                "frequency": count,
                "percentage": round((count / len(metadata_records)) * 100, 2) if metadata_records else 0
            }
            for keyword, count in keyword_counter.most_common(limit)
        ]
        
        # Get top topics
        top_topics = [
            {
                "topic": topic,
                "frequency": count,
                "percentage": round((count / len(metadata_records)) * 100, 2) if metadata_records else 0
            }
            for topic, count in topic_counter.most_common(limit)
        ]
        
        return {
            "trending_keywords": top_keywords,
            "trending_topics": top_topics,
            "total_documents_analyzed": len(metadata_records),
            "date_range_days": days,
            "unique_keywords": len(keyword_counter),
            "unique_topics": len(topic_counter)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trending topics: {str(e)}")


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = Query(50, ge=10, le=200),
    activity_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent system activity
    
    Returns:
    - Recent uploads
    - Recent queries
    - Recent approvals
    - User activity
    """
    try:
        # Query audit logs
        query = db.query(AuditLog).order_by(desc(AuditLog.timestamp))
        
        # Filter by activity type if specified
        if activity_type:
            query = query.filter(AuditLog.action == activity_type)
        
        # Role-based filtering
        if current_user.role not in ["developer", "moe_admin"]:
            # Non-admins only see their own activity or public actions
            query = query.filter(AuditLog.user_id == current_user.id)
        
        recent_logs = query.limit(limit).all()
        
        # Format activity
        activities = []
        for log in recent_logs:
            user = db.query(User).filter(User.id == log.user_id).first()
            
            activity = {
                "id": log.id,
                "action": log.action,
                "user_name": user.name if user else "Unknown",
                "user_email": user.email if user else "Unknown",
                "timestamp": log.timestamp.isoformat(),
                "metadata": log.action_metadata
            }
            activities.append(activity)
        
        # Activity summary
        action_counts = db.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.action).all()
        
        activity_summary = {
            action: count 
            for action, count in action_counts
        }
        
        return {
            "recent_activities": activities,
            "activity_summary": activity_summary,
            "total_activities": len(activities)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent activity: {str(e)}")


@router.get("/search-analytics")
async def get_search_analytics(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get search query analytics
    
    Returns:
    - Top search queries
    - Search frequency
    - Search trends over time
    """
    try:
        # Only admins can see search analytics
        if current_user.role not in ["developer", "moe_admin"]:
            raise HTTPException(
                status_code=403, 
                detail="Only administrators can view search analytics"
            )
        
        date_threshold = datetime.utcnow() - timedelta(days=days)
        
        # Get search queries from audit logs
        search_logs = db.query(AuditLog).filter(
            and_(
                AuditLog.action == "search_query",
                AuditLog.timestamp >= date_threshold
            )
        ).all()
        
        # Extract queries
        queries = []
        for log in search_logs:
            if log.action_metadata and isinstance(log.action_metadata, dict):
                query_text = log.action_metadata.get("query", "")
                if query_text:
                    queries.append({
                        "query": query_text,
                        "timestamp": log.timestamp.isoformat(),
                        "user_id": log.user_id
                    })
        
        # Count query frequencies
        query_texts = [q["query"] for q in queries]
        query_counter = Counter(query_texts)
        
        top_queries = [
            {
                "query": query,
                "frequency": count
            }
            for query, count in query_counter.most_common(20)
        ]
        
        # Search trends over time
        search_trends = db.query(
            func.date(AuditLog.timestamp).label('date'),
            func.count(AuditLog.id).label('count')
        ).filter(
            and_(
                AuditLog.action == "search_query",
                AuditLog.timestamp >= date_threshold
            )
        ).group_by(func.date(AuditLog.timestamp)).order_by('date').all()
        
        search_timeline = [
            {
                "date": date.isoformat(),
                "count": count
            }
            for date, count in search_trends
        ]
        
        return {
            "top_queries": top_queries,
            "total_searches": len(queries),
            "unique_queries": len(query_counter),
            "search_timeline": search_timeline,
            "date_range_days": days
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching search analytics: {str(e)}")


@router.get("/user-activity")
async def get_user_activity(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user activity statistics
    
    Returns:
    - Most active users
    - User activity by role
    - Activity distribution
    """
    try:
        # Only admins can see user activity
        if current_user.role not in ["developer", "moe_admin"]:
            raise HTTPException(
                status_code=403, 
                detail="Only administrators can view user activity"
            )
        
        date_threshold = datetime.utcnow() - timedelta(days=days)
        
        # Most active users
        active_users = db.query(
            AuditLog.user_id,
            func.count(AuditLog.id).label('activity_count')
        ).filter(
            AuditLog.timestamp >= date_threshold
        ).group_by(AuditLog.user_id).order_by(desc('activity_count')).limit(10).all()
        
        most_active = []
        for user_id, count in active_users:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                most_active.append({
                    "user_id": user.id,
                    "user_name": user.name,
                    "user_email": user.email,
                    "role": user.role,
                    "activity_count": count
                })
        
        # Activity by role
        role_activity = db.query(
            User.role,
            func.count(AuditLog.id).label('count')
        ).join(AuditLog, User.id == AuditLog.user_id).filter(
            AuditLog.timestamp >= date_threshold
        ).group_by(User.role).all()
        
        activity_by_role = {
            role: count 
            for role, count in role_activity
        }
        
        # Total active users
        total_active_users = db.query(func.count(func.distinct(AuditLog.user_id))).filter(
            AuditLog.timestamp >= date_threshold
        ).scalar()
        
        return {
            "most_active_users": most_active,
            "activity_by_role": activity_by_role,
            "total_active_users": total_active_users,
            "date_range_days": days
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user activity: {str(e)}")


@router.get("/institution-stats")
async def get_institution_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get institution-wise statistics
    
    Returns:
    - Documents by institution
    - Users by institution
    - Activity by institution
    """
    try:
        # Only admins can see institution stats
        if current_user.role not in ["developer", "moe_admin"]:
            raise HTTPException(
                status_code=403, 
                detail="Only administrators can view institution statistics"
            )
        
        # Documents by institution
        doc_stats = db.query(
            Institution.name,
            func.count(Document.id).label('document_count')
        ).outerjoin(Document, Institution.id == Document.institution_id).group_by(
            Institution.name
        ).all()
        
        documents_by_institution = {
            name: count 
            for name, count in doc_stats
        }
        
        # Users by institution
        user_stats = db.query(
            Institution.name,
            func.count(User.id).label('user_count')
        ).outerjoin(User, Institution.id == User.institution_id).group_by(
            Institution.name
        ).all()
        
        users_by_institution = {
            name: count 
            for name, count in user_stats
        }
        
        # Get all institutions with details
        institutions = db.query(Institution).all()
        
        institution_details = []
        for inst in institutions:
            doc_count = db.query(func.count(Document.id)).filter(
                Document.institution_id == inst.id
            ).scalar()
            
            user_count = db.query(func.count(User.id)).filter(
                User.institution_id == inst.id
            ).scalar()
            
            institution_details.append({
                "id": inst.id,
                "name": inst.name,
                "type": inst.type,
                "location": inst.location,
                "document_count": doc_count,
                "user_count": user_count
            })
        
        return {
            "documents_by_institution": documents_by_institution,
            "users_by_institution": users_by_institution,
            "institution_details": institution_details,
            "total_institutions": len(institutions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching institution stats: {str(e)}")


@router.get("/dashboard-summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard summary
    
    Returns all key metrics in one call for dashboard display
    """
    try:
        # Total documents (role-based - respects institutional autonomy)
        doc_query = db.query(Document)
        
        if current_user.role == "developer":
            pass  # Full access
        
        elif current_user.role == "moe_admin":
            # MoE Admin: LIMITED access
            doc_query = doc_query.filter(
                or_(
                    Document.visibility_level == "public",
                    Document.approval_status == "pending",
                    Document.institution_id == current_user.institution_id,
                    Document.uploader_id == current_user.id
                )
            )
        
        elif current_user.role == "university_admin":
            doc_query = doc_query.filter(
                or_(
                    Document.visibility_level == "public",
                    Document.institution_id == current_user.institution_id
                )
            )
        
        elif current_user.role == "document_officer":
            doc_query = doc_query.filter(
                or_(
                    Document.visibility_level == "public",
                    Document.institution_id == current_user.institution_id
                )
            )
        
        elif current_user.role == "student":
            doc_query = doc_query.filter(
                and_(
                    Document.approval_status == "approved",
                    or_(
                        Document.visibility_level == "public",
                        and_(
                            Document.visibility_level == "institution_only",
                            Document.institution_id == current_user.institution_id
                        )
                    )
                )
            )
        
        elif current_user.role == "public_viewer":
            doc_query = doc_query.filter(
                and_(
                    Document.approval_status == "approved",
                    Document.visibility_level == "public"
                )
            )
        
        total_documents = doc_query.count()
        
        # Pending approvals (admin only)
        pending_approvals = 0
        if current_user.role in ["developer", "moe_admin", "university_admin"]:
            pending_query = db.query(Document).filter(
                Document.approval_status == "pending"
            )
            if current_user.role == "university_admin":
                pending_query = pending_query.filter(
                    Document.institution_id == current_user.institution_id
                )
            pending_approvals = pending_query.count()
        
        # Total users (admin only)
        total_users = 0
        if current_user.role in ["developer", "moe_admin"]:
            total_users = db.query(User).count()
        
        # Recent uploads (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_uploads = doc_query.filter(
            Document.uploaded_at >= seven_days_ago
        ).count()
        
        # Recent searches (last 7 days, admin only)
        recent_searches = 0
        if current_user.role in ["developer", "moe_admin"]:
            recent_searches = db.query(AuditLog).filter(
                and_(
                    AuditLog.action == "search_query",
                    AuditLog.timestamp >= seven_days_ago
                )
            ).count()
        
        # Top categories
        category_stats = db.query(
            DocumentMetadata.document_type,
            func.count(Document.id).label('count')
        ).join(Document).filter(
            Document.id.in_([d.id for d in doc_query.all()])
        ).group_by(DocumentMetadata.document_type).order_by(desc('count')).limit(5).all()
        
        top_categories = [
            {"category": cat or "Uncategorized", "count": count}
            for cat, count in category_stats
        ]
        
        return {
            "total_documents": total_documents,
            "pending_approvals": pending_approvals,
            "total_users": total_users,
            "recent_uploads_7d": recent_uploads,
            "recent_searches_7d": recent_searches,
            "top_categories": top_categories,
            "user_role": current_user.role
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard summary: {str(e)}")
