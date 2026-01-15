#!/usr/bin/env python3
"""
Test Enhanced Frontend Integration
Tests the enhanced web scraping frontend integration with backend
"""
import requests
import json
import time

API_BASE = "http://localhost:8000/api/enhanced-web-scraping"

def test_enhanced_scraping_endpoints():
    """Test enhanced scraping API endpoints"""
    print("🧪 Testing Enhanced Web Scraping Frontend Integration")
    print("=" * 60)
    
    # Test 1: Available scrapers endpoint
    print("\n1. Testing Available Scrapers Endpoint")
    try:
        response = requests.get(f"{API_BASE}/available-scrapers")
        if response.status_code == 200:
            scrapers = response.json()
            print(f"✅ Available scrapers: {list(scrapers.keys())}")
            for key, name in scrapers.items():
                print(f"   - {key}: {name}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Enhanced stats endpoint
    print("\n2. Testing Enhanced Stats Endpoint")
    try:
        response = requests.get(f"{API_BASE}/stats-enhanced")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Enhanced stats retrieved:")
            print(f"   - Total sources: {stats.get('total_sources', 0)}")
            print(f"   - Total families: {stats.get('total_families', 0)}")
            print(f"   - Deduplication rate: {stats.get('deduplication_rate', 0)}%")
            print(f"   - RAG accuracy: {stats.get('rag_accuracy', 0)}%")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Stop scraping endpoint (mock test)
    print("\n3. Testing Stop Scraping Endpoint")
    try:
        response = requests.post(f"{API_BASE}/stop-scraping", json={
            "source_id": 1,
            "job_id": "test_job_123"
        })
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Stop scraping response: {result.get('message', 'Success')}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Enhanced scraping endpoint (mock test)
    print("\n4. Testing Enhanced Scraping Endpoint")
    try:
        response = requests.post(f"{API_BASE}/scrape-enhanced", json={
            "source_id": 1,
            "keywords": ["policy", "circular"],
            "max_documents": 100,
            "pagination_enabled": True,
            "max_pages": 5,
            "incremental": True
        })
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Enhanced scraping response: {result.get('message', 'Success')}")
        elif response.status_code == 404:
            print("⚠️  Source not found (expected for test)")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Enhanced Frontend Integration Test Complete")
    print("\n💡 Next steps:")
    print("   1. Start backend: uvicorn backend.main:app --reload")
    print("   2. Start frontend: cd frontend && npm run dev")
    print("   3. Test enhanced features: http://localhost:5173/admin/web-scraping")
    print("   4. Try enhanced scraping with site-specific scrapers")
    print("   5. Test stop button functionality")

if __name__ == "__main__":
    test_enhanced_scraping_endpoints()