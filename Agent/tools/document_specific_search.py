"""Document-specific search tool for @beacon in document chat"""
import logging
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

from Agent.embeddings.bge_embedder import BGEEmbedder
from Agent.vector_store.pgvector_store import PGVectorStore

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_HOSTNAME = os.getenv("DATABASE_HOSTNAME")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")

DATABASE_URL = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOSTNAME}:{DATABASE_PORT}/{DATABASE_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

embedder = BGEEmbedder()
vector_store = PGVectorStore()


def search_within_document(
    document_id: int,
    query: str,
    user_role: str = None,
    user_institution_id: int = None,
    top_k: int = 5
) -> str:
    """Search ONLY within a specific document for @beacon invocations"""
    try:
        logger.info(f"Searching within document {document_id} for query: {query}")
        
        query_embedding = embedder.embed_query(query)
        
        results = vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            user_role=user_role,
            user_institution_id=user_institution_id,
            document_id_filter=document_id
        )
        
        if not results:
            return f"No relevant information found in this document for query: '{query}'"
        
        formatted_results = []
        formatted_results.append(f"Found {len(results)} relevant sections in the document:\n")
        
        for i, result in enumerate(results, 1):
            chunk_text = result.get("chunk_text", "")
            score = result.get("score", 0.0)
            chunk_metadata = result.get("chunk_metadata", {})
            page_number = chunk_metadata.get("page_number", "Unknown")
            
            formatted_results.append(f"\n--- Result {i} (Relevance: {score:.2f}) ---")
            formatted_results.append(f"Page: {page_number}")
            formatted_results.append(f"Content: {chunk_text[:500]}...")
            formatted_results.append("")
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"Error searching within document {document_id}: {str(e)}")
        return f"Error searching document: {str(e)}"
