"""Lazy RAG search tools - search with on-demand embedding"""
import logging
from typing import List, Dict, Optional
from pathlib import Path
import os
from rank_bm25 import BM25Okapi

from Agent.retrieval.hybrid_retriever import HybridRetriever
from Agent.embeddings.bge_embedder import BGEEmbedder
from Agent.vector_store.faiss_store import FAISSVectorStore
from Agent.metadata.reranker import DocumentReranker
from Agent.lazy_rag.lazy_embedder import LazyEmbedder

# Setup logging
log_dir = Path("Agent/agent_logs")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "lazy_search.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize shared components
embedder = BGEEmbedder()
retriever = HybridRetriever(vector_weight=0.7, bm25_weight=0.3)
reranker = DocumentReranker(provider="gemini")
lazy_embedder = LazyEmbedder()


def search_documents_lazy(query: str, top_k: int = 5) -> str:
    """
    Lazy RAG search: Filter by metadata, rerank, then embed if needed
    
    Args:
        query: The search query
        top_k: Number of results to return
    
    Returns:
        Formatted search results with citations
    """
    logger.info(f"Lazy search for query: '{query}'")
    
    try:
        # Step 1: Get all documents with metadata from database
        from backend.database import SessionLocal, DocumentMetadata, Document
        db = SessionLocal()
        
        metadata_records = db.query(DocumentMetadata).join(Document).all()
        
        if not metadata_records:
            db.close()
            return "No documents found in the system."
        
        logger.info(f"Found {len(metadata_records)} documents with metadata")
        
        # Step 2: BM25 search on metadata keywords
        documents = []
        corpus = []
        for meta in metadata_records:
            doc_dict = {
                "id": meta.document_id,
                "title": meta.title,
                "department": meta.department,
                "document_type": meta.document_type,
                "summary": meta.summary,
                "keywords": meta.keywords or [],
                "embedding_status": meta.embedding_status,
                "filename": meta.document.filename,
                "text": meta.document.extracted_text
            }
            documents.append(doc_dict)
            
            # Create corpus for BM25
            text_for_bm25 = f"{meta.title or ''} {meta.bm25_keywords or ''} {meta.summary or ''}".lower()
            corpus.append(text_for_bm25.split())
        
        # BM25 search
        bm25 = BM25Okapi(corpus)
        query_tokens = query.lower().split()
        bm25_scores = bm25.get_scores(query_tokens)
        
        # Get top 20 candidates
        top_indices = bm25_scores.argsort()[-20:][::-1]
        candidates = [documents[i] for i in top_indices]
        
        logger.info(f"BM25 filtered to {len(candidates)} candidates")
        
        # Step 3: Rerank with LLM
        rerank_k = min(5, len(candidates))  # Don't ask for more than we have
        reranked_docs = reranker.rerank(query, candidates, top_k=rerank_k)
        logger.info(f"Reranked to top {len(reranked_docs)} documents")
        
        # Step 4: Check embedding status and embed if needed
        docs_to_embed = []
        for doc in reranked_docs:
            if doc['embedding_status'] != 'embedded':
                docs_to_embed.append(doc)
        
        if docs_to_embed:
            logger.info(f"Need to embed {len(docs_to_embed)} documents")
            
            # Embed documents
            embed_input = [
                {"id": doc['id'], "text": doc['text'], "filename": doc['filename']}
                for doc in docs_to_embed
            ]
            embed_results = lazy_embedder.embed_documents_batch(embed_input)
            
            # Update embedding status in database
            for result in embed_results:
                if result['status'] == 'success':
                    meta = db.query(DocumentMetadata).filter(
                        DocumentMetadata.document_id == result['doc_id']
                    ).first()
                    if meta:
                        meta.embedding_status = 'embedded'
            db.commit()
        
        # Step 5: Perform hybrid search on embedded documents
        all_results = []
        for doc in reranked_docs:
            index_path = f"Agent/vector_store/documents/{doc['id']}/faiss_index"
            
            if not os.path.exists(f"{index_path}.index"):
                logger.warning(f"Index not found for doc {doc['id']} after embedding attempt")
                continue
            
            # Load vector store
            vector_store = FAISSVectorStore(index_path=index_path)
            
            # Perform hybrid search
            results = retriever.retrieve(query, vector_store, embedder, top_k=3)
            
            # Add document info to results
            for result in results:
                result["document_id"] = doc['id']
                result["document_title"] = doc['title']
                all_results.append(result)
        
        db.close()
        
        if not all_results:
            return "No relevant information found."
        
        # Sort by score and take top_k
        all_results.sort(key=lambda x: x["score"], reverse=True)
        top_results = all_results[:top_k]
        
        # Format results
        formatted = f"Found {len(top_results)} relevant results:\n\n"
        for i, result in enumerate(top_results, 1):
            metadata = result["metadata"]
            formatted += f"**Result {i}** (Confidence: {result['score']:.2%})\n"
            formatted += f"Source: {metadata.get('filename', 'Unknown')}\n"
            formatted += f"Document ID: {result['document_id']}\n"
            formatted += f"Document: {result.get('document_title', 'Unknown')}\n"
            formatted += f"Chunk: {metadata.get('chunk_index', 'N/A')}\n"
            formatted += f"Text: {result['text'][:300]}...\n\n"
        
        logger.info(f"Returned {len(top_results)} results")
        return formatted
        
    except Exception as e:
        logger.error(f"Error in lazy search: {str(e)}")
        return f"Error searching documents: {str(e)}"


def search_specific_document_lazy(document_id: int, query: str, top_k: int = 5) -> str:
    """
    Search within a specific document (with lazy embedding)
    
    Args:
        document_id: The document ID to search in
        query: The search query
        top_k: Number of results to return
    
    Returns:
        Formatted search results from the specific document
    """
    logger.info(f"Lazy search in doc {document_id}: '{query}'")
    
    try:
        from backend.database import SessionLocal, DocumentMetadata, Document
        db = SessionLocal()
        
        # Get document
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            db.close()
            return f"Document {document_id} not found."
        
        # Get metadata
        metadata = db.query(DocumentMetadata).filter(
            DocumentMetadata.document_id == document_id
        ).first()
        
        # Check if embedded
        if not metadata or metadata.embedding_status != 'embedded':
            logger.info(f"Document {document_id} not embedded, embedding now...")
            
            # Embed document
            result = lazy_embedder.embed_document(
                doc_id=document_id,
                text=doc.extracted_text,
                filename=doc.filename
            )
            
            if result['status'] == 'success' and metadata:
                metadata.embedding_status = 'embedded'
                db.commit()
        
        db.close()
        
        # Now search
        index_path = f"Agent/vector_store/documents/{document_id}/faiss_index"
        
        if not os.path.exists(f"{index_path}.index"):
            return f"Document {document_id} could not be embedded."
        
        # Load vector store
        vector_store = FAISSVectorStore(index_path=index_path)
        
        # Perform hybrid search
        results = retriever.retrieve(query, vector_store, embedder, top_k=top_k)
        
        if not results:
            return f"No relevant information found in document {document_id}."
        
        # Format results
        formatted = f"Found {len(results)} results in Document {document_id}:\n\n"
        for i, result in enumerate(results, 1):
            metadata = result["metadata"]
            formatted += f"**Result {i}** (Confidence: {result['score']:.2%})\n"
            formatted += f"Source: {metadata.get('filename', 'Unknown')}\n"
            formatted += f"Chunk: {metadata.get('chunk_index', 'N/A')}\n"
            formatted += f"Text: {result['text'][:300]}...\n\n"
        
        logger.info(f"Returned {len(results)} results from doc {document_id}")
        return formatted
        
    except Exception as e:
        logger.error(f"Error in lazy search for doc {document_id}: {str(e)}")
        return f"Error searching document: {str(e)}"
