"""
Session-based storage for web scraping data
Persists data to disk until explicitly cleared
"""
import json
import os
from typing import List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SessionStorage:
    """Persistent storage for web scraping session data"""
    
    def __init__(self, storage_dir: str = "data/web_scraping_sessions"):
        """
        Initialize session storage
        
        Args:
            storage_dir: Directory to store session data
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.sources_file = self.storage_dir / "sources.json"
        self.logs_file = self.storage_dir / "logs.json"
        self.docs_file = self.storage_dir / "scraped_docs.json"
        self.counters_file = self.storage_dir / "counters.json"
        
        logger.info(f"Session storage initialized at: {self.storage_dir}")
    
    def load_sources(self) -> List[Dict]:
        """Load sources from disk"""
        try:
            if self.sources_file.exists():
                with open(self.sources_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} sources from disk")
                    return data
        except Exception as e:
            logger.error(f"Error loading sources: {e}")
        return []
    
    def save_sources(self, sources: List[Dict]) -> None:
        """Save sources to disk"""
        try:
            with open(self.sources_file, 'w', encoding='utf-8') as f:
                json.dump(sources, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(sources)} sources to disk")
        except Exception as e:
            logger.error(f"Error saving sources: {e}")
    
    def load_logs(self) -> List[Dict]:
        """Load logs from disk"""
        try:
            if self.logs_file.exists():
                with open(self.logs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} logs from disk")
                    return data
        except Exception as e:
            logger.error(f"Error loading logs: {e}")
        return []
    
    def save_logs(self, logs: List[Dict]) -> None:
        """Save logs to disk"""
        try:
            with open(self.logs_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(logs)} logs to disk")
        except Exception as e:
            logger.error(f"Error saving logs: {e}")
    
    def load_scraped_docs(self) -> List[Dict]:
        """Load scraped documents from disk"""
        try:
            if self.docs_file.exists():
                with open(self.docs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} scraped documents from disk")
                    return data
        except Exception as e:
            logger.error(f"Error loading scraped docs: {e}")
        return []
    
    def save_scraped_docs(self, docs: List[Dict]) -> None:
        """Save scraped documents to disk"""
        try:
            with open(self.docs_file, 'w', encoding='utf-8') as f:
                json.dump(docs, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(docs)} scraped documents to disk")
        except Exception as e:
            logger.error(f"Error saving scraped docs: {e}")
    
    def load_counters(self) -> Dict[str, int]:
        """Load ID counters from disk"""
        try:
            if self.counters_file.exists():
                with open(self.counters_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded counters from disk: {data}")
                    return data
        except Exception as e:
            logger.error(f"Error loading counters: {e}")
        return {"source_id": 1, "log_id": 1}
    
    def save_counters(self, source_id: int, log_id: int) -> None:
        """Save ID counters to disk"""
        try:
            data = {"source_id": source_id, "log_id": log_id}
            with open(self.counters_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved counters to disk: {data}")
        except Exception as e:
            logger.error(f"Error saving counters: {e}")
    
    def clear_all(self) -> None:
        """Clear all session data (on logout)"""
        try:
            for file in [self.sources_file, self.logs_file, self.docs_file, self.counters_file]:
                if file.exists():
                    file.unlink()
            logger.info("Cleared all session data")
        except Exception as e:
            logger.error(f"Error clearing session data: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return {
            "sources_count": len(self.load_sources()),
            "logs_count": len(self.load_logs()),
            "docs_count": len(self.load_scraped_docs()),
            "storage_dir": str(self.storage_dir),
            "files_exist": {
                "sources": self.sources_file.exists(),
                "logs": self.logs_file.exists(),
                "docs": self.docs_file.exists(),
                "counters": self.counters_file.exists()
            }
        }
