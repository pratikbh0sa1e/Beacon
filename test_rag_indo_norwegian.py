#!/usr/bin/env python3
"""Test RAG system with Indo-Norwegian query"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force CPU mode
import torch
torch.cuda.is_available = lambda: False

from Agent.rag_agent.react_agent import PolicyRAGAgent

def test_rag_indo_norwegian():
    """Test RAG system with Indo-Norwegian query"""
    
    print("🔍 Testing RAG System with Indo-Norwegian Query")
    print("=" * 60)
    
    try:
        # Initialize RAG agent
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            print("❌ GOOGLE_API_KEY not found in environment")
            return
        
        agent = PolicyRAGAgent(google_api_key=google_api_key)
        
        # Test different variations of the query
        queries = [
            "Indo-Norwegian Cooperation Programme",
            "Indo Norwegian Cooperation Programme",
            "INCP2",
            "Norwegian cooperation program",
            "Call for Applications for Indo-Norwegian Cooperation Programme"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n📝 Query {i}: '{query}'")
            print("-" * 40)
            
            result = agent.query(
                question=query,
                user_role="developer",  # Full access
                user_institution_id=None
            )
            
            print(f"📊 Status: {result.get('status', 'unknown')}")
            print(f"📊 Confidence: {result.get('confidence', 0):.2%}")
            print(f"📊 Citations: {len(result.get('citations', []))}")
            
            answer = result.get('answer', '')
            if "Indo-Norwegian" in answer or "INCP2" in answer or "Norwegian" in answer:
                print("✅ Found Indo-Norwegian content!")
            else:
                print("❌ No Indo-Norwegian content found")
                print(f"Answer preview: {answer[:200]}...")
            
            print("\n" + "="*60)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag_indo_norwegian()