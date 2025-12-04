"""remove government_dept type

Revision ID: remove_govt_dept_001
Revises: add_parent_ministry_001
Create Date: 2024-12-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_govt_dept_001'
down_revision = 'add_parent_ministry_001'
branch_labels = None
depends_on = None


def upgrade():
    # Convert any existing government_dept to university
    op.execute("""
        UPDATE institutions 
        SET type = 'university'
        WHERE type = 'government_dept'
    """)
    
    # Note: We keep the column as-is, just don't use government_dept anymore
    # Only two types now: 'ministry' and 'university'


def downgrade():
    # No downgrade needed - data is preserved
    pass
