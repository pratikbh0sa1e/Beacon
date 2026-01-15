#!/usr/bin/env python3
"""
Test script to simulate frontend authentication and API calls
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_frontend_auth_flow():
    """Test the complete authentication flow like the frontend does"""
    
    # Login as developer
    login_data = {
        "email": "root@beacon.system",
        "password": "|zqYAO%w[gAiX@orV!@gkz&mUAq_odMT"
    }
    
    print("🔐 Testing login...")
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        token_data = response.json()
        token = token_data["access_token"]
        user = token_data["user"]
        print(f"✅ Login successful! User: {user['name']} ({user['role']})")
        
        # Simulate how frontend stores and uses the token
        auth_data = {
            "state": {
                "token": token,
                "user": user
            }
        }
        
        # Headers like frontend API service
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test the exact endpoints the frontend calls
        print("\n🧪 Testing frontend API calls...")
        
        endpoints = [
            ("/api/web-scraping/sources", "Web scraping sources"),
            ("/api/enhanced-web-scraping/stats-enhanced", "Enhanced stats"),
            ("/api/web-scraping/logs?limit=10", "Scraping logs"),
            ("/api/web-scraping/scraped-documents?limit=1000", "Scraped documents"),
            ("/api/enhanced-web-scraping/document-families?limit=100", "Document families")
        ]
        
        for endpoint, description in endpoints:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
                if response.status_code == 200:
                    print(f"✅ {description}: OK")
                else:
                    print(f"❌ {description}: {response.status_code} - {response.text[:100]}")
            except Exception as e:
                print(f"❌ {description}: Request failed - {str(e)}")
        
        # Test enhanced scraping endpoint
        print(f"\n🧪 Testing enhanced scraping endpoint...")
        try:
            scrape_data = {
                "source_id": 1,
                "keywords": ["test"],
                "max_documents": 10,
                "pagination_enabled": True,
                "max_pages": 5,
                "incremental": True
            }
            response = requests.post(
                f"{BASE_URL}/api/enhanced-web-scraping/scrape-enhanced", 
                json=scrape_data, 
                headers=headers
            )
            if response.status_code in [200, 404]:  # 404 is OK if source doesn't exist
                print(f"✅ Enhanced scraping endpoint: Accessible ({response.status_code})")
            else:
                print(f"❌ Enhanced scraping endpoint: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            print(f"❌ Enhanced scraping endpoint: Request failed - {str(e)}")
            
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_frontend_auth_flow()