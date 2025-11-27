from abc import ABC, abstractmethod
from typing import List, Dict

class BaseChunker(ABC):
    """Abstract base class for chunking strategies"""
    
    @abstractmethod
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Chunk text into smaller pieces
        
        Args:
            text: The text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of dicts with 'text' and 'metadata' keys
        """
        pass
