#!/usr/bin/env python3
"""Test enhanced search directly"""
import sys
sys.path.append('.')
from dotenv import load_dotenv
load_dotenv()

from Agent.rag_enhanced.family_aware_retriever import FamilyAwareRetriever
from backend.database import SessionLocal

def test_enhanced_search_direct():
    retriever = FamilyAwareRetriever()
    db = SessionLocal()
    
    try:
        print("Testing enhanced search directly...")
        
        results = retriever.search_with_family_awareness(
            query="education policy",
            top_k=3,
            user_role="developer",
            user_institution_id=None,
            prefer_latest=True,
            family_diversity=True,
            db=db
        )
        
        print(f"Found {len(results)} results")
        
        if results:
            for i, result in enumerate(results):
                print(f"\nResult {i+1}:")
                print(f"  Document ID: {result['document_id']}")
                print(f"  Score: {result['score']:.3f}")
                print(f"  Family ID: {result.get('family_id', 'None')}")
                print(f"  Title: {result.get('document_title', 'Unknown')}")
                print(f"  Approval: {result.get('approval_status', 'Unknown')}")
        else:
            print("No results found")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_enhanced_search_direct()