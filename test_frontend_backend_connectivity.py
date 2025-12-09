"""
Test script to verify frontend-backend connectivity
Run this to check if all API endpoints are accessible
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, headers=None, description=""):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Method: {method.upper()}")
    print(f"URL: {url}")
    
    try:
        if method.lower() == "get":
            response = requests.get(url, headers=headers, timeout=5)
        elif method.lower() == "post":
            response = requests.post(url, json=data, headers=headers, timeout=5)
        elif method.lower() == "put":
            response = requests.put(url, json=data, headers=headers, timeout=5)
        elif method.lower() == "delete":
            response = requests.delete(url, headers=headers, timeout=5)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code < 400:
            print("✅ SUCCESS")
            try:
                print(f"Response: {json.dumps(response.json(), indent=2)[:200]}...")
            except:
                print(f"Response: {response.text[:200]}...")
        else:
            print("❌ FAILED")
            print(f"Error: {response.text[:200]}")
            
        return response.status_code < 400
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR - Backend not running?")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    print("="*60)
    print("FRONTEND-BACKEND CONNECTIVITY TEST")
    print("="*60)
    
    results = []
    
    # Test 1: Health Check
    results.append(test_endpoint(
        "GET", "/health",
        description="Health Check"
    ))
    
    # Test 2: Root Endpoint
    results.append(test_endpoint(
        "GET", "/",
        description="Root Endpoint"
    ))
    
    # Test 3: API Documentation
    results.append(test_endpoint(
        "GET", "/docs",
        description="API Documentation (Swagger)"
    ))
    
    # Test 4: Web Scraping Stats
    results.append(test_endpoint(
        "GET", "/api/web-scraping/stats",
        description="Web Scraping Stats"
    ))
    
    # Test 5: Web Scraping Sources
    results.append(test_endpoint(
        "GET", "/api/web-scraping/sources",
        description="Web Scraping Sources List"
    ))
    
    # Test 6: Web Scraping Logs
    results.append(test_endpoint(
        "GET", "/api/web-scraping/logs?limit=10",
        description="Web Scraping Logs"
    ))
    
    # Test 7: Scraped Documents
    results.append(test_endpoint(
        "GET", "/api/web-scraping/scraped-documents?limit=10",
        description="Scraped Documents"
    ))
    
    # Test 8: Login Endpoint (should fail without credentials, but endpoint should exist)
    results.append(test_endpoint(
        "POST", "/auth/login",
        data={"email": "test@example.com", "password": "test"},
        description="Login Endpoint (should return 404 for non-existent user)"
    ))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Backend is fully accessible!")
    else:
        print("\n⚠️ SOME TESTS FAILED - Check the errors above")
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Make sure backend is running: python -m uvicorn backend.main:app --reload")
    print("2. Make sure frontend is running: cd frontend && npm run dev")
    print("3. Check frontend .env file has: VITE_API_URL=http://localhost:8000")
    print("4. Open browser to: http://localhost:3000")
    print("="*60)

if __name__ == "__main__":
    main()
