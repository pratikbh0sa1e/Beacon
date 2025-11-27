from typing import List, Dict
from .base_chunker import BaseChunker

class AdaptiveChunker(BaseChunker):
    """Adaptive chunking based on document size"""
    
    def __init__(self):
        # Define size thresholds and corresponding chunk configs
        self.size_configs = [
            {"max_chars": 5000, "chunk_size": 500, "overlap": 50},      # Small docs
            {"max_chars": 20000, "chunk_size": 1000, "overlap": 100},   # Medium docs
            {"max_chars": 50000, "chunk_size": 1500, "overlap": 200},   # Large docs
            {"max_chars": float('inf'), "chunk_size": 2000, "overlap": 300}  # Very large docs
        ]
    
    def _get_chunk_config(self, text_length: int) -> Dict:
        """Determine chunk size and overlap based on document size"""
        for config in self.size_configs:
            if text_length <= config["max_chars"]:
                return {"chunk_size": config["chunk_size"], "overlap": config["overlap"]}
        return {"chunk_size": 2000, "overlap": 300}
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Chunk text adaptively based on document size
        
        Args:
            text: The text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of dicts with 'text', 'metadata', and 'chunk_index' keys
        """
        if not text or not text.strip():
            return []
        
        text_length = len(text)
        config = self._get_chunk_config(text_length)
        chunk_size = config["chunk_size"]
        overlap = config["overlap"]
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < text_length:
            end = start + chunk_size
            chunk_text = text[start:end]
            
            # Try to break at sentence boundary if possible
            if end < text_length:
                last_period = chunk_text.rfind('.')
                last_newline = chunk_text.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size * 0.7:  # Only break if we're past 70% of chunk
                    end = start + break_point + 1
                    chunk_text = text[start:end]
            
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "chunk_index": chunk_index,
                "chunk_size": len(chunk_text),
                "total_doc_size": text_length
            })
            
            chunks.append({
                "text": chunk_text.strip(),
                "metadata": chunk_metadata
            })
            
            start = end - overlap
            chunk_index += 1
        
        return chunks
