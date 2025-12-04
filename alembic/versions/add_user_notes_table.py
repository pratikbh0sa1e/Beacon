"""add user notes table

Revision ID: add_user_notes_001
Revises: add_document_workflow
Create Date: 2024-12-03 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_user_notes_001'
down_revision = 'add_document_workflow'
branch_labels = None
depends_on = None


def upgrade():
    # Check if table exists before creating
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'user_notes' not in inspector.get_table_names():
        # Create user_notes table
        op.create_table(
            'user_notes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('document_id', sa.Integer(), nullable=True),
            sa.Column('title', sa.String(length=500), nullable=True),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
            sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('color', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('idx_user_notes_user_document', 'user_notes', ['user_id', 'document_id'])
        op.create_index('idx_user_notes_created', 'user_notes', ['created_at'])
        op.create_index(op.f('ix_user_notes_user_id'), 'user_notes', ['user_id'])
        op.create_index(op.f('ix_user_notes_document_id'), 'user_notes', ['document_id'])
        
        # Create foreign keys
        op.create_foreign_key(
            'fk_user_notes_user_id',
            'user_notes', 'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_user_notes_document_id',
            'user_notes', 'documents',
            ['document_id'], ['id'],
            ondelete='CASCADE'
        )


def downgrade():
    op.drop_table('user_notes')
