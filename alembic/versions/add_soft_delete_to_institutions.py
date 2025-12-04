"""add soft delete to institutions

Revision ID: add_soft_delete_001
Revises: merge_govt_dept_001
Create Date: 2024-12-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_soft_delete_001'
down_revision = 'merge_govt_dept_001'
branch_labels = None
depends_on = None


def upgrade():
    # Add soft delete columns
    op.add_column('institutions', 
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )
    op.add_column('institutions', 
        sa.Column('deleted_by', sa.Integer(), nullable=True)
    )
    
    # Add foreign key
    op.create_foreign_key(
        'fk_institutions_deleted_by',
        'institutions', 'users',
        ['deleted_by'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add index for better query performance
    op.create_index(
        'idx_institutions_deleted_at',
        'institutions',
        ['deleted_at']
    )


def downgrade():
    op.drop_index('idx_institutions_deleted_at', 'institutions')
    op.drop_constraint('fk_institutions_deleted_by', 'institutions', type_='foreignkey')
    op.drop_column('institutions', 'deleted_by')
    op.drop_column('institutions', 'deleted_at')
