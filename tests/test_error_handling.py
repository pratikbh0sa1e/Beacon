"""
Test error handling for external data source system
"""
import pytest
from backend.utils.error_handlers import (
    handle_connection_error,
    handle_sync_error,
    handle_validation_error,
    handle_authorization_error,
    handle_not_found_error
)
from fastapi import HTTPException
import psycopg2


class TestConnectionErrorHandling:
    """Test connection error handling"""
    
    def test_invalid_credentials_error(self):
        """Test handling of authentication failures"""
        error = psycopg2.OperationalError("password authentication failed for user 'test'")
        result = handle_connection_error(error, "localhost", 5432, "testdb")
        
        assert result["status"] == "failed"
        assert result["error_code"] == "INVALID_CREDENTIALS"
        assert "username and password" in result["message"].lower()
        assert "hint" in result["details"]
    
    def test_connection_timeout_error(self):
        """Test handling of connection timeouts"""
        error = psycopg2.OperationalError("connection timed out")
        result = handle_connection_error(error, "remote.host.com", 5432, "testdb")
        
        assert result["status"] == "failed"
        assert result["error_code"] == "CONNECTION_TIMEOUT"
        assert "timed out" in result["message"].lower()
        assert result["details"]["host"] == "remote.host.com"
    
    def test_connection_refused_error(self):
        """Test handling of connection refused"""
        error = psycopg2.OperationalError("could not connect to server: Connection refused")
        result = handle_connection_error(error, "localhost", 5432, "testdb")
        
        assert result["status"] == "failed"
        assert result["error_code"] == "CONNECTION_REFUSED"
        assert "refused" in result["message"].lower()
    
    def test_database_not_found_error(self):
        """Test handling of database not found"""
        error = psycopg2.OperationalError('database "nonexistent" does not exist')
        result = handle_connection_error(error, "localhost", 5432, "nonexistent")
        
        assert result["status"] == "failed"
        assert result["error_code"] == "DATABASE_NOT_FOUND"
        assert "does not exist" in result["message"].lower()
    
    def test_host_not_found_error(self):
        """Test handling of hostname resolution failures"""
        error = psycopg2.OperationalError("could not translate host name to address")
        result = handle_connection_error(error, "invalid.host", 5432, "testdb")
        
        assert result["status"] == "failed"
        assert result["error_code"] == "HOST_NOT_FOUND"
        assert "resolve hostname" in result["message"].lower()


class TestSyncErrorHandling:
    """Test sync error handling"""
    
    def test_permission_denied_error(self):
        """Test handling of permission denied errors"""
        error = Exception("permission denied for table documents")
        result = handle_sync_error(error, "TestSource", "sync")
        
        assert result["status"] == "failed"
        assert result["error_code"] == "PERMISSION_DENIED"
        assert "permission" in result["message"].lower()
        assert "hint" in result["details"]
    
    def test_table_not_found_error(self):
        """Test handling of table not found errors"""
        error = Exception('relation "documents" does not exist')
        result = handle_sync_error(error, "TestSource", "sync")
        
        assert result["status"] == "failed"
        assert result["error_code"] == "TABLE_NOT_FOUND"
        assert "table" in result["message"].lower()
    
    def test_column_not_found_error(self):
        """Test handling of column not found errors"""
        error = Exception('column "file_data" does not exist')
        result = handle_sync_error(error, "TestSource", "sync")
        
        assert result["status"] == "failed"
        assert result["error_code"] == "COLUMN_NOT_FOUND"
        assert "column" in result["message"].lower()
    
    def test_quota_exceeded_error(self):
        """Test handling of quota exceeded errors"""
        error = Exception("disk quota exceeded")
        result = handle_sync_error(error, "TestSource", "sync")
        
        assert result["status"] == "failed"
        assert result["error_code"] == "QUOTA_EXCEEDED"
        assert "quota" in result["message"].lower()
    
    def test_credentials_unavailable_error(self):
        """Test handling of missing credentials"""
        error = Exception("Credentials not available. Source may have been rejected or revoked.")
        result = handle_sync_error(error, "TestSource", "sync")
        
        assert result["status"] == "failed"
        assert result["error_code"] == "CREDENTIALS_UNAVAILABLE"
        assert "credentials" in result["message"].lower()


class TestHTTPExceptionHandlers:
    """Test HTTP exception handlers"""
    
    def test_validation_error(self):
        """Test validation error creation"""
        exc = handle_validation_error("port", 99999, "must be between 1 and 65535")
        
        assert isinstance(exc, HTTPException)
        assert exc.status_code == 400
        assert "port" in exc.detail["field"]
        assert exc.detail["error_code"] == "VALIDATION_ERROR"
    
    def test_authorization_error(self):
        """Test authorization error creation"""
        exc = handle_authorization_error("student", "developer", "approval dashboard")
        
        assert isinstance(exc, HTTPException)
        assert exc.status_code == 403
        assert exc.detail["error_code"] == "AUTHORIZATION_ERROR"
        assert "developer" in exc.detail["required_role"]
    
    def test_not_found_error(self):
        """Test not found error creation"""
        exc = handle_not_found_error("Data source", 123)
        
        assert isinstance(exc, HTTPException)
        assert exc.status_code == 404
        assert exc.detail["error_code"] == "NOT_FOUND"
        assert exc.detail["resource_id"] == 123


class TestErrorMessageQuality:
    """Test that error messages are user-friendly"""
    
    def test_connection_errors_have_hints(self):
        """Test that connection errors include helpful hints"""
        error = psycopg2.OperationalError("password authentication failed")
        result = handle_connection_error(error, "localhost", 5432, "testdb")
        
        assert "hint" in result["details"]
        assert len(result["details"]["hint"]) > 0
        assert result["details"]["hint"] != ""
    
    def test_sync_errors_have_hints(self):
        """Test that sync errors include helpful hints"""
        error = Exception("permission denied for table documents")
        result = handle_sync_error(error, "TestSource", "sync")
        
        assert "hint" in result["details"]
        assert "SELECT" in result["details"]["hint"]
    
    def test_error_messages_are_descriptive(self):
        """Test that error messages are descriptive and actionable"""
        error = psycopg2.OperationalError("connection timed out")
        result = handle_connection_error(error, "remote.host.com", 5432, "testdb")
        
        # Message should mention the host
        assert "remote.host.com" in result["message"]
        
        # Message should be descriptive
        assert len(result["message"]) > 20
        
        # Should not just be the raw error
        assert result["message"] != str(error)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
