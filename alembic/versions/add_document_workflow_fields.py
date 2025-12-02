"""Add document workflow fields

Revision ID: add_document_workflow
Revises: f9827bb83764
Create Date: 2024-12-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_document_workflow'
down_revision = 'f9827bb83764'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to documents table
    op.add_column('documents', sa.Column('requires_moe_approval', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('documents', sa.Column('escalated_at', sa.DateTime(), nullable=True))
    op.add_column('documents', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('documents', sa.Column('expiry_date', sa.DateTime(), nullable=True))
    
    # Create index on requires_moe_approval
    op.create_index('idx_requires_moe_approval', 'documents', ['requires_moe_approval'])
    
    # Update existing documents: change 'pending' to 'draft' for consistency
    # Documents that are already approved stay approved
    op.execute("UPDATE documents SET approval_status = 'draft' WHERE approval_status = 'pending'")


def downgrade():
    # Remove indexes
    op.drop_index('idx_requires_moe_approval', table_name='documents')
    
    # Remove columns
    op.drop_column('documents', 'expiry_date')
    op.drop_column('documents', 'rejection_reason')
    op.drop_column('documents', 'escalated_at')
    op.drop_column('documents', 'requires_moe_approval')
    
    # Revert status changes
    op.execute("UPDATE documents SET approval_status = 'pending' WHERE approval_status = 'draft'")
