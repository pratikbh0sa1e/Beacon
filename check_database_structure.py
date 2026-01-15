#!/usr/bin/env python3
"""Check if document families table and related structures exist"""
import sys
import os
sys.path.append('.')
from dotenv import load_dotenv
load_dotenv()

from backend.database import SessionLocal, engine
from sqlalchemy import inspect

# Check if tables exist
inspector = inspect(engine)
tables = inspector.get_table_names()

print('Existing tables:')
for table in sorted(tables):
    print(f'  - {table}')

# Check if document_families exists
if 'document_families' in tables:
    print('\n✅ document_families table already exists')
    
    # Check columns
    columns = inspector.get_columns('document_families')
    print('Columns in document_families:')
    for col in columns:
        print(f'  - {col["name"]}: {col["type"]}')
else:
    print('\n❌ document_families table does not exist')

# Check if documents table has family-related columns
if 'documents' in tables:
    print('\n📋 Checking documents table for family columns...')
    doc_columns = inspector.get_columns('documents')
    family_columns = ['family_id', 'version_number', 'is_latest_version', 'content_hash', 'source_url']
    
    existing_family_cols = []
    missing_family_cols = []
    
    doc_col_names = [col['name'] for col in doc_columns]
    
    for col in family_columns:
        if col in doc_col_names:
            existing_family_cols.append(col)
        else:
            missing_family_cols.append(col)
    
    if existing_family_cols:
        print(f'✅ Existing family columns: {existing_family_cols}')
    if missing_family_cols:
        print(f'❌ Missing family columns: {missing_family_cols}')

# Check alembic version
try:
    db = SessionLocal()
    result = db.execute("SELECT version_num FROM alembic_version").fetchone()
    if result:
        print(f'\n📊 Current Alembic version: {result[0]}')
    db.close()
except Exception as e:
    print(f'\n⚠️ Could not check Alembic version: {e}')