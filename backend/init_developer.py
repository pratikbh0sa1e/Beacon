"""Initialize developer account on first run"""
import secrets
import string
import os
from sqlalchemy.orm import Session
import bcrypt
from backend.database import SessionLocal, User
from backend.constants.roles import DEVELOPER


# def generate_secure_password(length: int = 32) -> str:
#     """Generate a cryptographically secure random password"""
#     alphabet = string.ascii_letters + string.digits + string.punctuation
#     password = ''.join(secrets.choice(alphabet) for _ in range(length))
#     return password
def generate_secure_password(length: int = 32) -> str:
    """Generate a cryptographically secure random password (JSON-safe)"""
    # Exclude characters that break JSON or shell scripts: " ' \ `
    unsafe_chars = "\"'\\`"
    
    # Create safe punctuation list
    safe_punctuation = "".join([c for c in string.punctuation if c not in unsafe_chars])
    
    alphabet = string.ascii_letters + string.digits + safe_punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def initialize_developer_account():
    """
    Create initial developer account if none exists
    
    This runs once on application startup
    The password is printed to console and should be stored securely
    
    To reset password: Set environment variable RESET_DEVELOPER_PASSWORD=true
    """
    db: Session = SessionLocal()
    
    try:
        # Check if developer account exists
        developer = db.query(User).filter(User.role == DEVELOPER).first()
        
        # Check if password reset is requested via environment variable
        reset_password = os.getenv("RESET_DEVELOPER_PASSWORD", "false").lower() == "true"
        
        if developer and not reset_password:
            print("✓ Developer account already exists")
            print("  Email: root@beacon.system")
            print("  To reset password, set RESET_DEVELOPER_PASSWORD=true in .env")
            return
        
        # Generate secure password
        password = generate_secure_password(32)
        password_hash = hash_password(password)
        
        if developer and reset_password:
            # Update existing developer password
            developer.password_hash = password_hash
            db.commit()
            
            print("\n" + "="*80)
            print("🔄 DEVELOPER PASSWORD RESET")
            print("="*80)
            print(f"Username: root@beacon.system")
            print(f"New Password: {password}")
            print("="*80)
            print("⚠️  IMPORTANT: Save this password securely!")
            print("⚠️  Remove RESET_DEVELOPER_PASSWORD=true from .env after saving")
            print("="*80 + "\n")
            
        else:
            # Create new developer account
            developer = User(
                name="System Administrator",
                email="root@beacon.system",
                password_hash=password_hash,
                role=DEVELOPER,  # Use constant instead of hardcoded string
                institution_id=None,
                approved=True
            )
            
            db.add(developer)
            db.commit()
            
            print("\n" + "="*80)
            print("🔐 DEVELOPER ACCOUNT CREATED")
            print("="*80)
            print(f"Username: root@beacon.system")
            print(f"Password: {password}")
            print("="*80)
            print("⚠️  IMPORTANT: Save this password securely - it will not be shown again!")
            print("⚠️  To reset password later, set RESET_DEVELOPER_PASSWORD=true in .env")
            print("="*80 + "\n")
            
    except Exception as e:
        print(f"❌ Error with developer account: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # Can be run standalone for testing
    initialize_developer_account()