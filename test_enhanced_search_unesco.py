#!/usr/bin/env python3
"""Test enhanced search for UNESCO document"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Agent.rag_enhanced.family_aware_retriever import enhanced_search_documents

def test_unesco_search():
    """Test searching for UNESCO document"""
    
    queries = [
        "UNESCO prize for Girls' and Women's Education",
        "UNESCO prize Girls Women Education",
        "UNESCO education prize",
        "girls women education prize",
        "UNESCO 2024 prize",
        "extension submission nominations UNESCO"
    ]
    
    print("🔍 Testing Enhanced Search for UNESCO Document")
    print("=" * 60)
    
    for i, query in enumerate(queries, 1):
        print(f"\n📝 Query {i}: '{query}'")
        print("-" * 40)
        
        try:
            result = enhanced_search_documents(
                query=query,
                top_k=5,
                user_role="developer",  # Full access
                prefer_latest=True
            )
            
            print(result)
            
            # Check if UNESCO is mentioned in results
            if "UNESCO" in result:
                print("✅ Found UNESCO-related content!")
            else:
                print("❌ No UNESCO content found")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    test_unesco_search()