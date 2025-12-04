"""Add performance indexes for optimized queries

Revision ID: add_performance_indexes
Revises: 
Create Date: 2025-12-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = '4ffbefe61d8b'  # Links to the merge point
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes to frequently queried columns"""
    
    # Document table indexes
    op.create_index(
        'idx_doc_visibility_institution',
        'documents',
        ['visibility_level', 'institution_id'],
        unique=False
    )
    op.create_index(
        'idx_doc_approval_status',
        'documents',
        ['approval_status'],
        unique=False
    )
    op.create_index(
        'idx_doc_uploader',
        'documents',
        ['uploader_id'],
        unique=False
    )
    op.create_index(
        'idx_doc_uploaded_at',
        'documents',
        ['uploaded_at'],
        unique=False
    )
    op.create_index(
        'idx_doc_institution',
        'documents',
        ['institution_id'],
        unique=False
    )
    op.create_index(
        'idx_doc_requires_moe',
        'documents',
        ['requires_moe_approval'],
        unique=False
    )
    
    # DocumentMetadata table indexes
    op.create_index(
        'idx_meta_doc_type',
        'document_metadata',
        ['document_type'],
        unique=False
    )
    op.create_index(
        'idx_meta_department',
        'document_metadata',
        ['department'],
        unique=False
    )
    op.create_index(
        'idx_meta_updated_at',
        'document_metadata',
        ['updated_at'],
        unique=False
    )
    op.create_index(
        'idx_meta_embedding_status',
        'document_metadata',
        ['embedding_status'],
        unique=False
    )
    op.create_index(
        'idx_meta_metadata_status',
        'document_metadata',
        ['metadata_status'],
        unique=False
    )
    
    print("✅ Performance indexes created successfully!")


def downgrade():
    """Remove performance indexes"""
    
    # Drop Document table indexes
    op.drop_index('idx_doc_visibility_institution', table_name='documents')
    op.drop_index('idx_doc_approval_status', table_name='documents')
    op.drop_index('idx_doc_uploader', table_name='documents')
    op.drop_index('idx_doc_uploaded_at', table_name='documents')
    op.drop_index('idx_doc_institution', table_name='documents')
    op.drop_index('idx_doc_requires_moe', table_name='documents')
    
    # Drop DocumentMetadata table indexes
    op.drop_index('idx_meta_doc_type', table_name='document_metadata')
    op.drop_index('idx_meta_department', table_name='document_metadata')
    op.drop_index('idx_meta_updated_at', table_name='document_metadata')
    op.drop_index('idx_meta_embedding_status', table_name='document_metadata')
    op.drop_index('idx_meta_metadata_status', table_name='document_metadata')
    
    print("✅ Performance indexes removed successfully!")
