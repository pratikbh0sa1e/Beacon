"""add parent ministry to institutions

Revision ID: add_parent_ministry_001
Revises: generalize_ministry_001
Create Date: 2024-12-03 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_parent_ministry_001'
down_revision = 'generalize_ministry_001'
branch_labels = None
depends_on = None


def upgrade():
    # Add parent_ministry_id column
    op.add_column('institutions', 
        sa.Column('parent_ministry_id', sa.Integer(), nullable=True)
    )
    
    # Add foreign key
    op.create_foreign_key(
        'fk_institutions_parent_ministry',
        'institutions', 'institutions',
        ['parent_ministry_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add index for performance
    op.create_index(
        'idx_institutions_parent_ministry',
        'institutions',
        ['parent_ministry_id']
    )
    
    # Link existing universities to Ministry of Education (if exists)
    op.execute("""
        UPDATE institutions 
        SET parent_ministry_id = (
            SELECT id FROM institutions 
            WHERE name = 'Ministry of Education' 
            AND type = 'ministry'
            LIMIT 1
        )
        WHERE type = 'university'
        AND parent_ministry_id IS NULL
    """)


def downgrade():
    op.drop_constraint('fk_institutions_parent_ministry', 'institutions', type_='foreignkey')
    op.drop_index('idx_institutions_parent_ministry', 'institutions')
    op.drop_column('institutions', 'parent_ministry_id')
