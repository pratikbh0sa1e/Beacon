"""fix foreign key constraints for user deletion

Revision ID: fix_fk_constraints_001
Revises: add_soft_delete_001
Create Date: 2024-12-04 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_fk_constraints_001'
down_revision = 'add_soft_delete_001'
branch_labels = None
depends_on = None


def upgrade():
    """
    Fix foreign key constraints to handle user deletion properly
    
    Strategy:
    - audit_logs: SET NULL (preserve audit trail even if user deleted)
    - documents (uploader_id): SET NULL (preserve document even if uploader deleted)
    - documents (approved_by): SET NULL (preserve document even if approver deleted)
    - bookmarks: CASCADE (delete bookmarks when user deleted)
    - chat_sessions: CASCADE (delete chat sessions when user deleted)
    - user_notes: CASCADE (delete notes when user deleted)
    """
    
    # Use raw SQL for better control and to avoid locks
    connection = op.get_bind()
    
    # 1. Fix audit_logs foreign key
    print("Fixing audit_logs foreign key...")
    connection.execute(sa.text("""
        ALTER TABLE audit_logs 
        DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey CASCADE;
    """))
    
    connection.execute(sa.text("""
        ALTER TABLE audit_logs 
        ALTER COLUMN user_id DROP NOT NULL;
    """))
    
    connection.execute(sa.text("""
        ALTER TABLE audit_logs 
        ADD CONSTRAINT audit_logs_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id) 
        ON DELETE SET NULL;
    """))
    
    # 2. Fix documents uploader_id foreign key
    print("Fixing documents uploader_id foreign key...")
    connection.execute(sa.text("""
        ALTER TABLE documents 
        DROP CONSTRAINT IF EXISTS documents_uploader_id_fkey CASCADE;
    """))
    
    connection.execute(sa.text("""
        ALTER TABLE documents 
        ADD CONSTRAINT documents_uploader_id_fkey 
        FOREIGN KEY (uploader_id) REFERENCES users(id) 
        ON DELETE SET NULL;
    """))
    
    # 3. Fix documents approved_by foreign key
    print("Fixing documents approved_by foreign key...")
    connection.execute(sa.text("""
        ALTER TABLE documents 
        DROP CONSTRAINT IF EXISTS documents_approved_by_fkey CASCADE;
    """))
    
    connection.execute(sa.text("""
        ALTER TABLE documents 
        ADD CONSTRAINT documents_approved_by_fkey 
        FOREIGN KEY (approved_by) REFERENCES users(id) 
        ON DELETE SET NULL;
    """))
    
    # 4. Fix bookmarks foreign key (CASCADE)
    print("Fixing bookmarks foreign key...")
    connection.execute(sa.text("""
        ALTER TABLE bookmarks 
        DROP CONSTRAINT IF EXISTS bookmarks_user_id_fkey CASCADE;
    """))
    
    connection.execute(sa.text("""
        ALTER TABLE bookmarks 
        ADD CONSTRAINT bookmarks_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id) 
        ON DELETE CASCADE;
    """))
    
    # 5. Fix chat_sessions foreign key (CASCADE) - if table exists
    print("Fixing chat_sessions foreign key...")
    connection.execute(sa.text("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'chat_sessions') THEN
                ALTER TABLE chat_sessions 
                DROP CONSTRAINT IF EXISTS chat_sessions_user_id_fkey CASCADE;
                
                ALTER TABLE chat_sessions 
                ADD CONSTRAINT chat_sessions_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES users(id) 
                ON DELETE CASCADE;
            END IF;
        END $$;
    """))
    
    # 6. Fix user_notes foreign key (CASCADE) - if table exists
    print("Fixing user_notes foreign key...")
    connection.execute(sa.text("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_notes') THEN
                ALTER TABLE user_notes 
                DROP CONSTRAINT IF EXISTS fk_user_notes_user_id CASCADE;
                
                ALTER TABLE user_notes 
                ADD CONSTRAINT fk_user_notes_user_id 
                FOREIGN KEY (user_id) REFERENCES users(id) 
                ON DELETE CASCADE;
            END IF;
        END $$;
    """))
    
    print("All foreign key constraints fixed successfully!")


def downgrade():
    """Revert foreign key constraints"""
    
    # Revert audit_logs
    op.drop_constraint('audit_logs_user_id_fkey', 'audit_logs', type_='foreignkey')
    op.create_foreign_key(
        'audit_logs_user_id_fkey',
        'audit_logs', 'users',
        ['user_id'], ['id']
    )
    op.alter_column('audit_logs', 'user_id',
                    existing_type=sa.Integer(),
                    nullable=False)
    
    # Revert documents
    op.execute('ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_uploader_id_fkey')
    op.create_foreign_key(
        'documents_uploader_id_fkey',
        'documents', 'users',
        ['uploader_id'], ['id']
    )
    
    op.execute('ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_approved_by_fkey')
    op.create_foreign_key(
        'documents_approved_by_fkey',
        'documents', 'users',
        ['approved_by'], ['id']
    )
    
    # Revert bookmarks
    op.execute('ALTER TABLE bookmarks DROP CONSTRAINT IF EXISTS bookmarks_user_id_fkey')
    op.create_foreign_key(
        'bookmarks_user_id_fkey',
        'bookmarks', 'users',
        ['user_id'], ['id']
    )
    
    # Revert chat_sessions
    op.execute('ALTER TABLE chat_sessions DROP CONSTRAINT IF EXISTS chat_sessions_user_id_fkey')
    op.create_foreign_key(
        'chat_sessions_user_id_fkey',
        'chat_sessions', 'users',
        ['user_id'], ['id']
    )
    
    # Revert user_notes
    op.execute('ALTER TABLE user_notes DROP CONSTRAINT IF EXISTS fk_user_notes_user_id')
    op.create_foreign_key(
        'fk_user_notes_user_id',
        'user_notes', 'users',
        ['user_id'], ['id']
    )
