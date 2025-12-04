"""merge government dept removal with main branch

Revision ID: merge_govt_dept_001
Revises: b316767083e4, remove_govt_dept_001
Create Date: 2024-12-04 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_govt_dept_001'
down_revision = ('b316767083e4', 'remove_govt_dept_001')
branch_labels = None
depends_on = None


def upgrade():
    # Merge migration - no changes needed
    pass


def downgrade():
    # Merge migration - no changes needed
    pass
