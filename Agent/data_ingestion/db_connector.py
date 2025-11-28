"""
Connector for external PostgreSQL databases
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
import logging
from cryptography.fernet import Fernet
import os

logger = logging.getLogger(__name__)


class ExternalDBConnector:
    """Connect to external ministry databases and fetch documents"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize connector with encryption key for password decryption
        
        Args:
            encryption_key: Fernet encryption key (from env or generated)
        """
        self.encryption_key = encryption_key or os.getenv("DB_ENCRYPTION_KEY")
        if not self.encryption_key:
            raise ValueError("DB_ENCRYPTION_KEY not found in environment")
        
        self.cipher = Fernet(self.encryption_key.encode())
    
    def encrypt_password(self, password: str) -> str:
        """Encrypt database password"""
        return self.cipher.encrypt(password.encode()).decode()
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt database password"""
        return self.cipher.decrypt(encrypted_password.encode()).decode()
    
    def test_connection(self, host: str, port: int, database: str, 
                       username: str, password: str) -> Dict[str, Any]:
        """
        Test connection to external database
        
        Returns:
            Dict with status and message
        """
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password,
                connect_timeout=10
            )
            conn.close()
            return {"status": "success", "message": "Connection successful"}
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {"status": "failed", "message": str(e)}
    
    def fetch_documents(self, 
                       host: str, 
                       port: int, 
                       database: str,
                       username: str,
                       encrypted_password: str,
                       table_name: str,
                       file_column: str,
                       filename_column: str,
                       metadata_columns: Optional[List[str]] = None,
                       limit: Optional[int] = None,
                       offset: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch documents from external database
        
        Args:
            host, port, database, username: Connection params
            encrypted_password: Encrypted password
            table_name: Table containing documents
            file_column: Column with file data (bytea) or file path
            filename_column: Column with filename
            metadata_columns: Additional columns to fetch
            limit: Max documents to fetch
            offset: Pagination offset
        
        Returns:
            List of document dicts with file_data, filename, and metadata
        """
        password = self.decrypt_password(encrypted_password)
        documents = []
        
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password,
                connect_timeout=10
            )
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build query
            columns = [file_column, filename_column]
            if metadata_columns:
                columns.extend(metadata_columns)
            
            query = f"SELECT {', '.join(columns)} FROM {table_name}"
            
            # Add pagination
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            logger.info(f"Executing query: {query}")
            cursor.execute(query)
            
            rows = cursor.fetchall()
            
            for row in rows:
                # RealDictCursor returns dict-like objects
                doc = {
                    "file_data": row.get(file_column),  # Could be bytes or file path
                    "filename": row.get(filename_column),
                    "metadata": {}
                }
                
                # Extract additional metadata
                if metadata_columns:
                    for col in metadata_columns:
                        if col in row:
                            doc["metadata"][col] = row[col]
                
                documents.append(doc)
            
            cursor.close()
            conn.close()
            
            logger.info(f"Fetched {len(documents)} documents from {table_name}")
            return documents
            
        except Exception as e:
            logger.error(f"Error fetching documents: {str(e)}")
            raise
    
    def fetch_new_documents_since(self,
                                  host: str,
                                  port: int,
                                  database: str,
                                  username: str,
                                  encrypted_password: str,
                                  table_name: str,
                                  file_column: str,
                                  filename_column: str,
                                  timestamp_column: str,
                                  last_sync_time: str,
                                  metadata_columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch only new/updated documents since last sync
        
        Args:
            timestamp_column: Column tracking creation/update time
            last_sync_time: ISO format timestamp of last sync
        
        Returns:
            List of new documents
        """
        password = self.decrypt_password(encrypted_password)
        documents = []
        
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password,
                connect_timeout=10
            )
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            columns = [file_column, filename_column, timestamp_column]
            if metadata_columns:
                columns.extend(metadata_columns)
            
            query = f"""
                SELECT {', '.join(columns)} 
                FROM {table_name}
                WHERE {timestamp_column} > %s
                ORDER BY {timestamp_column} DESC
            """
            
            logger.info(f"Fetching documents since {last_sync_time}")
            cursor.execute(query, (last_sync_time,))
            
            rows = cursor.fetchall()
            
            for row in rows:
                doc = {
                    "file_data": row[file_column],
                    "filename": row[filename_column],
                    "timestamp": row[timestamp_column],
                    "metadata": {}
                }
                
                if metadata_columns:
                    for col in metadata_columns:
                        doc["metadata"][col] = row.get(col)
                
                documents.append(doc)
            
            cursor.close()
            conn.close()
            
            logger.info(f"Fetched {len(documents)} new documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error fetching new documents: {str(e)}")
            raise
