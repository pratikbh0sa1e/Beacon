import google.generativeai as genai
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class GeminiEmbedder:
    """Gemini embedding model wrapper"""
    
    def __init__(self, model_name: str = "models/embedding-001"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model_name = model_name
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        result = genai.embed_content(
            model=self.model_name,
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = self.embed_text(text)
            embeddings.append(embedding)
        return embeddings
