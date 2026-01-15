#!/usr/bin/env python3
"""Test the fixed RAG system with metadata fallback"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force CPU mode
import torch
torch.cuda.is_available = lambda: False

from Agent.rag_agent.react_agent import PolicyRAGAgent
import os

def test_fixed_rag():
    """Test the fixed RAG system"""
    
    print("🔍 Testing Fixed RAG System with Metadata Fallback")
    print("=" * 60)
    
    try:
        # Initialize RAG agent
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            print("❌ GOOGLE_API_KEY not found in environment")
            return
        
        agent = PolicyRAGAgent(google_api_key=google_api_key)
        
        # Test UNESCO query
        query = "UNESCO prize for Girls' and Women's Education"
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
        print(result.get('answer', 'No answer'))
        
        if result.get('citations'):
            print(f"\n📚 Citations:")
            for i, citation in enumerate(result['citations'], 1):
                print(f"   {i}. Doc {citation.get('document_id')} - {citation.get('source', 'Unknown')}")
        
        # Check if UNESCO is mentioned
        answer = result.get('answer', '')
        if "UNESCO" in answer:
            print("\n✅ Found UNESCO-related content!")
        else:
            print("\n❌ No UNESCO content found in answer")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_rag()