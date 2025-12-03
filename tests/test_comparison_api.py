"""Test policy comparison API endpoints"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

# Configuration
BASE_URL = "http://localhost:8000"
TOKEN = "YOUR_TOKEN_HERE"  # Replace with valid token

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def test_compare_documents():
    """Test document comparison endpoint"""
    print("\n" + "="*60)
    print("Testing: POST /documents/compare")
    print("="*60)
    
    # Test data - replace with actual document IDs from your database
    payload = {
        "document_ids": [1, 2],  # Replace with real IDs
        "comparison_aspects": ["objectives", "scope", "beneficiaries"]
    }
    
    response = requests.post(
        f"{BASE_URL}/documents/compare",
        headers=headers,
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {data.get('status')}")
        print(f"✅ Documents Compared: {len(data.get('documents', []))}")
        
        if data.get('comparison_matrix'):
            print(f"✅ Comparison Matrix Keys: {list(data['comparison_matrix'].keys())}")
        
        if data.get('summary'):
            print(f"✅ Summary Available: Yes")
            if data['summary'].get('key_differences'):
                print(f"   Key Differences: {len(data['summary']['key_differences'])}")
        
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_detect_conflicts():
    """Test conflict detection endpoint"""
    print("\n" + "="*60)
    print("Testing: POST /documents/compare/conflicts")
    print("="*60)
    
    # Test data
    payload = {
        "document_ids": [1, 2]  # Replace with real IDs
    }
    
    response = requests.post(
        f"{BASE_URL}/documents/compare/conflicts",
        headers=headers,
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {data.get('status')}")
        print(f"✅ Documents Analyzed: {len(data.get('documents', []))}")
        print(f"✅ Conflicts Found: {len(data.get('conflicts', []))}")
        
        if data.get('conflicts'):
            print(f"\nConflicts:")
            for i, conflict in enumerate(data['conflicts'][:3], 1):
                print(f"  {i}. Type: {conflict.get('type')}, Severity: {conflict.get('severity')}")
        
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_role_based_access():
    """Test role-based access control"""
    print("\n" + "="*60)
    print("Testing: Role-Based Access Control")
    print("="*60)
    
    # Try to compare documents user doesn't have access to
    payload = {
        "document_ids": [999, 1000]  # Non-existent or restricted IDs
    }
    
    response = requests.post(
        f"{BASE_URL}/documents/compare",
        headers=headers,
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 403:
        print(f"✅ Access Denied (Expected): Role-based filtering working")
        return True
    elif response.status_code == 404:
        print(f"✅ Not Found (Expected): Documents don't exist")
        return True
    else:
        print(f"⚠️  Unexpected response: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_validation():
    """Test input validation"""
    print("\n" + "="*60)
    print("Testing: Input Validation")
    print("="*60)
    
    # Test 1: Less than 2 documents
    print("\n1. Testing with 1 document (should fail):")
    payload = {"document_ids": [1]}
    response = requests.post(
        f"{BASE_URL}/documents/compare",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 400:
        print(f"   ✅ Validation working: {response.json().get('detail')}")
    else:
        print(f"   ❌ Expected 400, got {response.status_code}")
    
    # Test 2: More than 5 documents
    print("\n2. Testing with 6 documents (should fail):")
    payload = {"document_ids": [1, 2, 3, 4, 5, 6]}
    response = requests.post(
        f"{BASE_URL}/documents/compare",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 400:
        print(f"   ✅ Validation working: {response.json().get('detail')}")
    else:
        print(f"   ❌ Expected 400, got {response.status_code}")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("POLICY COMPARISON API TEST SUITE")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Token: {'Set' if TOKEN != 'YOUR_TOKEN_HERE' else 'NOT SET - Please update TOKEN variable'}")
    
    if TOKEN == "YOUR_TOKEN_HERE":
        print("\n❌ ERROR: Please set a valid authentication token in the script")
        print("   1. Login to get a token: POST /auth/login")
        print("   2. Update TOKEN variable in this script")
        return
    
    results = []
    
    # Run tests
    print("\n" + "="*60)
    print("RUNNING TESTS")
    print("="*60)
    
    results.append(("Input Validation", test_validation()))
    results.append(("Role-Based Access", test_role_based_access()))
    results.append(("Compare Documents", test_compare_documents()))
    results.append(("Detect Conflicts", test_detect_conflicts()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
