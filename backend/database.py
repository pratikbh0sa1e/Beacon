from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Date, ForeignKey, ARRAY, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import os
from dotenv import load_dotenv

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
    """Institutions (Universities, Government Departments)"""
    __tablename__ = "institutions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    location = Column(String(255), nullable=True)
    type = Column(String(50), nullable=False)  # university, government_dept, ministry
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="institution")


class User(Base):
    """Users with role-based access"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True)
    # Roles: developer, moe_admin, university_admin, document_officer, student, public_viewer
    
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    approved = Column(Boolean, default=False, nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    institution = relationship("Institution", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")
    uploaded_documents = relationship("Document", back_populates="uploader")


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
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Approval workflow
    approval_status = Column(String(50), default="pending", index=True)
    # Status: pending, approved, rejected
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    doc_metadata = Column(Text, nullable=True)
    
    # Relationships
    doc_metadata_rel = relationship("DocumentMetadata", back_populates="document", uselist=False, cascade="all, delete-orphan")
    uploader = relationship("User", foreign_keys=[uploader_id], back_populates="uploaded_documents")
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


class AuditLog(Base):
    """Audit trail for all system actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False, index=True)
    # Actions: login, logout, upload_document, approve_user, reject_user, 
    #          approve_document, reject_document, role_changed, search_query
    
    metadata = Column(JSONB, nullable=True)  # Additional context
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    user = relationship("User", back_populates="audit_logs")


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()