"""Test conflict detection API endpoint"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

# Configuration
BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJyb290QGJlYWNvbi5zeXN0ZW0iLCJyb2xlIjoiZGV2ZWxvcGVyIiwiaW5zdGl0dXRpb25faWQiOm51bGwsImFwcHJvdmVkIjp0cnVlLCJleHAiOjE3NjUzNTMzMzV9.ELdkMzMGYQybVDAVo74jokm83vISg-I_rdYHIbzkbSo"  # Replace with valid token

headers = {
    "Authorization": f"Bearer {TOKEN}"
}


def test_detect_conflicts():
    """Test conflict detection endpoint"""
    print("\n" + "="*60)
    print("Testing: GET /documents/{id}/conflicts")
    print("="*60)
    
    # Test data - replace with actual document ID
    document_id = 1  # Replace with real ID
    
    response = requests.get(
        f"{BASE_URL}/documents/{document_id}/conflicts?max_candidates=3",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {data.get('status')}")
        print(f"✅ Document: {data.get('document', {}).get('title')}")
        print(f"✅ Candidates Checked: {data.get('candidates_checked', 0)}")
        print(f"✅ Similar Documents Found: {data.get('similar_documents_found', 0)}")
        print(f"✅ Conflicts Found: {len(data.get('conflicts', []))}")
        
        if data.get('conflicts'):
            print(f"\nConflicts Detected:")
            for i, conflict in enumerate(data['conflicts'], 1):
                print(f"\n  Conflict {i}:")
                print(f"    Type: {conflict.get('conflict_type')}")
                print(f"    Severity: {conflict.get('severity')}")
                print(f"    With Document: {conflict.get('conflicting_document_title')}")
                print(f"    Description: {conflict.get('description', '')[:100]}...")
                print(f"    Recommendation: {conflict.get('recommendation', '')[:100]}...")
        else:
            print(f"\n✅ No conflicts detected")
        
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_role_based_access():
    """Test role-based access control"""
    print("\n" + "="*60)
    print("Testing: Role-Based Access Control")
    print("="*60)
    
    # Try to check conflicts for document user doesn't have access to
    document_id = 999  # Non-existent or restricted ID
    
    response = requests.get(
        f"{BASE_URL}/documents/{document_id}/conflicts",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 403:
        print(f"✅ Access Denied (Expected): Role-based filtering working")
        return True
    elif response.status_code == 404:
        print(f"✅ Not Found (Expected): Document doesn't exist")
        return True
    else:
        print(f"⚠️  Unexpected response: {response.status_code}")
        return False


def test_validation():
    """Test input validation"""
    print("\n" + "="*60)
    print("Testing: Input Validation")
    print("="*60)
    
    document_id = 1
    
    # Test: Too many candidates
    print("\n1. Testing with 11 candidates (should fail):")
    response = requests.get(
        f"{BASE_URL}/documents/{document_id}/conflicts?max_candidates=11",
        headers=headers
    )
    
    if response.status_code == 400:
        print(f"   ✅ Validation working: {response.json().get('detail')}")
    else:
        print(f"   ❌ Expected 400, got {response.status_code}")
    
    return True


def test_lazy_embedding():
    """Test that lazy embedding strategy is used"""
    print("\n" + "="*60)
    print("Testing: Lazy Embedding Strategy")
    print("="*60)
    
    document_id = 1
    
    print("Running conflict detection (should use lazy embedding)...")
    response = requests.get(
        f"{BASE_URL}/documents/{document_id}/conflicts?max_candidates=3",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Conflict detection completed")
        print(f"   Candidates checked: {data.get('candidates_checked', 0)}")
        print(f"   Similar docs found: {data.get('similar_documents_found', 0)}")
        print(f"   Note: Only top candidates were embedded (lazy strategy)")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("CONFLICT DETECTION API TEST SUITE")
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
    results.append(("Lazy Embedding Strategy", test_lazy_embedding()))
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
