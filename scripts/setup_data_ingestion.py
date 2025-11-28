"""
Setup script for data ingestion module
Run this after installing dependencies
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cryptography.fernet import Fernet
from dotenv import load_dotenv, set_key

load_dotenv()


def generate_and_save_key():
    """Generate encryption key and save to .env"""
    env_path = project_root / ".env"
    
    # Check if key already exists
    existing_key = os.getenv("DB_ENCRYPTION_KEY")
    if existing_key:
        print("✅ DB_ENCRYPTION_KEY already exists in .env")
        return existing_key
    
    # Generate new key
    key = Fernet.generate_key().decode()
    
    # Save to .env
    set_key(env_path, "DB_ENCRYPTION_KEY", key)
    
    print("\n" + "="*60)
    print("✅ ENCRYPTION KEY GENERATED AND SAVED")
    print("="*60)
    print(f"\nKey saved to .env file")
    print(f"DB_ENCRYPTION_KEY={key}")
    print("\n" + "="*60)
    print("⚠️  IMPORTANT: Keep this key secure!")
    print("⚠️  Backup your .env file")
    print("="*60 + "\n")
    
    return key


def create_migration():
    """Create database migration for new tables"""
    print("\n📦 Creating database migration...")
    print("Run these commands:")
    print("  alembic revision --autogenerate -m 'Add external data sources'")
    print("  alembic upgrade head")


def check_dependencies():
    """Check if required packages are installed"""
    required = ["schedule", "psycopg2", "cryptography"]
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    print("✅ All dependencies installed")
    return True


def main():
    print("\n🚀 Data Ingestion Module Setup\n")
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Generate encryption key
    generate_and_save_key()
    
    # Migration instructions
    create_migration()
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Run database migrations (see above)")
    print("2. Start your server: uvicorn backend.main:app --reload")
    print("3. Register data sources via API")
    print("\nAPI Documentation: http://localhost:8000/docs")
    print("Data Ingestion README: Agent/data_ingestion/README.md\n")


if __name__ == "__main__":
    main()
