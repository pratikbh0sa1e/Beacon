"""Test script for citation extraction"""
import os
from dotenv import load_dotenv
from Agent.rag_agent.react_agent import PolicyRAGAgent
import json

# Load environment variables
load_dotenv()

def test_citations():
    """Test if citations are being extracted properly"""
    print("🧪 Testing Citation Extraction")
    print("=" * 60)
    
    # Initialize agent
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ GOOGLE_API_KEY not found in .env")
        return
    
    print("✅ Initializing agent...")
    agent = PolicyRAGAgent(google_api_key=google_api_key)
    
    # Test queries
    test_queries = [
        "Who is Sarthak Bhoj?",
        "What is Sarthak's email and phone number?",
        "Tell me about Sarthak's education background"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {query}")
        print("=" * 60)
        
        try:
            result = agent.query(query)
            
            print(f"\n📝 Answer:")
            print(result["answer"][:200] + "..." if len(result["answer"]) > 200 else result["answer"])
            
            print(f"\n📚 Citations: {len(result['citations'])}")
            if result["citations"]:
                for j, citation in enumerate(result["citations"], 1):
                    print(f"  {j}. Document ID: {citation['document_id']}")
                    print(f"     Source: {citation['source']}")
                    print(f"     Tool: {citation['tool']}")
            else:
                print("  ⚠️  No citations found!")
            
            print(f"\n🎯 Confidence: {result['confidence']:.2%}")
            print(f"📊 Status: {result['status']}")
            
            # Pretty print full result
            print(f"\n📄 Full JSON Response:")
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("\n" + "="*60)
        
        # Wait between queries to avoid rate limits
        if i < len(test_queries):
            print("⏳ Waiting 5 seconds before next query...")
            import time
            time.sleep(5)
    
    print("\n✅ Citation test completed!")

if __name__ == "__main__":
    test_citations()
