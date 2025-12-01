"""add email verification fields

Revision ID: add_email_verification
Revises: 9efcc1f82b81
Create Date: 2024-12-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_email_verification'
down_revision = '9efcc1f82b81'
branch_labels = None
depends_on = None


def upgrade():
    # Add email verification fields to users table
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('verification_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('verification_token_expires', sa.DateTime(), nullable=True))
    
    # Create indexes
    op.create_index('ix_users_email_verified', 'users', ['email_verified'])
    op.create_index('ix_users_verification_token', 'users', ['verification_token'], unique=True)


def downgrade():
    # Remove indexes
    op.drop_index('ix_users_verification_token', 'users')
    op.drop_index('ix_users_email_verified', 'users')
    
    # Remove columns
    op.drop_column('users', 'verification_token_expires')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'email_verified')
