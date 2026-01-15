from sentence_transformers import SentenceTransformer
from typing import List
import torch
import logging
from pathlib import Path
from Agent.embeddings.embedding_config import get_model_name, get_model_info, get_active_engine_config, ACTIVE_MODEL

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
    """
    Configurable embedding model wrapper with singleton pattern
    
    Supports multiple models via embedding_config.py:
    - bge-large-en: English-only (1024-dim)
    - bge-m3: Multilingual (1024-dim) - RECOMMENDED for Indian govt docs
    - multilingual-e5-large: Alternative multilingual (1024-dim)
    - labse: Smaller multilingual (768-dim)
    
    To switch models: Edit ACTIVE_MODEL in Agent/embeddings/embedding_config.py
    """
    _instance = None
    _model = None
    _dimension = None
    _active_model_key = None
    
    def __new__(cls, model_name: str = None, device: str = None):
        """Singleton pattern to avoid loading model multiple times"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, model_name: str = None, device: str = None):
        """
        Initialize embedder (only loads model once)
        
        Args:
            model_name: Model name (optional, uses config if None)
            device: 'cuda', 'cpu', or None (auto-detect)
        """
        # Use configured model if no model_name provided
        if model_name is None:
            model_name = get_model_name()
        
        # Get engine type from config
        config = get_active_engine_config()
        engine_type = config.get("engine", "sentence-transformers")
        
        # Check if we need to reload (model changed)
        if self._model is not None and self._active_model_key == ACTIVE_MODEL:
            logger.debug(f"Reusing existing model '{ACTIVE_MODEL}' (dimension: {self._dimension})")
            self.model = self._model
            self.dimension = self._dimension
            self.model_key = self._active_model_key
            self.engine_type = engine_type
            return
        
        # Model changed or first load
        if self._model is not None:
            logger.warning(f"Model changed from '{self._active_model_key}' to '{ACTIVE_MODEL}'. Reloading...")
        
        logger.info(f"Loading embedding model '{model_name}' (config: {ACTIVE_MODEL})...")
        logger.info(get_model_info())
        
        # Load based on engine type
        if engine_type == "gemini":
            self._init_gemini_model(model_name)
        else:
            self._init_sentence_transformer(model_name, device)
        
        self.model_key = ACTIVE_MODEL
        self.engine_type = engine_type
        
        # Cache for singleton
        BGEEmbedder._model = self.model
        BGEEmbedder._dimension = self.dimension
        BGEEmbedder._active_model_key = ACTIVE_MODEL
        
        logger.info(f"Model loaded successfully! Embedding dimension: {self.dimension}")
    
    def _init_sentence_transformer(self, model_name: str, device: str = None):
        """Initialize Sentence Transformer model"""
        if device is None:
            # Force CPU mode to avoid CUDA memory issues
            device = 'cpu'
            logger.info("Forcing CPU mode to avoid CUDA memory issues")
        
        logger.info(f"Using Sentence Transformers on {device}")
        self.model = SentenceTransformer(model_name, device=device)
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    def _init_gemini_model(self, model_name: str):
        """Initialize Gemini embedding model"""
        import google.generativeai as genai
        import os
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        logger.info("Using Google Gemini embeddings (cloud)")
        genai.configure(api_key=api_key)
        self.model = {"type": "gemini", "model_name": model_name}
        # Gemini native dimension is 768, but we pad to 1024 for BGE-M3 compatibility
        self.dimension = 1024  # Padded dimension for pgvector compatibility
        self.genai = genai
        logger.info("Gemini embeddings will be padded from 768 to 1024 dimensions")
    
    def _pad_embedding(self, embedding: List[float], target_dim: int = 1024) -> List[float]:
        """
        Pad embedding to target dimension with zeros
        
        Args:
            embedding: Original embedding
            target_dim: Target dimension (default: 1024 for BGE-M3 compatibility)
        
        Returns:
            Padded embedding
        """
        current_dim = len(embedding)
        if current_dim >= target_dim:
            return embedding
        
        # Pad with zeros
        padding = [0.0] * (target_dim - current_dim)
        return embedding + padding
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        logger.debug(f"Embedding single text (length: {len(text)} chars)")
        
        if self.engine_type == "gemini":
            result = self.genai.embed_content(
                model=self.model["model_name"],
                content=text,
                task_type="retrieval_document"
            )
            embedding = result['embedding']
            # Pad Gemini embeddings (768) to 1024 for BGE-M3 compatibility
            embedding = self._pad_embedding(embedding, target_dim=1024)
            logger.debug(f"Padded Gemini embedding from 768 to {len(embedding)} dims")
            return embedding
        else:
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
        
        if self.engine_type == "gemini":
            # Gemini doesn't have native batch support, process one by one
            embeddings = []
            for i, text in enumerate(texts):
                result = self.genai.embed_content(
                    model=self.model["model_name"],
                    content=text,
                    task_type="retrieval_document"
                )
                embedding = result['embedding']
                # Pad Gemini embeddings (768) to 1024 for BGE-M3 compatibility
                embedding = self._pad_embedding(embedding, target_dim=1024)
                embeddings.append(embedding)
                
                if (i + 1) % 10 == 0:
                    logger.debug(f"Embedded {i + 1}/{len(texts)} texts (padded to 1024 dims)")
            
            logger.info(f"Successfully generated {len(embeddings)} embeddings (padded to 1024 dims)")
            return embeddings
        else:
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
