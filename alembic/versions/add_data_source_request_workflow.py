"""add data source request workflow

Revision ID: add_data_source_workflow
Revises: 
Create Date: 2024-12-04

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'add_data_source_workflow'
down_revision = None  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns for request/approval workflow
    op.add_column('external_data_sources', 
        sa.Column('institution_id', sa.Integer(), sa.ForeignKey('institutions.id'), nullable=True))
    
    op.add_column('external_data_sources',
        sa.Column('requested_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
    
    op.add_column('external_data_sources',
        sa.Column('approved_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
    
    op.add_column('external_data_sources',
        sa.Column('request_status', sa.String(20), nullable=False, server_default='approved'))
    
    op.add_column('external_data_sources',
        sa.Column('data_classification', sa.String(20), nullable=True))
    
    op.add_column('external_data_sources',
        sa.Column('request_notes', sa.Text(), nullable=True))
    
    op.add_column('external_data_sources',
        sa.Column('rejection_reason', sa.Text(), nullable=True))
    
    op.add_column('external_data_sources',
        sa.Column('requested_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')))
    
    op.add_column('external_data_sources',
        sa.Column('approved_at', sa.DateTime(), nullable=True))
    
    # Create indexes for performance
    op.create_index('idx_external_data_sources_institution', 'external_data_sources', ['institution_id'])
    op.create_index('idx_external_data_sources_status', 'external_data_sources', ['request_status'])
    op.create_index('idx_external_data_sources_requester', 'external_data_sources', ['requested_by_user_id'])
    op.create_index('idx_external_data_sources_classification', 'external_data_sources', ['data_classification'])


def downgrade():
    # Remove indexes
    op.drop_index('idx_external_data_sources_classification', 'external_data_sources')
    op.drop_index('idx_external_data_sources_requester', 'external_data_sources')
    op.drop_index('idx_external_data_sources_status', 'external_data_sources')
    op.drop_index('idx_external_data_sources_institution', 'external_data_sources')
    
    # Remove columns
    op.drop_column('external_data_sources', 'approved_at')
    op.drop_column('external_data_sources', 'requested_at')
    op.drop_column('external_data_sources', 'rejection_reason')
    op.drop_column('external_data_sources', 'request_notes')
    op.drop_column('external_data_sources', 'data_classification')
    op.drop_column('external_data_sources', 'request_status')
    op.drop_column('external_data_sources', 'approved_by_user_id')
    op.drop_column('external_data_sources', 'requested_by_user_id')
    op.drop_column('external_data_sources', 'institution_id')
