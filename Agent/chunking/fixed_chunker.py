from typing import List, Dict
from .base_chunker import BaseChunker

class FixedChunker(BaseChunker):
    """Fixed-size chunking strategy"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Chunk text into fixed-size pieces"""
        if not text or not text.strip():
            return []
        
        chunks = []
        start = 0
        chunk_index = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata["chunk_index"] = chunk_index
            
            chunks.append({
                "text": chunk_text.strip(),
                "metadata": chunk_metadata
            })
            
            start = end - self.overlap
            chunk_index += 1
        
        return chunks
