"""Test hybrid retrieval functionality"""
import sys
sys.path.append('.')

from Agent.retrieval.hybrid_retriever import HybridRetriever
from Agent.embeddings.bge_embedder import BGEEmbedder
from Agent.vector_store.faiss_store import FAISSVectorStore
import numpy as np
import os

def test_hybrid_retrieval():
    """Test hybrid retrieval (Vector + BM25)"""
    print("\n=== Testing Hybrid Retrieval ===")
    
    try:
        # Setup
        embedder = BGEEmbedder()
        retriever = HybridRetriever(vector_weight=0.7, bm25_weight=0.3)
        store = FAISSVectorStore(index_path="tests/test_retrieval_index")
        
        # Create test documents
        test_docs = [
            "The education policy focuses on improving student outcomes and teacher training.",
            "Healthcare regulations require hospitals to maintain quality standards.",
            "Environmental protection laws aim to reduce pollution and preserve nature.",
            "Financial policies govern banking operations and monetary transactions.",
            "Transportation infrastructure includes roads, railways, and airports."
        ]
        
        # Generate embeddings
        embeddings = embedder.embed_batch(test_docs)
        
        # Create metadata with chunk_text
        metadata = [
            {
                "filename": f"doc_{i}.txt",
                "chunk_index": i,
                "chunk_text": doc
            }
            for i, doc in enumerate(test_docs)
        ]
        
        # Add to store
        store.add_embeddings(embeddings, metadata, "test_retrieval_hash")
        
        print(f"✅ Test documents indexed")
        print(f"   Documents: {len(test_docs)}")
        
        # Test queries
        queries = [
            "education and teachers",
            "hospital quality",
            "pollution control"
        ]
        
        for query in queries:
            print(f"\n📝 Query: '{query}'")
            results = retriever.retrieve(query, store, embedder, top_k=2)
            
            print(f"   Results: {len(results)}")
            for i, result in enumerate(results, 1):
                print(f"   {i}. Score: {result['score']:.3f} (V:{result['vector_score']:.3f}, B:{result['bm25_score']:.3f})")
                print(f"      Text: {result['text'][:60]}...")
        
        print(f"\n✅ Hybrid retrieval test successful")
        return True
        
    except Exception as e:
        print(f"❌ Hybrid retrieval test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def cleanup():
    """Clean up test files"""
    import shutil
    test_files = [
        "tests/test_retrieval_index.index",
        "tests/test_retrieval_index.metadata",
        "tests/test_retrieval_index.hashes"
    ]
    for file in test_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"🧹 Cleaned up: {file}")
        except Exception as e:
            print(f"⚠️  Could not delete {file}: {e}")


if __name__ == "__main__":
    print("🚀 Starting Retrieval Tests")
    print("=" * 50)
    
    try:
        test_hybrid_retrieval()
        
        print("\n" + "=" * 50)
        print("✅ All retrieval tests completed!")
    finally:
        print("\n🧹 Cleaning up test files...")
        cleanup()
