"""Fix alembic version table"""
from backend.database import engine
from sqlalchemy import text

# Check current version
with engine.begin() as conn:
    result = conn.execute(text("SELECT * FROM alembic_version"))
    current = result.fetchall()
    print("Current alembic versions:", current)
    
    # Delete the problematic version
    conn.execute(text("DELETE FROM alembic_version WHERE version_num = 'merge_ocr_password'"))
    print("Deleted merge_ocr_password")
    
    # Set to add_additional_indexes (the last good migration)
    conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('add_additional_indexes')"))
    print("Set version to add_additional_indexes")
    
    # Check again
    result = conn.execute(text("SELECT * FROM alembic_version"))
    current = result.fetchall()
    print("After cleanup:", current)
