"""merge ocr and password heads

Revision ID: merge_ocr_password
Revises: add_ocr_support, make_password_nullable
Create Date: 2025-12-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_ocr_password'
down_revision = ('add_ocr_support', 'make_password_nullable')
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration, no changes needed
    pass


def downgrade():
    # This is a merge migration, no changes needed
    pass
