#!/usr/bin/env python3
"""Test comprehensive queries to ensure all work"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force CPU mode
import torch
torch.cuda.is_available = lambda: False

from Agent.rag_agent.react_agent import search_documents_with_metadata_fallback

def test_comprehensive_queries():
    """Test various types of queries to ensure comprehensive coverage"""
    
    print("🔍 Testing Comprehensive Query Coverage")
    print("=" * 60)
    
    # Test different types of queries
    test_queries = [
        # Specific document names
        "Indo-Norwegian Cooperation Programme",
        "UNESCO prize for Girls' and Women's Education", 
        "INCP2",
        "Stipendium Hungaricum",
        
        # General topics
        "scholarship programs",
        "education policy",
        "student welfare",
        "digital education",
        "higher education guidelines",
        
        # Partial matches
        "Norwegian cooperation",
        "UNESCO education",
        "UGC guidelines",
        "fellowship programs",
        
        # Broad searches
        "policy documents",
        "government circulars",
        "ministry notifications",
        "university grants"
    ]
    
    results_summary = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: '{query}'")
        print("-" * 40)
        
        try:
            result = search_documents_with_metadata_fallback(
                query=query,
                top_k=3,  # Limit to 3 for faster testing
                user_role="developer",
                user_institution_id=None
            )
            
            # Analyze results
            if "No documents found" in result or "Error" in result:
                status = "❌ FAILED"
                found_docs = 0
            else:
                status = "✅ SUCCESS"
                # Count documents found
                found_docs = result.count("Document ID:")
            
            results_summary.append({
                "query": query,
                "status": status,
                "found_docs": found_docs
            })
            
            print(f"{status} - Found {found_docs} documents")
            
            # Show first result for verification
            if found_docs > 0:
                lines = result.split('\n')
                for line in lines:
                    if "Document:" in line and not line.startswith("Document ID:"):
                        print(f"   First result: {line.strip()}")
                        break
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results_summary.append({
                "query": query,
                "status": "❌ ERROR",
                "found_docs": 0
            })
    
    # Summary report
    print(f"\n" + "="*60)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("="*60)
    
    total_queries = len(test_queries)
    successful_queries = sum(1 for r in results_summary if r["status"] == "✅ SUCCESS")
    failed_queries = total_queries - successful_queries
    
    print(f"Total Queries Tested: {total_queries}")
    print(f"Successful Queries: {successful_queries}")
    print(f"Failed Queries: {failed_queries}")
    print(f"Success Rate: {(successful_queries/total_queries)*100:.1f}%")
    
    if failed_queries > 0:
        print(f"\n❌ Failed Queries:")
        for r in results_summary:
            if r["status"] != "✅ SUCCESS":
                print(f"   - {r['query']} ({r['status']})")
    
    print(f"\n✅ Successful Queries:")
    for r in results_summary:
        if r["status"] == "✅ SUCCESS":
            print(f"   - {r['query']} ({r['found_docs']} docs)")
    
    # Overall assessment
    if successful_queries == total_queries:
        print(f"\n🎉 PERFECT! All queries working correctly!")
    elif successful_queries >= total_queries * 0.9:
        print(f"\n✅ EXCELLENT! 90%+ queries working correctly!")
    elif successful_queries >= total_queries * 0.8:
        print(f"\n👍 GOOD! 80%+ queries working correctly!")
    else:
        print(f"\n⚠️ NEEDS IMPROVEMENT! Less than 80% success rate")

if __name__ == "__main__":
    test_comprehensive_queries()