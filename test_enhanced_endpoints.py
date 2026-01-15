#!/usr/bin/env python3
"""
Test script to verify enhanced web scraping endpoints are working
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test enhanced web scraping endpoints"""
    
    # First, try to login as developer
    login_data = {
        "email": "root@beacon.system",
        "password": "|zqYAO%w[gAiX@orV!@gkz&mUAq_odMT"  # Developer password
    }
    
    print("🔐 Testing login...")
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            user = token_data["user"]
            print(f"✅ Login successful! User: {user['name']} ({user['role']})")
            
            # Set headers for authenticated requests
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test enhanced endpoints
            endpoints_to_test = [
                "/api/enhanced-web-scraping/stats-enhanced",
                "/api/enhanced-web-scraping/document-families?limit=10",
                "/api/enhanced-web-scraping/available-scrapers"
            ]
            
            for endpoint in endpoints_to_test:
                print(f"\n🧪 Testing {endpoint}...")
                try:
                    response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
                    print(f"Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ Success! Response keys: {list(data.keys()) if isinstance(data, dict) else f'Array with {len(data)} items'}")
                    else:
                        print(f"❌ Error: {response.text}")
                        
                except Exception as e:
                    print(f"❌ Request failed: {str(e)}")
            
        else:
            print(f"❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Login request failed: {str(e)}")

if __name__ == "__main__":
    test_endpoints()