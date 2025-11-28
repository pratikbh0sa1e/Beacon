"""
Sync service to orchestrate document fetching and processing
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from Agent.data_ingestion.db_connector import ExternalDBConnector
from Agent.data_ingestion.document_processor import ExternalDocumentProcessor
from Agent.data_ingestion.models import ExternalDataSource, SyncLog

logger = logging.getLogger(__name__)


class SyncService:
    """Orchestrate syncing documents from external sources"""
    
    def __init__(self):
        self.connector = ExternalDBConnector()
    
    def sync_source(self, 
                   source_id: int,
                   db: Session,
                   limit: Optional[int] = None,
                   force_full_sync: bool = False) -> Dict[str, Any]:
        """
        Sync documents from a specific external source
        
        Args:
            source_id: ID of external data source
            db: Database session
            limit: Max documents to sync (None = all)
            force_full_sync: If True, sync all docs; if False, only new ones
        
        Returns:
            Sync result summary
        """
        start_time = datetime.utcnow()
        
        # Get source config
        source = db.query(ExternalDataSource).filter(
            ExternalDataSource.id == source_id
        ).first()
        
        if not source:
            return {"status": "error", "message": "Data source not found"}
        
        if not source.sync_enabled:
            return {"status": "skipped", "message": "Sync disabled for this source"}
        
        # Update status
        source.last_sync_status = "in_progress"
        db.commit()
        
        try:
            # Fetch documents
            if force_full_sync or not source.last_sync_at:
                logger.info(f"Full sync for {source.name}")
                documents = self.connector.fetch_documents(
                    host=source.host,
                    port=source.port,
                    database=source.database_name,
                    username=source.username,
                    encrypted_password=source.password_encrypted,
                    table_name=source.table_name,
                    file_column=source.file_column,
                    filename_column=source.filename_column,
                    metadata_columns=source.metadata_columns,
                    limit=limit
                )
            else:
                # Incremental sync (requires timestamp column)
                logger.info(f"Incremental sync for {source.name} since {source.last_sync_at}")
                # For now, do full sync - incremental requires timestamp column config
                documents = self.connector.fetch_documents(
                    host=source.host,
                    port=source.port,
                    database=source.database_name,
                    username=source.username,
                    encrypted_password=source.password_encrypted,
                    table_name=source.table_name,
                    file_column=source.file_column,
                    filename_column=source.filename_column,
                    metadata_columns=source.metadata_columns,
                    limit=limit
                )
            
            # Initialize processor based on storage type
            if source.storage_type == "supabase":
                # Decrypt Supabase key
                supabase_key = self.connector.decrypt_password(source.supabase_key_encrypted)
                processor = ExternalDocumentProcessor(
                    supabase_url=source.supabase_url,
                    supabase_key=supabase_key
                )
                
                # Process documents from Supabase
                processing_result = self._process_supabase_documents(
                    documents=documents,
                    processor=processor,
                    source=source
                )
            else:
                # Process documents from database (BLOB)
                processor = ExternalDocumentProcessor()
                processing_result = processor.process_batch(
                    documents=documents,
                    source_name=source.name
                )
            
            # Update source stats
            source.total_documents_synced += processing_result["success"]
            source.last_sync_at = datetime.utcnow()
            source.last_sync_status = "success"
            source.last_sync_message = f"Synced {processing_result['success']}/{processing_result['total']} documents"
            
            # Create sync log
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            sync_log = SyncLog(
                source_id=source.id,
                source_name=source.name,
                status="success",
                documents_fetched=processing_result["total"],
                documents_processed=processing_result["success"],
                documents_failed=processing_result["failed"],
                sync_duration_seconds=int(duration),
                started_at=start_time,
                completed_at=end_time
            )
            
            db.add(sync_log)
            db.commit()
            
            return {
                "status": "success",
                "source_name": source.name,
                "documents_fetched": processing_result["total"],
                "documents_processed": processing_result["success"],
                "documents_failed": processing_result["failed"],
                "duration_seconds": int(duration)
            }
        
        except Exception as e:
            logger.error(f"Sync failed for {source.name}: {str(e)}")
            
            # Update source status
            source.last_sync_status = "failed"
            source.last_sync_message = str(e)
            
            # Create error log
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            sync_log = SyncLog(
                source_id=source.id,
                source_name=source.name,
                status="failed",
                documents_fetched=0,
                documents_processed=0,
                documents_failed=0,
                error_message=str(e),
                sync_duration_seconds=int(duration),
                started_at=start_time,
                completed_at=end_time
            )
            
            db.add(sync_log)
            db.commit()
            
            return {
                "status": "failed",
                "source_name": source.name,
                "error": str(e)
            }
    
    def _process_supabase_documents(self,
                                   documents: list,
                                   processor: ExternalDocumentProcessor,
                                   source: ExternalDataSource) -> Dict[str, Any]:
        """
        Process documents stored in Supabase
        
        Args:
            documents: List of document records from DB (with file paths)
            processor: Document processor with Supabase fetcher
            source: Data source configuration
        
        Returns:
            Processing result summary
        """
        results = {
            "total": len(documents),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for doc in documents:
            # Get file path from database record
            file_data = doc.get("file_data")  # This could be a URL or path
            
            if not file_data:
                logger.warning(f"Skipping document with no file path: {doc.get('filename')}")
                results["failed"] += 1
                results["details"].append({
                    "status": "error",
                    "filename": doc.get("filename", "unknown"),
                    "message": "No file path found in database"
                })
                continue
            
            # Convert to string if needed
            file_data = str(file_data)
            
            # Extract path from URL if it's a full Supabase URL
            # Example: https://xxx.supabase.co/storage/v1/object/public/resumes/resumes/file.pdf
            # We need: resumes/file.pdf
            if file_data.startswith("http"):
                # It's a full URL, extract the path after bucket name
                try:
                    # Split by bucket name to get the path
                    if f"/object/public/{source.supabase_bucket}/" in file_data:
                        file_path = file_data.split(f"/object/public/{source.supabase_bucket}/")[1]
                    else:
                        # Fallback: use filename from doc
                        file_path = doc.get("filename", "")
                        if source.file_path_prefix:
                            file_path = source.file_path_prefix + file_path
                except Exception as e:
                    logger.error(f"Error extracting path from URL {file_data}: {e}")
                    results["failed"] += 1
                    results["details"].append({
                        "status": "error",
                        "filename": doc.get("filename", "unknown"),
                        "message": f"Failed to extract path from URL: {str(e)}"
                    })
                    continue
            else:
                # It's already a path
                file_path = file_data
                
                # Add prefix if needed
                if source.file_path_prefix and not file_path.startswith(source.file_path_prefix):
                    file_path = source.file_path_prefix + file_path
            
            # Process document from Supabase
            result = processor.process_document_from_supabase(
                file_path=file_path,
                bucket_name=source.supabase_bucket,
                source_name=source.name,
                metadata=doc.get("metadata")
            )
            
            results["details"].append(result)
            
            if result["status"] == "success":
                results["success"] += 1
            else:
                results["failed"] += 1
        
        logger.info(f"Supabase batch processing complete: {results['success']}/{results['total']} successful")
        return results
    
    def sync_all_sources(self, db: Session) -> Dict[str, Any]:
        """
        Sync all enabled data sources
        
        Returns:
            Summary of all syncs
        """
        sources = db.query(ExternalDataSource).filter(
            ExternalDataSource.sync_enabled == True
        ).all()
        
        results = {
            "total_sources": len(sources),
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        for source in sources:
            result = self.sync_source(source.id, db)
            results["details"].append(result)
            
            if result["status"] == "success":
                results["successful"] += 1
            else:
                results["failed"] += 1
        
        return results
