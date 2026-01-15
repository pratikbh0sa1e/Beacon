#!/usr/bin/env python3
"""Test the fixed RAG system with Indo-Norwegian query"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force CPU mode
import torch
torch.cuda.is_available = lambda: False

from Agent.rag_agent.react_agent import PolicyRAGAgent

def test_fixed_rag_indo_norwegian():
    """Test the fixed RAG system with Indo-Norwegian query"""
    
    print("🔍 Testing Fixed RAG System - Indo-Norwegian Query")
    print("=" * 60)
    
    try:
        # Initialize RAG agent
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            print("❌ GOOGLE_API_KEY not found in environment")
            return
        
        agent = PolicyRAGAgent(google_api_key=google_api_key)
        
        # Test the specific query that was failing
        query = "Indo-Norwegian Cooperation Programme"
        print(f"📝 Query: '{query}'")
        print("-" * 40)
        
        result = agent.query(
            question=query,
            user_role="developer",  # Full access
            user_institution_id=None
        )
        
        print("✅ RAG Query completed!")
        print(f"\n📊 Status: {result.get('status', 'unknown')}")
        print(f"📊 Confidence: {result.get('confidence', 0):.2%}")
        print(f"📊 Citations: {len(result.get('citations', []))}")
        
        print(f"\n📄 Answer:")
        answer = result.get('answer', 'No answer')
        print(answer)
        
        if result.get('citations'):
            print(f"\n📚 Citations:")
            for i, citation in enumerate(result['citations'], 1):
                print(f"   {i}. Doc {citation.get('document_id')} - {citation.get('source', 'Unknown')}")
        
        # Check if Indo-Norwegian content was found
        if "Indo-Norwegian" in answer or "INCP2" in answer:
            print("\n✅ SUCCESS: Found Indo-Norwegian content!")
            
            # Check if the correct documents were found
            citations = result.get('citations', [])
            correct_docs = [c for c in citations if c.get('document_id') in ['139', '248', 139, 248]]
            
            if correct_docs:
                print(f"✅ Found {len(correct_docs)} correct document citations!")
            else:
                print("⚠️ Found Indo-Norwegian content but not the specific documents")
        else:
            print("\n❌ FAILED: No Indo-Norwegian content found")
            print("This indicates the metadata fallback is still not working properly")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_rag_indo_norwegian()