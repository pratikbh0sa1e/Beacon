from typing import List
import logging
import os
from pathlib import Path
from Agent.embeddings.embedding_config import get_model_name, get_model_info, get_active_engine_config, ACTIVE_MODEL
from backend.utils.quota_manager import get_quota_manager, QuotaExceededException

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
    Cloud-optimized embedding model wrapper with quota management
    
    DEPLOYMENT MODE: Cloud-only for free deployment
    - Uses Google Gemini Embeddings API (1,500 requests/day)
    - Automatic quota management and error handling
    - No local models to reduce memory requirements
    
    For local development, set CLOUD_ONLY_MODE=false in .env
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
        Initialize embedder with cloud-first approach
        
        Args:
            model_name: Model name (optional, uses config if None)
            device: Ignored in cloud mode
        """
        # Check if cloud-only mode is enabled (default for deployment)
        self.cloud_only = os.getenv("CLOUD_ONLY_MODE", "true").lower() == "true"
        
        # Use configured model if no model_name provided
        if model_name is None:
            model_name = get_model_name()
        
        # Get engine type from config
        config = get_active_engine_config()
        engine_type = config.get("engine", "gemini" if self.cloud_only else "sentence-transformers")
        
        # Force Gemini in cloud-only mode
        if self.cloud_only:
            engine_type = "gemini"
            logger.info("Cloud-only mode enabled - using Gemini embeddings")
        
        # Check if we need to reload (model changed)
        if self._model is not None and self._active_model_key == ACTIVE_MODEL:
            logger.debug(f"Reusing existing model '{ACTIVE_MODEL}' (dimension: {self._dimension})")
            self.model = self._model
            self.dimension = self._dimension
            self.model_key = self._active_model_key
            self.engine_type = engine_type
            self.quota_manager = get_quota_manager()
            return
        
        # Model changed or first load
        if self._model is not None:
            logger.warning(f"Model changed from '{self._active_model_key}' to '{ACTIVE_MODEL}'. Reloading...")
        
        logger.info(f"Loading embedding model '{model_name}' (config: {ACTIVE_MODEL})...")
        logger.info(get_model_info())
        
        # Initialize quota manager
        self.quota_manager = get_quota_manager()
        
        # Load based on engine type
        if engine_type == "gemini" or self.cloud_only:
            self._init_gemini_model(model_name)
        else:
            # Only allow local models in development mode
            if not self.cloud_only:
                self._init_sentence_transformer(model_name, device)
            else:
                raise ValueError("Local models not available in cloud-only mode. Set CLOUD_ONLY_MODE=false for development.")
        
        self.model_key = ACTIVE_MODEL
        self.engine_type = engine_type
        
        # Cache for singleton
        BGEEmbedder._model = self.model
        BGEEmbedder._dimension = self.dimension
        BGEEmbedder._active_model_key = ACTIVE_MODEL
        
        logger.info(f"Model loaded successfully! Embedding dimension: {self.dimension}")
    
    def _init_sentence_transformer(self, model_name: str, device: str = None):
        """Initialize Sentence Transformer model (development only)"""
        if self.cloud_only:
            raise ValueError("Sentence Transformers not available in cloud-only mode")
        
        try:
            from sentence_transformers import SentenceTransformer
            import torch
        except ImportError:
            raise ImportError("sentence-transformers not installed. Use cloud-only mode for deployment.")
        
        if device is None:
            device = 'cpu'
            logger.info("Using CPU mode for local development")
        
        logger.info(f"Using Sentence Transformers on {device}")
        self.model = SentenceTransformer(model_name, device=device)
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    def _init_gemini_model(self, model_name: str):
        """Initialize Gemini embedding model with quota management"""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai not installed. Install with: pip install google-generativeai")
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        logger.info("Using Google Gemini embeddings (cloud) with quota management")
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
        """Generate embedding for a single text with quota management"""
        logger.debug(f"Embedding single text (length: {len(text)} chars)")
        
        if self.engine_type == "gemini" or self.cloud_only:
            # Check quota before making API call
            try:
                allowed, error_msg, quota_info = self.quota_manager.check_quota("gemini_embeddings", 1)
                if not allowed:
                    raise QuotaExceededException("gemini_embeddings", quota_info)
                
                result = self.genai.embed_content(
                    model=self.model["model_name"],
                    content=text,
                    task_type="retrieval_document"
                )
                
                # Consume quota after successful API call
                self.quota_manager.consume_quota("gemini_embeddings", 1)
                
                embedding = result['embedding']
                # Pad Gemini embeddings (768) to 1024 for BGE-M3 compatibility
                embedding = self._pad_embedding(embedding, target_dim=1024)
                logger.debug(f"Padded Gemini embedding from 768 to {len(embedding)} dims")
                return embedding
                
            except QuotaExceededException as e:
                logger.error(f"Quota exceeded for embeddings: {e}")
                raise ValueError(f"Daily embedding quota exceeded. Please try again tomorrow. {error_msg}")
            except Exception as e:
                logger.error(f"Gemini embedding failed: {e}")
                raise ValueError(f"Embedding service temporarily unavailable: {str(e)}")
        else:
            # Local model (development only)
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with quota management
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing (ignored for Gemini)
        """
        logger.info(f"Embedding batch of {len(texts)} texts")
        
        if self.engine_type == "gemini" or self.cloud_only:
            # Check quota for entire batch
            try:
                allowed, error_msg, quota_info = self.quota_manager.check_quota("gemini_embeddings", len(texts))
                if not allowed:
                    raise QuotaExceededException("gemini_embeddings", quota_info)
                
                # Gemini doesn't have native batch support, process one by one
                embeddings = []
                successful_requests = 0
                
                for i, text in enumerate(texts):
                    try:
                        result = self.genai.embed_content(
                            model=self.model["model_name"],
                            content=text,
                            task_type="retrieval_document"
                        )
                        embedding = result['embedding']
                        # Pad Gemini embeddings (768) to 1024 for BGE-M3 compatibility
                        embedding = self._pad_embedding(embedding, target_dim=1024)
                        embeddings.append(embedding)
                        successful_requests += 1
                        
                        if (i + 1) % 10 == 0:
                            logger.debug(f"Embedded {i + 1}/{len(texts)} texts (padded to 1024 dims)")
                    
                    except Exception as e:
                        logger.error(f"Failed to embed text {i+1}: {e}")
                        # Add zero embedding as placeholder
                        embeddings.append([0.0] * 1024)
                
                # Consume quota for successful requests only
                if successful_requests > 0:
                    self.quota_manager.consume_quota("gemini_embeddings", successful_requests)
                
                logger.info(f"Successfully generated {successful_requests}/{len(texts)} embeddings (padded to 1024 dims)")
                return embeddings
                
            except QuotaExceededException as e:
                logger.error(f"Quota exceeded for batch embeddings: {e}")
                raise ValueError(f"Daily embedding quota exceeded. Please try again tomorrow. {error_msg}")
            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                raise ValueError(f"Embedding service temporarily unavailable: {str(e)}")
        else:
            # Local model (development only)
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
    
    def get_quota_status(self) -> dict:
        """Get current quota status for embeddings"""
        return self.quota_manager.get_quota_status("gemini_embeddings")
