"""
Generate encryption key for database passwords
Run this once and add the key to your .env file
"""
from cryptography.fernet import Fernet

def generate_encryption_key():
    """Generate a new Fernet encryption key"""
    key = Fernet.generate_key()
    return key.decode()

if __name__ == "__main__":
    key = generate_encryption_key()
    print("\n" + "="*60)
    print("ENCRYPTION KEY GENERATED")
    print("="*60)
    print(f"\nAdd this to your .env file:\n")
    print(f"DB_ENCRYPTION_KEY={key}")
    print("\n" + "="*60)
    print("⚠️  IMPORTANT: Keep this key secure!")
    print("⚠️  If you lose it, you won't be able to decrypt passwords")
    print("="*60 + "\n")
