#!/usr/bin/env python3
"""Test metadata search directly for Indo-Norwegian"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal, DocumentMetadata, Document
from sqlalchemy import or_, and_
from rank_bm25 import BM25Okapi

def test_metadata_search_direct():
    """Test metadata search directly"""
    
    print("🔍 Testing Metadata Search for Indo-Norwegian")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        query = "Indo-Norwegian Cooperation Programme"
        query_words = query.lower().split()
        
        print(f"📝 Query: '{query}'")
        print(f"📝 Query words: {query_words}")
        
        # Search in metadata fields
        search_conditions = []
        for word in query_words:
            if len(word) > 2:  # Skip very short words
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
                    "title": meta.title if meta and meta.title else doc.filename
                })
                
                # Handle None values properly
                title = meta.title if meta and meta.title else ""
                summary = meta.summary if meta and meta.summary else ""
                keywords = meta.bm25_keywords if meta and meta.bm25_keywords else ""
                filename = doc.filename if doc.filename else ""
                
                searchable_text = f"{title} {summary} {keywords} {filename}".lower()
                corpus.append(searchable_text.split())
            
            bm25 = BM25Okapi(corpus)
            query_tokens = query.lower().split()
            bm25_scores = bm25.get_scores(query_tokens)
            
            # Sort by relevance
            ranked_indices = bm25_scores.argsort()[::-1]
            
            print(f"\n📊 Top 10 Results:")
            for i in range(min(10, len(ranked_indices))):
                idx = ranked_indices[i]
                doc_dict = documents[idx]
                score = bm25_scores[idx]
                
                print(f"\n**Result {i+1}** (Score: {score:.3f})")
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
    test_metadata_search_direct()