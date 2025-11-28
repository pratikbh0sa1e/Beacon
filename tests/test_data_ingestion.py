"""
Test suite for external data ingestion module
"""
import pytest
import os
from cryptography.fernet import Fernet
from Agent.data_ingestion.db_connector import ExternalDBConnector


class TestEncryption:
    """Test password encryption/decryption"""
    
    def test_encrypt_decrypt(self):
        """Test that encryption and decryption work correctly"""
        # Generate test key
        key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = key
        
        connector = ExternalDBConnector()
        
        # Test password
        original_password = "test_password_123"
        
        # Encrypt
        encrypted = connector.encrypt_password(original_password)
        assert encrypted != original_password
        assert len(encrypted) > 0
        
        # Decrypt
        decrypted = connector.decrypt_password(encrypted)
        assert decrypted == original_password
        
        print("✅ Encryption/Decryption test passed")
    
    def test_different_passwords(self):
        """Test that different passwords produce different encrypted values"""
        key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = key
        
        connector = ExternalDBConnector()
        
        password1 = "password1"
        password2 = "password2"
        
        encrypted1 = connector.encrypt_password(password1)
        encrypted2 = connector.encrypt_password(password2)
        
        assert encrypted1 != encrypted2
        
        print("✅ Different passwords test passed")


class TestConnectionTest:
    """Test database connection testing"""
    
    def test_invalid_connection(self):
        """Test connection to invalid database"""
        key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = key
        
        connector = ExternalDBConnector()
        
        result = connector.test_connection(
            host="invalid-host.example.com",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass"
        )
        
        assert result["status"] == "failed"
        assert "message" in result
        
        print("✅ Invalid connection test passed")


def run_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("Testing Data Ingestion Module")
    print("="*60 + "\n")
    
    # Test encryption
    test_encryption = TestEncryption()
    test_encryption.test_encrypt_decrypt()
    test_encryption.test_different_passwords()
    
    # Test connection
    test_connection = TestConnectionTest()
    test_connection.test_invalid_connection()
    
    print("\n" + "="*60)
    print("All Tests Passed! ✅")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_tests()
