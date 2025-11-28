"""Initialize developer account on first run"""
import secrets
import string
from sqlalchemy.orm import Session
import bcrypt

from backend.database import SessionLocal, User
from backend.constants.roles import ROLES


def generate_secure_password(length: int = 32) -> str:
    """Generate a cryptographically secure random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
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
    """
    db: Session = SessionLocal()
    
    try:
        # Check if any developer account exists
        # developer_exists = db.query(User).filter(User.role == "developer").first()

        developer_exists = db.query(User).filter(User.role == ROLES.DEVELOPER).first()
        
        if developer_exists:
            print("✓ Developer account already exists")
            return
        
        # Generate secure password
        password = generate_secure_password(32)
        password_hash = hash_password(password)
        
        # Create developer account
        developer = User(
            name="System Administrator",
            email="root@beacon.system",
            password_hash=password_hash,
            role="developer",
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
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"Error creating developer account: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    initialize_developer_account()