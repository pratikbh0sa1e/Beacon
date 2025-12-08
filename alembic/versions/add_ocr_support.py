"""add ocr support

Revision ID: add_ocr_support
Revises: add_user_notes_table
Create Date: 2025-12-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_ocr_support'
down_revision = 'add_additional_indexes'
branch_labels = None
depends_on = None


def upgrade():
    # Create ocr_results table
    op.create_table(
        'ocr_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('engine_used', sa.String(50), nullable=False, server_default='easyocr'),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('extraction_time', sa.Float(), nullable=True),
        sa.Column('language_detected', sa.String(50), nullable=True),
        sa.Column('preprocessing_applied', postgresql.JSONB(), nullable=True),
        sa.Column('raw_result', sa.Text(), nullable=True),
        sa.Column('processed_result', sa.Text(), nullable=True),
        sa.Column('needs_review', sa.Boolean(), server_default='false'),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('issues', postgresql.JSONB(), nullable=True),
        sa.Column('pages_with_ocr', postgresql.JSONB(), nullable=True),
        sa.Column('pages_with_text', postgresql.JSONB(), nullable=True),
        sa.Column('rotation_corrected', sa.Integer(), nullable=True),
        sa.Column('tables_extracted', postgresql.JSONB(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL')
    )
    
    # Create indexes for performance
    op.create_index('idx_ocr_results_document_id', 'ocr_results', ['document_id'])
    op.create_index('idx_ocr_results_needs_review', 'ocr_results', ['needs_review'])
    op.create_index('idx_ocr_results_confidence', 'ocr_results', ['confidence_score'])
    
    # Add OCR-related columns to documents table
    op.add_column('documents', sa.Column('is_scanned', sa.Boolean(), server_default='false'))
    op.add_column('documents', sa.Column('ocr_status', sa.String(20), nullable=True))
    op.add_column('documents', sa.Column('ocr_confidence', sa.Float(), nullable=True))
    
    # Create index on ocr_status
    op.create_index('idx_documents_ocr_status', 'documents', ['ocr_status'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_documents_ocr_status', table_name='documents')
    op.drop_index('idx_ocr_results_confidence', table_name='ocr_results')
    op.drop_index('idx_ocr_results_needs_review', table_name='ocr_results')
    op.drop_index('idx_ocr_results_document_id', table_name='ocr_results')
    
    # Drop columns from documents
    op.drop_column('documents', 'ocr_confidence')
    op.drop_column('documents', 'ocr_status')
    op.drop_column('documents', 'is_scanned')
    
    # Drop ocr_results table
    op.drop_table('ocr_results')
