"""merge email verification and chat history

Revision ID: f9827bb83764
Revises: add_email_verification, e6175865ca0d
Create Date: 2025-12-01 20:07:06.235983

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9827bb83764'
down_revision = ('add_email_verification', 'e6175865ca0d')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
