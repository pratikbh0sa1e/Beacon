"""Fix alembic version table"""
from backend.database import engine
from sqlalchemy import text

with engine.begin() as conn:
    # Check current version
    result = conn.execute(text('SELECT * FROM alembic_version'))
    current = list(result)
    print(f"Current version: {current}")
    
    # Delete the problematic version
    conn.execute(text("DELETE FROM alembic_version"))
    print("Cleared alembic_version table")
    
    # Check again
    result = conn.execute(text('SELECT * FROM alembic_version'))
    current = list(result)
    print(f"After cleanup: {current}")
