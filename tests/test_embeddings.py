"""Test embedding and vector store functionality"""
import sys
sys.path.append('.')

from Agent.embeddings.bge_embedder import BGEEmbedder
from Agent.vector_store.faiss_store import FAISSVectorStore
from Agent.chunking.adaptive_chunker import AdaptiveChunker
import numpy as np
import os

def test_embedder():
    """Test BGE embedder"""
    print("\n=== Testing BGE Embedder ===")
    
    try:
        embedder = BGEEmbedder()
        
        # Test single embedding
        text = "This is a test document about government policies."
        embedding = embedder.embed_text(text)
        
        print(f"✅ Single embedding generated")
        print(f"   Dimension: {len(embedding)}")
        print(f"   Sample values: {embedding[:5]}")
        
        # Test batch embedding
        texts = [
            "Education policy guidelines",
            "Healthcare regulations",
            "Environmental standards"
        ]
        embeddings = embedder.embed_batch(texts)
        
        print(f"✅ Batch embeddings generated")
        print(f"   Count: {len(embeddings)}")
        print(f"   Dimension: {len(embeddings[0])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedder test failed: {str(e)}")
        return False


def test_chunker():
    """Test adaptive chunker"""
    print("\n=== Testing Adaptive Chunker ===")
    
    try:
        chunker = AdaptiveChunker()
        
        # Test small document
        small_text = "This is a small test document. " * 20
        chunks = chunker.chunk_text(small_text, {"filename": "test.txt"})
        
        print(f"✅ Small document chunked")
        print(f"   Text length: {len(small_text)} chars")
        print(f"   Chunks: {len(chunks)}")
        print(f"   Chunk sizes: {[len(c['text']) for c in chunks]}")
        
        # Test large document
        large_text = "This is a large test document. " * 500
        chunks = chunker.chunk_text(large_text, {"filename": "test_large.txt"})
        
        print(f"✅ Large document chunked")
        print(f"   Text length: {len(large_text)} chars")
        print(f"   Chunks: {len(chunks)}")
        print(f"   Chunk sizes: {[len(c['text']) for c in chunks[:3]]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Chunker test failed: {str(e)}")
        return False


def test_faiss_store():
    """Test FAISS vector store"""
    print("\n=== Testing FAISS Vector Store ===")
    
    try:
        # Create test store
        store = FAISSVectorStore(index_path="tests/test_faiss_index")
        
        # Create test embeddings
        embeddings = [
            np.random.rand(1024).tolist() for _ in range(5)
        ]
        
        metadata = [
            {
                "filename": f"test_{i}.txt",
                "chunk_index": i,
                "chunk_text": f"Test chunk {i}"
            }
            for i in range(5)
        ]
        
        # Add embeddings
        success = store.add_embeddings(embeddings, metadata, "test_doc_hash")
        
        if success:
            print(f"✅ Embeddings added to FAISS")
            
            # Get stats
            stats = store.get_stats()
            print(f"   Total vectors: {stats['total_vectors']}")
            print(f"   Dimension: {stats['dimension']}")
            
            # Test search
            query_embedding = np.random.rand(1024).tolist()
            results = store.search(query_embedding, k=3)
            
            print(f"✅ Search completed")
            print(f"   Results: {len(results)}")
            
            return True
        else:
            print(f"❌ Failed to add embeddings")
            return False
        
    except Exception as e:
        print(f"❌ FAISS store test failed: {str(e)}")
        return False


def cleanup():
    """Clean up test files"""
    import shutil
    test_files = [
        "tests/test_faiss_index.index",
        "tests/test_faiss_index.metadata",
        "tests/test_faiss_index.hashes"
    ]
    for file in test_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"🧹 Cleaned up: {file}")
        except Exception as e:
            print(f"⚠️  Could not delete {file}: {e}")


if __name__ == "__main__":
    print("🚀 Starting Embedding Tests")
    print("=" * 50)
    
    try:
        test_embedder()
        test_chunker()
        test_faiss_store()
        
        print("\n" + "=" * 50)
        print("✅ All embedding tests completed!")
    finally:
        print("\n🧹 Cleaning up test files...")
        cleanup()
