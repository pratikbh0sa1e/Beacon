"""
Password validation utility with strong security requirements
"""
import re
from typing import Tuple


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password meets security requirements
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)
    - At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    # Check minimum length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Check maximum length (prevent DoS)
    if len(password) > 128:
        return False, "Password must not exceed 128 characters"
    
    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter (A-Z)"
    
    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter (a-z)"
    
    # Check for digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit (0-9)"
    
    # Check for special character
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        return False, "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"
    
    # Check for common weak passwords
    common_passwords = [
        'password', 'password123', '12345678', 'qwerty123', 
        'admin123', 'welcome123', 'letmein123', 'monkey123'
    ]
    if password.lower() in common_passwords:
        return False, "Password is too common. Please choose a stronger password"
    
    return True, "Password is strong"


def get_password_requirements() -> dict:
    """
    Get password requirements for display to users
    
    Returns:
        Dict with password requirements
    """
    return {
        "min_length": 8,
        "max_length": 128,
        "requires_uppercase": True,
        "requires_lowercase": True,
        "requires_digit": True,
        "requires_special_char": True,
        "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
        "description": "Password must be 8-128 characters with at least one uppercase letter, one lowercase letter, one digit, and one special character"
    }


def generate_password_hint(password: str) -> str:
    """
    Generate helpful hint about what's missing from password
    
    Args:
        password: Password to check
        
    Returns:
        Helpful hint message
    """
    hints = []
    
    if len(password) < 8:
        hints.append(f"Add {8 - len(password)} more characters")
    
    if not re.search(r'[A-Z]', password):
        hints.append("Add an uppercase letter (A-Z)")
    
    if not re.search(r'[a-z]', password):
        hints.append("Add a lowercase letter (a-z)")
    
    if not re.search(r'\d', password):
        hints.append("Add a digit (0-9)")
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        hints.append("Add a special character (!@#$%^&*)")
    
    if not hints:
        return "Password meets all requirements"
    
    return "Missing: " + ", ".join(hints)
