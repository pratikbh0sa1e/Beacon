"""Test insights API endpoints"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
# You'll need to replace this with a valid token from your system
TOKEN = "YOUR_TOKEN_HERE"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}


def test_document_stats():
    """Test document statistics endpoint"""
    print("\n" + "="*60)
    print("Testing: GET /insights/document-stats")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/insights/document-stats", headers=headers)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total Documents: {data['total_documents']}")
        print(f"✅ Recent Uploads (7d): {data['recent_uploads_7d']}")
        print(f"✅ Documents by Category: {data['documents_by_category']}")
        print(f"✅ Documents by Status: {data['documents_by_status']}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_trending_topics():
    """Test trending topics endpoint"""
    print("\n" + "="*60)
    print("Testing: GET /insights/trending-topics")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/insights/trending-topics?limit=10&days=30", 
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total Documents Analyzed: {data['total_documents_analyzed']}")
        print(f"✅ Unique Keywords: {data['unique_keywords']}")
        print(f"✅ Unique Topics: {data['unique_topics']}")
        
        if data['trending_keywords']:
            print(f"\nTop 5 Keywords:")
            for i, kw in enumerate(data['trending_keywords'][:5], 1):
                print(f"  {i}. {kw['keyword']} (frequency: {kw['frequency']})")
        
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_recent_activity():
    """Test recent activity endpoint"""
    print("\n" + "="*60)
    print("Testing: GET /insights/recent-activity")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/insights/recent-activity?limit=20", 
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total Activities: {data['total_activities']}")
        print(f"✅ Activity Summary: {data['activity_summary']}")
        
        if data['recent_activities']:
            print(f"\nRecent Activities (top 5):")
            for i, activity in enumerate(data['recent_activities'][:5], 1):
                print(f"  {i}. {activity['action']} by {activity['user_name']} at {activity['timestamp']}")
        
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_dashboard_summary():
    """Test dashboard summary endpoint"""
    print("\n" + "="*60)
    print("Testing: GET /insights/dashboard-summary")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/insights/dashboard-summary", headers=headers)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total Documents: {data['total_documents']}")
        print(f"✅ Pending Approvals: {data['pending_approvals']}")
        print(f"✅ Total Users: {data['total_users']}")
        print(f"✅ Recent Uploads (7d): {data['recent_uploads_7d']}")
        print(f"✅ Recent Searches (7d): {data['recent_searches_7d']}")
        print(f"✅ User Role: {data['user_role']}")
        
        if data['top_categories']:
            print(f"\nTop Categories:")
            for cat in data['top_categories']:
                print(f"  - {cat['category']}: {cat['count']}")
        
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_search_analytics():
    """Test search analytics endpoint (admin only)"""
    print("\n" + "="*60)
    print("Testing: GET /insights/search-analytics (Admin Only)")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/insights/search-analytics?days=30", 
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total Searches: {data['total_searches']}")
        print(f"✅ Unique Queries: {data['unique_queries']}")
        
        if data['top_queries']:
            print(f"\nTop Queries:")
            for i, query in enumerate(data['top_queries'][:5], 1):
                print(f"  {i}. {query['query']} (frequency: {query['frequency']})")
        
        return True
    elif response.status_code == 403:
        print(f"⚠️  Access Denied (expected for non-admin users)")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_user_activity():
    """Test user activity endpoint (admin only)"""
    print("\n" + "="*60)
    print("Testing: GET /insights/user-activity (Admin Only)")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/insights/user-activity?days=30", 
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total Active Users: {data['total_active_users']}")
        print(f"✅ Activity by Role: {data['activity_by_role']}")
        
        if data['most_active_users']:
            print(f"\nMost Active Users:")
            for i, user in enumerate(data['most_active_users'][:5], 1):
                print(f"  {i}. {user['user_name']} ({user['role']}): {user['activity_count']} actions")
        
        return True
    elif response.status_code == 403:
        print(f"⚠️  Access Denied (expected for non-admin users)")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_institution_stats():
    """Test institution statistics endpoint (admin only)"""
    print("\n" + "="*60)
    print("Testing: GET /insights/institution-stats (Admin Only)")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/insights/institution-stats", headers=headers)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total Institutions: {data['total_institutions']}")
        print(f"✅ Documents by Institution: {data['documents_by_institution']}")
        print(f"✅ Users by Institution: {data['users_by_institution']}")
        
        if data['institution_details']:
            print(f"\nInstitution Details:")
            for inst in data['institution_details'][:5]:
                print(f"  - {inst['name']} ({inst['type']}): {inst['document_count']} docs, {inst['user_count']} users")
        
        return True
    elif response.status_code == 403:
        print(f"⚠️  Access Denied (expected for non-admin users)")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("INSIGHTS API TEST SUITE")
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
    results.append(("Document Stats", test_document_stats()))
    results.append(("Trending Topics", test_trending_topics()))
    results.append(("Recent Activity", test_recent_activity()))
    results.append(("Dashboard Summary", test_dashboard_summary()))
    results.append(("Search Analytics", test_search_analytics()))
    results.append(("User Activity", test_user_activity()))
    results.append(("Institution Stats", test_institution_stats()))
    
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
