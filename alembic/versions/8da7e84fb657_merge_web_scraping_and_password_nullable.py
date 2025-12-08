"""merge web scraping and password nullable

Revision ID: 8da7e84fb657
Revises: add_web_scraping, make_password_nullable
Create Date: 2025-12-08 14:59:23.394972

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8da7e84fb657'
down_revision = ('add_web_scraping', 'make_password_nullable')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
