"""
Test multilingual embedding support with BGE-M3
Tests English, Hindi, and mixed language content
"""
import os
import sys
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Agent.embeddings.bge_embedder import BGEEmbedder
from Agent.embeddings.embedding_config import get_model_info, list_available_models, ACTIVE_MODEL


def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def test_model_loading():
    """Test that the configured model loads correctly"""
    print("\n" + "="*60)
    print("Test 1: Model Loading")
    print("="*60)
    
    try:
        embedder = BGEEmbedder()
        print(f"✅ Model loaded successfully!")
        print(f"   Active Model: {ACTIVE_MODEL}")
        print(f"   Dimension: {embedder.get_dimension()}")
        return True
    except Exception as e:
        print(f"❌ Model loading failed: {str(e)}")
        return False


def test_english_embeddings():
    """Test English text embeddings"""
    print("\n" + "="*60)
    print("Test 2: English Embeddings")
    print("="*60)
    
    embedder = BGEEmbedder()
    
    # Test texts
    text1 = "The Ministry of Education announced new policy guidelines for higher education."
    text2 = "Education ministry releases updated regulations for universities and colleges."
    text3 = "The weather is sunny today with clear skies."
    
    print(f"\n📝 Text 1: {text1}")
    print(f"📝 Text 2: {text2}")
    print(f"📝 Text 3: {text3}")
    
    try:
        # Generate embeddings
        emb1 = embedder.embed_text(text1)
        emb2 = embedder.embed_text(text2)
        emb3 = embedder.embed_text(text3)
        
        # Calculate similarities
        sim_1_2 = cosine_similarity(emb1, emb2)
        sim_1_3 = cosine_similarity(emb1, emb3)
        
        print(f"\n📊 Similarity Results:")
        print(f"   Text 1 ↔ Text 2 (similar topics): {sim_1_2:.4f}")
        print(f"   Text 1 ↔ Text 3 (different topics): {sim_1_3:.4f}")
        
        # Verify semantic understanding
        if sim_1_2 > sim_1_3:
            print(f"✅ Semantic similarity working correctly!")
            print(f"   Similar texts have higher similarity ({sim_1_2:.4f} > {sim_1_3:.4f})")
            return True
        else:
            print(f"⚠️  Unexpected similarity scores")
            return False
            
    except Exception as e:
        print(f"❌ English embedding test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_hindi_embeddings():
    """Test Hindi text embeddings"""
    print("\n" + "="*60)
    print("Test 3: Hindi Embeddings")
    print("="*60)
    
    embedder = BGEEmbedder()
    
    # Test texts in Hindi
    text_hindi_1 = "शिक्षा मंत्रालय ने उच्च शिक्षा के लिए नई नीति दिशानिर्देश जारी किए।"
    text_hindi_2 = "शिक्षा विभाग ने विश्वविद्यालयों के लिए नए नियम प्रकाशित किए।"
    text_hindi_3 = "आज मौसम धूप वाला है और आसमान साफ है।"
    
    print(f"\n📝 Hindi Text 1: {text_hindi_1}")
    print(f"📝 Hindi Text 2: {text_hindi_2}")
    print(f"📝 Hindi Text 3: {text_hindi_3}")
    
    try:
        # Generate embeddings
        emb1 = embedder.embed_text(text_hindi_1)
        emb2 = embedder.embed_text(text_hindi_2)
        emb3 = embedder.embed_text(text_hindi_3)
        
        # Calculate similarities
        sim_1_2 = cosine_similarity(emb1, emb2)
        sim_1_3 = cosine_similarity(emb1, emb3)
        
        print(f"\n📊 Similarity Results:")
        print(f"   Hindi Text 1 ↔ 2 (similar topics): {sim_1_2:.4f}")
        print(f"   Hindi Text 1 ↔ 3 (different topics): {sim_1_3:.4f}")
        
        if sim_1_2 > sim_1_3:
            print(f"✅ Hindi semantic similarity working!")
            return True
        else:
            print(f"⚠️  Unexpected Hindi similarity scores")
            return False
            
    except Exception as e:
        print(f"❌ Hindi embedding test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_cross_lingual_search():
    """Test cross-lingual search (English query, Hindi document)"""
    print("\n" + "="*60)
    print("Test 4: Cross-Lingual Search")
    print("="*60)
    
    embedder = BGEEmbedder()
    
    # English query
    query_en = "education policy for universities"
    
    # Documents in different languages
    doc_en = "The Ministry of Education announced new policy guidelines for higher education institutions."
    doc_hindi = "शिक्षा मंत्रालय ने उच्च शिक्षा संस्थानों के लिए नई नीति दिशानिर्देश जारी किए।"
    doc_unrelated = "The weather forecast predicts rain tomorrow afternoon."
    
    print(f"\n🔍 Query (English): {query_en}")
    print(f"\n📄 Document 1 (English): {doc_en}")
    print(f"📄 Document 2 (Hindi): {doc_hindi}")
    print(f"📄 Document 3 (Unrelated): {doc_unrelated}")
    
    try:
        # Generate embeddings
        query_emb = embedder.embed_text(query_en)
        doc1_emb = embedder.embed_text(doc_en)
        doc2_emb = embedder.embed_text(doc_hindi)
        doc3_emb = embedder.embed_text(doc_unrelated)
        
        # Calculate similarities
        sim_query_en = cosine_similarity(query_emb, doc1_emb)
        sim_query_hindi = cosine_similarity(query_emb, doc2_emb)
        sim_query_unrelated = cosine_similarity(query_emb, doc3_emb)
        
        print(f"\n📊 Cross-Lingual Search Results:")
        print(f"   Query ↔ English Doc: {sim_query_en:.4f}")
        print(f"   Query ↔ Hindi Doc: {sim_query_hindi:.4f}")
        print(f"   Query ↔ Unrelated Doc: {sim_query_unrelated:.4f}")
        
        # Both English and Hindi docs should be more similar than unrelated
        if sim_query_en > sim_query_unrelated and sim_query_hindi > sim_query_unrelated:
            print(f"✅ Cross-lingual search working!")
            print(f"   English query successfully matches both English and Hindi documents")
            print(f"   about the same topic, while rejecting unrelated content")
            return True
        else:
            print(f"⚠️  Cross-lingual search may need tuning")
            return False
            
    except Exception as e:
        print(f"❌ Cross-lingual test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_embeddings():
    """Test batch embedding generation"""
    print("\n" + "="*60)
    print("Test 5: Batch Embeddings")
    print("="*60)
    
    embedder = BGEEmbedder()
    
    texts = [
        "Government policy document on education reform",
        "शिक्षा सुधार पर सरकारी नीति दस्तावेज़",
        "Healthcare guidelines for rural areas",
        "ग्रामीण क्षेत्रों के लिए स्वास्थ्य दिशानिर्देश",
        "Infrastructure development plan"
    ]
    
    print(f"\n📝 Embedding {len(texts)} texts in batch...")
    
    try:
        embeddings = embedder.embed_batch(texts, batch_size=8)
        
        print(f"✅ Batch embedding successful!")
        print(f"   Generated {len(embeddings)} embeddings")
        print(f"   Dimension: {len(embeddings[0])}")
        
        # Verify all embeddings have correct dimension
        expected_dim = embedder.get_dimension()
        all_correct = all(len(emb) == expected_dim for emb in embeddings)
        
        if all_correct:
            print(f"✅ All embeddings have correct dimension ({expected_dim})")
            return True
        else:
            print(f"❌ Dimension mismatch detected")
            return False
            
    except Exception as e:
        print(f"❌ Batch embedding test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 Multilingual Embedding Test Suite")
    print("="*60)
    
    # Show configuration
    print(get_model_info())
    
    # Run tests
    results = []
    results.append(("Model Loading", test_model_loading()))
    results.append(("English Embeddings", test_english_embeddings()))
    results.append(("Hindi Embeddings", test_hindi_embeddings()))
    results.append(("Cross-Lingual Search", test_cross_lingual_search()))
    results.append(("Batch Embeddings", test_batch_embeddings()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! Multilingual embeddings are working correctly.")
        print(f"   Active Model: {ACTIVE_MODEL}")
        print(f"   You can now process documents in English, Hindi, and other languages!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        sys.exit(1)
