"""make password_encrypted nullable for credential deletion

Revision ID: make_password_nullable
Revises: 9efcc1f82b81
Create Date: 2025-12-04 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'make_password_nullable'
down_revision = '9efcc1f82b81'
branch_labels = None
depends_on = None


def upgrade():
    """Make password_encrypted nullable to support credential deletion on rejection"""
    # For PostgreSQL
    op.alter_column('external_data_sources', 'password_encrypted',
                    existing_type=sa.Text(),
                    nullable=True)


def downgrade():
    """Revert password_encrypted to NOT NULL"""
    # For PostgreSQL
    op.alter_column('external_data_sources', 'password_encrypted',
                    existing_type=sa.Text(),
                    nullable=False)
