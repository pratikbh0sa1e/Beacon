"""
API endpoints for managing external data sources
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from backend.database import get_db, User
from backend.routers.auth_router import get_current_user
from Agent.data_ingestion.models import ExternalDataSource, SyncLog
from Agent.data_ingestion.db_connector import ExternalDBConnector
from Agent.data_ingestion.sync_service import SyncService

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


@router.post("/create")
async def create_data_source(
    source: DataSourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register a new external data source
    
    - Only developers can create data sources
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


@router.post("/test-connection")
async def test_connection(
    connection: ConnectionTest
):
    """
    Test connection to external database
    """
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
    
    except Exception as e:
        return {
            "status": "failed",
            "message": str(e)
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
