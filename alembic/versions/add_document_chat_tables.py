"""add document chat tables

Revision ID: add_document_chat
Revises: 
Create Date: 2024-12-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_document_chat'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create document_chat_messages table
    op.create_table(
        'document_chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('parent_message_id', sa.Integer(), nullable=True),
        sa.Column('message_type', sa.String(length=20), nullable=False, server_default='user'),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('mentioned_user_ids', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_message_id'], ['document_chat_messages.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_document_chat_messages_document_id', 'document_chat_messages', ['document_id'])
    op.create_index('ix_document_chat_messages_user_id', 'document_chat_messages', ['user_id'])
    op.create_index('ix_document_chat_messages_parent_message_id', 'document_chat_messages', ['parent_message_id'])
    op.create_index('ix_document_chat_messages_message_type', 'document_chat_messages', ['message_type'])
    op.create_index('ix_document_chat_messages_created_at', 'document_chat_messages', ['created_at'])
    
    # Create document_chat_participants table
    op.create_table(
        'document_chat_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('last_seen', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'user_id', name='unique_document_user_participant')
    )
    op.create_index('ix_document_chat_participants_document_id', 'document_chat_participants', ['document_id'])
    op.create_index('ix_document_chat_participants_user_id', 'document_chat_participants', ['user_id'])


def downgrade():
    op.drop_table('document_chat_participants')
    op.drop_table('document_chat_messages')
