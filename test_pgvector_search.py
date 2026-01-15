#!/usr/bin/env python3
"""Test pgvector search directly"""
import sys
sys.path.append('.')
from dotenv import load_dotenv
load_dotenv()

from Agent.vector_store.pgvector_store import PGVectorStore
from Agent.embeddings.bge_embedder import BGEEmbedder
import numpy as np

def test_pgvector_search():
    embedder = BGEEmbedder()
    pgvector_store = PGVectorStore()

    query_embedding = embedder.embed_text('education')
    if isinstance(query_embedding, list):
        query_embedding = np.array(query_embedding)

    print(f'Query embedding shape: {query_embedding.shape}')

    # Test without role filtering first
    from backend.database import SessionLocal
    db = SessionLocal()

    results = pgvector_store.search(
        query_embedding=query_embedding,
        top_k=3,
        user_role=None,  # No role filtering
        user_institution_id=None,
        db=db
    )

    print(f'Found {len(results)} results without role filtering')
    for i, result in enumerate(results[:2]):
        print(f'Result {i+1}: Doc {result["document_id"]} - Score: {result["score"]:.3f}')
        print(f'  Text: {result["text"][:100]}...')

    # Test with developer role
    results_dev = pgvector_store.search(
        query_embedding=query_embedding,
        top_k=3,
        user_role='developer',
        user_institution_id=None,
        db=db
    )

    print(f'\nFound {len(results_dev)} results with developer role')

    db.close()

if __name__ == "__main__":
    test_pgvector_search()