"""
PDF and document downloader for web scraping
"""
import requests
import os
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFDownloader:
    """Download documents from URLs"""
    
    def __init__(self, download_dir: str = "temp_downloads"):
        """
        Initialize downloader
        
        Args:
            download_dir: Directory to store downloaded files
        """
        self.download_dir = download_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BEACON Policy Intelligence Bot/1.0'
        })
        
        # Create download directory if it doesn't exist
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
    
    def download_document(self, url: str,
                         filename: Optional[str] = None,
                         timeout: int = 60,
                         retry_count: int = 3) -> Dict[str, Any]:
        """
        Download a document from URL with retry logic
        
        Args:
            url: Document URL
            filename: Custom filename (optional, will generate from URL if not provided)
            timeout: Download timeout in seconds
            retry_count: Number of retry attempts for failed downloads
        
        Returns:
            Dict with download status and file info
        """
        last_error = None
        
        for attempt in range(retry_count):
            try:
                logger.info(f"Downloading: {url} (attempt {attempt + 1}/{retry_count})")
                
                # Generate filename if not provided
                if not filename:
                    filename = self._generate_filename(url)
                
                filepath = os.path.join(self.download_dir, filename)
                
                # Try different user agents on retry
                headers = {
                    'User-Agent': self._get_user_agent(attempt),
                    'Accept': 'application/pdf,application/octet-stream,*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': url.rsplit('/', 1)[0] + '/'
                }
                
                # Download file
                response = self.session.get(url, timeout=timeout, stream=True, headers=headers)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                
                # Write to file
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Get file size
                file_size = os.path.getsize(filepath)
                
                # Calculate file hash for deduplication
                file_hash = self._calculate_file_hash(filepath)
                
                logger.info(f"Downloaded {filename} ({file_size} bytes)")
                
                return {
                    "status": "success",
                    "url": url,
                    "filepath": filepath,
                    "filename": filename,
                    "file_size": file_size,
                    "file_hash": file_hash,
                    "content_type": content_type,
                    "downloaded_at": datetime.utcnow().isoformat()
                }
            
            except requests.exceptions.Timeout as e:
                last_error = f"Download timeout"
                logger.warning(f"Timeout downloading {url} (attempt {attempt + 1}/{retry_count})")
                if attempt < retry_count - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
            
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                logger.warning(f"Error downloading {url}: {str(e)} (attempt {attempt + 1}/{retry_count})")
                if attempt < retry_count - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
            
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.warning(f"Unexpected error downloading {url}: {str(e)} (attempt {attempt + 1}/{retry_count})")
                if attempt < retry_count - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
        
        # All retries failed
        logger.error(f"Failed to download {url} after {retry_count} attempts: {last_error}")
        return {
            "status": "error",
            "url": url,
            "error": last_error,
            "attempts": retry_count,
            "downloaded_at": datetime.utcnow().isoformat()
        }
    
    def download_batch(self, urls: list,
                      max_concurrent: int = 5) -> Dict[str, Any]:
        """
        Download multiple documents
        
        Args:
            urls: List of document URLs
            max_concurrent: Maximum concurrent downloads
        
        Returns:
            Dict with batch download results
        """
        results = {
            "total": len(urls),
            "successful": 0,
            "failed": 0,
            "downloads": []
        }
        
        for url in urls:
            result = self.download_document(url)
            results["downloads"].append(result)
            
            if result["status"] == "success":
                results["successful"] += 1
            else:
                results["failed"] += 1
        
        logger.info(f"Batch download complete: {results['successful']}/{results['total']} successful")
        return results
    
    def _generate_filename(self, url: str) -> str:
        """
        Generate filename from URL
        
        Args:
            url: Document URL
        
        Returns:
            Generated filename
        """
        # Extract filename from URL
        url_parts = url.split('/')
        filename = url_parts[-1]
        
        # Remove query parameters
        if '?' in filename:
            filename = filename.split('?')[0]
        
        # If no extension, add .pdf
        if '.' not in filename:
            filename += '.pdf'
        
        # Add timestamp to avoid collisions
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        filename = f"{timestamp}_{name}{ext}"
        
        # Sanitize filename
        filename = self._sanitize_filename(filename)
        
        return filename
    
    def _sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters from filename"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
    
    def _get_user_agent(self, attempt: int = 0) -> str:
        """
        Get user agent string, rotating through different ones on retry
        
        Args:
            attempt: Retry attempt number
        
        Returns:
            User agent string
        """
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'BEACON Policy Intelligence Bot/1.0 (Educational Research)',
        ]
        return user_agents[attempt % len(user_agents)]
    
    def _calculate_file_hash(self, filepath: str) -> str:
        """
        Calculate SHA256 hash of file for deduplication
        
        Args:
            filepath: Path to file
        
        Returns:
            SHA256 hash string
        """
        sha256_hash = hashlib.sha256()
        
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def cleanup_downloads(self, older_than_days: int = 7):
        """
        Clean up old downloaded files
        
        Args:
            older_than_days: Delete files older than this many days
        """
        try:
            current_time = datetime.utcnow().timestamp()
            cutoff_time = current_time - (older_than_days * 24 * 60 * 60)
            
            deleted_count = 0
            
            for filename in os.listdir(self.download_dir):
                filepath = os.path.join(self.download_dir, filename)
                
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        deleted_count += 1
                        logger.info(f"Deleted old file: {filename}")
            
            logger.info(f"Cleanup complete: {deleted_count} files deleted")
        
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def get_file_info(self, filepath: str) -> Dict[str, Any]:
        """
        Get information about a downloaded file
        
        Args:
            filepath: Path to file
        
        Returns:
            Dict with file information
        """
        try:
            stat = os.stat(filepath)
            
            return {
                "filepath": filepath,
                "filename": os.path.basename(filepath),
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "hash": self._calculate_file_hash(filepath)
            }
        
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return {"error": str(e)}
