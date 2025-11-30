"""
Process documents fetched from external sources
Reuses existing text extraction utilities
"""
import os
import tempfile
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from backend.utils.text_extractor import extract_text
from backend.utils.supabase_storage import upload_to_supabase
from backend.database import Document, DocumentMetadata, SessionLocal
from Agent.data_ingestion.supabase_fetcher import SupabaseFetcher
from Agent.metadata.extractor import MetadataExtractor

logger = logging.getLogger(__name__)


class ExternalDocumentProcessor:
    """Process documents from external sources using existing pipeline"""
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """
        Initialize processor
        
        Args:
            supabase_url: Supabase URL if fetching from Supabase storage
            supabase_key: Supabase key if fetching from Supabase storage
        """
        self.temp_dir = tempfile.gettempdir()
        self.supabase_fetcher = None
        self.metadata_extractor = MetadataExtractor()
        
        if supabase_url and supabase_key:
            self.supabase_fetcher = SupabaseFetcher(supabase_url, supabase_key)
    
    def process_document_from_supabase(self,
                                      file_path: str,
                                      bucket_name: str,
                                      source_name: str,
                                      metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a document from Supabase storage
        
        Args:
            file_path: Path to file in Supabase bucket (e.g., "resume/file.pdf")
            bucket_name: Supabase bucket name
            source_name: Name of external data source
            metadata: Additional metadata
        
        Returns:
            Dict with processing result
        """
        if not self.supabase_fetcher:
            return {
                "status": "error",
                "filename": file_path,
                "message": "Supabase fetcher not initialized"
            }
        
        try:
            # Fetch file from Supabase
            file_data = self.supabase_fetcher.fetch_file(bucket_name, file_path)
            
            if not file_data:
                return {
                    "status": "error",
                    "filename": file_path,
                    "message": "Failed to fetch file from Supabase"
                }
            
            # Extract filename from path
            filename = os.path.basename(file_path)
            
            # Process using existing method
            return self.process_document(
                file_data=file_data,
                filename=filename,
                source_name=source_name,
                metadata=metadata
            )
        
        except Exception as e:
            logger.error(f"Error processing Supabase document {file_path}: {str(e)}")
            return {
                "status": "error",
                "filename": file_path,
                "message": str(e)
            }
    
    def process_document(self, 
                        file_data: bytes,
                        filename: str,
                        source_name: str,
                        metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a single document from external source
        
        Args:
            file_data: Raw file bytes
            filename: Original filename
            source_name: Name of external data source
            metadata: Additional metadata from source DB
        
        Returns:
            Dict with processing result
        """
        try:
            # Determine file type
            file_ext = filename.split(".")[-1].lower()
            if file_ext not in ["pdf", "docx", "pptx", "jpeg", "jpg", "png"]:
                return {
                    "status": "error",
                    "filename": filename,
                    "message": f"Unsupported file type: {file_ext}"
                }
            
            # Save to temp file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_filename = f"{timestamp}_{filename}"
            temp_path = os.path.join(self.temp_dir, temp_filename)
            
            with open(temp_path, "wb") as f:
                f.write(file_data)
            
            # Extract text using existing utility
            extracted_text = extract_text(temp_path, file_ext)
            
            # Upload to Supabase
            s3_url = upload_to_supabase(temp_path, temp_filename)
            
            # Save to database
            db = SessionLocal()
            try:
                doc = Document(
                    filename=filename,
                    file_type=file_ext,
                    file_path=temp_path,
                    s3_url=s3_url,
                    extracted_text=extracted_text,
                    doc_metadata=str({
                        "source": source_name,
                        "external_metadata": metadata or {}
                    })
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)
                
                # Extract metadata for lazy RAG
                logger.info(f"Extracting metadata for doc {doc.id}: {filename}")
                try:
                    extracted_metadata = self.metadata_extractor.extract_metadata(extracted_text, filename)
                    
                    doc_metadata = DocumentMetadata(
                        document_id=doc.id,
                        title=extracted_metadata.get('title'),
                        department=extracted_metadata.get('department'),
                        document_type=extracted_metadata.get('document_type'),
                        date_published=extracted_metadata.get('date_published'),
                        keywords=extracted_metadata.get('keywords'),
                        summary=extracted_metadata.get('summary'),
                        key_topics=extracted_metadata.get('key_topics'),
                        entities=extracted_metadata.get('entities'),
                        bm25_keywords=extracted_metadata.get('bm25_keywords'),
                        text_length=extracted_metadata.get('text_length'),
                        embedding_status='uploaded',
                        metadata_status='ready'
                    )
                    
                    db.add(doc_metadata)
                    db.commit()
                    logger.info(f"Metadata extracted for doc {doc.id}: {extracted_metadata.get('title')}")
                    
                except Exception as e:
                    logger.error(f"Error extracting metadata for doc {doc.id}: {str(e)}")
                    # Don't fail the whole process if metadata extraction fails
                
                result = {
                    "status": "success",
                    "filename": filename,
                    "document_id": doc.id,
                    "s3_url": s3_url,
                    "text_length": len(extracted_text),
                    "source": source_name
                }
                
                logger.info(f"Processed document {filename} from {source_name}")
                return result
                
            finally:
                db.close()
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            return {
                "status": "error",
                "filename": filename,
                "message": str(e)
            }
    
    def process_batch(self,
                     documents: List[Dict[str, Any]],
                     source_name: str) -> Dict[str, Any]:
        """
        Process multiple documents in batch
        
        Args:
            documents: List of dicts with file_data, filename, metadata
            source_name: Name of external data source
        
        Returns:
            Summary of batch processing
        """
        results = {
            "total": len(documents),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for doc in documents:
            result = self.process_document(
                file_data=doc["file_data"],
                filename=doc["filename"],
                source_name=source_name,
                metadata=doc.get("metadata")
            )
            
            results["details"].append(result)
            
            if result["status"] == "success":
                results["success"] += 1
            else:
                results["failed"] += 1
        
        logger.info(f"Batch processing complete: {results['success']}/{results['total']} successful")
        return results
