"""Test RAG agent and tools"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"

def test_chat_health():
    """Test chat service health"""
    print("\n=== Testing Chat Health ===")
    
    response = requests.get(f"{BASE_URL}/chat/health")
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {data}")
    
    if response.status_code == 200 and data.get('status') == 'healthy':
        print("✅ Chat service is healthy")
        return True
    else:
        print("❌ Chat service is unhealthy")
        return False


def test_simple_query():
    """Test simple Q&A query"""
    print("\n=== Testing Simple Query ===")
    
    payload = {
        "question": "What documents are available in the system?",
        "thread_id": "test_session_1"
    }
    
    response = requests.post(f"{BASE_URL}/chat/query", json=payload)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Answer: {data.get('answer')[:200]}...")
        print(f"Confidence: {data.get('confidence')}")
        print(f"Status: {data.get('status')}")
        print("✅ Simple query successful")
        return data
    else:
        print(f"❌ Simple query failed: {response.text}")
        return None


def test_search_query():
    """Test search-based query"""
    print("\n=== Testing Search Query ===")
    
    payload = {
        "question": "Search for information about education policies",
        "thread_id": "test_session_2"
    }
    
    response = requests.post(f"{BASE_URL}/chat/query", json=payload)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Answer: {data.get('answer')[:200]}...")
        print(f"Confidence: {data.get('confidence')}")
        print("✅ Search query successful")
        return data
    else:
        print(f"❌ Search query failed: {response.text}")
        return None


def test_comparison_query():
    """Test policy comparison query"""
    print("\n=== Testing Comparison Query ===")
    
    payload = {
        "question": "Compare documents 1 and 2 on their main topics",
        "thread_id": "test_session_3"
    }
    
    response = requests.post(f"{BASE_URL}/chat/query", json=payload)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Answer: {data.get('answer')[:200]}...")
        print(f"Confidence: {data.get('confidence')}")
        print("✅ Comparison query successful")
        return data
    else:
        print(f"❌ Comparison query failed: {response.text}")
        return None


def test_web_search_query():
    """Test web search query"""
    print("\n=== Testing Web Search Query ===")
    
    payload = {
        "question": "Search the web for latest education policy updates in India",
        "thread_id": "test_session_4"
    }
    
    response = requests.post(f"{BASE_URL}/chat/query", json=payload)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Answer: {data.get('answer')[:200]}...")
        print(f"Confidence: {data.get('confidence')}")
        print("✅ Web search query successful")
        return data
    else:
        print(f"❌ Web search query failed: {response.text}")
        return None


def test_multi_step_reasoning():
    """Test multi-step reasoning"""
    print("\n=== Testing Multi-Step Reasoning ===")
    
    payload = {
        "question": "First, find all documents about education. Then, summarize the key points from the most relevant one.",
        "thread_id": "test_session_5"
    }
    
    response = requests.post(f"{BASE_URL}/chat/query", json=payload)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Answer: {data.get('answer')[:300]}...")
        print(f"Confidence: {data.get('confidence')}")
        print("✅ Multi-step reasoning successful")
        return data
    else:
        print(f"❌ Multi-step reasoning failed: {response.text}")
        return None


if __name__ == "__main__":
    print("🚀 Starting Agent Tests")
    print("=" * 50)
    
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except:
        print("❌ Server is not running! Start with: uvicorn backend.main:app --reload")
        exit(1)
    
    # Run tests
    test_chat_health()
    test_simple_query()
    test_search_query()
    # test_comparison_query()  # Uncomment if you have multiple documents
    # test_web_search_query()  # Uncomment to test web search
    # test_multi_step_reasoning()  # Uncomment for complex queries
    
    print("\n" + "=" * 50)
    print("✅ All agent tests completed!")
