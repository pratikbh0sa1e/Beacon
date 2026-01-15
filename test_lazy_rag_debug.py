#!/usr/bin/env python3
"""Debug lazy RAG implementation"""
import sys
import os
sys.path.append('.')
from dotenv import load_dotenv
load_dotenv()

print('Testing pgvector search directly...')
from Agent.vector_store.pgvector_store import PGVectorStore
from Agent.embeddings.bge_embedder import BGEEmbedder
import numpy as np

# Initialize components
embedder = BGEEmbedder()
pgvector_store = PGVectorStore()

# Generate query embedding
query = 'education'
query_embedding = embedder.embed_text(query)
if isinstance(query_embedding, list):
    query_embedding = np.array(query_embedding)

print(f'Query embedding shape: {query_embedding.shape}')

# Search directly
results = pgvector_store.search(
    query_embedding=query_embedding,
    top_k=3,
    user_role='developer'
)

print(f'Found {len(results)} results')
for i, result in enumerate(results):
    print(f'Result {i+1}: Doc {result["document_id"]} - Score: {result["score"]:.3f}')
    print(f'Text: {result["text"][:100]}...')
    print()

# Test lazy search
print('\n' + '='*50)
print('Testing lazy search...')
from Agent.tools.lazy_search_tools import search_documents_lazy

result = search_documents_lazy('education', top_k=3, user_role='developer')
print('Lazy search result:')
print(result)