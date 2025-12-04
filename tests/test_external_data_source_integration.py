"""
Integration Tests for External Data Source System

This module contains comprehensive integration tests that verify the complete
workflows of the external data source system, including:
- Submit → Approve → Sync → Notification workflow
- Rejection workflow with reason
- Role-based access control across all pages
- Data isolation between institutions
- Error scenarios and recovery
"""
import pytest
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet

from Agent.data_ingestion.db_connector import ExternalDBConnector
from Agent.data_ingestion.models import ExternalDataSource
from backend.database import Base, User, Institution


# Test database setup
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def setup_test_db():
    """Create test database tables"""
    Institution.__table__.create(bind=test_engine, checkfirst=True)
    User.__table__.create(bind=test_engine, checkfirst=True)
    ExternalDataSource.__table__.create(bind=test_engine, checkfirst=True)


def teardown_test_db():
    """Drop test database tables"""
    ExternalDataSource.__table__.drop(bind=test_engine, checkfirst=True)
    User.__table__.drop(bind=test_engine, checkfirst=True)
    Institution.__table__.drop(bind=test_engine, checkfirst=True)


class TestCompleteWorkflow:
    """Test the complete submit → approve → sync → notification workflow"""
    
    @pytest.fixture(autouse=True, scope="function")
    def setup(self):
        """Setup test database and mock data"""
        teardown_test_db()
        setup_test_db()
        self.db = TestSessionLocal()
        
        # Setup encryption
        self.key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = self.key
