"""Add document_metadata table for lazy RAG

Revision ID: 002
Revises: 001
Create Date: 2024-11-27 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

# revision identifiers, used by Alembic.
revision = '002'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create document_metadata table
    op.create_table(
        'document_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        
        # Auto-extracted metadata
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('department', sa.String(200), nullable=True),
        sa.Column('document_type', sa.String(100), nullable=True),
        sa.Column('date_published', sa.Date(), nullable=True),
        sa.Column('keywords', ARRAY(sa.Text()), nullable=True),
        
        # LLM-generated metadata
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('key_topics', ARRAY(sa.Text()), nullable=True),
        sa.Column('entities', JSONB(), nullable=True),
        
        # Status tracking
        sa.Column('embedding_status', sa.String(20), nullable=False, server_default='uploaded'),
        sa.Column('metadata_status', sa.String(20), nullable=False, server_default='processing'),
        sa.Column('last_accessed', sa.DateTime(), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=False, server_default='0'),
        
        # Search optimization
        sa.Column('bm25_keywords', sa.Text(), nullable=True),
        sa.Column('text_length', sa.Integer(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE')
    )
    
    # Create indexes
    op.create_index('idx_document_id', 'document_metadata', ['document_id'])
    op.create_index('idx_embedding_status', 'document_metadata', ['embedding_status'])
    op.create_index('idx_metadata_status', 'document_metadata', ['metadata_status'])
    op.create_index('idx_department', 'document_metadata', ['department'])
    op.create_index('idx_document_type', 'document_metadata', ['document_type'])
    op.create_index('idx_keywords_gin', 'document_metadata', ['keywords'], postgresql_using='gin')


def downgrade():
    op.drop_table('document_metadata')
