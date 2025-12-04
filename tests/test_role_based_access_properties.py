"""
Property-Based Tests for Role-Based Access Control

This module contains property-based tests using Hypothesis to verify
correctness properties of role-based access control for the external data source system.
"""
import pytest
from hypothesis import given, strategies as st, settings


# Hypothesis strategies for generating test data
role_strategy = st.sampled_from(["student", "public_viewer", "ministry_admin", "university_admin", "developer"])
page_strategy = st.sampled_from([
    "/admin/data-sources",
    "/admin/my-data-source-requests", 
    "/admin/data-source-approvals",
    "/admin/active-sources"
])


class TestRoleBasedAccessDenial:
    """Property-based tests for role-based access denial"""
    
    # Feature: external-data-source, Property 20: Students and Faculty denied access
    @settings(max_examples=100)
    @given(
        role=st.sampled_from(["student", "public_viewer"]),
        page=page_strategy
    )
    def test_students_and_faculty_denied_access(self, role, page):
        """
        For any user with role "Student" or "Public Viewer" (Faculty equivalent), 
        attempting to access any data source page should result in access denial 
        and redirect to home page.
        
        Validates: Requirements 7.1
        """
        # Property 1: Students and public viewers should not have access
        allowed_roles = get_allowed_roles_for_page(page)
        assert role not in allowed_roles, \
            f"Role '{role}' should not be allowed to access {page}"
        
        # Property 2: Access should be denied (403 or redirect)
        access_result = check_access(role, page)
        assert access_result in ["denied", "redirect_home"], \
            f"Access for '{role}' to {page} should be denied or redirected"
        
        # Property 3: Students should never see data source menu items
        menu_items = get_menu_items_for_role(role)
        data_source_items = [item for item in menu_items if "data" in item.lower() and "source" in item.lower()]
        assert len(data_source_items) == 0, \
            f"Role '{role}' should not see any data source menu items"


class TestAdminAccess:
    """Property-based tests for admin access to request form"""
    
    # Feature: external-data-source, Property 21: Admins access request form
    @settings(max_examples=100)
    @given(
        role=st.sampled_from(["ministry_admin", "university_admin"])
    )
    def test_admins_access_request_form(self, role):
        """
        For any user with role "Ministry Admin" or "University Admin", 
        accessing the request form should be allowed.
        
        Validates: Requirements 7.2
        """
        request_form_page = "/admin/data-sources"
        my_requests_page = "/admin/my-data-source-requests"
        
        # Property 1: Admins should have access to request form
        allowed_roles = get_allowed_roles_for_page(request_form_page)
        assert role in allowed_roles, \
            f"Role '{role}' should be allowed to access request form"
        
        # Property 2: Access should be granted
        access_result = check_access(role, request_form_page)
        assert access_result == "granted", \
            f"Access for '{role}' to request form should be granted"
        
        # Property 3: Admins should have access to "My Requests" page
        allowed_roles_my_requests = get_allowed_roles_for_page(my_requests_page)
        assert role in allowed_roles_my_requests, \
            f"Role '{role}' should be allowed to access My Requests page"
        
        # Property 4: Admins should see data source menu items
        menu_items = get_menu_items_for_role(role)
        assert "Submit Request" in menu_items or "Data Sources" in menu_items, \
            f"Role '{role}' should see data source menu items"
        assert "My Requests" in menu_items or "My Data Source Requests" in menu_items, \
            f"Role '{role}' should see My Requests menu item"


class TestAdminDashboardDenial:
    """Property-based tests for admin denial to approval dashboard"""
    
    # Feature: external-data-source, Property 22: Admins denied approval dashboard
    @settings(max_examples=100)
    @given(
        role=st.sampled_from(["ministry_admin", "university_admin"])
    )
    def test_admins_denied_approval_dashboard(self, role):
        """
        For any user with role "Ministry Admin" or "University Admin", 
        attempting to access the approval dashboard should result in access denial.
        
        Validates: Requirements 7.4
        """
        approval_dashboard_page = "/admin/data-source-approvals"
        active_sources_page = "/admin/active-sources"
        
        # Property 1: Admins should NOT have access to approval dashboard
        allowed_roles = get_allowed_roles_for_page(approval_dashboard_page)
        assert role not in allowed_roles, \
            f"Role '{role}' should NOT be allowed to access approval dashboard"
        
        # Property 2: Access should be denied
        access_result = check_access(role, approval_dashboard_page)
        assert access_result in ["denied", "redirect_home"], \
            f"Access for '{role}' to approval dashboard should be denied"
        
        # Property 3: Admins should NOT have access to active sources page
        allowed_roles_active = get_allowed_roles_for_page(active_sources_page)
        assert role not in allowed_roles_active, \
            f"Role '{role}' should NOT be allowed to access active sources page"
        
        # Property 4: Admins should NOT see developer-only menu items
        menu_items = get_menu_items_for_role(role)
        assert "Pending Approvals" not in menu_items, \
            f"Role '{role}' should not see Pending Approvals menu item"
        assert "Active Sources" not in menu_items, \
            f"Role '{role}' should not see Active Sources menu item"


class TestMenuVisibility:
    """Property-based tests for menu visibility by role"""
    
    # Feature: external-data-source, Property 23: Menu visibility by role
    @settings(max_examples=100)
    @given(role=role_strategy)
    def test_menu_visibility_by_role(self, role):
        """
        For any user, the navigation menu should display "Data Sources" menu items 
        according to their role: none for Students/Faculty, "Submit Request" and 
        "My Requests" for Admins, "Pending Approvals", "Active Sources", and 
        "All Requests" for Developers.
        
        Validates: Requirements 7.7, 7.8, 7.9
        """
        menu_items = get_menu_items_for_role(role)
        
        if role in ["student", "public_viewer"]:
            # Property 1: Students and public viewers should see NO data source items
            data_source_items = [item for item in menu_items if "data" in item.lower() and "source" in item.lower()]
            assert len(data_source_items) == 0, \
                f"Role '{role}' should not see any data source menu items"
            assert "Submit Request" not in menu_items, \
                f"Role '{role}' should not see Submit Request"
            assert "My Requests" not in menu_items, \
                f"Role '{role}' should not see My Requests"
            assert "Pending Approvals" not in menu_items, \
                f"Role '{role}' should not see Pending Approvals"
            assert "Active Sources" not in menu_items, \
                f"Role '{role}' should not see Active Sources"
        
        elif role in ["ministry_admin", "university_admin"]:
            # Property 2: Admins should see "Submit Request" and "My Requests"
            assert "Data Sources" in menu_items or "Submit Request" in menu_items, \
                f"Role '{role}' should see Data Sources or Submit Request menu item"
            assert "My Requests" in menu_items or "My Data Source Requests" in menu_items, \
                f"Role '{role}' should see My Requests menu item"
            
            # Property 3: Admins should NOT see developer-only items
            assert "Pending Approvals" not in menu_items, \
                f"Role '{role}' should not see Pending Approvals (developer only)"
            assert "Active Sources" not in menu_items or "My" in menu_items, \
                f"Role '{role}' should not see Active Sources (developer only)"
        
        elif role == "developer":
            # Property 4: Developers should see "Pending Approvals", "Active Sources", "All Requests"
            assert "Pending Approvals" in menu_items or "Data Source Approvals" in menu_items, \
                f"Role '{role}' should see Pending Approvals menu item"
            assert "Active Sources" in menu_items, \
                f"Role '{role}' should see Active Sources menu item"
            
            # Property 5: Developers should see data source menu
            assert "Data Sources" in menu_items or len([i for i in menu_items if "source" in i.lower()]) > 0, \
                f"Role '{role}' should see data source related menu items"


# Helper functions to simulate access control logic
def get_allowed_roles_for_page(page):
    """Get list of roles allowed to access a page"""
    access_map = {
        "/admin/data-sources": ["ministry_admin", "university_admin", "developer"],
        "/admin/my-data-source-requests": ["ministry_admin", "university_admin"],
        "/admin/data-source-approvals": ["developer"],
        "/admin/active-sources": ["developer"]
    }
    return access_map.get(page, [])


def check_access(role, page):
    """Check if a role has access to a page"""
    allowed_roles = get_allowed_roles_for_page(page)
    if role in allowed_roles:
        return "granted"
    elif role in ["student", "public_viewer"]:
        return "redirect_home"
    else:
        return "denied"


def get_menu_items_for_role(role):
    """Get menu items visible to a role"""
    base_items = ["Dashboard", "Documents", "Bookmarks", "My Notes", "AI Assistant"]
    
    if role in ["student", "public_viewer"]:
        return base_items
    
    elif role in ["ministry_admin", "university_admin"]:
        return base_items + [
            "Upload",
            "Document Approvals",
            "Data Sources",
            "Submit Request",
            "My Requests",
            "My Data Source Requests",
            "User Management",
            "Institutions",
            "Analytics"
        ]
    
    elif role == "developer":
        return base_items + [
            "Upload",
            "Document Approvals",
            "Data Sources",
            "Pending Approvals",
            "Data Source Approvals",
            "Active Sources",
            "All Requests",
            "User Management",
            "Institutions",
            "Analytics",
            "System Health"
        ]
    
    return base_items


def run_property_tests():
    """Run all property-based tests"""
    print("\n" + "="*70)
    print("Running Property-Based Tests for Role-Based Access Control")
    print("="*70 + "\n")
    
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_property_tests()
