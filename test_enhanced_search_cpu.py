#!/usr/bin/env python3
"""Test enhanced search with CPU mode"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force CPU mode
import torch
torch.cuda.is_available = lambda: False

from Agent.rag_enhanced.family_aware_retriever import enhanced_search_documents

def test_unesco_search_cpu():
    """Test searching for UNESCO document with CPU mode"""
    
    print("🔍 Testing Enhanced Search for UNESCO Document (CPU Mode)")
    print("=" * 60)
    
    query = "UNESCO prize for Girls' and Women's Education"
    print(f"📝 Query: '{query}'")
    print("-" * 40)
    
    try:
        result = enhanced_search_documents(
            query=query,
            top_k=5,
            user_role="developer",  # Full access
            prefer_latest=True
        )
        
        print("✅ Search completed successfully!")
        print("\n📊 Results:")
        print(result)
        
        # Check if UNESCO is mentioned in results
        if "UNESCO" in result:
            print("\n✅ Found UNESCO-related content!")
        else:
            print("\n❌ No UNESCO content found")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_unesco_search_cpu()