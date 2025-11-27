import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Optional
from pathlib import Path

class FAISSVectorStore:
    """FAISS vector store for document embeddings"""
    
    def __init__(self, dimension: int = None, index_path: str = "Agent/vector_store/faiss_index"):
        self.dimension = dimension
        self.index_path = index_path
        self.index = None
        self.metadata_store = []  # Store metadata for each vector
        self.doc_hashes = {}  # Track document hashes to avoid duplicates
        
        # Create directory if it doesn't exist
        Path(index_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing index or create new one
        self.load_index()
    
    def _create_index(self, dimension: int = None):
        """Create a new FAISS index"""
        if dimension:
            self.dimension = dimension
        if not self.dimension:
            raise ValueError("Dimension must be specified to create a new index")
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata_store = []
        self.doc_hashes = {}
    
    def load_index(self):
        """Load existing FAISS index from disk"""
        index_file = f"{self.index_path}.index"
        metadata_file = f"{self.index_path}.metadata"
        hashes_file = f"{self.index_path}.hashes"
        
        if os.path.exists(index_file):
            self.index = faiss.read_index(index_file)
            self.dimension = self.index.d  # Get dimension from loaded index
            
            if os.path.exists(metadata_file):
                with open(metadata_file, 'rb') as f:
                    self.metadata_store = pickle.load(f)
            
            if os.path.exists(hashes_file):
                with open(hashes_file, 'rb') as f:
                    self.doc_hashes = pickle.load(f)
        else:
            # Don't create index yet, wait for first embedding
            pass
    
    def save_index(self):
        """Save FAISS index to disk"""
        index_file = f"{self.index_path}.index"
        metadata_file = f"{self.index_path}.metadata"
        hashes_file = f"{self.index_path}.hashes"
        
        faiss.write_index(self.index, index_file)
        
        with open(metadata_file, 'wb') as f:
            pickle.dump(self.metadata_store, f)
        
        with open(hashes_file, 'wb') as f:
            pickle.dump(self.doc_hashes, f)
    
    def document_exists(self, doc_hash: str) -> bool:
        """Check if document already exists in the store"""
        return doc_hash in self.doc_hashes
    
    def add_embeddings(self, embeddings: List[List[float]], metadata: List[Dict], doc_hash: str):
        """Add embeddings and metadata to the store"""
        if self.document_exists(doc_hash):
            return False  # Document already exists
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Create index if it doesn't exist yet
        if self.index is None:
            self._create_index(dimension=embeddings_array.shape[1])
        
        # Add to FAISS index
        self.index.add(embeddings_array)
        
        # Store metadata
        self.metadata_store.extend(metadata)
        
        # Track document hash
        self.doc_hashes[doc_hash] = {
            "start_idx": len(self.metadata_store) - len(metadata),
            "end_idx": len(self.metadata_store),
            "num_chunks": len(metadata)
        }
        
        # Save to disk
        self.save_index()
        
        return True
    
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        """Search for similar vectors"""
        query_array = np.array([query_embedding]).astype('float32')
        distances, indices = self.index.search(query_array, k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata_store):
                results.append({
                    "metadata": self.metadata_store[idx],
                    "distance": float(dist)
                })
        
        return results
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        return {
            "total_vectors": self.index.ntotal,
            "total_documents": len(self.doc_hashes),
            "dimension": self.dimension
        }
