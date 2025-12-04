"""
API endpoints for managing external data sources
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from backend.database import get_db, User, Notification
from backend.routers.auth_router import get_current_user
from Agent.data_ingestion.models import ExternalDataSource, SyncLog
from Agent.data_ingestion.db_connector import ExternalDBConnector
from Agent.data_ingestion.sync_service import SyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-sources", tags=["data-sources"])


# Pydantic models for request/response
class DataSourceCreate(BaseModel):
    name: str
    ministry_name: str
    description: Optional[str] = None
    host: str
    port: int = 5432
    database_name: str
    username: str
    password: str  # Will be encrypted before storage
    table_name: str
    file_column: str
    filename_column: str
    metadata_columns: Optional[List[str]] = None
    
    # Storage configuration (for files in Supabase/S3)
    storage_type: str = "database"  # "database" or "supabase"
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None  # Will be encrypted
    supabase_bucket: Optional[str] = None
    file_path_prefix: Optional[str] = None  # e.g., "resume/"
    
    sync_enabled: bool = True
    sync_frequency: str = "daily"


class DataSourceRequest(BaseModel):
    """Request model for Ministry/University admins"""
    name: str
    ministry_name: str
    description: Optional[str] = None
    host: str
    port: int = 5432
    database_name: str
    username: str
    password: str
    table_name: str
    file_column: str
    filename_column: str
    metadata_columns: Optional[List[str]] = None
    storage_type: str = "database"
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_bucket: Optional[str] = None
    file_path_prefix: Optional[str] = None
    
    # Classification (only for ministry admin)
    data_classification: Optional[str] = None  # public, educational, confidential
    request_notes: Optional[str] = None


class ApprovalAction(BaseModel):
    """Approve or reject request"""
    rejection_reason: Optional[str] = None


class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    ministry_name: Optional[str] = None
    description: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    table_name: Optional[str] = None
    file_column: Optional[str] = None
    filename_column: Optional[str] = None
    metadata_columns: Optional[List[str]] = None
    storage_type: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_bucket: Optional[str] = None
    file_path_prefix: Optional[str] = None
    sync_enabled: Optional[bool] = None
    sync_frequency: Optional[str] = None


class ConnectionTest(BaseModel):
    host: str
    port: int = 5432
    database_name: str
    username: str
    password: str


@router.post("/request")
async def request_data_source(
    request: DataSourceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a data source connection request
    
    - Ministry Admin can request with classification
    - University Admin can request (auto-classified as institutional)
    """
    # Check permissions
    if current_user.role not in ["ministry_admin", "university_admin"]:
        raise HTTPException(
            status_code=403, 
            detail="Only Ministry or University Admins can request data sources"
        )
    
    # Validate institution association
    if not current_user.institution_id:
        raise HTTPException(
            status_code=400,
            detail="User must be associated with an institution to request data sources"
        )
    
    try:
        # Validate required fields
        if not request.name or not request.name.strip():
            raise HTTPException(status_code=400, detail="Data source name is required")
        
        if not request.host or not request.host.strip():
            raise HTTPException(status_code=400, detail="Database host is required")
        
        if not request.database_name or not request.database_name.strip():
            raise HTTPException(status_code=400, detail="Database name is required")
        
        if not request.username or not request.username.strip():
            raise HTTPException(status_code=400, detail="Database username is required")
        
        if not request.password or not request.password.strip():
            raise HTTPException(status_code=400, detail="Database password is required")
        
        # Validate port range
        if request.port < 1 or request.port > 65535:
            raise HTTPException(
                status_code=400, 
                detail="Port must be between 1 and 65535"
            )
        
        # Check if name already exists
        existing = db.query(ExternalDataSource).filter(
            ExternalDataSource.name == request.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Data source with this name already exists"
            )
        
        # Validate data classification for ministry admins
        valid_classifications = ["public", "educational", "confidential", "institutional"]
        if current_user.role == "ministry_admin" and request.data_classification:
            if request.data_classification not in valid_classifications:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid data classification. Must be one of: {', '.join(valid_classifications)}"
                )
        
        # Encrypt password
        try:
            connector = ExternalDBConnector()
            encrypted_password = connector.encrypt_password(request.password)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to encrypt password: {str(e)}"
            )
        
        # Encrypt Supabase key if provided
        encrypted_supabase_key = None
        if request.supabase_key:
            try:
                encrypted_supabase_key = connector.encrypt_password(request.supabase_key)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to encrypt Supabase key: {str(e)}"
                )
        
        # Determine classification
        if current_user.role == "university_admin":
            # University admin - always institutional
            data_classification = "institutional"
            institution_id = current_user.institution_id
        else:
            # Ministry admin - use provided classification
            data_classification = request.data_classification or "educational"
            institution_id = current_user.institution_id
        
        # Create data source request
        new_source = ExternalDataSource(
            name=request.name,
            ministry_name=request.ministry_name,
            description=request.description,
            db_type="postgresql",
            host=request.host,
            port=request.port,
            database_name=request.database_name,
            username=request.username,
            password_encrypted=encrypted_password,
            table_name=request.table_name,
            file_column=request.file_column,
            filename_column=request.filename_column,
            metadata_columns=request.metadata_columns,
            storage_type=request.storage_type,
            supabase_url=request.supabase_url,
            supabase_key_encrypted=encrypted_supabase_key,
            supabase_bucket=request.supabase_bucket,
            file_path_prefix=request.file_path_prefix,
            
            # Request workflow fields
            institution_id=institution_id,
            requested_by_user_id=current_user.id,
            request_status="pending",
            data_classification=data_classification,
            request_notes=request.request_notes,
            requested_at=datetime.utcnow(),
            
            # Sync disabled until approved
            sync_enabled=False,
            sync_frequency="daily"
        )
        
        db.add(new_source)
        db.commit()
        db.refresh(new_source)
        
        # TODO: Send notification to developers
        
        return {
            "status": "success",
            "message": "Data source request submitted successfully. Awaiting developer approval.",
            "request_id": new_source.id,
            "name": new_source.name,
            "request_status": new_source.request_status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-requests")
async def get_my_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's data source requests
    
    - Ministry/University admins see their own requests
    """
    if current_user.role not in ["ministry_admin", "university_admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    requests = db.query(ExternalDataSource).filter(
        ExternalDataSource.requested_by_user_id == current_user.id
    ).order_by(ExternalDataSource.requested_at.desc()).all()
    
    return {
        "total": len(requests),
        "requests": [
            {
                "id": r.id,
                "name": r.name,
                "ministry_name": r.ministry_name,
                "description": r.description,
                "request_status": r.request_status,
                "data_classification": r.data_classification,
                "request_notes": r.request_notes,
                "rejection_reason": r.rejection_reason,
                "requested_at": r.requested_at,
                "approved_at": r.approved_at,
                "approved_by": {
                    "id": r.approved_by.id if r.approved_by else None,
                    "name": r.approved_by.name if r.approved_by else None,
                    "email": r.approved_by.email if r.approved_by else None
                } if r.approved_by else None,
                "last_sync_at": r.last_sync_at,
                "total_documents_synced": r.total_documents_synced
            }
            for r in requests
        ]
    }


@router.get("/requests/pending")
async def get_pending_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all pending data source requests
    
    - Only developers can view pending requests
    """
    if current_user.role != "developer":
        raise HTTPException(status_code=403, detail="Developer access only")
    
    requests = db.query(ExternalDataSource).filter(
        ExternalDataSource.request_status == "pending"
    ).order_by(ExternalDataSource.requested_at.desc()).all()
    
    return {
        "total": len(requests),
        "requests": [
            {
                "id": r.id,
                "name": r.name,
                "ministry_name": r.ministry_name,
                "description": r.description,
                "host": r.host,
                "port": r.port,
                "database_name": r.database_name,
                "username": r.username,
                "table_name": r.table_name,
                "data_classification": r.data_classification,
                "request_notes": r.request_notes,
                "requested_by": {
                    "id": r.requested_by.id if r.requested_by else None,
                    "name": r.requested_by.name if r.requested_by else None,
                    "email": r.requested_by.email if r.requested_by else None,
                    "role": r.requested_by.role if r.requested_by else None
                },
                "institution": {
                    "id": r.institution.id if r.institution else None,
                    "name": r.institution.name if r.institution else None
                },
                "requested_at": r.requested_at
            }
            for r in requests
        ]
    }


@router.get("/active")
async def get_active_sources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active data sources (approved, active, or failed)
    
    - Only developers can view active sources
    """
    if current_user.role != "developer":
        raise HTTPException(status_code=403, detail="Developer access only")
    
    # Active sources include approved, active, and failed statuses
    # (failed sources were approved but sync failed)
    sources = db.query(ExternalDataSource).filter(
        ExternalDataSource.request_status.in_(["approved", "active", "failed"])
    ).order_by(ExternalDataSource.approved_at.desc()).all()
    
    return {
        "total": len(sources),
        "sources": [
            {
                "id": s.id,
                "name": s.name,
                "ministry_name": s.ministry_name,
                "description": s.description,
                "db_type": s.db_type,
                "host": s.host,
                "port": s.port,
                "database_name": s.database_name,
                "table_name": s.table_name,
                "request_status": s.request_status,
                "data_classification": s.data_classification,
                "institution": {
                    "id": s.institution.id if s.institution else None,
                    "name": s.institution.name if s.institution else None,
                    "type": s.institution.type if s.institution else None
                },
                "requested_by": {
                    "id": s.requested_by.id if s.requested_by else None,
                    "name": s.requested_by.name if s.requested_by else None,
                    "email": s.requested_by.email if s.requested_by else None
                },
                "approved_by": {
                    "id": s.approved_by.id if s.approved_by else None,
                    "name": s.approved_by.name if s.approved_by else None,
                    "email": s.approved_by.email if s.approved_by else None
                } if s.approved_by else None,
                "sync_enabled": s.sync_enabled,
                "last_sync_at": s.last_sync_at,
                "last_sync_status": s.last_sync_status,
                "last_sync_message": s.last_sync_message,
                "total_documents_synced": s.total_documents_synced,
                "requested_at": s.requested_at,
                "approved_at": s.approved_at
            }
            for s in sources
        ]
    }


@router.post("/requests/{request_id}/approve")
async def approve_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Approve a data source request
    
    - Only developers can approve
    - Starts sync automatically
    """
    if current_user.role != "developer":
        raise HTTPException(
            status_code=403, 
            detail="Developer access only"
        )
    
    # Validate request_id
    if request_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid request ID"
        )
    
    source = db.query(ExternalDataSource).filter(
        ExternalDataSource.id == request_id
    ).first()
    
    if not source:
        raise HTTPException(
            status_code=404, 
            detail="Request not found"
        )
    
    if source.request_status != "pending":
        raise HTTPException(
            status_code=400, 
            detail=f"Request is already {source.request_status}. Only pending requests can be approved."
        )
    
    try:
        # Update status
        source.request_status = "approved"
        source.approved_by_user_id = current_user.id
        source.approved_at = datetime.utcnow()
        source.sync_enabled = True
        
        db.commit()
        db.refresh(source)
        
        # Send notification to requester
        notification = Notification(
            user_id=source.requested_by_user_id,
            type="data_source_approved",
            title="Data Source Request Approved",
            message=f"Your data source request '{source.name}' has been approved by {current_user.name}. Synchronization has started.",
            priority="high",
            action_url=f"/admin/my-data-source-requests",
            action_label="View Request",
            action_metadata={
                "source_id": source.id,
                "source_name": source.name,
                "approved_by": current_user.name,
                "approved_by_id": current_user.id
            }
        )
        db.add(notification)
        db.commit()
        
        # Start sync in background
        def run_sync():
            from backend.database import SessionLocal
            bg_db = SessionLocal()
            try:
                sync_service = SyncService()
                sync_service.sync_source(request_id, bg_db)
            except Exception as sync_error:
                # Log sync error but don't fail the approval
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Sync failed for source {request_id}: {str(sync_error)}")
            finally:
                bg_db.close()
        
        background_tasks.add_task(run_sync)
        
        return {
            "status": "success",
            "message": f"Data source '{source.name}' approved. Sync started.",
            "source_id": source.id,
            "approved_at": source.approved_at,
            "approved_by": current_user.name
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to approve request: {str(e)}"
        )


@router.post("/requests/{request_id}/reject")
async def reject_request(
    request_id: int,
    action: ApprovalAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a data source request
    
    - Only developers can reject
    - Requires rejection reason
    """
    if current_user.role != "developer":
        raise HTTPException(
            status_code=403, 
            detail="Developer access only"
        )
    
    # Validate request_id
    if request_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid request ID"
        )
    
    # Validate rejection reason
    if not action.rejection_reason or not action.rejection_reason.strip():
        raise HTTPException(
            status_code=400, 
            detail="Rejection reason is required and cannot be empty"
        )
    
    if len(action.rejection_reason.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Rejection reason must be at least 10 characters"
        )
    
    source = db.query(ExternalDataSource).filter(
        ExternalDataSource.id == request_id
    ).first()
    
    if not source:
        raise HTTPException(
            status_code=404, 
            detail="Request not found"
        )
    
    if source.request_status != "pending":
        raise HTTPException(
            status_code=400, 
            detail=f"Request is already {source.request_status}. Only pending requests can be rejected."
        )
    
    try:
        # Update status
        source.request_status = "rejected"
        source.approved_by_user_id = current_user.id
        source.approved_at = datetime.utcnow()
        source.rejection_reason = action.rejection_reason.strip()
        source.sync_enabled = False
        
        # Delete stored credentials as per requirement 8.4
        source.password_encrypted = None
        if source.supabase_key_encrypted:
            source.supabase_key_encrypted = None
        
        db.commit()
        db.refresh(source)
        
        # Send notification to requester with rejection reason
        notification = Notification(
            user_id=source.requested_by_user_id,
            type="data_source_rejected",
            title="Data Source Request Rejected",
            message=f"Your data source request '{source.name}' has been rejected by {current_user.name}. Reason: {action.rejection_reason}",
            priority="high",
            action_url=f"/admin/my-data-source-requests",
            action_label="View Request",
            action_metadata={
                "source_id": source.id,
                "source_name": source.name,
                "rejected_by": current_user.name,
                "rejected_by_id": current_user.id,
                "rejection_reason": action.rejection_reason
            }
        )
        db.add(notification)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Data source '{source.name}' rejected. Credentials have been deleted.",
            "rejection_reason": action.rejection_reason,
            "rejected_by": current_user.name,
            "rejected_at": source.approved_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to reject request: {str(e)}"
        )


@router.post("/create")
async def create_data_source(
    source: DataSourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register a new external data source (Direct creation - Developer only)
    
    - Only developers can create data sources directly
    - For Ministry/University admins, use /request endpoint
    """
    # Check permissions
    if current_user.role != "developer":
        raise HTTPException(status_code=403, detail="Developer access only")
   
    try:
        # Check if name already exists
        existing = db.query(ExternalDataSource).filter(
            ExternalDataSource.name == source.name
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Data source with this name already exists")
        
        # Encrypt password
        connector = ExternalDBConnector()
        encrypted_password = connector.encrypt_password(source.password)
        
        # Encrypt Supabase key if provided
        encrypted_supabase_key = None
        if source.supabase_key:
            encrypted_supabase_key = connector.encrypt_password(source.supabase_key)
        
        # Create data source
        new_source = ExternalDataSource(
            name=source.name,
            ministry_name=source.ministry_name,
            description=source.description,
            db_type="postgresql",
            host=source.host,
            port=source.port,
            database_name=source.database_name,
            username=source.username,
            password_encrypted=encrypted_password,
            table_name=source.table_name,
            file_column=source.file_column,
            filename_column=source.filename_column,
            metadata_columns=source.metadata_columns,
            storage_type=source.storage_type,
            supabase_url=source.supabase_url,
            supabase_key_encrypted=encrypted_supabase_key,
            supabase_bucket=source.supabase_bucket,
            file_path_prefix=source.file_path_prefix,
            sync_enabled=source.sync_enabled,
            sync_frequency=source.sync_frequency
        )
        
        db.add(new_source)
        db.commit()
        db.refresh(new_source)
        
        return {
            "status": "success",
            "message": "Data source created successfully",
            "source_id": new_source.id,
            "name": new_source.name
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_data_sources(
    ministry_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all registered data sources
    
    - Only developers can view data sources
    """
    # Check permissions
    if current_user.role != "developer":
        raise HTTPException(status_code=403, detail="Developer access only")
    query = db.query(ExternalDataSource)
    
    if ministry_name:
        query = query.filter(ExternalDataSource.ministry_name.ilike(f"%{ministry_name}%"))
    
    sources = query.all()
    
    return {
        "total": len(sources),
        "sources": [
            {
                "id": s.id,
                "name": s.name,
                "ministry_name": s.ministry_name,
                "description": s.description,
                "host": s.host,
                "database_name": s.database_name,
                "sync_enabled": s.sync_enabled,
                "sync_frequency": s.sync_frequency,
                "last_sync_at": s.last_sync_at,
                "last_sync_status": s.last_sync_status,
                "total_documents_synced": s.total_documents_synced,
                "created_at": s.created_at
            }
            for s in sources
        ]
    }


@router.get("/{source_id}")
async def get_data_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific data source
    
    - Only developers can view data sources
    """
    # Check permissions
    if current_user.role != "developer":
        raise HTTPException(status_code=403, detail="Developer access only")
    source = db.query(ExternalDataSource).filter(
        ExternalDataSource.id == source_id
    ).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    return {
        "id": source.id,
        "name": source.name,
        "ministry_name": source.ministry_name,
        "description": source.description,
        "host": source.host,
        "port": source.port,
        "database_name": source.database_name,
        "username": source.username,
        "table_name": source.table_name,
        "file_column": source.file_column,
        "filename_column": source.filename_column,
        "metadata_columns": source.metadata_columns,
        "sync_enabled": source.sync_enabled,
        "sync_frequency": source.sync_frequency,
        "last_sync_at": source.last_sync_at,
        "last_sync_status": source.last_sync_status,
        "last_sync_message": source.last_sync_message,
        "total_documents_synced": source.total_documents_synced,
        "created_at": source.created_at,
        "updated_at": source.updated_at
    }


@router.put("/{source_id}")
async def update_data_source(
    source_id: int,
    updates: DataSourceUpdate,
    db: Session = Depends(get_db)
):
    """
    Update data source configuration
    """
    source = db.query(ExternalDataSource).filter(
        ExternalDataSource.id == source_id
    ).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    try:
        # Update fields
        update_data = updates.dict(exclude_unset=True)
        
        # Handle password encryption if provided
        if "password" in update_data:
            connector = ExternalDBConnector()
            update_data["password_encrypted"] = connector.encrypt_password(update_data.pop("password"))
        
        for key, value in update_data.items():
            setattr(source, key, value)
        
        source.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "success",
            "message": "Data source updated successfully"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{source_id}")
async def delete_data_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a data source
    
    - Only developers can delete data sources
    """
    # Check permissions
    if current_user.role != "developer":
        raise HTTPException(status_code=403, detail="Developer access only")
    source = db.query(ExternalDataSource).filter(
        ExternalDataSource.id == source_id
    ).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    try:
        db.delete(source)
        db.commit()
        
        return {
            "status": "success",
            "message": "Data source deleted successfully"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{source_id}/revoke-access")
async def revoke_access(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke access to a data source by deleting credentials
    
    - Only developers can revoke access
    - Credentials are deleted but source record is preserved for audit trail
    - Requirement 8.5
    """
    # Check permissions
    if current_user.role != "developer":
        raise HTTPException(status_code=403, detail="Developer access only")
    
    source = db.query(ExternalDataSource).filter(
        ExternalDataSource.id == source_id
    ).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    try:
        # Delete credentials
        source.password_encrypted = None
        if source.supabase_key_encrypted:
            source.supabase_key_encrypted = None
        
        # Disable sync
        source.sync_enabled = False
        source.last_sync_status = "revoked"
        source.last_sync_message = f"Access revoked by {current_user.name} on {datetime.utcnow()}"
        
        db.commit()
        db.refresh(source)
        
        # Send notification to requester
        if source.requested_by_user_id:
            notification = Notification(
                user_id=source.requested_by_user_id,
                type="data_source_revoked",
                title="Data Source Access Revoked",
                message=f"Access to data source '{source.name}' has been revoked by {current_user.name}. All credentials have been deleted.",
                priority="high",
                action_url=f"/admin/my-data-source-requests",
                action_label="View Details",
                action_metadata={
                    "source_id": source.id,
                    "source_name": source.name,
                    "revoked_by": current_user.name,
                    "revoked_by_id": current_user.id
                }
            )
            db.add(notification)
            db.commit()
        
        return {
            "status": "success",
            "message": f"Access to data source '{source.name}' has been revoked. Credentials deleted.",
            "source_id": source.id,
            "revoked_by": current_user.name
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-connection")
async def test_connection(
    connection: ConnectionTest
):
    """
    Test connection to external database
    
    Returns connection status without storing credentials
    """
    # Validate required fields
    if not connection.host or not connection.host.strip():
        return {
            "status": "failed",
            "error_code": "VALIDATION_ERROR",
            "message": "Database host is required"
        }
    
    if not connection.database_name or not connection.database_name.strip():
        return {
            "status": "failed",
            "error_code": "VALIDATION_ERROR",
            "message": "Database name is required"
        }
    
    if not connection.username or not connection.username.strip():
        return {
            "status": "failed",
            "error_code": "VALIDATION_ERROR",
            "message": "Database username is required"
        }
    
    if not connection.password or not connection.password.strip():
        return {
            "status": "failed",
            "error_code": "VALIDATION_ERROR",
            "message": "Database password is required"
        }
    
    # Validate port range
    if connection.port < 1 or connection.port > 65535:
        return {
            "status": "failed",
            "error_code": "VALIDATION_ERROR",
            "message": "Port must be between 1 and 65535"
        }
    
    try:
        connector = ExternalDBConnector()
        result = connector.test_connection(
            host=connection.host,
            port=connection.port,
            database=connection.database_name,
            username=connection.username,
            password=connection.password
        )
        return result
    
    except ValueError as e:
        # Encryption key not configured
        return {
            "status": "failed",
            "error_code": "CONFIGURATION_ERROR",
            "message": f"Server configuration error: {str(e)}",
            "details": {
                "hint": "Contact system administrator. Encryption key may not be configured."
            }
        }
    
    except Exception as e:
        logger.error(f"Unexpected error in test_connection: {str(e)}")
        return {
            "status": "failed",
            "error_code": "UNKNOWN_ERROR",
            "message": f"Connection test failed: {str(e)}"
        }


@router.post("/{source_id}/sync")
async def trigger_sync(
    source_id: int,
    background_tasks: BackgroundTasks,
    limit: Optional[int] = None,
    force_full: bool = False,
    db: Session = Depends(get_db)
):
    """
    Manually trigger sync for a data source
    """
    source = db.query(ExternalDataSource).filter(
        ExternalDataSource.id == source_id
    ).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    # Run sync in background
    def run_sync():
        from backend.database import SessionLocal
        bg_db = SessionLocal()
        try:
            sync_service = SyncService()
            sync_service.sync_source(source_id, bg_db, limit=limit, force_full_sync=force_full)
        finally:
            bg_db.close()
    
    background_tasks.add_task(run_sync)
    
    return {
        "status": "sync_started",
        "source_id": source_id,
        "source_name": source.name,
        "message": "Sync started in background"
    }


@router.post("/sync-all")
async def sync_all_sources(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger sync for all enabled data sources
    
    - Only developers can trigger syncs
    """
    # Check permissions
    if current_user.role != "developer":
        raise HTTPException(status_code=403, detail="Developer access only")
    def run_sync_all():
        from backend.database import SessionLocal
        bg_db = SessionLocal()
        try:
            sync_service = SyncService()
            sync_service.sync_all_sources(bg_db)
        finally:
            bg_db.close()
    
    background_tasks.add_task(run_sync_all)
    
    return {
        "status": "sync_started",
        "message": "Sync started for all enabled sources"
    }


@router.get("/{source_id}/sync-logs")
async def get_sync_logs(
    source_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get sync history for a data source
    """
    logs = db.query(SyncLog).filter(
        SyncLog.source_id == source_id
    ).order_by(SyncLog.started_at.desc()).limit(limit).all()
    
    return {
        "source_id": source_id,
        "total_logs": len(logs),
        "logs": [
            {
                "id": log.id,
                "status": log.status,
                "documents_fetched": log.documents_fetched,
                "documents_processed": log.documents_processed,
                "documents_failed": log.documents_failed,
                "error_message": log.error_message,
                "sync_duration_seconds": log.sync_duration_seconds,
                "started_at": log.started_at,
                "completed_at": log.completed_at
            }
            for log in logs
        ]
    }


@router.get("/sync-logs/all")
async def get_all_sync_logs(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get recent sync logs across all sources
    """
    logs = db.query(SyncLog).order_by(
        SyncLog.started_at.desc()
    ).limit(limit).all()
    
    return {
        "total_logs": len(logs),
        "logs": [
            {
                "id": log.id,
                "source_id": log.source_id,
                "source_name": log.source_name,
                "status": log.status,
                "documents_fetched": log.documents_fetched,
                "documents_processed": log.documents_processed,
                "documents_failed": log.documents_failed,
                "error_message": log.error_message,
                "sync_duration_seconds": log.sync_duration_seconds,
                "started_at": log.started_at,
                "completed_at": log.completed_at
            }
            for log in logs
        ]
    }
