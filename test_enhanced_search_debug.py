#!/usr/bin/env python3
"""Debug enhanced search step by step"""
import sys
sys.path.append('.')
from dotenv import load_dotenv
load_dotenv()

from Agent.rag_enhanced.family_aware_retriever import FamilyAwareRetriever
from backend.database import SessionLocal

def test_enhanced_search_debug():
    retriever = FamilyAwareRetriever()
    db = SessionLocal()
    
    try:
        print("Testing family-aware search step by step...")
        
        # Step 1: Test basic search
        results = retriever.search_with_family_awareness(
            query="education",
            top_k=3,
            user_role="developer",
            user_institution_id=None,
            db=db
        )
        
        print(f"Step 1 - Basic search: Found {len(results)} results")
        
        if results:
            for i, result in enumerate(results[:2]):
                print(f"  Result {i+1}: Doc {result['document_id']} - Score: {result['score']:.3f}")
                print(f"    Family: {result.get('family_id', 'None')}")
                print(f"    Title: {result.get('document_title', 'Unknown')}")
        
        # Step 2: Test family search
        print("\nStep 2 - Testing family search...")
        families = retriever.find_related_families("education", top_k=3, db=db)
        print(f"Found {len(families)} related families")
        
        for family in families[:2]:
            print(f"  Family {family['family_id']}: {family['canonical_title']}")
            print(f"    Score: {family['score']:.3f}, Docs: {family['document_count']}")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_enhanced_search_debug()