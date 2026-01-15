#!/usr/bin/env python3
"""Test pgvector search directly"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force CPU mode
import torch
torch.cuda.is_available = lambda: False

import numpy as np
from backend.database import SessionLocal, DocumentEmbedding
from Agent.embeddings.bge_embedder import BGEEmbedder

def test_pgvector_direct():
    """Test pgvector search directly"""
    
    print("🔍 Testing PGVector Search Directly")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Initialize embedder
        embedder = BGEEmbedder()
        
        # Generate query embedding
        query = "UNESCO prize for Girls' and Women's Education"
        print(f"📝 Query: '{query}'")
        
        query_embedding = embedder.embed_text(query)
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
        
        print(f"📊 Query embedding shape: {query_embedding.shape}")
        
        # Test direct pgvector search
        print("\n🔍 Testing direct pgvector cosine distance search...")
        
        results = db.query(DocumentEmbedding).order_by(
            DocumentEmbedding.embedding.cosine_distance(query_embedding.tolist())
        ).limit(10).all()
        
        print(f"📊 Found {len(results)} results")
        
        for i, result in enumerate(results, 1):
            # Calculate similarity score
            doc_embedding = np.array(result.embedding)
            distance = np.linalg.norm(query_embedding - doc_embedding)
            score = 1.0 / (1.0 + distance)
            
            print(f"\n**Result {i}** (Score: {score:.4f})")
            print(f"   Document ID: {result.document_id}")
            print(f"   Chunk Index: {result.chunk_index}")
            print(f"   Text: {result.chunk_text[:200]}...")
        
        # Test specific UNESCO document embeddings
        print(f"\n" + "="*60)
        print("🔍 Testing specific UNESCO document embeddings...")
        
        unesco_doc_ids = [250, 140, 141, 249]  # Known UNESCO docs
        
        for doc_id in unesco_doc_ids:
            doc_embeddings = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.document_id == doc_id
            ).all()
            
            print(f"\n📄 Document {doc_id}: {len(doc_embeddings)} chunks")
            
            for embedding in doc_embeddings:
                doc_embedding = np.array(embedding.embedding)
                distance = np.linalg.norm(query_embedding - doc_embedding)
                score = 1.0 / (1.0 + distance)
                
                print(f"   Chunk {embedding.chunk_index}: Score {score:.4f}")
                print(f"   Text: {embedding.chunk_text[:150]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_pgvector_direct()