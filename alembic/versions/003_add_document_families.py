"""Add document families for versioning system

Revision ID: 003
Revises: 002
Create Date: 2026-01-07 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create document_families table
    op.create_table('document_families',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('canonical_title', sa.String(length=500), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('ministry', sa.String(length=200), nullable=True),
        sa.Column('family_centroid_embedding', Vector(1024), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for document_families
    op.create_index('idx_families_category', 'document_families', ['category'])
    op.create_index('idx_families_ministry', 'document_families', ['ministry'])
    
    # Add family_id to documents table
    op.add_column('documents', sa.Column('family_id', sa.Integer(), nullable=True))
    op.add_column('documents', sa.Column('version_number', sa.String(length=20), nullable=True, server_default='1.0'))
    op.add_column('documents', sa.Column('is_latest_version', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('documents', sa.Column('superseded_by_id', sa.Integer(), nullable=True))
    op.add_column('documents', sa.Column('supersedes_id', sa.Integer(), nullable=True))
    op.add_column('documents', sa.Column('content_hash', sa.String(length=64), nullable=True))
    op.add_column('documents', sa.Column('source_url', sa.String(length=1000), nullable=True))
    op.add_column('documents', sa.Column('last_modified_at_source', sa.DateTime(), nullable=True))
    
    # Create foreign key constraints
    op.create_foreign_key('fk_documents_family_id', 'documents', 'document_families', ['family_id'], ['id'])
    op.create_foreign_key('fk_documents_superseded_by', 'documents', 'documents', ['superseded_by_id'], ['id'])
    op.create_foreign_key('fk_documents_supersedes', 'documents', 'documents', ['supersedes_id'], ['id'])
    
    # Create indexes for new document columns
    op.create_index('idx_documents_family_id', 'documents', ['family_id'])
    op.create_index('idx_documents_is_latest', 'documents', ['is_latest_version'])
    op.create_index('idx_documents_content_hash', 'documents', ['content_hash'])
    op.create_index('idx_documents_source_url', 'documents', ['source_url'])
    op.create_index('idx_documents_family_latest', 'documents', ['family_id', 'is_latest_version'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_documents_family_latest', table_name='documents')
    op.drop_index('idx_documents_source_url', table_name='documents')
    op.drop_index('idx_documents_content_hash', table_name='documents')
    op.drop_index('idx_documents_is_latest', table_name='documents')
    op.drop_index('idx_documents_family_id', table_name='documents')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_documents_supersedes', 'documents', type_='foreignkey')
    op.drop_constraint('fk_documents_superseded_by', 'documents', type_='foreignkey')
    op.drop_constraint('fk_documents_family_id', 'documents', type_='foreignkey')
    
    # Drop columns from documents table
    op.drop_column('documents', 'last_modified_at_source')
    op.drop_column('documents', 'source_url')
    op.drop_column('documents', 'content_hash')
    op.drop_column('documents', 'supersedes_id')
    op.drop_column('documents', 'superseded_by_id')
    op.drop_column('documents', 'is_latest_version')
    op.drop_column('documents', 'version_number')
    op.drop_column('documents', 'family_id')
    
    # Drop document_families table indexes
    op.drop_index('idx_families_ministry', table_name='document_families')
    op.drop_index('idx_families_category', table_name='document_families')
    
    # Drop document_families table
    op.drop_table('document_families')