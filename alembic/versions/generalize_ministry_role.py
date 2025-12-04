"""generalize ministry role

Revision ID: generalize_ministry_001
Revises: add_user_notes_001
Create Date: 2024-12-03 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'generalize_ministry_001'
down_revision = 'add_user_notes_001'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Update role from MINISTRY_ADMIN to ministry_admin
    op.execute("""
        UPDATE users 
        SET role = 'ministry_admin' 
        WHERE role = 'MINISTRY_ADMIN'
    """)
    
    # 2. Ensure Ministry of Education exists
    op.execute("""
        INSERT INTO institutions (name, type, location, created_at)
        VALUES ('Ministry of Education', 'ministry', 'New Delhi', NOW())
        ON CONFLICT (name) DO NOTHING
    """)
    
    # 3. Link existing ministry_admin users to MoE if not linked
    op.execute("""
        UPDATE users 
        SET institution_id = (
            SELECT id FROM institutions 
            WHERE name = 'Ministry of Education' 
            LIMIT 1
        )
        WHERE role = 'ministry_admin' 
        AND institution_id IS NULL
    """)
    
    # 4. Add other major ministries for future use
    op.execute("""
        INSERT INTO institutions (name, type, location, created_at)
        VALUES 
            ('Ministry of Health and Family Welfare', 'ministry', 'New Delhi', NOW()),
            ('Ministry of Finance', 'ministry', 'New Delhi', NOW()),
            ('Ministry of Home Affairs', 'ministry', 'New Delhi', NOW())
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade():
    # Revert role change
    op.execute("""
        UPDATE users 
        SET role = 'MINISTRY_ADMIN' 
        WHERE role = 'ministry_admin'
    """)
    
    # Note: We don't delete institutions as they might be in use
