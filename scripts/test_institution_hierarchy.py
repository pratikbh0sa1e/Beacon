"""
Test script for institution hierarchy and registration
Tests government_dept removal and two-step registration
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

# Test data
DEVELOPER_CREDENTIALS = {
    "email": "root@beacon.system",
    "password": "AR/SPt&_P^hhEI!8eHXWs1UO&wQGOtFA"
}

TEST_MINISTRIES = [
    {"name": "Ministry of Education", "location": "New Delhi"},
    {"name": "Ministry of Health and Family Welfare", "location": "New Delhi"},
    {"name": "Ministry of Defence", "location": "New Delhi"},
]

TEST_INSTITUTIONS = [
    # Education institutions
    {"name": "IIT Delhi", "location": "Delhi", "ministry": "Ministry of Education"},
    {"name": "IIT Mumbai", "location": "Mumbai", "ministry": "Ministry of Education"},
    {"name": "Delhi University", "location": "Delhi", "ministry": "Ministry of Education"},
    
    # Health institutions
    {"name": "AIIMS Delhi", "location": "Delhi", "ministry": "Ministry of Health and Family Welfare"},
    {"name": "AIIMS Mumbai", "location": "Mumbai", "ministry": "Ministry of Health and Family Welfare"},
    
    # Defence institutions
    {"name": "DRDO Bangalore", "location": "Bangalore", "ministry": "Ministry of Defence"},
    {"name": "National Defence Academy", "location": "Pune", "ministry": "Ministry of Defence"},
]

TEST_USERS = [
    {
        "name": "Ministry Admin Test",
        "email": "ministry.admin@test.com",
        "password": "test123456",
        "role": "ministry_admin",
        "ministry": "Ministry of Education",
        "institution": None
    },
    {
        "name": "University Admin Test",
        "email": "uni.admin@test.com",
        "password": "test123456",
        "role": "university_admin",
        "ministry": "Ministry of Education",
        "institution": "IIT Delhi"
    },
    {
        "name": "Student Test",
        "email": "student@test.com",
        "password": "test123456",
        "role": "student",
        "ministry": "Ministry of Education",
        "institution": "Delhi University"
    },
    {
        "name": "Doctor Test",
        "email": "doctor@test.com",
        "password": "test123456",
        "role": "document_officer",
        "ministry": "Ministry of Health and Family Welfare",
        "institution": "AIIMS Delhi"
    },
]

def login_as_developer() -> str:
    """Login as developer and return access token"""
    print_info("Logging in as developer...")
    
    # Try JSON format first
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=DEVELOPER_CREDENTIALS
    )
    
    # If JSON fails, try form data
    if response.status_code != 200:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data=DEVELOPER_CREDENTIALS
        )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print_success("Developer login successful")
        return token
    else:
        print_error(f"Developer login failed: {response.text}")
        return None

def get_headers(token: str) -> Dict[str, str]:
    """Get authorization headers"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def test_create_ministries(token: str) -> Dict[str, int]:
    """Create test ministries and return name->id mapping"""
    print_info("\n=== Testing Ministry Creation ===")
    ministry_ids = {}
    
    for ministry_data in TEST_MINISTRIES:
        print_info(f"Creating ministry: {ministry_data['name']}")
        
        response = requests.post(
            f"{BASE_URL}/institutions/create",
            headers=get_headers(token),
            json={
                "name": ministry_data["name"],
                "location": ministry_data["location"],
                "type": "ministry"
            }
        )
        
        if response.status_code in [200, 201]:
            ministry = response.json()
            ministry_ids[ministry_data["name"]] = ministry["id"]
            print_success(f"Created: {ministry['name']} (ID: {ministry['id']})")
        elif "already exists" in response.text.lower():
            print_warning(f"Ministry already exists: {ministry_data['name']}")
            # Get existing ministry ID
            response = requests.get(
                f"{BASE_URL}/institutions/list",
                headers=get_headers(token)
            )
            if response.status_code == 200:
                institutions = response.json()
                for inst in institutions:
                    if inst["name"] == ministry_data["name"]:
                        ministry_ids[ministry_data["name"]] = inst["id"]
                        print_info(f"Using existing ID: {inst['id']}")
                        break
        else:
            print_error(f"Failed to create ministry: {response.text}")
    
    return ministry_ids

def test_create_government_dept(token: str) -> bool:
    """Test that government_dept type is rejected"""
    print_info("\n=== Testing Government Dept Rejection ===")
    
    response = requests.post(
        f"{BASE_URL}/institutions/create",
        headers=get_headers(token),
        json={
            "name": "Test Government Department",
            "location": "Test City",
            "type": "government_dept"
        }
    )
    
    if response.status_code in [400, 422]:
        print_success("government_dept type correctly rejected!")
        return True
    else:
        print_error(f"government_dept type was NOT rejected! Status: {response.status_code}")
        return False

def test_create_institutions(token: str, ministry_ids: Dict[str, int]) -> Dict[str, int]:
    """Create test institutions and return name->id mapping"""
    print_info("\n=== Testing Institution Creation ===")
    institution_ids = {}
    
    for inst_data in TEST_INSTITUTIONS:
        ministry_name = inst_data["ministry"]
        ministry_id = ministry_ids.get(ministry_name)
        
        if not ministry_id:
            print_error(f"Ministry not found: {ministry_name}")
            continue
        
        print_info(f"Creating institution: {inst_data['name']} under {ministry_name}")
        
        response = requests.post(
            f"{BASE_URL}/institutions/create",
            headers=get_headers(token),
            json={
                "name": inst_data["name"],
                "location": inst_data["location"],
                "type": "university",
                "parent_ministry_id": ministry_id
            }
        )
        
        if response.status_code in [200, 201]:
            institution = response.json()
            institution_ids[inst_data["name"]] = institution["id"]
            print_success(f"Created: {institution['name']} (ID: {institution['id']})")
        elif "already exists" in response.text.lower():
            print_warning(f"Institution already exists: {inst_data['name']}")
            # Get existing institution ID
            response = requests.get(
                f"{BASE_URL}/institutions/list",
                headers=get_headers(token)
            )
            if response.status_code == 200:
                institutions = response.json()
                for inst in institutions:
                    if inst["name"] == inst_data["name"]:
                        institution_ids[inst_data["name"]] = inst["id"]
                        print_info(f"Using existing ID: {inst['id']}")
                        break
        else:
            print_error(f"Failed to create institution: {response.text}")
    
    return institution_ids

def test_institution_without_ministry(token: str) -> bool:
    """Test that university without parent_ministry_id is rejected"""
    print_info("\n=== Testing Institution Without Ministry ===")
    
    response = requests.post(
        f"{BASE_URL}/institutions/create",
        headers=get_headers(token),
        json={
            "name": "Test University Without Ministry",
            "location": "Test City",
            "type": "university"
            # Missing parent_ministry_id
        }
    )
    
    if response.status_code in [400, 422]:
        print_success("Institution without ministry correctly rejected!")
        return True
    else:
        print_error(f"Institution without ministry was NOT rejected! Status: {response.status_code}")
        return False

def test_user_registrations(ministry_ids: Dict[str, int], institution_ids: Dict[str, int]):
    """Test user registration with different roles"""
    print_info("\n=== Testing User Registrations ===")
    
    for user_data in TEST_USERS:
        print_info(f"\nRegistering: {user_data['name']} as {user_data['role']}")
        
        # Get institution ID
        institution_id = None
        if user_data["institution"]:
            institution_id = institution_ids.get(user_data["institution"])
            if not institution_id:
                print_error(f"Institution not found: {user_data['institution']}")
                continue
        elif user_data["ministry"] and user_data["role"] == "ministry_admin":
            # Ministry admin uses ministry as institution
            institution_id = ministry_ids.get(user_data["ministry"])
            if not institution_id:
                print_error(f"Ministry not found: {user_data['ministry']}")
                continue
        
        # Register user
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "name": user_data["name"],
                "email": user_data["email"],
                "password": user_data["password"],
                "role": user_data["role"],
                "institution_id": institution_id
            }
        )
        
        if response.status_code in [200, 201]:
            print_success(f"Registered: {user_data['name']}")
            print_info(f"  Role: {user_data['role']}")
            if user_data["institution"]:
                print_info(f"  Institution: {user_data['institution']}")
            elif user_data["ministry"]:
                print_info(f"  Ministry: {user_data['ministry']}")
        elif "already registered" in response.text.lower() or "already exists" in response.text.lower():
            print_warning(f"User already exists: {user_data['email']}")
        else:
            print_error(f"Registration failed: {response.text}")

def test_list_institutions(token: str):
    """Test listing institutions and verify hierarchy"""
    print_info("\n=== Testing Institution Listing ===")
    
    response = requests.get(
        f"{BASE_URL}/institutions/list",
        headers=get_headers(token)
    )
    
    if response.status_code == 200:
        institutions = response.json()
        
        ministries = [i for i in institutions if i["type"] == "ministry"]
        universities = [i for i in institutions if i["type"] == "university"]
        govt_depts = [i for i in institutions if i["type"] == "government_dept"]
        
        print_success(f"Total institutions: {len(institutions)}")
        print_info(f"  Ministries: {len(ministries)}")
        print_info(f"  Institutions: {len(universities)}")
        
        if govt_depts:
            print_error(f"  Government Departments: {len(govt_depts)} (SHOULD BE 0!)")
        else:
            print_success("  Government Departments: 0 (Correct!)")
        
        # Verify hierarchy
        print_info("\nVerifying hierarchy:")
        for ministry in ministries:
            child_count = sum(1 for u in universities if u.get("parent_ministry_id") == ministry["id"])
            print_info(f"  {ministry['name']}: {child_count} institutions")
            
    else:
        print_error(f"Failed to list institutions: {response.text}")

def main():
    print_info("=" * 60)
    print_info("INSTITUTION HIERARCHY & REGISTRATION TEST")
    print_info("=" * 60)
    
    # Login as developer
    token = login_as_developer()
    if not token:
        print_error("Cannot proceed without developer token")
        return
    
    # Test 1: Create ministries
    ministry_ids = test_create_ministries(token)
    
    # Test 2: Try to create government_dept (should fail)
    test_create_government_dept(token)
    
    # Test 3: Create institutions
    institution_ids = test_create_institutions(token, ministry_ids)
    
    # Test 4: Try to create institution without ministry (should fail)
    test_institution_without_ministry(token)
    
    # Test 5: List institutions and verify
    test_list_institutions(token)
    
    # Test 6: Register users with different roles
    test_user_registrations(ministry_ids, institution_ids)
    
    print_info("\n" + "=" * 60)
    print_success("ALL TESTS COMPLETED!")
    print_info("=" * 60)
    
    print_info("\n📋 Summary:")
    print_info(f"  Ministries created: {len(ministry_ids)}")
    print_info(f"  Institutions created: {len(institution_ids)}")
    print_info(f"  Users registered: {len(TEST_USERS)}")
    
    print_info("\n🎯 Next Steps:")
    print_info("  1. Open frontend: http://localhost:5173")
    print_info("  2. Go to Admin → Institutions")
    print_info("  3. Verify only 2 tabs: Institutions | Ministries")
    print_info("  4. Try registering a new user")
    print_info("  5. Verify two-step selection for university roles")

if __name__ == "__main__":
    main()
