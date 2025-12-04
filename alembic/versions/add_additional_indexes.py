"""Add additional performance indexes for notifications, bookmarks, and chat

Revision ID: add_additional_indexes
Revises: add_performance_indexes
Create Date: 2025-12-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_additional_indexes'
down_revision = 'add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade():
    """Add additional performance indexes"""
    
    # Notifications table indexes
    op.create_index(
        'idx_notifications_user_read',
        'notifications',
        ['user_id', 'read'],
        unique=False
    )
    op.create_index(
        'idx_notifications_created',
        'notifications',
        ['created_at'],
        unique=False
    )
    op.create_index(
        'idx_notifications_user_type',
        'notifications',
        ['user_id', 'type'],
        unique=False
    )
    
    # Bookmarks table indexes
    op.create_index(
        'idx_bookmarks_user_created',
        'bookmarks',
        ['user_id', 'created_at'],
        unique=False
    )
    
    # Chat messages table indexes
    op.create_index(
        'idx_chat_messages_session_created',
        'chat_messages',
        ['session_id', 'created_at'],
        unique=False
    )
    
    # Document chat messages table indexes
    op.create_index(
        'idx_doc_chat_messages_doc_created',
        'document_chat_messages',
        ['document_id', 'created_at'],
        unique=False
    )
    op.create_index(
        'idx_doc_chat_messages_user',
        'document_chat_messages',
        ['user_id'],
        unique=False
    )
    
    print("✅ Additional performance indexes created successfully!")


def downgrade():
    """Remove additional performance indexes"""
    
    # Drop Notifications indexes
    op.drop_index('idx_notifications_user_read', table_name='notifications')
    op.drop_index('idx_notifications_created', table_name='notifications')
    op.drop_index('idx_notifications_user_type', table_name='notifications')
    
    # Drop Bookmarks indexes
    op.drop_index('idx_bookmarks_user_created', table_name='bookmarks')
    
    # Drop Chat messages indexes
    op.drop_index('idx_chat_messages_session_created', table_name='chat_messages')
    
    # Drop Document chat messages indexes
    op.drop_index('idx_doc_chat_messages_doc_created', table_name='document_chat_messages')
    op.drop_index('idx_doc_chat_messages_user', table_name='document_chat_messages')
    
    print("✅ Additional performance indexes removed successfully!")
