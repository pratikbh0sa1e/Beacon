from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Date, ForeignKey, ARRAY, Boolean, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime
import os
from dotenv import load_dotenv
from sqlalchemy import UniqueConstraint

load_dotenv()

# Construct DATABASE_URL from individual components
DATABASE_HOSTNAME = os.getenv("DATABASE_HOSTNAME")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")

DATABASE_URL = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOSTNAME}:{DATABASE_PORT}/{DATABASE_NAME}"

# Create engine with connection pooling and timeout settings
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Institution(Base):
    """Institutions (Universities, Research Centres, Hospitals, etc.) and Ministries"""
    __tablename__ = "institutions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    location = Column(String(255), nullable=True)
    type = Column(String(50), nullable=False)  # university, ministry
    parent_ministry_id = Column(Integer, ForeignKey("institutions.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Soft delete fields
    deleted_at = Column(DateTime, nullable=True, index=True)
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="institution", foreign_keys="User.institution_id")
    deleted_by_user = relationship("User", foreign_keys=[deleted_by])
    parent_ministry = relationship("Institution", remote_side=[id], foreign_keys=[parent_ministry_id], backref="child_universities")


class User(Base):
    """Users with role-based access"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True)
    # Roles: developer, MINISTRY_ADMIN, university_admin, document_officer, student, public_viewer
    
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    approved = Column(Boolean, default=False, nullable=False, index=True)
    
    # Email verification fields
    email_verified = Column(Boolean, default=False, nullable=False, index=True)
    verification_token = Column(String(255), nullable=True, unique=True, index=True)
    verification_token_expires = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    institution = relationship("Institution", back_populates="users", foreign_keys=[institution_id])
    audit_logs = relationship("AuditLog", back_populates="user")
    bookmarks = relationship("Bookmark", cascade="all, delete-orphan", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

    # ✅ FIXED: Specify foreign_keys to resolve ambiguity
    uploaded_documents = relationship(
        "Document",
        foreign_keys="Document.uploader_id",
        back_populates="uploader"
    )
    approved_documents = relationship(
        "Document",
        foreign_keys="Document.approved_by",
        back_populates="approver"
    )


class Document(Base):
    """Documents with metadata and access control"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_type = Column(String)
    file_path = Column(String)
    s3_url = Column(String)
    extracted_text = Column(Text)
    
    # Access control
    visibility_level = Column(String(50), default="public")
    # Levels: public, institution_only, restricted, confidential
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    uploader_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Preserve document if uploader deleted
    download_allowed = Column(Boolean, default=False, nullable=False)
    # Approval workflow
    approval_status = Column(String(50), default="draft", index=True)
    # Status: draft, pending, under_review, changes_requested, approved, 
    #         restricted_approved, archived, rejected, flagged, expired
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Preserve document if approver deleted
    approved_at = Column(DateTime, nullable=True)
    # Escalation flag for MoE review
    requires_moe_approval = Column(Boolean, default=False, nullable=False, index=True)
    escalated_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    user_description = Column(Text, nullable=True)
    version = Column(String(50), default="1.0")
    # ✅ FIXED: Renamed from 'metadata' to 'additional_metadata' to avoid SQLAlchemy conflict
    additional_metadata = Column(Text, nullable=True)
    
    # Relationships
    doc_metadata_rel = relationship(
        "DocumentMetadata",
        back_populates="document",
        uselist=False,
        cascade="all, delete-orphan"
    )
    bookmarks = relationship("Bookmark", cascade="all, delete-orphan", back_populates="document")

    # ✅ FIXED: Specify foreign_keys in both relationships
    uploader = relationship(
        "User",
        foreign_keys=[uploader_id],
        back_populates="uploaded_documents"
    )
    approver = relationship(
        "User",
        foreign_keys=[approved_by],
        back_populates="approved_documents"
    )
    
    institution = relationship("Institution")


class DocumentMetadata(Base):
    """Metadata extracted from documents"""
    __tablename__ = "document_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Auto-extracted metadata
    title = Column(String(500), nullable=True)
    department = Column(String(200), nullable=True, index=True)
    document_type = Column(String(100), nullable=True, index=True)
    date_published = Column(Date, nullable=True)
    keywords = Column(ARRAY(Text), nullable=True)
    
    # LLM-generated metadata
    summary = Column(Text, nullable=True)
    key_topics = Column(ARRAY(Text), nullable=True)
    entities = Column(JSONB, nullable=True)
    
    # Status tracking
    embedding_status = Column(String(20), nullable=False, default='uploaded', index=True)
    metadata_status = Column(String(20), nullable=False, default='processing', index=True)
    last_accessed = Column(DateTime, nullable=True)
    access_count = Column(Integer, nullable=False, default=0)
    
    # Search optimization
    bm25_keywords = Column(Text, nullable=True)
    text_length = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    document = relationship("Document", back_populates="doc_metadata_rel")


class ExternalDataSource(Base):
    """Registry of external data sources (ministry databases)"""
    __tablename__ = "external_data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    ministry_name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Connection details
    db_type = Column(String(50), nullable=False, default="postgresql")
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False, default=5432)
    database_name = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    password_encrypted = Column(Text, nullable=False)
    
    # Document retrieval config
    table_name = Column(String(100), nullable=True)
    file_column = Column(String(100), nullable=True)
    filename_column = Column(String(100), nullable=True)
    metadata_columns = Column(JSON, nullable=True)
    
    # Storage configuration (for files in Supabase/S3)
    storage_type = Column(String(20), nullable=True, default="database")  # "database" or "supabase"
    supabase_url = Column(String(500), nullable=True)
    supabase_key_encrypted = Column(Text, nullable=True)
    supabase_bucket = Column(String(100), nullable=True)
    file_path_prefix = Column(String(200), nullable=True)  # e.g., "resume/"
    
    # Sync configuration
    sync_enabled = Column(Boolean, nullable=False, default=True)
    sync_frequency = Column(String(20), nullable=False, default="daily")
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String(20), nullable=True)
    last_sync_message = Column(Text, nullable=True)
    
    # Stats
    total_documents_synced = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class SyncLog(Base):
    """Log of sync operations"""
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, nullable=False, index=True)
    source_name = Column(String(200), nullable=False)
    
    status = Column(String(20), nullable=False)
    documents_fetched = Column(Integer, nullable=False, default=0)
    documents_processed = Column(Integer, nullable=False, default=0)
    documents_failed = Column(Integer, nullable=False, default=0)
    
    error_message = Column(Text, nullable=True)
    sync_duration_seconds = Column(Integer, nullable=True)
    
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class AuditLog(Base):
    """Audit trail for all system actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # SET NULL to preserve audit trail
    action = Column(String(100), nullable=False, index=True)
    # Actions: login, logout, upload_document, approve_user, reject_user, 
    #          approve_document, reject_document, role_changed, search_query
    
    # ✅ FIXED: Renamed from 'metadata' to 'action_metadata' to avoid SQLAlchemy conflict
    action_metadata = Column(JSONB, nullable=True)  # Additional context
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    user = relationship("User", back_populates="audit_logs")

class Bookmark(Base):
    """User document bookmarks"""
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "document_id", name="unique_user_document_bookmark"),
    )

    # Relationships
    user = relationship("User", back_populates="bookmarks")
    document = relationship("Document", back_populates="bookmarks")


class Notification(Base):
    """System notifications with hierarchical routing"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Recipient
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Notification content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, index=True)
    # Types: user_approval, document_approval, role_change, system_alert, upload_success, etc.
    
    # Priority levels
    priority = Column(String(20), nullable=False, default="medium", index=True)
    # Priorities: critical, high, medium, low
    
    # Status
    read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    
    # Action metadata
    action_url = Column(String(500), nullable=True)  # URL to navigate to
    action_label = Column(String(100), nullable=True)  # CTA button text
    action_metadata = Column(JSONB, nullable=True)  # Additional data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    
    # Relationship
    user = relationship("User", foreign_keys=[user_id])


class ChatSession(Base):
    """Chat sessions for storing conversation history"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False, default="New Chat")
    thread_id = Column(String(100), nullable=False, unique=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """Individual messages within chat sessions"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    citations = Column(JSONB, default=list)  # Array of citation objects
    confidence = Column(Integer, nullable=True)  # 0-100 (percentage)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship
    session = relationship("ChatSession", back_populates="messages")


class DocumentEmbedding(Base):
    """Vector embeddings stored in pgvector for centralized RAG access"""
    __tablename__ = "document_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(1024), nullable=False)  # BGE-large-en-v1.5 produces 1024-dim vectors
    
    # Denormalized fields for efficient filtering (copied from Document table)
    visibility_level = Column(String(50), nullable=False, index=True)
    institution_id = Column(Integer, nullable=True, index=True)
    approval_status = Column(String(50), nullable=False, index=True)
    
    # Metadata for each chunk (renamed to avoid SQLAlchemy conflict)
    chunk_metadata = Column(JSONB, nullable=True)  # Stores filename, page_number, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_doc_chunk', 'document_id', 'chunk_index'),
        Index('idx_visibility_institution', 'visibility_level', 'institution_id'),
        Index('idx_approval_status', 'approval_status'),
    )


class DocumentChatMessage(Base):
    """Messages in document-specific chat rooms"""
    __tablename__ = "document_chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    
    # Threading support
    parent_message_id = Column(Integer, ForeignKey("document_chat_messages.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Message type: 'user', 'system', 'beacon'
    message_type = Column(String(20), nullable=False, default="user", index=True)
    
    # For beacon responses
    citations = Column(JSONB, nullable=True)
    
    # Mentioned users
    mentioned_user_ids = Column(ARRAY(Integer), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", foreign_keys=[document_id])
    user = relationship("User", foreign_keys=[user_id])
    parent_message = relationship("DocumentChatMessage", remote_side=[id], foreign_keys=[parent_message_id])
    replies = relationship("DocumentChatMessage", back_populates="parent_message", foreign_keys=[parent_message_id])


class DocumentChatParticipant(Base):
    """Track active participants in document chat rooms"""
    __tablename__ = "document_chat_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Activity tracking
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint("document_id", "user_id", name="unique_document_user_participant"),
    )
    
    # Relationships
    document = relationship("Document", foreign_keys=[document_id])
    user = relationship("User", foreign_keys=[user_id])


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UserNote(Base):
    """Personal study notes - private to each user"""
    __tablename__ = "user_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Note content
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    tags = Column(ARRAY(String), nullable=True)
    
    # Metadata
    is_pinned = Column(Boolean, default=False, nullable=False)
    color = Column(String(20), nullable=True)  # For color-coding notes
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    document = relationship("Document", foreign_keys=[document_id])
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_user_notes_user_document", "user_id", "document_id"),
        Index("idx_user_notes_created", "created_at"),
    )
