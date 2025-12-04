"""
Email validation utilities including domain validation and disposable email detection
"""
import re
import dns.resolver
from typing import Tuple, Optional
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Disposable email domains to block
DISPOSABLE_EMAIL_DOMAINS = {
    "tempmail.com", "10minutemail.com", "guerrillamail.com", "mailinator.com",
    "throwaway.email", "temp-mail.org", "fakeinbox.com", "trashmail.com",
    "yopmail.com", "getnada.com", "maildrop.cc", "sharklasers.com",
    "guerrillamailblock.com", "spam4.me", "grr.la", "discard.email"
}

# Institution domain mappings (add your actual domains here)
INSTITUTION_DOMAINS = {
    "ministry_admin": [
        "moe.gov.in",  # Ministry of Education
        "education.gov.in",
        "shiksha.gov.in"
    ],
    "university_admin": [
        # Add university domains here as you collect them
        # Example: "university.edu", "college.ac.in"
    ]
}

# Enable/disable domain validation (configurable via .env)
ENABLE_DOMAIN_VALIDATION = os.getenv("ENABLE_DOMAIN_VALIDATION", "false").lower() == "true"


def is_valid_email_format(email: str) -> bool:
    """
    Check if email has valid format using regex
    
    Args:
        email: Email address to validate
    
    Returns:
        bool: True if format is valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_disposable_email(email: str) -> bool:
    """
    Check if email is from a disposable email provider
    
    Args:
        email: Email address to check
    
    Returns:
        bool: True if disposable
    """
    domain = email.split('@')[-1].lower()
    return domain in DISPOSABLE_EMAIL_DOMAINS


def check_mx_records(domain: str) -> bool:
    """
    Check if domain has valid MX (mail exchange) records
    
    Args:
        domain: Domain to check
    
    Returns:
        bool: True if MX records exist
    """
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        return len(mx_records) > 0
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return False
    except Exception as e:
        logger.warning(f"MX record check failed for {domain}: {str(e)}")
        return True  # Don't block on DNS errors


def validate_institution_domain(email: str, role: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that email domain matches required institution domain for role
    
    Args:
        email: Email address to validate
        role: User role (MINISTRY_ADMIN, university_admin, etc.)
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    # Skip validation if disabled
    if not ENABLE_DOMAIN_VALIDATION:
        return True, None
    
    # Only validate for admin roles
    if role not in ["ministry_admin", "university_admin"]:
        return True, None
    
    domain = email.split('@')[-1].lower()
    allowed_domains = INSTITUTION_DOMAINS.get(role, [])
    
    if not allowed_domains:
        # No domain restrictions configured for this role
        return True, None
    
    if domain not in allowed_domains:
        role_name = "Ministry of Education" if role == "ministry_admin" else "University"
        return False, f"{role_name} accounts must use an official institutional email address"
    
    return True, None


def validate_email(email: str, role: str = None) -> Tuple[bool, Optional[str]]:
    """
    Comprehensive email validation
    
    Args:
        email: Email address to validate
        role: User role (optional, for domain validation)
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    # Check format
    if not is_valid_email_format(email):
        return False, "Invalid email format"
    
    # Check disposable email
    if is_disposable_email(email):
        return False, "Disposable email addresses are not allowed"
    
    # Check MX records
    domain = email.split('@')[-1]
    if not check_mx_records(domain):
        return False, f"Email domain '{domain}' does not have valid mail servers"
    
    # Check institution domain if role provided
    if role:
        is_valid, error = validate_institution_domain(email, role)
        if not is_valid:
            return False, error
    
    return True, None


def add_institution_domain(role: str, domain: str):
    """
    Add a domain to the institution domain whitelist
    
    Args:
        role: User role (MINISTRY_ADMIN, university_admin)
        domain: Domain to add (e.g., "university.edu")
    """
    if role in INSTITUTION_DOMAINS:
        if domain not in INSTITUTION_DOMAINS[role]:
            INSTITUTION_DOMAINS[role].append(domain.lower())
            logger.info(f"Added domain {domain} for role {role}")
