"""Complete document families implementation

Revision ID: 004
Revises: fix_vector_dim_1024
Create Date: 2026-01-07 23:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = 'fix_vector_dim_1024'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing family-related columns to documents table
    op.add_column('documents', sa.Column('family_id', sa.Integer(), nullable=True))
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
    op.create_index('idx_documents_content_hash', 'documents', ['content_hash'])
    op.create_index('idx_documents_source_url', 'documents', ['source_url'])
    op.create_index('idx_documents_family_latest', 'documents', ['family_id', 'is_latest_version'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_documents_family_latest', table_name='documents')
    op.drop_index('idx_documents_source_url', table_name='documents')
    op.drop_index('idx_documents_content_hash', table_name='documents')
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
    op.drop_column('documents', 'family_id')