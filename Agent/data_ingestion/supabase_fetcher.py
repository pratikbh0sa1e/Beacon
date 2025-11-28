"""
Fetch documents from Supabase storage buckets
"""
import logging
from typing import Dict, Any, Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseFetcher:
    """Fetch documents from Supabase storage"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize Supabase client
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
        """
        self.client: Client = create_client(supabase_url, supabase_key)
        self.supabase_url = supabase_url
    
    def fetch_file(self, bucket_name: str, file_path: str) -> Optional[bytes]:
        """
        Fetch a single file from Supabase storage
        
        Args:
            bucket_name: Name of the storage bucket
            file_path: Path to file in bucket (e.g., "resume/file.pdf")
        
        Returns:
            File bytes or None if error
        """
        try:
            logger.info(f"Fetching file from Supabase: {bucket_name}/{file_path}")
            
            # Download file
            response = self.client.storage.from_(bucket_name).download(file_path)
            
            if response:
                logger.info(f"Successfully fetched file: {file_path} ({len(response)} bytes)")
                return response
            else:
                logger.error(f"Empty response for file: {file_path}")
                return None
        
        except Exception as e:
            logger.error(f"Error fetching file {file_path}: {str(e)}")
            return None
    
    def list_files(self, bucket_name: str, path_prefix: str = "") -> list:
        """
        List files in a Supabase storage bucket
        
        Args:
            bucket_name: Name of the storage bucket
            path_prefix: Prefix to filter files (e.g., "resume/")
        
        Returns:
            List of file objects
        """
        try:
            logger.info(f"Listing files in {bucket_name}/{path_prefix}")
            
            # List files
            files = self.client.storage.from_(bucket_name).list(path_prefix)
            
            logger.info(f"Found {len(files)} files in {bucket_name}/{path_prefix}")
            return files
        
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []
    
    def get_public_url(self, bucket_name: str, file_path: str) -> str:
        """
        Get public URL for a file
        
        Args:
            bucket_name: Name of the storage bucket
            file_path: Path to file in bucket
        
        Returns:
            Public URL
        """
        try:
            url = self.client.storage.from_(bucket_name).get_public_url(file_path)
            return url
        except Exception as e:
            logger.error(f"Error getting public URL: {str(e)}")
            return ""
