#!/usr/bin/env python3
"""Fix RAG by adding metadata-based fallback search"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Agent.tools.lazy_search_tools import search_documents_lazy

def create_metadata_fallback_search():
    """Create a metadata-based fallback search function"""
    
    code = '''
def search_documents_with_metadata_fallback(query: str, top_k: int = 5, user_role: Optional[str] = None, user_institution_id: Optional[int] = None) -> str:
    """
    Enhanced search with metadata fallback when vector search fails
    """
    logger.info(f"Enhanced search with metadata fallback for query: '{query}'")
    
    try:
        from backend.database import SessionLocal, DocumentMetadata, Document
        from sqlalchemy import or_, and_
        from rank_bm25 import BM25Okapi
        
        db = SessionLocal()
        
        # Step 1: Try vector search first
        vector_results = search_documents_lazy(query, top_k, user_role, user_institution_id)
        
        # Check if vector search found good results
        if "Found 0 relevant results" not in vector_results and "No relevant documents found" not in vector_results:
            logger.info("Vector search successful, returning results")
            db.close()
            return vector_results
        
        logger.info("Vector search failed, trying metadata-based search...")
        
        # Step 2: Metadata-based search as fallback
        query_words = query.lower().split()
        
        # Build query for metadata search
        metadata_query = db.query(Document, DocumentMetadata).outerjoin(
            DocumentMetadata, Document.id == DocumentMetadata.document_id
        ).filter(
            Document.approval_status.in_(['approved', 'pending'])
        )
        
        # Apply role-based filters
        from backend.constants.roles import DEVELOPER, MINISTRY_ADMIN, UNIVERSITY_ADMIN
        if user_role == DEVELOPER:
            pass  # Can access all
        elif user_role == MINISTRY_ADMIN:
            metadata_query = metadata_query.filter(
                Document.visibility_level.in_(['public', 'restricted', 'institution_only'])
            )
        elif user_role == UNIVERSITY_ADMIN:
            metadata_query = metadata_query.filter(
                or_(
                    Document.visibility_level == 'public',
                    and_(
                        Document.visibility_level.in_(['institution_only', 'restricted']),
                        Document.institution_id == user_institution_id
                    )
                )
            )
        else:
            filters = [Document.visibility_level == 'public']
            if user_institution_id:
                filters.append(
                    and_(
                        Document.visibility_level == 'institution_only',
                        Document.institution_id == user_institution_id
                    )
                )
            metadata_query = metadata_query.filter(or_(*filters))
        
        # Search in metadata fields
        search_conditions = []
        for word in query_words:
            word_conditions = [
                DocumentMetadata.title.ilike(f'%{word}%'),
                DocumentMetadata.summary.ilike(f'%{word}%'),
                DocumentMetadata.bm25_keywords.ilike(f'%{word}%'),
                Document.filename.ilike(f'%{word}%')
            ]
            search_conditions.extend(word_conditions)
        
        if search_conditions:
            metadata_query = metadata_query.filter(or_(*search_conditions))
        
        metadata_results = metadata_query.all()
        
        if not metadata_results:
            db.close()
            return f"No documents found matching '{query}' in titles, summaries, or keywords."
        
        # Step 3: Rank results using BM25 on metadata
        documents = []
        corpus = []
        
        for doc, meta in metadata_results:
            doc_dict = {
                "doc": doc,
                "meta": meta,
                "id": doc.id,
                "title": meta.title if meta else doc.filename,
                "filename": doc.filename
            }
            documents.append(doc_dict)
            
            # Create searchable text from metadata
            searchable_text = f"{meta.title or ''} {meta.summary or ''} {meta.bm25_keywords or ''} {doc.filename}".lower()
            corpus.append(searchable_text.split())
        
        # Rank using BM25
        bm25 = BM25Okapi(corpus)
        query_tokens = query.lower().split()
        bm25_scores = bm25.get_scores(query_tokens)
        
        # Sort by relevance score
        ranked_indices = bm25_scores.argsort()[::-1]  # Descending order
        top_results = [documents[i] for i in ranked_indices[:top_k]]
        
        # Step 4: Format results
        formatted = f"Found {len(top_results)} relevant results (metadata search):\\n\\n"
        
        for i, doc_dict in enumerate(top_results, 1):
            doc = doc_dict['doc']
            meta = doc_dict['meta']
            score = bm25_scores[ranked_indices[i-1]]
            
            approval_badge = "✅ Approved" if doc.approval_status == 'approved' else "⏳ Pending Approval"
            
            formatted += f"**Result {i}** (Relevance Score: {score:.2f}) [{approval_badge}]\\n"
            formatted += f"Source: {doc.filename}\\n"
            formatted += f"Document ID: {doc.id}\\n"
            formatted += f"Document: {meta.title if meta else doc.filename}\\n"
            formatted += f"Approval Status: {doc.approval_status}\\n"
            formatted += f"Visibility: {doc.visibility_level}\\n"
            
            if meta and meta.summary:
                formatted += f"Summary: {meta.summary[:300]}...\\n"
            
            formatted += "\\n"
        
        db.close()
        logger.info(f"Metadata search returned {len(top_results)} results")
        return formatted
        
    except Exception as e:
        logger.error(f"Error in enhanced search with metadata fallback: {str(e)}")
        return f"Error searching documents: {str(e)}"
'''
    
    return code

def test_metadata_search():
    """Test the metadata-based search"""
    
    print("🔍 Testing Metadata-Based Search for UNESCO Document")
    print("=" * 60)
    
    from backend.database import SessionLocal, DocumentMetadata, Document
    from sqlalchemy import or_
    from rank_bm25 import BM25Okapi
    
    db = SessionLocal()
    
    try:
        query = "UNESCO prize for Girls' and Women's Education"
        query_words = query.lower().split()
        
        print(f"📝 Query: '{query}'")
        print(f"📝 Query words: {query_words}")
        
        # Search in metadata fields
        search_conditions = []
        for word in query_words:
            word_conditions = [
                DocumentMetadata.title.ilike(f'%{word}%'),
                DocumentMetadata.summary.ilike(f'%{word}%'),
                DocumentMetadata.bm25_keywords.ilike(f'%{word}%'),
                Document.filename.ilike(f'%{word}%')
            ]
            search_conditions.extend(word_conditions)
        
        metadata_query = db.query(Document, DocumentMetadata).outerjoin(
            DocumentMetadata, Document.id == DocumentMetadata.document_id
        ).filter(
            Document.approval_status.in_(['approved', 'pending'])
        )
        
        if search_conditions:
            metadata_query = metadata_query.filter(or_(*search_conditions))
        
        metadata_results = metadata_query.all()
        
        print(f"📊 Found {len(metadata_results)} documents in metadata search")
        
        if metadata_results:
            # Rank using BM25
            documents = []
            corpus = []
            
            for doc, meta in metadata_results:
                documents.append({
                    "doc": doc,
                    "meta": meta,
                    "id": doc.id,
                    "title": meta.title if meta else doc.filename
                })
                
                searchable_text = f"{meta.title or ''} {meta.summary or ''} {meta.bm25_keywords or ''} {doc.filename}".lower()
                corpus.append(searchable_text.split())
            
            bm25 = BM25Okapi(corpus)
            query_tokens = query.lower().split()
            bm25_scores = bm25.get_scores(query_tokens)
            
            # Sort by relevance
            ranked_indices = bm25_scores.argsort()[::-1]
            
            print(f"\\n📊 Top 5 Results:")
            for i in range(min(5, len(ranked_indices))):
                idx = ranked_indices[i]
                doc_dict = documents[idx]
                score = bm25_scores[idx]
                
                print(f"\\n**Result {i+1}** (Score: {score:.3f})")
                print(f"   Document ID: {doc_dict['id']}")
                print(f"   Title: {doc_dict['title']}")
                print(f"   Approval: {doc_dict['doc'].approval_status}")
                
                if doc_dict['meta'] and doc_dict['meta'].summary:
                    print(f"   Summary: {doc_dict['meta'].summary[:200]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_metadata_search()