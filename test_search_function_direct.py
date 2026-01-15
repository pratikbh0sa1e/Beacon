#!/usr/bin/env python3
"""Test the search function directly without RAG agent"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force CPU mode
import torch
torch.cuda.is_available = lambda: False

# Import the search function directly
from Agent.rag_agent.react_agent import search_documents_with_metadata_fallback

def test_search_function_direct():
    """Test the search function directly"""
    
    print("🔍 Testing Search Function Directly - Indo-Norwegian Query")
    print("=" * 60)
    
    try:
        # Test the specific query that was failing
        query = "Indo-Norwegian Cooperation Programme"
        print(f"📝 Query: '{query}'")
        print("-" * 40)
        
        result = search_documents_with_metadata_fallback(
            query=query,
            top_k=5,
            user_role="developer",  # Full access
            user_institution_id=None
        )
        
        print("✅ Search completed!")
        print(f"\n📄 Results:")
        print(result)
        
        # Check if Indo-Norwegian content was found
        if "Indo-Norwegian" in result or "INCP2" in result:
            print("\n✅ SUCCESS: Found Indo-Norwegian content!")
            
            # Check if the correct documents were found
            if "Document ID: 139" in result or "Document ID: 248" in result:
                print("✅ Found the correct document IDs (139 or 248)!")
            else:
                print("⚠️ Found Indo-Norwegian content but not the specific documents")
        else:
            print("\n❌ FAILED: No Indo-Norwegian content found")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search_function_direct()