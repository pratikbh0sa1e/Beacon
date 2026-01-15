#!/usr/bin/env python3
"""
Test Enhanced Web Scraping with Authentication
Tests the enhanced web scraping functionality with proper authentication
"""
import requests
import json
import time

API_BASE = "http://localhost:8000"

def get_auth_token():
    """Get authentication token for testing"""
    try:
        # Login with developer account
        login_data = {
            "email": "root@beacon.system",
            "password": "admin123"  # Default developer password
        }
        
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data["access_token"]
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_enhanced_scraping_with_auth():
    """Test enhanced scraping with authentication"""
    print("🧪 Testing Enhanced Web Scraping with Authentication")
    print("=" * 60)
    
    # Get authentication token
    print("\n0. Getting Authentication Token")
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authentication successful")
    
    # Test 1: Available scrapers endpoint
    print("\n1. Testing Available Scrapers Endpoint")
    try:
        response = requests.get(f"{API_BASE}/api/enhanced-web-scraping/available-scrapers", headers=headers)
        if response.status_code == 200:
            scrapers = response.json()
            print(f"✅ Available scrapers: {list(scrapers.keys())}")
            for key, name in scrapers.items():
                print(f"   - {key}: {name}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Enhanced stats endpoint
    print("\n2. Testing Enhanced Stats Endpoint")
    try:
        response = requests.get(f"{API_BASE}/api/enhanced-web-scraping/stats-enhanced", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Enhanced stats retrieved:")
            print(f"   - Total sources: {stats.get('total_sources', 0)}")
            print(f"   - Total families: {stats.get('total_families', 0)}")
            print(f"   - Deduplication rate: {stats.get('deduplication_rate', 0)}%")
            print(f"   - RAG accuracy: {stats.get('rag_accuracy', 0)}%")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Stop scraping endpoint (mock test)
    print("\n3. Testing Stop Scraping Endpoint")
    try:
        response = requests.post(f"{API_BASE}/api/enhanced-web-scraping/stop-scraping", 
                               json={
                                   "source_id": 1,
                                   "job_id": "test_job_123"
                               }, 
                               headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Stop scraping response: {result.get('message', 'Success')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Get existing sources first
    print("\n4. Getting Existing Sources")
    try:
        response = requests.get(f"{API_BASE}/api/web-scraping/sources", headers=headers)
        if response.status_code == 200:
            sources = response.json()
            print(f"✅ Found {len(sources)} existing sources")
            if sources:
                source_id = sources[0]["id"]
                source_name = sources[0]["name"]
                print(f"   - Using source: {source_name} (ID: {source_id})")
                
                # Test 5: Enhanced scraping endpoint with real source
                print("\n5. Testing Enhanced Scraping Endpoint")
                try:
                    response = requests.post(f"{API_BASE}/api/enhanced-web-scraping/scrape-enhanced", 
                                           json={
                                               "source_id": source_id,
                                               "keywords": ["policy", "circular"],
                                               "max_documents": 10,  # Small number for testing
                                               "pagination_enabled": True,
                                               "max_pages": 2,
                                               "incremental": True
                                           }, 
                                           headers=headers)
                    if response.status_code == 200:
                        result = response.json()
                        print(f"✅ Enhanced scraping response: {result.get('message', 'Success')}")
                        print(f"   - Status: {result.get('status', 'unknown')}")
                        if 'documents_new' in result:
                            print(f"   - New documents: {result.get('documents_new', 0)}")
                            print(f"   - Updated documents: {result.get('documents_updated', 0)}")
                            print(f"   - Skipped documents: {result.get('documents_skipped', 0)}")
                    else:
                        print(f"❌ Failed: {response.status_code}")
                        print(f"Response: {response.text}")
                except Exception as e:
                    print(f"❌ Error: {e}")
            else:
                print("⚠️  No sources found for testing enhanced scraping")
        else:
            print(f"❌ Failed to get sources: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Enhanced Web Scraping Test Complete")
    print("\n💡 Next steps:")
    print("   1. Frontend should now work with enhanced endpoints")
    print("   2. Test the UI at: http://localhost:5173/admin/web-scraping")
    print("   3. Try creating a new source with enhanced options")
    print("   4. Test the stop button functionality")

if __name__ == "__main__":
    test_enhanced_scraping_with_auth()