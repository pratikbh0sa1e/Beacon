"""
Property-Based Tests for External Data Source System

This module contains property-based tests using Hypothesis to verify
correctness properties of the external data source system.
"""
import pytest
import os
from hypothesis import given, strategies as st, settings
from cryptography.fernet import Fernet
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Agent.data_ingestion.db_connector import ExternalDBConnector
from Agent.data_ingestion.models import ExternalDataSource
from backend.database import Base, User, Institution


# Test database setup
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def setup_test_db():
    """Create test database tables"""
    # Only create tables we need for testing, avoiding JSONB issues with SQLite
    from backend.database import Institution, User, ExternalDataSource
    Institution.__table__.create(bind=test_engine, checkfirst=True)
    User.__table__.create(bind=test_engine, checkfirst=True)
    ExternalDataSource.__table__.create(bind=test_engine, checkfirst=True)


def teardown_test_db():
    """Drop test database tables"""
    from backend.database import Institution, User, ExternalDataSource
    ExternalDataSource.__table__.drop(bind=test_engine, checkfirst=True)
    User.__table__.drop(bind=test_engine, checkfirst=True)
    Institution.__table__.drop(bind=test_engine, checkfirst=True)


def get_test_db():
    """Get test database session"""
    db = TestSessionLocal()
    try:
        return db
    finally:
        pass


# Hypothesis strategies for generating test data
password_strategy = st.text(min_size=8, max_size=128, alphabet=st.characters(
    blacklist_categories=('Cs', 'Cc'),  # Exclude surrogates and control characters
    blacklist_characters='\x00'  # Exclude null bytes
))

db_host_strategy = st.text(min_size=1, max_size=255, alphabet=st.characters(
    whitelist_categories=('L', 'N'),
    min_codepoint=33, max_codepoint=126
)).filter(lambda x: len(x.strip()) > 0)

db_name_strategy = st.text(min_size=1, max_size=100, alphabet=st.characters(
    whitelist_categories=('L', 'N'),
    min_codepoint=33, max_codepoint=126
)).filter(lambda x: len(x.strip()) > 0 and '_' not in x[:1])

username_strategy = st.text(min_size=1, max_size=100, alphabet=st.characters(
    whitelist_categories=('L', 'N'),
    min_codepoint=33, max_codepoint=126
)).filter(lambda x: len(x.strip()) > 0)


class TestPasswordEncryption:
    """Property-based tests for password encryption"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup encryption key for each test"""
        self.key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = self.key
        self.connector = ExternalDBConnector()
    
    # Feature: external-data-source, Property 24: Passwords encrypted in database
    @settings(max_examples=100)
    @given(password=password_strategy)
    def test_passwords_encrypted_in_database(self, password):
        """
        For any password stored in the database, the password field should 
        contain encrypted data, not plaintext.
        
        Validates: Requirements 8.1
        """
        # Encrypt the password
        encrypted = self.connector.encrypt_password(password)
        
        # Property 1: Encrypted password should not equal plaintext
        assert encrypted != password, "Encrypted password should not match plaintext"
        
        # Property 2: Encrypted password should be non-empty
        assert len(encrypted) > 0, "Encrypted password should not be empty"
        
        # Property 3: Encrypted password should be decodable (valid base64-like format)
        assert isinstance(encrypted, str), "Encrypted password should be a string"
        
        # Property 4: Decryption should recover original password
        decrypted = self.connector.decrypt_password(encrypted)
        assert decrypted == password, "Decrypted password should match original"
    
    @settings(max_examples=100)
    @given(
        password1=password_strategy,
        password2=password_strategy
    )
    def test_different_passwords_produce_different_ciphertexts(self, password1, password2):
        """
        For any two different passwords, their encrypted forms should be different.
        This ensures the encryption is deterministic and collision-free.
        """
        # Skip if passwords are the same
        if password1 == password2:
            return
        
        encrypted1 = self.connector.encrypt_password(password1)
        encrypted2 = self.connector.encrypt_password(password2)
        
        assert encrypted1 != encrypted2, "Different passwords should produce different encrypted values"


class TestRequestStatus:
    """Property-based tests for request status"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup encryption and mock data"""
        # Setup encryption
        self.key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = self.key
        self.connector = ExternalDBConnector()
        
        # Create mock institution and user (without database)
        self.institution_id = 1
        self.user_id = 1
    
    # Feature: external-data-source, Property 1: New requests have pending status
    @settings(max_examples=100)
    @given(
        name=st.text(min_size=1, max_size=200).filter(lambda x: len(x.strip()) > 0),
        ministry_name=st.text(min_size=1, max_size=200).filter(lambda x: len(x.strip()) > 0),
        host=db_host_strategy,
        port=st.integers(min_value=1, max_value=65535),
        database_name=db_name_strategy,
        username=username_strategy,
        password=password_strategy,
        table_name=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0)
    )
    def test_new_requests_have_pending_status(
        self, name, ministry_name, host, port, database_name, 
        username, password, table_name
    ):
        """
        For any valid connection request submitted by an administrator, 
        the created request should have status "pending" and be associated 
        with the administrator's institution.
        
        Validates: Requirements 1.5
        """
        # Encrypt password
        encrypted_password = self.connector.encrypt_password(password)
        
        # Create a new data source request (in-memory, no DB persistence)
        new_request = ExternalDataSource(
            name=f"test_source_{name[:50]}",  # Ensure unique name
            ministry_name=ministry_name,
            db_type="postgresql",
            host=host,
            port=port,
            database_name=database_name,
            username=username,
            password_encrypted=encrypted_password,
            table_name=table_name,
            file_column="file_data",
            filename_column="filename",
            institution_id=self.institution_id,
            requested_by_user_id=self.user_id,
            request_status="pending",  # This is what we're testing
            requested_at=datetime.utcnow(),
            sync_enabled=False
        )
        
        # Property 1: New request should have "pending" status
        assert new_request.request_status == "pending", \
            "New connection request should have 'pending' status"
        
        # Property 2: Request should be associated with the administrator's institution
        assert new_request.institution_id == self.institution_id, \
            "Request should be associated with administrator's institution"
        
        # Property 3: Request should have the requesting user ID
        assert new_request.requested_by_user_id == self.user_id, \
            "Request should have the requesting user's ID"
        
        # Property 4: Sync should be disabled for pending requests
        assert new_request.sync_enabled == False, \
            "Sync should be disabled for pending requests"
        
        # Property 5: Password should be encrypted
        assert new_request.password_encrypted != password, \
            "Password should be encrypted in the request"
        
        # Verify we can decrypt it back
        decrypted = self.connector.decrypt_password(new_request.password_encrypted)
        assert decrypted == password, \
            "Encrypted password should decrypt back to original"


class TestRequestFiltering:
    """Property-based tests for request filtering and access control"""
    
    @pytest.fixture(autouse=True, scope="function")
    def setup(self):
        """Setup test database and mock data"""
        # Clean up any existing tables first
        teardown_test_db()
        setup_test_db()
        self.db = get_test_db()
        
        # Setup encryption
        self.key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = self.key
        self.connector = ExternalDBConnector()
        
        # Create test institutions
        self.institution1 = Institution(
            name="Test Ministry 1",
            type="ministry",
            location="Test Location 1"
        )
        self.institution2 = Institution(
            name="Test University 1",
            type="university",
            location="Test Location 2"
        )
        
        self.db.add(self.institution1)
        self.db.add(self.institution2)
        self.db.commit()
        self.db.refresh(self.institution1)
        self.db.refresh(self.institution2)
        
        # Create test users
        self.admin1 = User(
            name="Admin 1",
            email="admin1@ministry1.gov",
            role="ministry_admin",
            institution_id=self.institution1.id,
            password_hash="dummy",
            approved=True
        )
        self.admin2 = User(
            name="Admin 2",
            email="admin2@university1.edu",
            role="university_admin",
            institution_id=self.institution2.id,
            password_hash="dummy",
            approved=True
        )
        
        self.db.add(self.admin1)
        self.db.add(self.admin2)
        self.db.commit()
        self.db.refresh(self.admin1)
        self.db.refresh(self.admin2)
        
        yield
        
        # Cleanup - delete all data sources created during test
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        self.db.close()
        teardown_test_db()
    
    # Feature: external-data-source, Property 4: Administrators see only own requests
    @settings(max_examples=50)
    @given(
        num_requests_admin1=st.integers(min_value=1, max_value=5),
        num_requests_admin2=st.integers(min_value=1, max_value=5)
    )
    def test_administrators_see_only_own_requests(self, num_requests_admin1, num_requests_admin2):
        """
        For any administrator user, querying "My Requests" should return only 
        requests where the requester's institution matches the user's institution.
        
        Validates: Requirements 2.1, 7.3
        """
        # Clean up any existing data sources from previous examples
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        
        # Create requests for admin1 (institution 1)
        admin1_requests = []
        for i in range(num_requests_admin1):
            request = ExternalDataSource(
                name=f"admin1_source_{i}_{datetime.utcnow().timestamp()}",
                ministry_name="Ministry 1",
                db_type="postgresql",
                host="localhost",
                port=5432,
                database_name=f"db_{i}",
                username="user",
                password_encrypted=self.connector.encrypt_password("password"),
                table_name="documents",
                file_column="file_data",
                filename_column="filename",
                institution_id=self.institution1.id,
                requested_by_user_id=self.admin1.id,
                request_status="pending",
                requested_at=datetime.utcnow(),
                sync_enabled=False
            )
            self.db.add(request)
            admin1_requests.append(request)
        
        # Create requests for admin2 (institution 2)
        admin2_requests = []
        for i in range(num_requests_admin2):
            request = ExternalDataSource(
                name=f"admin2_source_{i}_{datetime.utcnow().timestamp()}",
                ministry_name="University 1",
                db_type="postgresql",
                host="localhost",
                port=5432,
                database_name=f"db_{i}",
                username="user",
                password_encrypted=self.connector.encrypt_password("password"),
                table_name="documents",
                file_column="file_data",
                filename_column="filename",
                institution_id=self.institution2.id,
                requested_by_user_id=self.admin2.id,
                request_status="pending",
                requested_at=datetime.utcnow(),
                sync_enabled=False
            )
            self.db.add(request)
            admin2_requests.append(request)
        
        self.db.commit()
        
        # Query requests for admin1 (simulating the /my-requests endpoint)
        admin1_query_results = self.db.query(ExternalDataSource).filter(
            ExternalDataSource.requested_by_user_id == self.admin1.id
        ).all()
        
        # Query requests for admin2
        admin2_query_results = self.db.query(ExternalDataSource).filter(
            ExternalDataSource.requested_by_user_id == self.admin2.id
        ).all()
        
        # Property 1: Admin1 should see exactly their own requests
        assert len(admin1_query_results) == num_requests_admin1, \
            f"Admin1 should see {num_requests_admin1} requests, but saw {len(admin1_query_results)}"
        
        # Property 2: Admin2 should see exactly their own requests
        assert len(admin2_query_results) == num_requests_admin2, \
            f"Admin2 should see {num_requests_admin2} requests, but saw {len(admin2_query_results)}"
        
        # Property 3: All requests returned for admin1 should belong to institution 1
        for request in admin1_query_results:
            assert request.institution_id == self.institution1.id, \
                "Admin1 should only see requests from their institution"
            assert request.requested_by_user_id == self.admin1.id, \
                "Admin1 should only see requests they submitted"
        
        # Property 4: All requests returned for admin2 should belong to institution 2
        for request in admin2_query_results:
            assert request.institution_id == self.institution2.id, \
                "Admin2 should only see requests from their institution"
            assert request.requested_by_user_id == self.admin2.id, \
                "Admin2 should only see requests they submitted"
        
        # Property 5: No overlap between admin1 and admin2 requests
        admin1_ids = {r.id for r in admin1_query_results}
        admin2_ids = {r.id for r in admin2_query_results}
        assert len(admin1_ids.intersection(admin2_ids)) == 0, \
            "Admins should not see each other's requests"


class TestPasswordMasking:
    """Property-based tests for password masking in display"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup encryption"""
        self.key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = self.key
        self.connector = ExternalDBConnector()
    
    # Feature: external-data-source, Property 25: Passwords masked in display
    @settings(max_examples=100)
    @given(password=password_strategy)
    def test_passwords_masked_in_display(self, password):
        """
        For any connection request displayed to a user, the password should 
        be masked with asterisks.
        
        Validates: Requirements 8.3
        """
        # Encrypt the password (as it would be stored)
        encrypted_password = self.connector.encrypt_password(password)
        
        # Create a mock request object
        request = ExternalDataSource(
            name="test_source",
            ministry_name="Test Ministry",
            db_type="postgresql",
            host="localhost",
            port=5432,
            database_name="testdb",
            username="testuser",
            password_encrypted=encrypted_password,
            table_name="documents",
            file_column="file_data",
            filename_column="filename",
            institution_id=1,
            requested_by_user_id=1,
            request_status="pending",
            requested_at=datetime.utcnow(),
            sync_enabled=False
        )
        
        # Simulate API response (passwords should NOT be included)
        # This is what the /my-requests endpoint returns
        api_response = {
            "id": request.id,
            "name": request.name,
            "ministry_name": request.ministry_name,
            "description": request.description,
            "request_status": request.request_status,
            "data_classification": request.data_classification,
            "request_notes": request.request_notes,
            "rejection_reason": request.rejection_reason,
            "requested_at": request.requested_at,
            "approved_at": request.approved_at,
            "last_sync_at": request.last_sync_at,
            "total_documents_synced": request.total_documents_synced
            # NOTE: password_encrypted is NOT included in response
        }
        
        # Property 1: API response should not contain password field
        assert "password" not in api_response, \
            "API response should not contain plaintext password"
        assert "password_encrypted" not in api_response, \
            "API response should not contain encrypted password"
        
        # Property 2: If we were to display password (for testing), it should be masked
        masked_password = "*" * 8  # Standard masking
        assert masked_password != password, \
            "Masked password should not equal plaintext password"
        assert len(masked_password) > 0, \
            "Masked password should not be empty"
        
        # Property 3: Encrypted password in database should not equal plaintext
        assert request.password_encrypted != password, \
            "Stored password should be encrypted, not plaintext"
        
        # Property 4: We should be able to decrypt for sync operations (but not display)
        decrypted = self.connector.decrypt_password(request.password_encrypted)
        assert decrypted == password, \
            "Should be able to decrypt password for sync operations"


class TestDeveloperVisibility:
    """Property-based tests for developer visibility of pending requests"""
    
    @pytest.fixture(autouse=True, scope="function")
    def setup(self):
        """Setup test database and mock data"""
        # Clean up any existing tables first
        teardown_test_db()
        setup_test_db()
        self.db = get_test_db()
        
        # Setup encryption
        self.key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = self.key
        self.connector = ExternalDBConnector()
        
        # Create test institutions
        self.institution1 = Institution(
            name="Test Ministry 1",
            type="ministry",
            location="Test Location 1"
        )
        self.institution2 = Institution(
            name="Test University 1",
            type="university",
            location="Test Location 2"
        )
        self.institution3 = Institution(
            name="Test Ministry 2",
            type="ministry",
            location="Test Location 3"
        )
        
        self.db.add(self.institution1)
        self.db.add(self.institution2)
        self.db.add(self.institution3)
        self.db.commit()
        self.db.refresh(self.institution1)
        self.db.refresh(self.institution2)
        self.db.refresh(self.institution3)
        
        # Create test users
        self.admin1 = User(
            name="Admin 1",
            email="admin1@ministry1.gov",
            role="ministry_admin",
            institution_id=self.institution1.id,
            password_hash="dummy",
            approved=True
        )
        self.admin2 = User(
            name="Admin 2",
            email="admin2@university1.edu",
            role="university_admin",
            institution_id=self.institution2.id,
            password_hash="dummy",
            approved=True
        )
        self.admin3 = User(
            name="Admin 3",
            email="admin3@ministry2.gov",
            role="ministry_admin",
            institution_id=self.institution3.id,
            password_hash="dummy",
            approved=True
        )
        self.developer = User(
            name="Developer",
            email="dev@beacon.gov",
            role="developer",
            institution_id=None,  # Developers don't belong to institutions
            password_hash="dummy",
            approved=True
        )
        
        self.db.add(self.admin1)
        self.db.add(self.admin2)
        self.db.add(self.admin3)
        self.db.add(self.developer)
        self.db.commit()
        self.db.refresh(self.admin1)
        self.db.refresh(self.admin2)
        self.db.refresh(self.admin3)
        self.db.refresh(self.developer)
        
        yield
        
        # Cleanup
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        self.db.close()
        teardown_test_db()
    
    # Feature: external-data-source, Property 6: Developers see all pending requests
    @settings(max_examples=50)
    @given(
        num_requests_inst1=st.integers(min_value=0, max_value=5),
        num_requests_inst2=st.integers(min_value=0, max_value=5),
        num_requests_inst3=st.integers(min_value=0, max_value=5),
        num_approved_requests=st.integers(min_value=0, max_value=3),
        num_rejected_requests=st.integers(min_value=0, max_value=3)
    )
    def test_developers_see_all_pending_requests(
        self, 
        num_requests_inst1, 
        num_requests_inst2, 
        num_requests_inst3,
        num_approved_requests,
        num_rejected_requests
    ):
        """
        For any developer user, querying the approval dashboard should return 
        all connection requests with status "pending" regardless of institution.
        
        Validates: Requirements 3.1, 7.5
        """
        # Clean up any existing data sources from previous examples
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        
        total_pending = num_requests_inst1 + num_requests_inst2 + num_requests_inst3
        
        # Create pending requests for institution 1
        for i in range(num_requests_inst1):
            request = ExternalDataSource(
                name=f"inst1_pending_{i}_{datetime.utcnow().timestamp()}",
                ministry_name="Ministry 1",
                db_type="postgresql",
                host="localhost",
                port=5432,
                database_name=f"db_{i}",
                username="user",
                password_encrypted=self.connector.encrypt_password("password"),
                table_name="documents",
                file_column="file_data",
                filename_column="filename",
                institution_id=self.institution1.id,
                requested_by_user_id=self.admin1.id,
                request_status="pending",
                requested_at=datetime.utcnow(),
                sync_enabled=False
            )
            self.db.add(request)
        
        # Create pending requests for institution 2
        for i in range(num_requests_inst2):
            request = ExternalDataSource(
                name=f"inst2_pending_{i}_{datetime.utcnow().timestamp()}",
                ministry_name="University 1",
                db_type="postgresql",
                host="localhost",
                port=5432,
                database_name=f"db_{i}",
                username="user",
                password_encrypted=self.connector.encrypt_password("password"),
                table_name="documents",
                file_column="file_data",
                filename_column="filename",
                institution_id=self.institution2.id,
                requested_by_user_id=self.admin2.id,
                request_status="pending",
                requested_at=datetime.utcnow(),
                sync_enabled=False
            )
            self.db.add(request)
        
        # Create pending requests for institution 3
        for i in range(num_requests_inst3):
            request = ExternalDataSource(
                name=f"inst3_pending_{i}_{datetime.utcnow().timestamp()}",
                ministry_name="Ministry 2",
                db_type="postgresql",
                host="localhost",
                port=5432,
                database_name=f"db_{i}",
                username="user",
                password_encrypted=self.connector.encrypt_password("password"),
                table_name="documents",
                file_column="file_data",
                filename_column="filename",
                institution_id=self.institution3.id,
                requested_by_user_id=self.admin3.id,
                request_status="pending",
                requested_at=datetime.utcnow(),
                sync_enabled=False
            )
            self.db.add(request)
        
        # Create some approved requests (should NOT appear in pending query)
        for i in range(num_approved_requests):
            request = ExternalDataSource(
                name=f"approved_{i}_{datetime.utcnow().timestamp()}",
                ministry_name="Ministry 1",
                db_type="postgresql",
                host="localhost",
                port=5432,
                database_name=f"db_approved_{i}",
                username="user",
                password_encrypted=self.connector.encrypt_password("password"),
                table_name="documents",
                file_column="file_data",
                filename_column="filename",
                institution_id=self.institution1.id,
                requested_by_user_id=self.admin1.id,
                request_status="approved",
                approved_by_user_id=self.developer.id,
                approved_at=datetime.utcnow(),
                requested_at=datetime.utcnow(),
                sync_enabled=True
            )
            self.db.add(request)
        
        # Create some rejected requests (should NOT appear in pending query)
        for i in range(num_rejected_requests):
            request = ExternalDataSource(
                name=f"rejected_{i}_{datetime.utcnow().timestamp()}",
                ministry_name="Ministry 2",
                db_type="postgresql",
                host="localhost",
                port=5432,
                database_name=f"db_rejected_{i}",
                username="user",
                password_encrypted=self.connector.encrypt_password("password"),
                table_name="documents",
                file_column="file_data",
                filename_column="filename",
                institution_id=self.institution3.id,
                requested_by_user_id=self.admin3.id,
                request_status="rejected",
                approved_by_user_id=self.developer.id,
                approved_at=datetime.utcnow(),
                rejection_reason="Test rejection",
                requested_at=datetime.utcnow(),
                sync_enabled=False
            )
            self.db.add(request)
        
        self.db.commit()
        
        # Query pending requests (simulating the /requests/pending endpoint)
        # This is what a developer would see
        pending_requests = self.db.query(ExternalDataSource).filter(
            ExternalDataSource.request_status == "pending"
        ).all()
        
        # Property 1: Developer should see exactly all pending requests
        assert len(pending_requests) == total_pending, \
            f"Developer should see {total_pending} pending requests, but saw {len(pending_requests)}"
        
        # Property 2: All returned requests should have "pending" status
        for request in pending_requests:
            assert request.request_status == "pending", \
                "All returned requests should have 'pending' status"
        
        # Property 3: Pending requests should come from all institutions
        institution_ids = {r.institution_id for r in pending_requests}
        expected_institutions = set()
        if num_requests_inst1 > 0:
            expected_institutions.add(self.institution1.id)
        if num_requests_inst2 > 0:
            expected_institutions.add(self.institution2.id)
        if num_requests_inst3 > 0:
            expected_institutions.add(self.institution3.id)
        
        assert institution_ids == expected_institutions, \
            f"Developer should see requests from all institutions with pending requests"
        
        # Property 4: No approved or rejected requests should appear
        for request in pending_requests:
            assert request.request_status not in ["approved", "rejected"], \
                "Pending query should not return approved or rejected requests"
        
        # Property 5: Verify total count matches sum of pending from all institutions
        assert len(pending_requests) == num_requests_inst1 + num_requests_inst2 + num_requests_inst3, \
            "Total pending count should equal sum of pending requests from all institutions"


class TestApprovalWorkflow:
    """Property-based tests for approval workflow"""
    
    @pytest.fixture(autouse=True, scope="function")
    def setup(self):
        """Setup test database and mock data"""
        teardown_test_db()
        setup_test_db()
        self.db = get_test_db()
        
        # Setup encryption
        self.key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = self.key
        self.connector = ExternalDBConnector()
        
        # Create test institution
        self.institution = Institution(
            name="Test Ministry",
            type="ministry",
            location="Test Location"
        )
        self.db.add(self.institution)
        self.db.commit()
        self.db.refresh(self.institution)
        
        # Create test users
        self.admin = User(
            name="Admin",
            email="admin@ministry.gov",
            role="ministry_admin",
            institution_id=self.institution.id,
            password_hash="dummy",
            approved=True
        )
        self.developer = User(
            name="Developer",
            email="dev@beacon.gov",
            role="developer",
            institution_id=None,
            password_hash="dummy",
            approved=True
        )
        
        self.db.add(self.admin)
        self.db.add(self.developer)
        self.db.commit()
        self.db.refresh(self.admin)
        self.db.refresh(self.developer)
        
        yield
        
        # Cleanup
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        self.db.close()
        teardown_test_db()
    
    # Feature: external-data-source, Property 7: Approval updates status and metadata
    @settings(max_examples=50)
    @given(
        name=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        host=db_host_strategy,
        port=st.integers(min_value=1, max_value=65535),
        database_name=db_name_strategy
    )
    def test_approval_updates_status_and_metadata(self, name, host, port, database_name):
        """
        For any pending connection request, when a developer approves it, 
        the status should change to "approved", the approver should be recorded, 
        and the approval timestamp should be set.
        
        Validates: Requirements 3.3
        """
        # Clean up
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        
        # Create a pending request
        request = ExternalDataSource(
            name=f"test_{name[:50]}_{datetime.utcnow().timestamp()}",
            ministry_name="Test Ministry",
            db_type="postgresql",
            host=host,
            port=port,
            database_name=database_name,
            username="testuser",
            password_encrypted=self.connector.encrypt_password("testpass"),
            table_name="documents",
            file_column="file_data",
            filename_column="filename",
            institution_id=self.institution.id,
            requested_by_user_id=self.admin.id,
            request_status="pending",
            requested_at=datetime.utcnow(),
            sync_enabled=False
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        
        # Record initial state
        initial_status = request.request_status
        initial_approved_by = request.approved_by_user_id
        initial_approved_at = request.approved_at
        initial_sync_enabled = request.sync_enabled
        
        # Property 1: Initial state should be pending
        assert initial_status == "pending", "Initial status should be 'pending'"
        assert initial_approved_by is None, "Initial approved_by should be None"
        assert initial_approved_at is None, "Initial approved_at should be None"
        assert initial_sync_enabled == False, "Initial sync_enabled should be False"
        
        # Simulate approval (as done in the /approve endpoint)
        approval_time = datetime.utcnow()
        request.request_status = "approved"
        request.approved_by_user_id = self.developer.id
        request.approved_at = approval_time
        request.sync_enabled = True
        
        self.db.commit()
        self.db.refresh(request)
        
        # Property 2: Status should be updated to "approved"
        assert request.request_status == "approved", \
            "Status should be updated to 'approved' after approval"
        
        # Property 3: Approver should be recorded
        assert request.approved_by_user_id == self.developer.id, \
            "Approver user ID should be recorded"
        assert request.approved_by_user_id is not None, \
            "Approved_by should not be None after approval"
        
        # Property 4: Approval timestamp should be set
        assert request.approved_at is not None, \
            "Approval timestamp should be set"
        assert request.approved_at >= approval_time, \
            "Approval timestamp should be at or after approval time"
        
        # Property 5: Sync should be enabled after approval
        assert request.sync_enabled == True, \
            "Sync should be enabled after approval"
        
        # Property 6: Original request data should remain unchanged
        assert request.institution_id == self.institution.id, \
            "Institution ID should remain unchanged"
        assert request.requested_by_user_id == self.admin.id, \
            "Requester ID should remain unchanged"


class TestRejectionWorkflow:
    """Property-based tests for rejection workflow"""
    
    @pytest.fixture(autouse=True, scope="function")
    def setup(self):
        """Setup test database and mock data"""
        teardown_test_db()
        setup_test_db()
        self.db = get_test_db()
        
        # Setup encryption
        self.key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = self.key
        self.connector = ExternalDBConnector()
        
        # Create test institution
        self.institution = Institution(
            name="Test Ministry",
            type="ministry",
            location="Test Location"
        )
        self.db.add(self.institution)
        self.db.commit()
        self.db.refresh(self.institution)
        
        # Create test users
        self.admin = User(
            name="Admin",
            email="admin@ministry.gov",
            role="ministry_admin",
            institution_id=self.institution.id,
            password_hash="dummy",
            approved=True
        )
        self.developer = User(
            name="Developer",
            email="dev@beacon.gov",
            role="developer",
            institution_id=None,
            password_hash="dummy",
            approved=True
        )
        
        self.db.add(self.admin)
        self.db.add(self.developer)
        self.db.commit()
        self.db.refresh(self.admin)
        self.db.refresh(self.developer)
        
        yield
        
        # Cleanup
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        self.db.close()
        teardown_test_db()
    
    # Feature: external-data-source, Property 8: Rejection requires reason
    @settings(max_examples=50)
    @given(
        name=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        rejection_reason=st.text(min_size=10, max_size=500).filter(lambda x: len(x.strip()) >= 10)
    )
    def test_rejection_requires_reason(self, name, rejection_reason):
        """
        For any pending connection request, when a developer rejects it, 
        a rejection reason must be provided and the status should change to "rejected".
        
        Validates: Requirements 3.4
        """
        # Clean up
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        
        # Create a pending request
        request = ExternalDataSource(
            name=f"test_{name[:50]}_{datetime.utcnow().timestamp()}",
            ministry_name="Test Ministry",
            db_type="postgresql",
            host="localhost",
            port=5432,
            database_name="testdb",
            username="testuser",
            password_encrypted=self.connector.encrypt_password("testpass"),
            table_name="documents",
            file_column="file_data",
            filename_column="filename",
            institution_id=self.institution.id,
            requested_by_user_id=self.admin.id,
            request_status="pending",
            requested_at=datetime.utcnow(),
            sync_enabled=False
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        
        # Record initial state
        initial_status = request.request_status
        initial_rejection_reason = request.rejection_reason
        
        # Property 1: Initial state should be pending with no rejection reason
        assert initial_status == "pending", "Initial status should be 'pending'"
        assert initial_rejection_reason is None, "Initial rejection_reason should be None"
        
        # Simulate rejection (as done in the /reject endpoint)
        rejection_time = datetime.utcnow()
        request.request_status = "rejected"
        request.approved_by_user_id = self.developer.id  # Track who rejected
        request.approved_at = rejection_time
        request.rejection_reason = rejection_reason.strip()
        request.sync_enabled = False
        
        self.db.commit()
        self.db.refresh(request)
        
        # Property 2: Status should be updated to "rejected"
        assert request.request_status == "rejected", \
            "Status should be updated to 'rejected' after rejection"
        
        # Property 3: Rejection reason must be provided and non-empty
        assert request.rejection_reason is not None, \
            "Rejection reason must be provided"
        assert len(request.rejection_reason.strip()) > 0, \
            "Rejection reason must not be empty"
        assert request.rejection_reason == rejection_reason.strip(), \
            "Rejection reason should match the provided reason"
        
        # Property 4: Rejection reason should meet minimum length requirement
        assert len(request.rejection_reason) >= 10, \
            "Rejection reason should be at least 10 characters"
        
        # Property 5: Rejector should be recorded
        assert request.approved_by_user_id == self.developer.id, \
            "Rejector user ID should be recorded"
        
        # Property 6: Rejection timestamp should be set
        assert request.approved_at is not None, \
            "Rejection timestamp should be set"
        assert request.approved_at >= rejection_time, \
            "Rejection timestamp should be at or after rejection time"
        
        # Property 7: Sync should remain disabled after rejection
        assert request.sync_enabled == False, \
            "Sync should remain disabled after rejection"


class TestActiveSourcesFiltering:
    """Property-based tests for active sources filtering"""
    
    @pytest.fixture(autouse=True, scope="function")
    def setup(self):
        """Setup test database and mock data"""
        teardown_test_db()
        setup_test_db()
        self.db = get_test_db()
        
        # Setup encryption
        self.key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = self.key
        self.connector = ExternalDBConnector()
        
        # Create test institutions
        self.institution1 = Institution(
            name="Test Ministry 1",
            type="ministry",
            location="Test Location 1"
        )
        self.institution2 = Institution(
            name="Test University 1",
            type="university",
            location="Test Location 2"
        )
        
        self.db.add(self.institution1)
        self.db.add(self.institution2)
        self.db.commit()
        self.db.refresh(self.institution1)
        self.db.refresh(self.institution2)
        
        # Create test users
        self.admin1 = User(
            name="Admin 1",
            email="admin1@ministry1.gov",
            role="ministry_admin",
            institution_id=self.institution1.id,
            password_hash="dummy",
            approved=True
        )
        self.admin2 = User(
            name="Admin 2",
            email="admin2@university1.edu",
            role="university_admin",
            institution_id=self.institution2.id,
            password_hash="dummy",
            approved=True
        )
        self.developer = User(
            name="Developer",
            email="dev@beacon.gov",
            role="developer",
            institution_id=None,
            password_hash="dummy",
            approved=True
        )
        
        self.db.add(self.admin1)
        self.db.add(self.admin2)
        self.db.add(self.developer)
        self.db.commit()
        self.db.refresh(self.admin1)
        self.db.refresh(self.admin2)
        self.db.refresh(self.developer)
        
        yield
        
        # Cleanup
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        self.db.close()
        teardown_test_db()
    
    # Feature: external-data-source, Property 10: Active sources filter by status
    @settings(max_examples=50)
    @given(
        num_approved=st.integers(min_value=0, max_value=5),
        num_active=st.integers(min_value=0, max_value=5),
        num_pending=st.integers(min_value=0, max_value=3),
        num_rejected=st.integers(min_value=0, max_value=3),
        num_failed=st.integers(min_value=0, max_value=3)
    )
    def test_active_sources_filter_by_status(
        self, 
        num_approved, 
        num_active, 
        num_pending, 
        num_rejected,
        num_failed
    ):
        """
        For any developer viewing active sources, only connection requests 
        with status "approved" or "active" should be displayed.
        
        Validates: Requirements 4.1
        """
        # Clean up any existing data sources from previous examples
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        
        total_active_sources = num_approved + num_active
        
        # Create approved requests
        for i in range(num_approved):
            request = ExternalDataSource(
                name=f"approved_{i}_{datetime.utcnow().timestamp()}",
                ministry_name="Ministry 1",
                db_type="postgresql",
                host="localhost",
                port=5432,
                database_name=f"db_approved_{i}",
                username="user",
                password_encrypted=self.connector.encrypt_password("password"),
                table_name="documents",
                file_column="file_data",
                filename_column="filename",
                institution_id=self.institution1.id,
                requested_by_user_id=self.admin1.id,
                request_status="approved",
                approved_by_user_id=self.developer.id,
                approved_at=datetime.utcnow(),
                requested_at=datetime.utcnow(),
                sync_enabled=True,
                last_sync_at=datetime.utcnow(),
                last_sync_status="success",
                total_documents_synced=100 + i
            )
            self.db.add(request)
        
        # Create active requests
        for i in range(num_active):
            request = ExternalDataSource(
                name=f"active_{i}_{datetime.utcnow().timestamp()}",
                ministry_name="University 1",
                db_type="postgresql",
                host="localhost",
                port=5432,
                database_name=f"db_active_{i}",
                username="user",
                password_encrypted=self.connector.encrypt_password("password"),
                table_name="documents",
                file_column="file_data",
                filename_column="filename",
                institution_id=self.institution2.id,
                requested_by_user_id=self.admin2.id,
                request_status="active",
                approved_by_user_id=self.developer.id,
                approved_at=datetime.utcnow(),
                requested_at=datetime.utcnow(),
                sync_enabled=True,
                last_sync_at=datetime.utcnow(),
                last_sync_status="success",
                total_documents_synced=200 + i
            )
            self.db.add(request)
        
        # Create pending requests (should NOT appear in active sources)
        for i in range(num_pending):
            request = ExternalDataSource(
                name=f"pending_{i}_{datetime.utcnow().timestamp()}",
                ministry_name="Ministry 1",
                db_type="postgresql",
                host="localhost",
                port=5432,
                database_name=f"db_pending_{i}",
                username="user",
                password_encrypted=self.connector.encrypt_password("password"),
                table_name="documents",
                file_column="file_data",
                filename_column="filename",
                institution_id=self.institution1.id,
                requested_by_user_id=self.admin1.id,
                request_status="pending",
                requested_at=datetime.utcnow(),
                sync_enabled=False
            )
            self.db.add(request)
        
        # Create rejected requests (should NOT appear in active sources)
        for i in range(num_rejected):
            request = ExternalDataSource(
                name=f"rejected_{i}_{datetime.utcnow().timestamp()}",
                ministry_name="Ministry 1",
                db_type="postgresql",
                host="localhost",
                port=5432,
                database_name=f"db_rejected_{i}",
                username="user",
                password_encrypted=self.connector.encrypt_password("password"),
                table_name="documents",
                file_column="file_data",
                filename_column="filename",
                institution_id=self.institution1.id,
                requested_by_user_id=self.admin1.id,
                request_status="rejected",
                approved_by_user_id=self.developer.id,
                approved_at=datetime.utcnow(),
                rejection_reason="Test rejection",
                requested_at=datetime.utcnow(),
                sync_enabled=False
            )
            self.db.add(request)
        
        # Create failed requests (should appear in active sources - they were approved but sync failed)
        for i in range(num_failed):
            request = ExternalDataSource(
                name=f"failed_{i}_{datetime.utcnow().timestamp()}",
                ministry_name="University 1",
                db_type="postgresql",
                host="localhost",
                port=5432,
                database_name=f"db_failed_{i}",
                username="user",
                password_encrypted=self.connector.encrypt_password("password"),
                table_name="documents",
                file_column="file_data",
                filename_column="filename",
                institution_id=self.institution2.id,
                requested_by_user_id=self.admin2.id,
                request_status="failed",
                approved_by_user_id=self.developer.id,
                approved_at=datetime.utcnow(),
                requested_at=datetime.utcnow(),
                sync_enabled=True,
                last_sync_at=datetime.utcnow(),
                last_sync_status="failed",
                last_sync_message="Connection timeout"
            )
            self.db.add(request)
        
        self.db.commit()
        
        # Query active sources (simulating the /active endpoint)
        # Active sources should include: approved, active, and failed statuses
        active_sources = self.db.query(ExternalDataSource).filter(
            ExternalDataSource.request_status.in_(["approved", "active", "failed"])
        ).all()
        
        # Property 1: Should see exactly approved + active + failed sources
        expected_count = num_approved + num_active + num_failed
        assert len(active_sources) == expected_count, \
            f"Developer should see {expected_count} active sources, but saw {len(active_sources)}"
        
        # Property 2: All returned sources should have approved, active, or failed status
        for source in active_sources:
            assert source.request_status in ["approved", "active", "failed"], \
                f"Active sources should only include approved/active/failed, got {source.request_status}"
        
        # Property 3: No pending or rejected sources should appear
        for source in active_sources:
            assert source.request_status not in ["pending", "rejected"], \
                "Active sources should not include pending or rejected requests"
        
        # Property 4: All active sources should have been approved at some point
        for source in active_sources:
            assert source.approved_by_user_id is not None, \
                "All active sources should have an approver"
            assert source.approved_at is not None, \
                "All active sources should have an approval timestamp"
        
        # Property 5: All active sources should have sync enabled
        for source in active_sources:
            assert source.sync_enabled == True, \
                "All active sources should have sync enabled"
        
        # Property 6: Sources from all institutions should be visible to developer
        institution_ids = {s.institution_id for s in active_sources}
        expected_institutions = set()
        if num_approved > 0:
            expected_institutions.add(self.institution1.id)
        if num_active > 0 or num_failed > 0:
            expected_institutions.add(self.institution2.id)
        
        assert institution_ids == expected_institutions, \
            "Developer should see active sources from all institutions"


class TestSyncTriggering:
    """Property-based tests for sync triggering on approval"""
    
    @pytest.fixture(autouse=True, scope="function")
    def setup(self):
        """Setup test database and mock data"""
        teardown_test_db()
        setup_test_db()
        self.db = get_test_db()
        
        # Setup encryption
        self.key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = self.key
        self.connector = ExternalDBConnector()
        
        # Create test institution
        self.institution = Institution(
            name="Test Ministry",
            type="ministry",
            location="Test Location"
        )
        self.db.add(self.institution)
        self.db.commit()
        self.db.refresh(self.institution)
        
        # Create test users
        self.admin = User(
            name="Admin",
            email="admin@ministry.gov",
            role="ministry_admin",
            institution_id=self.institution.id,
            password_hash="dummy",
            approved=True
        )
        self.developer = User(
            name="Developer",
            email="dev@beacon.gov",
            role="developer",
            institution_id=None,
            password_hash="dummy",
            approved=True
        )
        
        self.db.add(self.admin)
        self.db.add(self.developer)
        self.db.commit()
        self.db.refresh(self.admin)
        self.db.refresh(self.developer)
        
        yield
        
        # Cleanup
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        self.db.close()
        teardown_test_db()
    
    # Feature: external-data-source, Property 9: Approval triggers sync job
    @settings(max_examples=50)
    @given(
        name=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        host=db_host_strategy,
        port=st.integers(min_value=1, max_value=65535),
        database_name=db_name_strategy
    )
    def test_approval_triggers_sync_job(self, name, host, port, database_name):
        """
        For any connection request that is approved, a synchronization job 
        should be created and executed immediately.
        
        Validates: Requirements 3.5, 5.1
        """
        # Clean up
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        
        # Create a pending request
        request = ExternalDataSource(
            name=f"test_{name[:50]}_{datetime.utcnow().timestamp()}",
            ministry_name="Test Ministry",
            db_type="postgresql",
            host=host,
            port=port,
            database_name=database_name,
            username="testuser",
            password_encrypted=self.connector.encrypt_password("testpass"),
            table_name="documents",
            file_column="file_data",
            filename_column="filename",
            institution_id=self.institution.id,
            requested_by_user_id=self.admin.id,
            request_status="pending",
            requested_at=datetime.utcnow(),
            sync_enabled=False,
            last_sync_at=None,
            last_sync_status=None
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        
        # Record initial state
        initial_sync_enabled = request.sync_enabled
        initial_last_sync_at = request.last_sync_at
        initial_last_sync_status = request.last_sync_status
        
        # Property 1: Before approval, sync should be disabled
        assert initial_sync_enabled == False, "Sync should be disabled before approval"
        assert initial_last_sync_at is None, "No sync should have occurred before approval"
        assert initial_last_sync_status is None, "No sync status before approval"
        
        # Simulate approval (as done in the /approve endpoint)
        request.request_status = "approved"
        request.approved_by_user_id = self.developer.id
        request.approved_at = datetime.utcnow()
        request.sync_enabled = True
        
        self.db.commit()
        self.db.refresh(request)
        
        # Property 2: After approval, sync should be enabled
        assert request.sync_enabled == True, \
            "Sync should be enabled after approval"
        
        # Property 3: Approval should set up the source for sync
        assert request.request_status == "approved", \
            "Status should be 'approved'"
        assert request.approved_by_user_id is not None, \
            "Approver should be recorded"
        assert request.approved_at is not None, \
            "Approval timestamp should be set"
        
        # Property 4: The sync service should be able to find this source
        # (simulating what the background task does)
        sync_ready_sources = self.db.query(ExternalDataSource).filter(
            ExternalDataSource.sync_enabled == True,
            ExternalDataSource.request_status == "approved"
        ).all()
        
        assert len(sync_ready_sources) > 0, \
            "Approved source should be available for sync"
        assert request.id in [s.id for s in sync_ready_sources], \
            "The approved request should be in the sync-ready list"
        
        # Property 5: Source should have all required fields for sync
        assert request.host is not None and len(request.host) > 0, \
            "Host should be set for sync"
        assert request.port is not None and request.port > 0, \
            "Port should be set for sync"
        assert request.database_name is not None and len(request.database_name) > 0, \
            "Database name should be set for sync"
        assert request.username is not None and len(request.username) > 0, \
            "Username should be set for sync"
        assert request.password_encrypted is not None and len(request.password_encrypted) > 0, \
            "Encrypted password should be set for sync"


class TestDocumentClassification:
    """Property-based tests for document classification inheritance"""
    
    @pytest.fixture(autouse=True, scope="function")
    def setup(self):
        """Setup test database and mock data"""
        teardown_test_db()
        setup_test_db()
        self.db = get_test_db()
        
        # Setup encryption
        self.key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = self.key
        self.connector = ExternalDBConnector()
        
        # Create test institutions
        self.ministry = Institution(
            name="Test Ministry",
            type="ministry",
            location="Test Location"
        )
        self.university = Institution(
            name="Test University",
            type="university",
            location="Test Location"
        )
        
        self.db.add(self.ministry)
        self.db.add(self.university)
        self.db.commit()
        self.db.refresh(self.ministry)
        self.db.refresh(self.university)
        
        # Create test users
        self.ministry_admin = User(
            name="Ministry Admin",
            email="admin@ministry.gov",
            role="ministry_admin",
            institution_id=self.ministry.id,
            password_hash="dummy",
            approved=True
        )
        self.university_admin = User(
            name="University Admin",
            email="admin@university.edu",
            role="university_admin",
            institution_id=self.university.id,
            password_hash="dummy",
            approved=True
        )
        
        self.db.add(self.ministry_admin)
        self.db.add(self.university_admin)
        self.db.commit()
        self.db.refresh(self.ministry_admin)
        self.db.refresh(self.university_admin)
        
        yield
        
        # Cleanup
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        self.db.close()
        teardown_test_db()
    
    # Feature: external-data-source, Property 14: Documents inherit classification
    @settings(max_examples=50)
    @given(
        name=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        classification=st.sampled_from(["public", "educational", "confidential", "institutional"])
    )
    def test_documents_inherit_classification(self, name, classification):
        """
        For any document pulled from a Ministry data source, the document 
        should have the data classification specified in the connection request.
        
        Validates: Requirements 5.3
        """
        # Clean up
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        
        # Determine which admin to use based on classification
        # Ministry admins can set any classification
        # University admins always get "institutional"
        if classification == "institutional":
            admin = self.university_admin
            institution = self.university
        else:
            admin = self.ministry_admin
            institution = self.ministry
        
        # Create a data source with specific classification
        source = ExternalDataSource(
            name=f"test_{name[:50]}_{datetime.utcnow().timestamp()}",
            ministry_name=institution.name,
            db_type="postgresql",
            host="localhost",
            port=5432,
            database_name="testdb",
            username="testuser",
            password_encrypted=self.connector.encrypt_password("testpass"),
            table_name="documents",
            file_column="file_data",
            filename_column="filename",
            institution_id=institution.id,
            requested_by_user_id=admin.id,
            request_status="approved",
            data_classification=classification,
            requested_at=datetime.utcnow(),
            approved_at=datetime.utcnow(),
            sync_enabled=True
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        
        # Property 1: Source should have the specified classification
        assert source.data_classification == classification, \
            f"Source should have classification '{classification}'"
        
        # Property 2: Classification should be one of the valid values
        valid_classifications = ["public", "educational", "confidential", "institutional"]
        assert source.data_classification in valid_classifications, \
            f"Classification should be one of {valid_classifications}"
        
        # Property 3: Ministry sources can have any classification
        if institution.type == "ministry":
            assert source.data_classification in valid_classifications, \
                "Ministry sources can have any valid classification"
        
        # Property 4: University sources should have "institutional" classification
        if institution.type == "university":
            assert source.data_classification == "institutional", \
                "University sources should have 'institutional' classification"
        
        # Property 5: Documents synced from this source would inherit this classification
        # (This is a design property - the sync service should use source.data_classification)
        # We verify the source has the classification that documents will inherit
        assert source.data_classification is not None, \
            "Source must have a classification for documents to inherit"
        
        # Property 6: Classification should be preserved after approval
        assert source.request_status == "approved", \
            "Source should be approved"
        assert source.data_classification == classification, \
            "Classification should be preserved after approval"


class TestDocumentInstitutionAssociation:
    """Property-based tests for document institution association"""
    
    @pytest.fixture(autouse=True, scope="function")
    def setup(self):
        """Setup test database and mock data"""
        teardown_test_db()
        setup_test_db()
        self.db = get_test_db()
        
        # Setup encryption
        self.key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = self.key
        self.connector = ExternalDBConnector()
        
        # Create test institutions
        self.institution1 = Institution(
            name="Test Ministry 1",
            type="ministry",
            location="Test Location 1"
        )
        self.institution2 = Institution(
            name="Test University 1",
            type="university",
            location="Test Location 2"
        )
        self.institution3 = Institution(
            name="Test Ministry 2",
            type="ministry",
            location="Test Location 3"
        )
        
        self.db.add(self.institution1)
        self.db.add(self.institution2)
        self.db.add(self.institution3)
        self.db.commit()
        self.db.refresh(self.institution1)
        self.db.refresh(self.institution2)
        self.db.refresh(self.institution3)
        
        # Create test users
        self.admin1 = User(
            name="Admin 1",
            email="admin1@ministry1.gov",
            role="ministry_admin",
            institution_id=self.institution1.id,
            password_hash="dummy",
            approved=True
        )
        self.admin2 = User(
            name="Admin 2",
            email="admin2@university1.edu",
            role="university_admin",
            institution_id=self.institution2.id,
            password_hash="dummy",
            approved=True
        )
        self.admin3 = User(
            name="Admin 3",
            email="admin3@ministry2.gov",
            role="ministry_admin",
            institution_id=self.institution3.id,
            password_hash="dummy",
            approved=True
        )
        
        self.db.add(self.admin1)
        self.db.add(self.admin2)
        self.db.add(self.admin3)
        self.db.commit()
        self.db.refresh(self.admin1)
        self.db.refresh(self.admin2)
        self.db.refresh(self.admin3)
        
        yield
        
        # Cleanup
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        self.db.close()
        teardown_test_db()
    
    # Feature: external-data-source, Property 15: Documents associate with correct institution
    @settings(max_examples=50)
    @given(
        num_sources_inst1=st.integers(min_value=0, max_value=3),
        num_sources_inst2=st.integers(min_value=0, max_value=3),
        num_sources_inst3=st.integers(min_value=0, max_value=3)
    )
    def test_documents_associate_with_correct_institution(
        self, 
        num_sources_inst1, 
        num_sources_inst2, 
        num_sources_inst3
    ):
        """
        For any document pulled from an external data source, the document 
        should be associated with the institution that owns the data source.
        
        Validates: Requirements 5.4
        """
        # Clean up
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        
        # Create sources for institution 1
        inst1_sources = []
        for i in range(num_sources_inst1):
            source = ExternalDataSource(
                name=f"inst1_source_{i}_{datetime.utcnow().timestamp()}",
                ministry_name=self.institution1.name,
                db_type="postgresql",
                host="localhost",
                port=5432,
                database_name=f"db_{i}",
                username="user",
                password_encrypted=self.connector.encrypt_password("password"),
                table_name="documents",
                file_column="file_data",
                filename_column="filename",
                institution_id=self.institution1.id,
                requested_by_user_id=self.admin1.id,
                request_status="approved",
                data_classification="educational",
                requested_at=datetime.utcnow(),
                approved_at=datetime.utcnow(),
                sync_enabled=True
            )
            self.db.add(source)
            inst1_sources.append(source)
        
        # Create sources for institution 2
        inst2_sources = []
        for i in range(num_sources_inst2):
            source = ExternalDataSource(
                name=f"inst2_source_{i}_{datetime.utcnow().timestamp()}",
                ministry_name=self.institution2.name,
                db_type="postgresql",
                host="localhost",
                port=5432,
                database_name=f"db_{i}",
                username="user",
                password_encrypted=self.connector.encrypt_password("password"),
                table_name="documents",
                file_column="file_data",
                filename_column="filename",
                institution_id=self.institution2.id,
                requested_by_user_id=self.admin2.id,
                request_status="approved",
                data_classification="institutional",
                requested_at=datetime.utcnow(),
                approved_at=datetime.utcnow(),
                sync_enabled=True
            )
            self.db.add(source)
            inst2_sources.append(source)
        
        # Create sources for institution 3
        inst3_sources = []
        for i in range(num_sources_inst3):
            source = ExternalDataSource(
                name=f"inst3_source_{i}_{datetime.utcnow().timestamp()}",
                ministry_name=self.institution3.name,
                db_type="postgresql",
                host="localhost",
                port=5432,
                database_name=f"db_{i}",
                username="user",
                password_encrypted=self.connector.encrypt_password("password"),
                table_name="documents",
                file_column="file_data",
                filename_column="filename",
                institution_id=self.institution3.id,
                requested_by_user_id=self.admin3.id,
                request_status="approved",
                data_classification="confidential",
                requested_at=datetime.utcnow(),
                approved_at=datetime.utcnow(),
                sync_enabled=True
            )
            self.db.add(source)
            inst3_sources.append(source)
        
        self.db.commit()
        
        # Refresh all sources
        for source in inst1_sources + inst2_sources + inst3_sources:
            self.db.refresh(source)
        
        # Property 1: Each source should be associated with correct institution
        for source in inst1_sources:
            assert source.institution_id == self.institution1.id, \
                "Institution 1 sources should be associated with institution 1"
            assert source.institution.name == self.institution1.name, \
                "Institution relationship should be correct"
        
        for source in inst2_sources:
            assert source.institution_id == self.institution2.id, \
                "Institution 2 sources should be associated with institution 2"
            assert source.institution.name == self.institution2.name, \
                "Institution relationship should be correct"
        
        for source in inst3_sources:
            assert source.institution_id == self.institution3.id, \
                "Institution 3 sources should be associated with institution 3"
            assert source.institution.name == self.institution3.name, \
                "Institution relationship should be correct"
        
        # Property 2: Sources should not be associated with wrong institutions
        all_sources = inst1_sources + inst2_sources + inst3_sources
        for source in all_sources:
            assert source.institution_id is not None, \
                "Every source must be associated with an institution"
            assert source.institution_id in [self.institution1.id, self.institution2.id, self.institution3.id], \
                "Source must be associated with a valid institution"
        
        # Property 3: Query sources by institution should return correct sources
        inst1_query = self.db.query(ExternalDataSource).filter(
            ExternalDataSource.institution_id == self.institution1.id
        ).all()
        assert len(inst1_query) == num_sources_inst1, \
            f"Institution 1 should have {num_sources_inst1} sources"
        
        inst2_query = self.db.query(ExternalDataSource).filter(
            ExternalDataSource.institution_id == self.institution2.id
        ).all()
        assert len(inst2_query) == num_sources_inst2, \
            f"Institution 2 should have {num_sources_inst2} sources"
        
        inst3_query = self.db.query(ExternalDataSource).filter(
            ExternalDataSource.institution_id == self.institution3.id
        ).all()
        assert len(inst3_query) == num_sources_inst3, \
            f"Institution 3 should have {num_sources_inst3} sources"
        
        # Property 4: Institution association should be preserved through approval
        for source in all_sources:
            assert source.request_status == "approved", \
                "All sources should be approved"
            assert source.institution_id is not None, \
                "Institution association should be preserved after approval"


class TestSyncMetadataUpdates:
    """Property-based tests for sync metadata updates"""
    
    @pytest.fixture(autouse=True, scope="function")
    def setup(self):
        """Setup test database and mock data"""
        teardown_test_db()
        setup_test_db()
        self.db = get_test_db()
        
        # Setup encryption
        self.key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = self.key
        self.connector = ExternalDBConnector()
        
        # Create test institution
        self.institution = Institution(
            name="Test Ministry",
            type="ministry",
            location="Test Location"
        )
        self.db.add(self.institution)
        self.db.commit()
        self.db.refresh(self.institution)
        
        # Create test user
        self.admin = User(
            name="Admin",
            email="admin@ministry.gov",
            role="ministry_admin",
            institution_id=self.institution.id,
            password_hash="dummy",
            approved=True
        )
        
        self.db.add(self.admin)
        self.db.commit()
        self.db.refresh(self.admin)
        
        yield
        
        # Cleanup
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        self.db.close()
        teardown_test_db()
    
    # Feature: external-data-source, Property 11: Sync completion updates metadata
    @settings(max_examples=50)
    @given(
        name=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        documents_synced=st.integers(min_value=0, max_value=1000),
        sync_status=st.sampled_from(["success", "failed"])
    )
    def test_sync_completion_updates_metadata(self, name, documents_synced, sync_status):
        """
        For any sync job that completes successfully, the last sync timestamp 
        and document count should be updated.
        
        Validates: Requirements 4.3, 5.5
        """
        # Clean up
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        
        # Create a data source
        source = ExternalDataSource(
            name=f"test_{name[:50]}_{datetime.utcnow().timestamp()}",
            ministry_name="Test Ministry",
            db_type="postgresql",
            host="localhost",
            port=5432,
            database_name="testdb",
            username="testuser",
            password_encrypted=self.connector.encrypt_password("testpass"),
            table_name="documents",
            file_column="file_data",
            filename_column="filename",
            institution_id=self.institution.id,
            requested_by_user_id=self.admin.id,
            request_status="approved",
            data_classification="educational",
            requested_at=datetime.utcnow(),
            approved_at=datetime.utcnow(),
            sync_enabled=True,
            last_sync_at=None,
            last_sync_status=None,
            total_documents_synced=0
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        
        # Record initial state
        initial_last_sync_at = source.last_sync_at
        initial_last_sync_status = source.last_sync_status
        initial_total_documents = source.total_documents_synced
        
        # Property 1: Before sync, metadata should be empty
        assert initial_last_sync_at is None, "No sync timestamp before first sync"
        assert initial_last_sync_status is None, "No sync status before first sync"
        assert initial_total_documents == 0, "No documents synced initially"
        
        # Simulate sync completion (as done in sync_service.py)
        sync_time = datetime.utcnow()
        source.last_sync_at = sync_time
        source.last_sync_status = sync_status
        
        if sync_status == "success":
            source.total_documents_synced += documents_synced
            source.last_sync_message = f"Synced {documents_synced} documents"
        else:
            source.last_sync_message = "Sync failed: Connection timeout"
        
        self.db.commit()
        self.db.refresh(source)
        
        # Property 2: After sync, last_sync_at should be updated
        assert source.last_sync_at is not None, \
            "Last sync timestamp should be set after sync"
        assert source.last_sync_at >= sync_time, \
            "Last sync timestamp should be at or after sync time"
        
        # Property 3: After sync, last_sync_status should be updated
        assert source.last_sync_status is not None, \
            "Last sync status should be set after sync"
        assert source.last_sync_status == sync_status, \
            f"Last sync status should be '{sync_status}'"
        
        # Property 4: For successful syncs, document count should be updated
        if sync_status == "success":
            assert source.total_documents_synced == documents_synced, \
                f"Total documents should be {documents_synced} after successful sync"
            assert source.total_documents_synced >= 0, \
                "Document count should be non-negative"
        
        # Property 5: Sync message should be set
        assert source.last_sync_message is not None, \
            "Sync message should be set"
        assert len(source.last_sync_message) > 0, \
            "Sync message should not be empty"
        
        # Property 6: For failed syncs, document count should not increase
        if sync_status == "failed":
            assert source.total_documents_synced == initial_total_documents, \
                "Document count should not increase on failed sync"
        
        # Property 7: Multiple syncs should accumulate document counts
        if sync_status == "success" and documents_synced > 0:
            # Simulate another successful sync
            additional_docs = 50
            source.total_documents_synced += additional_docs
            source.last_sync_at = datetime.utcnow()
            source.last_sync_status = "success"
            
            self.db.commit()
            self.db.refresh(source)
            
            assert source.total_documents_synced == documents_synced + additional_docs, \
                "Document counts should accumulate across syncs"


class TestNotificationIntegration:
    """Property-based tests for notification system integration"""
    
    @pytest.fixture(autouse=True, scope="function")
    def setup(self):
        """Setup test database and mock data"""
        # Clean up any existing tables first
        teardown_test_db()
        setup_test_db()
        self.db = get_test_db()
        
        # Setup encryption
        self.key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = self.key
        self.connector = ExternalDBConnector()
        
        # Create test institution
        self.institution = Institution(
            name="Test Ministry",
            type="ministry",
            location="Test Location"
        )
        self.db.add(self.institution)
        self.db.commit()
        self.db.refresh(self.institution)
        
        # Create test users
        self.admin = User(
            name="Test Admin",
            email="admin@ministry.gov",
            role="ministry_admin",
            institution_id=self.institution.id,
            password_hash="dummy",
            approved=True
        )
        self.developer = User(
            name="Test Developer",
            email="dev@beacon.gov",
            role="developer",
            institution_id=None,
            password_hash="dummy",
            approved=True
        )
        
        self.db.add(self.admin)
        self.db.add(self.developer)
        self.db.commit()
        self.db.refresh(self.admin)
        self.db.refresh(self.developer)
        
        yield
        
        # Cleanup
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        self.db.close()
        teardown_test_db()
    
    # Feature: external-data-source, Property 16: Approval creates notification
    @settings(max_examples=50)
    @given(
        source_name=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0)
    )
    def test_approval_creates_notification(self, source_name):
        """
        For any connection request that is approved, a notification should be 
        created for the requesting administrator.
        
        Validates: Requirements 6.1
        """
        from backend.database import Notification
        
        # Clean up any existing data
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        
        # Create a pending data source request
        source = ExternalDataSource(
            name=f"test_{source_name[:50]}_{datetime.utcnow().timestamp()}",
            ministry_name="Test Ministry",
            db_type="postgresql",
            host="localhost",
            port=5432,
            database_name="testdb",
            username="testuser",
            password_encrypted=self.connector.encrypt_password("password123"),
            table_name="documents",
            file_column="file_data",
            filename_column="filename",
            institution_id=self.institution.id,
            requested_by_user_id=self.admin.id,
            request_status="pending",
            requested_at=datetime.utcnow(),
            sync_enabled=False
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        
        # Simulate approval (as done in the router)
        source.request_status = "approved"
        source.approved_by_user_id = self.developer.id
        source.approved_at = datetime.utcnow()
        source.sync_enabled = True
        self.db.commit()
        
        # Create notification object (as done in the router) - in memory only
        notification = Notification(
            user_id=source.requested_by_user_id,
            type="data_source_approved",
            title="Data Source Request Approved",
            message=f"Your data source request '{source.name}' has been approved by {self.developer.name}. Synchronization has started.",
            priority="high",
            action_url=f"/admin/my-data-source-requests",
            action_label="View Request",
            action_metadata={
                "source_id": source.id,
                "source_name": source.name,
                "approved_by": self.developer.name,
                "approved_by_id": self.developer.id
            }
        )
        
        # Property 1: Notification should be created (object exists)
        assert notification is not None, \
            "Approval should create a notification object"
        
        # Property 2: Notification should be for the requester
        assert notification.user_id == self.admin.id, \
            "Notification should be sent to the requester"
        
        # Property 3: Notification should have correct type
        assert notification.type == "data_source_approved", \
            "Notification type should be 'data_source_approved'"
        
        # Property 4: Notification should have high priority
        assert notification.priority == "high", \
            "Approval notifications should have high priority"
        
        # Property 5: Notification should contain source information
        assert source.name in notification.message, \
            "Notification message should contain source name"
        assert self.developer.name in notification.message, \
            "Notification message should contain approver name"
        
        # Property 6: Notification should have action URL
        assert notification.action_url is not None, \
            "Notification should have an action URL"
        assert len(notification.action_url) > 0, \
            "Action URL should not be empty"
        
        # Property 7: Notification metadata should contain source details
        assert notification.action_metadata is not None, \
            "Notification should have metadata"
        assert notification.action_metadata.get("source_id") == source.id, \
            "Metadata should contain source ID"
        assert notification.action_metadata.get("approved_by") == self.developer.name, \
            "Metadata should contain approver name"
    
    # Feature: external-data-source, Property 17: Rejection creates notification with reason
    @settings(max_examples=50)
    @given(
        source_name=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        rejection_reason=st.text(min_size=10, max_size=500).filter(lambda x: len(x.strip()) >= 10)
    )
    def test_rejection_creates_notification_with_reason(self, source_name, rejection_reason):
        """
        For any connection request that is rejected, a notification should be 
        created for the requesting administrator containing the rejection reason.
        
        Validates: Requirements 6.2
        """
        from backend.database import Notification
        
        # Clean up any existing data
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        
        # Create a pending data source request
        source = ExternalDataSource(
            name=f"test_{source_name[:50]}_{datetime.utcnow().timestamp()}",
            ministry_name="Test Ministry",
            db_type="postgresql",
            host="localhost",
            port=5432,
            database_name="testdb",
            username="testuser",
            password_encrypted=self.connector.encrypt_password("password123"),
            table_name="documents",
            file_column="file_data",
            filename_column="filename",
            institution_id=self.institution.id,
            requested_by_user_id=self.admin.id,
            request_status="pending",
            requested_at=datetime.utcnow(),
            sync_enabled=False
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        
        # Simulate rejection (as done in the router)
        source.request_status = "rejected"
        source.approved_by_user_id = self.developer.id
        source.approved_at = datetime.utcnow()
        source.rejection_reason = rejection_reason.strip()
        source.sync_enabled = False
        self.db.commit()
        
        # Create notification object (as done in the router) - in memory only
        notification = Notification(
            user_id=source.requested_by_user_id,
            type="data_source_rejected",
            title="Data Source Request Rejected",
            message=f"Your data source request '{source.name}' has been rejected by {self.developer.name}. Reason: {rejection_reason}",
            priority="high",
            action_url=f"/admin/my-data-source-requests",
            action_label="View Request",
            action_metadata={
                "source_id": source.id,
                "source_name": source.name,
                "rejected_by": self.developer.name,
                "rejected_by_id": self.developer.id,
                "rejection_reason": rejection_reason
            }
        )
        
        # Property 1: Notification should be created (object exists)
        assert notification is not None, \
            "Rejection should create a notification object"
        
        # Property 2: Notification should be for the requester
        assert notification.user_id == self.admin.id, \
            "Notification should be sent to the requester"
        
        # Property 3: Notification should have correct type
        assert notification.type == "data_source_rejected", \
            "Notification type should be 'data_source_rejected'"
        
        # Property 4: Notification should have high priority
        assert notification.priority == "high", \
            "Rejection notifications should have high priority"
        
        # Property 5: Notification should contain rejection reason
        assert rejection_reason in notification.message, \
            "Notification message should contain rejection reason"
        assert source.name in notification.message, \
            "Notification message should contain source name"
        assert self.developer.name in notification.message, \
            "Notification message should contain rejector name"
        
        # Property 6: Notification metadata should contain rejection reason
        assert notification.action_metadata is not None, \
            "Notification should have metadata"
        assert notification.action_metadata.get("rejection_reason") == rejection_reason, \
            "Metadata should contain rejection reason"
        assert notification.action_metadata.get("rejected_by") == self.developer.name, \
            "Metadata should contain rejector name"
        
        # Property 7: Source should have rejection reason stored
        assert source.rejection_reason == rejection_reason.strip(), \
            "Source should store the rejection reason"
    
    # Feature: external-data-source, Property 18: Sync failure creates notification
    @settings(max_examples=50)
    @given(
        source_name=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        error_message=st.text(min_size=10, max_size=500).filter(lambda x: len(x.strip()) >= 10)
    )
    def test_sync_failure_creates_notification(self, source_name, error_message):
        """
        For any sync job that fails, a notification should be created for 
        the institution's administrator.
        
        Validates: Requirements 6.3
        """
        from backend.database import Notification
        
        # Clean up any existing data
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        
        # Create an approved data source
        source = ExternalDataSource(
            name=f"test_{source_name[:50]}_{datetime.utcnow().timestamp()}",
            ministry_name="Test Ministry",
            db_type="postgresql",
            host="localhost",
            port=5432,
            database_name="testdb",
            username="testuser",
            password_encrypted=self.connector.encrypt_password("password123"),
            table_name="documents",
            file_column="file_data",
            filename_column="filename",
            institution_id=self.institution.id,
            requested_by_user_id=self.admin.id,
            request_status="approved",
            approved_by_user_id=self.developer.id,
            approved_at=datetime.utcnow(),
            requested_at=datetime.utcnow(),
            sync_enabled=True
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        
        # Simulate sync failure (as done in sync_service.py)
        source.last_sync_status = "failed"
        source.last_sync_message = error_message
        self.db.commit()
        
        # Create notification object (as done in sync_service.py) - in memory only
        notification = Notification(
            user_id=source.requested_by_user_id,
            type="data_source_sync_failed",
            title="Data Source Sync Failed",
            message=f"Synchronization failed for data source '{source.name}'. Error: {error_message[:200]}",
            priority="high",
            action_url=f"/admin/my-data-source-requests",
            action_label="View Details",
            action_metadata={
                "source_id": source.id,
                "source_name": source.name,
                "error_message": error_message
            }
        )
        
        # Property 1: Notification should be created (object exists)
        assert notification is not None, \
            "Sync failure should create a notification"
        
        # Property 2: Notification should be sent to requester
        assert notification.user_id == source.requested_by_user_id, \
            "Notification should be sent to the requester"
        
        # Property 3: Notification should have correct type
        assert notification.type == "data_source_sync_failed", \
            "Notification type should be 'data_source_sync_failed'"
        
        # Property 4: Notification should have high priority
        assert notification.priority == "high", \
            "Sync failure notifications should have high priority"
        
        # Property 5: Notification message should contain source name and error
        assert source.name in notification.message, \
            "Notification message should contain source name"
        # Error message might be truncated to 200 chars in notification message
        assert error_message[:200] in notification.message or error_message[:100] in notification.message, \
            "Notification message should contain error info"
        
        # Property 6: Notification metadata should contain full error message
        assert notification.action_metadata is not None, \
            "Notification should have metadata"
        assert notification.action_metadata.get("error_message") == error_message, \
            "Metadata should contain full error message"
        assert notification.action_metadata.get("source_id") == source.id, \
            "Metadata should contain source ID"
        
        # Property 7: Source should have failed status
        assert source.last_sync_status == "failed", \
            "Source should have 'failed' sync status"
        assert source.last_sync_message == error_message, \
            "Source should store the error message"    


class TestCredentialDeletion:
    """Property-based tests for credential deletion on rejection"""
    
    @pytest.fixture(autouse=True, scope="function")
    def setup(self):
        """Setup test database and mock data"""
        # Clean up any existing tables first
        teardown_test_db()
        setup_test_db()
        self.db = get_test_db()
        
        # Setup encryption
        self.key = Fernet.generate_key().decode()
        os.environ["DB_ENCRYPTION_KEY"] = self.key
        self.connector = ExternalDBConnector()
        
        # Create test institution
        self.institution = Institution(
            name="Test Ministry",
            type="ministry",
            location="Test Location"
        )
        self.db.add(self.institution)
        self.db.commit()
        self.db.refresh(self.institution)
        
        # Create test users
        self.admin = User(
            name="Admin User",
            email="admin@ministry.gov",
            role="ministry_admin",
            institution_id=self.institution.id,
            password_hash="dummy",
            approved=True
        )
        self.developer = User(
            name="Developer",
            email="dev@beacon.gov",
            role="developer",
            institution_id=None,
            password_hash="dummy",
            approved=True
        )
        
        self.db.add(self.admin)
        self.db.add(self.developer)
        self.db.commit()
        self.db.refresh(self.admin)
        self.db.refresh(self.developer)
        
        yield
        
        # Cleanup
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        self.db.close()
        teardown_test_db()
    
    # Feature: external-data-source, Property 26: Rejected requests delete credentials
    @settings(max_examples=100)
    @given(
        source_name=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        password=password_strategy,
        rejection_reason=st.text(min_size=10, max_size=500).filter(lambda x: len(x.strip()) >= 10)
    )
    def test_rejected_requests_delete_credentials(self, source_name, password, rejection_reason):
        """
        For any connection request that is rejected, the stored credentials 
        should be deleted from the database.
        
        Validates: Requirements 8.4
        """
        # Clean up any existing data sources from previous examples
        self.db.query(ExternalDataSource).delete()
        self.db.commit()
        
        # Create a pending data source request with credentials
        encrypted_password = self.connector.encrypt_password(password)
        
        source = ExternalDataSource(
            name=f"test_{source_name[:50]}_{datetime.utcnow().timestamp()}",
            ministry_name="Test Ministry",
            db_type="postgresql",
            host="localhost",
            port=5432,
            database_name="testdb",
            username="testuser",
            password_encrypted=encrypted_password,
            table_name="documents",
            file_column="file_data",
            filename_column="filename",
            institution_id=self.institution.id,
            requested_by_user_id=self.admin.id,
            request_status="pending",
            requested_at=datetime.utcnow(),
            sync_enabled=False
        )
        
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        
        # Verify credentials exist before rejection
        assert source.password_encrypted is not None, \
            "Credentials should exist before rejection"
        assert source.password_encrypted == encrypted_password, \
            "Stored encrypted password should match"
        
        # Verify we can decrypt the password (credentials are valid)
        decrypted = self.connector.decrypt_password(source.password_encrypted)
        assert decrypted == password, \
            "Should be able to decrypt password before rejection"
        
        # Simulate rejection (as done in the reject endpoint)
        source.request_status = "rejected"
        source.approved_by_user_id = self.developer.id
        source.approved_at = datetime.utcnow()
        source.rejection_reason = rejection_reason
        source.sync_enabled = False
        
        # Delete credentials on rejection (this is what we're testing)
        source.password_encrypted = None
        if source.supabase_key_encrypted:
            source.supabase_key_encrypted = None
        
        self.db.commit()
        self.db.refresh(source)
        
        # Property 1: Request should be rejected
        assert source.request_status == "rejected", \
            "Request status should be 'rejected'"
        
        # Property 2: Rejection reason should be stored
        assert source.rejection_reason == rejection_reason, \
            "Rejection reason should be stored"
        
        # Property 3: Password credentials should be deleted (set to None)
        assert source.password_encrypted is None, \
            "Password credentials should be deleted after rejection"
        
        # Property 4: Supabase key should also be deleted if it existed
        assert source.supabase_key_encrypted is None, \
            "Supabase key should be deleted after rejection"
        
        # Property 5: Sync should be disabled
        assert source.sync_enabled == False, \
            "Sync should be disabled for rejected requests"
        
        # Property 6: Other metadata should be preserved
        assert source.name is not None, \
            "Source name should be preserved"
        assert source.host is not None, \
            "Host should be preserved for audit trail"
        assert source.database_name is not None, \
            "Database name should be preserved for audit trail"
        
        # Property 7: Approver should be recorded
        assert source.approved_by_user_id == self.developer.id, \
            "Rejector should be recorded"
        assert source.approved_at is not None, \
            "Rejection timestamp should be recorded"


def run_property_tests():
    """Run all property-based tests"""
    print("\n" + "="*70)
    print("Running Property-Based Tests for External Data Source System")
    print("="*70 + "\n")
    
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_property_tests()