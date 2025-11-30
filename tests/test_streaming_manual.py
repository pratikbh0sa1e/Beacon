"""
Manual test script for streaming functionality
Run this to test the streaming endpoints
"""
import requests
import json
import sys
import time

# Configuration
BASE_URL = "http://localhost:8000"
TEST_QUESTION = "What are the main education policies?"
THREAD_ID = f"test-{int(time.time())}"

# You'll need to get a valid token by logging in first
# For testing, you can temporarily disable auth or use a valid token
AUTH_TOKEN = None  # Set this to a valid token


def test_chat_streaming():
    """Test chat streaming endpoint"""
    print("=" * 60)
    print("Testing Chat Streaming")
    print("=" * 60)
    
    url = f"{BASE_URL}/chat/query/stream"
    headers = {
        "Content-Type": "application/json",
    }
    
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    
    data = {
        "question": TEST_QUESTION,
        "thread_id": THREAD_ID
    }
    
    print(f"\nQuestion: {TEST_QUESTION}")
    print(f"Thread ID: {THREAD_ID}")
    print("\nStreaming response:\n")
    
    try:
        with requests.post(url, json=data, headers=headers, stream=True, timeout=60) as response:
            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code}")
                print(response.text)
                return False
            
            content_tokens = []
            citations = []
            metadata = {}
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    
                    if line.startswith('data: '):
                        try:
                            event = json.loads(line[6:])
                            event_type = event.get('type')
                            
                            if event_type == 'content':
                                token = event.get('token', '')
                                content_tokens.append(token)
                                print(token, end='', flush=True)
                                
                            elif event_type == 'citation':
                                citation = event.get('citation', {})
                                citations.append(citation)
                                print(f"\n\n📚 Citation: {citation.get('document_title', 'Unknown')} (Page {citation.get('page_number', '?')})")
                                
                            elif event_type == 'metadata':
                                metadata = event
                                print(f"\n\n✅ Confidence: {event.get('confidence', 0) * 100:.0f}%")
                                print(f"Status: {event.get('status', 'unknown')}")
                                
                            elif event_type == 'error':
                                print(f"\n\n❌ Error: {event.get('message', 'Unknown error')}")
                                print(f"Recoverable: {event.get('recoverable', False)}")
                                return False
                                
                            elif event_type == 'done':
                                print("\n\n✓ Stream complete")
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"\n\nError parsing JSON: {e}")
                            print(f"Line: {line}")
            
            # Summary
            print("\n" + "=" * 60)
            print("Summary:")
            print(f"  Total tokens: {len(content_tokens)}")
            print(f"  Total citations: {len(citations)}")
            print(f"  Final confidence: {metadata.get('confidence', 0) * 100:.0f}%")
            print("=" * 60)
            
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"\n\n❌ Request failed: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return False


def test_non_streaming():
    """Test non-streaming endpoint for comparison"""
    print("\n\n" + "=" * 60)
    print("Testing Non-Streaming (for comparison)")
    print("=" * 60)
    
    url = f"{BASE_URL}/chat/query"
    headers = {
        "Content-Type": "application/json",
    }
    
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    
    data = {
        "question": TEST_QUESTION,
        "thread_id": THREAD_ID
    }
    
    print(f"\nQuestion: {TEST_QUESTION}")
    print("\nWaiting for response...\n")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=data, headers=headers, timeout=60)
        elapsed = time.time() - start_time
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return False
        
        result = response.json()
        
        print(f"Answer: {result.get('answer', 'No answer')}")
        print(f"\nCitations: {len(result.get('citations', []))}")
        print(f"Confidence: {result.get('confidence', 0) * 100:.0f}%")
        print(f"Time taken: {elapsed:.2f}s")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False


def check_health():
    """Check if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Server is running")
            return True
        else:
            print(f"⚠️  Server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Server is not running")
        print(f"   Make sure the backend is running at {BASE_URL}")
        return False


def main():
    """Main test runner"""
    print("\n" + "=" * 60)
    print("STREAMING FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Check server health
    if not check_health():
        print("\nPlease start the backend server:")
        print("  uvicorn backend.main:app --reload")
        sys.exit(1)
    
    # Note about authentication
    if not AUTH_TOKEN:
        print("\n⚠️  Note: AUTH_TOKEN not set")
        print("   If authentication is required, set AUTH_TOKEN in this script")
        print("   or temporarily disable auth for testing")
    
    print("\n")
    
    # Run tests
    streaming_success = test_chat_streaming()
    
    if streaming_success:
        # Compare with non-streaming
        test_non_streaming()
    
    print("\n" + "=" * 60)
    if streaming_success:
        print("✅ Streaming test completed successfully!")
    else:
        print("❌ Streaming test failed")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
