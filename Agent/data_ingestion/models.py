"""
Database models for external data source management

Note: Models are now defined in backend/database.py
This file imports them for convenience
"""
from backend.database import ExternalDataSource, SyncLog

__all__ = ['ExternalDataSource', 'SyncLog']
