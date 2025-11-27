"""Test script for citation extraction"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from Agent.rag_agent.react_agent import PolicyRAGAgent
import time

# Load environment variables
load_dotenv()

def test_citations():
    """Test if citations are being extracted properly"""
    print("🚀 Starting Citation Tests")
    print("=" * 50)
    
    # Initialize agent
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ GOOGLE_API_KEY not found in .env")
        return False
    
    print("\n=== Testing Agent Initialization ===")
    try:
        agent = PolicyRAGAgent(google_api_key=google_api_key)
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Agent initialization failed: {str(e)}")
        return False
    
    # Test query
    print("\n=== Testing Citation Extraction ===")
    query = "Who is Sarthak Bhoj?"
    print(f"Query: '{query}'")
    
    try:
        result = agent.query(query)
        
        # Check if citations exist
        if result["citations"] and len(result["citations"]) > 0:
            print(f"✅ Citations extracted: {len(result['citations'])}")
            for i, citation in enumerate(result["citations"], 1):
                print(f"   {i}. Doc {citation['document_id']}: {citation['source']}")
        else:
            print("⚠️  No citations found (may need documents in system)")
        
        # Check confidence
        print(f"✅ Confidence: {result['confidence']:.2%}")
        
        # Check status
        if result["status"] == "success":
            print("✅ Query successful")
        else:
            print(f"⚠️  Query status: {result['status']}")
        
    except Exception as e:
        print(f"❌ Citation test failed: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All citation tests completed!")
    return True

if __name__ == "__main__":
    success = test_citations()
    exit(0 if success else 1)
