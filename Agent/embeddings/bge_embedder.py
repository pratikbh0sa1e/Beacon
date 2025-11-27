from sentence_transformers import SentenceTransformer
from typing import List
import torch
import logging
from pathlib import Path

# Setup logging
log_dir = Path("Agent/agent_logs")
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "embeddings.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BGEEmbedder:
    """BGE (BAAI General Embedding) model wrapper"""
    
    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5", device: str = None):
        """
        Initialize BGE embedder
        
        Args:
            model_name: HuggingFace model name (default: bge-small for speed)
            device: 'cuda', 'cpu', or None (auto-detect)
        """
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        logger.info(f"Loading BGE model '{model_name}' on {device}...")
        self.model = SentenceTransformer(model_name, device=device)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded! Embedding dimension: {self.dimension}")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        logger.debug(f"Embedding single text (length: {len(text)} chars)")
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
        """
        logger.info(f"Embedding batch of {len(texts)} texts with batch_size={batch_size}")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension
