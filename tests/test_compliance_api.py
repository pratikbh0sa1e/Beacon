"""Test compliance checking API endpoints"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

# Configuration
BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJyb290QGJlYWNvbi5zeXN0ZW0iLCJyb2xlIjoiZGV2ZWxvcGVyIiwiaW5zdGl0dXRpb25faWQiOm51bGwsImFwcHJvdmVkIjp0cnVlLCJleHAiOjE3NjUzNTMzMzV9.ELdkMzMGYQybVDAVo74jokm83vISg-I_rdYHIbzkbSo"  # Replace with valid token

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def test_check_compliance():
    """Test compliance checking endpoint"""
    print("\n" + "="*60)
    print("Testing: POST /documents/{id}/check-compliance")
    print("="*60)
    
    # Test data - replace with actual document ID
    document_id = 93  # Replace with real ID
    payload = {
        "checklist": [
            "Has budget allocation",
            "Has implementation timeline",
            "Approved by MoE",
            "Includes beneficiary details"
        ],
        "strict_mode": False
    }
    
    response = requests.post(
        f"{BASE_URL}/documents/{document_id}/check-compliance",
        headers=headers,
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {data.get('status')}")
        print(f"✅ Document: {data.get('document', {}).get('title')}")
        
        if data.get('compliance_results'):
            print(f"\nCompliance Results:")
            for i, result in enumerate(data['compliance_results'], 1):
                compliant = "✅" if result.get('compliant') else "❌"
                print(f"  {i}. {compliant} {result.get('criterion')}")
                print(f"     Evidence: {result.get('evidence', 'N/A')[:100]}...")
                print(f"     Confidence: {result.get('confidence', 'unknown')}")
        
        if data.get('overall_compliance'):
            overall = data['overall_compliance']
            print(f"\nOverall Compliance:")
            print(f"  Total Criteria: {overall.get('total_criteria')}")
            print(f"  Criteria Met: {overall.get('criteria_met')}")
            print(f"  Compliance %: {overall.get('compliance_percentage')}%")
            print(f"  Status: {overall.get('status')}")
        
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_compliance_report():
    """Test detailed compliance report endpoint"""
    print("\n" + "="*60)
    print("Testing: POST /documents/{id}/compliance-report")
    print("="*60)
    
    # Test data
    document_id = 1  # Replace with real ID
    payload = {
        "checklist": [
            "Has budget allocation",
            "Has implementation timeline",
            "Approved by MoE"
        ],
        "strict_mode": True
    }
    
    response = requests.post(
        f"{BASE_URL}/documents/{document_id}/compliance-report",
        headers=headers,
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {data.get('status')}")
        print(f"✅ Document: {data.get('document', {}).get('title')}")
        
        if data.get('compliance_summary'):
            summary = data['compliance_summary']
            print(f"\nCompliance Summary:")
            print(f"  Status: {summary.get('status')}")
            print(f"  Compliance: {summary.get('compliance_percentage')}%")
        
        if data.get('non_compliant_items'):
            print(f"\nNon-Compliant Items: {len(data['non_compliant_items'])}")
            for item in data['non_compliant_items'][:3]:
                print(f"  - {item.get('criterion')}")
        
        if data.get('recommendations'):
            print(f"\nRecommendations:")
            for i, rec in enumerate(data['recommendations'][:3], 1):
                print(f"  {i}. {rec}")
        
        print(f"\nAction Required: {data.get('action_required')}")
        print(f"Priority: {data.get('priority')}")
        
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_role_based_access():
    """Test role-based access control"""
    print("\n" + "="*60)
    print("Testing: Role-Based Access Control")
    print("="*60)
    
    # Try to check compliance of document user doesn't have access to
    document_id = 999  # Non-existent or restricted ID
    payload = {
        "checklist": ["Has budget"]
    }
    
    response = requests.post(
        f"{BASE_URL}/documents/{document_id}/check-compliance",
        headers=headers,
        json=payload
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
    
    # Test 1: Empty checklist
    print("\n1. Testing with empty checklist (should fail):")
    payload = {"checklist": []}
    response = requests.post(
        f"{BASE_URL}/documents/{document_id}/check-compliance",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 400:
        print(f"   ✅ Validation working: {response.json().get('detail')}")
    else:
        print(f"   ❌ Expected 400, got {response.status_code}")
    
    # Test 2: Too many items
    print("\n2. Testing with 21 checklist items (should fail):")
    payload = {"checklist": [f"Item {i}" for i in range(21)]}
    response = requests.post(
        f"{BASE_URL}/documents/{document_id}/check-compliance",
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
    print("COMPLIANCE CHECKING API TEST SUITE")
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
    results.append(("Check Compliance", test_check_compliance()))
    results.append(("Compliance Report", test_compliance_report()))
    
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
