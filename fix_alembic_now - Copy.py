"""
Emergency Alembic Fix Script
This will reset your alembic_version table to match your current migration files
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Build database URL
DATABASE_URL = f"postgresql://{os.getenv('DATABASE_USERNAME')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOSTNAME')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"

print("🔧 Alembic Emergency Fix")
print("=" * 50)

# Create engine
engine = create_engine(DATABASE_URL)

# Connect and fix (using transaction context manager)
with engine.begin() as conn:  # begin() auto-commits on success
    # Check current version
    try:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        current = result.fetchone()
        if current:
            print(f"❌ Current (broken) version: {current[0]}")
        else:
            print("⚠️  No version found in alembic_version table")
    except Exception as e:
        print(f"⚠️  Error reading alembic_version: {e}")
    
    # Option 1: Delete the broken version
    print("\n🔨 Deleting broken version...")
    conn.execute(text("DELETE FROM alembic_version"))
    print("✅ Deleted broken version")
    
    # Option 2: Insert the correct version
    # Use the latest migration from your files
    latest_revision = 'add_performance_indexes'  # Change this if needed
    
    print(f"\n📝 Setting version to: {latest_revision}")
    conn.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('{latest_revision}')"))
    print("✅ Version updated!")
    
    # Verify
    result = conn.execute(text("SELECT version_num FROM alembic_version"))
    new_version = result.fetchone()
    print(f"\n✅ New version: {new_version[0]}")

print("\n" + "=" * 50)
print("🎉 Alembic fixed! Now run: alembic current")
print("\nIf you see the correct version, you're good to go!")
print("If you need to apply new migrations, run: alembic upgrade head")
