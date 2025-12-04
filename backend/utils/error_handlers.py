"""
Centralized error handling utilities for external data source system
"""
from typing import Dict, Any, Optional
import logging
import psycopg2
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DataSourceError(Exception):
    """Base exception for data source errors"""
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ConnectionError(DataSourceError):
    """Database connection errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONNECTION_ERROR", details)


class AuthenticationError(DataSourceError):
    """Authentication/credential errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class SyncError(DataSourceError):
    """Sync operation errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SYNC_ERROR", details)


class ValidationError(DataSourceError):
    """Input validation errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


def handle_connection_error(error: Exception, host: str, port: int, database: str) -> Dict[str, Any]:
    """
    Handle database connection errors with user-friendly messages
    
    Args:
        error: The exception that occurred
        host: Database host
        port: Database port
        database: Database name
    
    Returns:
        Dict with status, message, and error_code
    """
    error_str = str(error).lower()
    
    # Invalid credentials
    if "authentication failed" in error_str or "password authentication failed" in error_str:
        return {
            "status": "failed",
            "error_code": "INVALID_CREDENTIALS",
            "message": "Authentication failed. Please check your username and password.",
            "details": {
                "host": host,
                "database": database,
                "hint": "Verify that the username and password are correct."
            }
        }
    
    # Connection timeout
    if "timeout" in error_str or "timed out" in error_str:
        return {
            "status": "failed",
            "error_code": "CONNECTION_TIMEOUT",
            "message": f"Connection to {host}:{port} timed out. The database server may be unreachable.",
            "details": {
                "host": host,
                "port": port,
                "hint": "Check if the host and port are correct, and ensure the database server is running and accessible from this network."
            }
        }
    
    # Connection refused
    if "connection refused" in error_str or "could not connect" in error_str:
        return {
            "status": "failed",
            "error_code": "CONNECTION_REFUSED",
            "message": f"Connection refused by {host}:{port}. The database server may not be running or may not accept connections.",
            "details": {
                "host": host,
                "port": port,
                "hint": "Verify that the database server is running and configured to accept remote connections."
            }
        }
    
    # Database not found
    if "database" in error_str and ("does not exist" in error_str or "not found" in error_str):
        return {
            "status": "failed",
            "error_code": "DATABASE_NOT_FOUND",
            "message": f"Database '{database}' does not exist on the server.",
            "details": {
                "database": database,
                "hint": "Check the database name spelling and ensure the database has been created."
            }
        }
    
    # Host not found
    if "could not translate host name" in error_str or "name or service not known" in error_str:
        return {
            "status": "failed",
            "error_code": "HOST_NOT_FOUND",
            "message": f"Could not resolve hostname '{host}'. The host may not exist or DNS lookup failed.",
            "details": {
                "host": host,
                "hint": "Verify the hostname is correct and accessible from your network."
            }
        }
    
    # SSL/TLS errors
    if "ssl" in error_str or "certificate" in error_str:
        return {
            "status": "failed",
            "error_code": "SSL_ERROR",
            "message": "SSL/TLS connection error. The database may require SSL or have certificate issues.",
            "details": {
                "hint": "Check SSL configuration and certificate validity."
            }
        }
    
    # Generic connection error
    return {
        "status": "failed",
        "error_code": "CONNECTION_ERROR",
        "message": f"Failed to connect to database: {str(error)}",
        "details": {
            "host": host,
            "port": port,
            "database": database,
            "error": str(error)
        }
    }


def handle_sync_error(error: Exception, source_name: str, operation: str = "sync") -> Dict[str, Any]:
    """
    Handle sync operation errors with user-friendly messages
    
    Args:
        error: The exception that occurred
        source_name: Name of the data source
        operation: Operation being performed (sync, fetch, process)
    
    Returns:
        Dict with status, message, and error_code
    """
    error_str = str(error).lower()
    
    # Permission denied
    if "permission denied" in error_str or "access denied" in error_str:
        return {
            "status": "failed",
            "error_code": "PERMISSION_DENIED",
            "message": f"Permission denied while accessing {source_name}. The database user may lack necessary privileges.",
            "details": {
                "source": source_name,
                "hint": "Ensure the database user has SELECT permissions on the specified table."
            }
        }
    
    # Table/column not found
    if "relation" in error_str and "does not exist" in error_str:
        return {
            "status": "failed",
            "error_code": "TABLE_NOT_FOUND",
            "message": f"Table or column not found in {source_name}. The schema may have changed.",
            "details": {
                "source": source_name,
                "hint": "Verify that the table name and column names are correct and exist in the database."
            }
        }
    
    if "column" in error_str and ("does not exist" in error_str or "not found" in error_str):
        return {
            "status": "failed",
            "error_code": "COLUMN_NOT_FOUND",
            "message": f"Column not found in {source_name}. The table schema may have changed.",
            "details": {
                "source": source_name,
                "hint": "Check that all configured column names (file_column, filename_column, metadata_columns) exist in the table."
            }
        }
    
    # Data type mismatch
    if "type" in error_str and ("mismatch" in error_str or "invalid" in error_str):
        return {
            "status": "failed",
            "error_code": "SCHEMA_MISMATCH",
            "message": f"Data type mismatch in {source_name}. The column types may not match expected format.",
            "details": {
                "source": source_name,
                "hint": "Ensure file_column contains binary data (bytea) or text paths, and filename_column contains text."
            }
        }
    
    # Quota/storage errors
    if "quota" in error_str or "disk full" in error_str or "out of space" in error_str:
        return {
            "status": "failed",
            "error_code": "QUOTA_EXCEEDED",
            "message": f"Storage quota exceeded while syncing {source_name}.",
            "details": {
                "source": source_name,
                "hint": "Free up storage space or increase quota limits."
            }
        }
    
    # Credentials missing/revoked
    if "credentials not available" in error_str or "revoked" in error_str:
        return {
            "status": "failed",
            "error_code": "CREDENTIALS_UNAVAILABLE",
            "message": f"Credentials not available for {source_name}. The source may have been rejected or revoked.",
            "details": {
                "source": source_name,
                "hint": "Submit a new connection request if access is needed."
            }
        }
    
    # Generic sync error
    return {
        "status": "failed",
        "error_code": "SYNC_ERROR",
        "message": f"Sync failed for {source_name}: {str(error)}",
        "details": {
            "source": source_name,
            "operation": operation,
            "error": str(error)
        }
    }


def handle_validation_error(field: str, value: Any, constraint: str) -> HTTPException:
    """
    Create HTTPException for validation errors
    
    Args:
        field: Field name that failed validation
        value: The invalid value
        constraint: Description of the constraint that was violated
    
    Returns:
        HTTPException with 400 status
    """
    return HTTPException(
        status_code=400,
        detail={
            "error_code": "VALIDATION_ERROR",
            "message": f"Validation failed for field '{field}': {constraint}",
            "field": field,
            "constraint": constraint
        }
    )


def handle_authorization_error(user_role: str, required_role: str, resource: str) -> HTTPException:
    """
    Create HTTPException for authorization errors
    
    Args:
        user_role: Current user's role
        required_role: Required role for the operation
        resource: Resource being accessed
    
    Returns:
        HTTPException with 403 status
    """
    return HTTPException(
        status_code=403,
        detail={
            "error_code": "AUTHORIZATION_ERROR",
            "message": f"Access denied. {required_role} role required to access {resource}.",
            "user_role": user_role,
            "required_role": required_role,
            "resource": resource
        }
    )


def handle_not_found_error(resource_type: str, resource_id: Any) -> HTTPException:
    """
    Create HTTPException for resource not found errors
    
    Args:
        resource_type: Type of resource (e.g., "Data source", "Request")
        resource_id: ID of the resource
    
    Returns:
        HTTPException with 404 status
    """
    return HTTPException(
        status_code=404,
        detail={
            "error_code": "NOT_FOUND",
            "message": f"{resource_type} with ID {resource_id} not found.",
            "resource_type": resource_type,
            "resource_id": resource_id
        }
    )


def log_and_handle_exception(error: Exception, context: str, logger_instance: logging.Logger = logger) -> HTTPException:
    """
    Log exception and convert to appropriate HTTPException
    
    Args:
        error: The exception that occurred
        context: Context description for logging
        logger_instance: Logger to use
    
    Returns:
        HTTPException with appropriate status code
    """
    # Log the error
    logger_instance.error(f"{context}: {str(error)}", exc_info=True)
    
    # Handle specific exception types
    if isinstance(error, HTTPException):
        return error
    
    if isinstance(error, SQLAlchemyError):
        return HTTPException(
            status_code=500,
            detail={
                "error_code": "DATABASE_ERROR",
                "message": "Database operation failed. Please try again later.",
                "context": context
            }
        )
    
    if isinstance(error, psycopg2.Error):
        return HTTPException(
            status_code=500,
            detail={
                "error_code": "EXTERNAL_DB_ERROR",
                "message": "External database operation failed.",
                "context": context,
                "details": str(error)
            }
        )
    
    # Generic error
    return HTTPException(
        status_code=500,
        detail={
            "error_code": "INTERNAL_ERROR",
            "message": f"An unexpected error occurred: {str(error)}",
            "context": context
        }
    )
