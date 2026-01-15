#!/usr/bin/env python3
"""Check actual table columns"""
import sys
import os
sys.path.append('.')
from dotenv import load_dotenv
load_dotenv()

from backend.database import SessionLocal, engine
from sqlalchemy import inspect

# Check documents table structure
inspector = inspect(engine)
doc_columns = inspector.get_columns('documents')

print('📋 Documents table columns:')
for col in doc_columns:
    print(f'  - {col["name"]}: {col["type"]}')

# Check document_families table structure  
family_columns = inspector.get_columns('document_families')
print('\n📋 Document_families table columns:')
for col in family_columns:
    print(f'  - {col["name"]}: {col["type"]}')

# Check if there are any foreign key relationships
fks = inspector.get_foreign_keys('documents')
print('\n🔗 Foreign keys in documents table:')
for fk in fks:
    print(f'  - {fk["constrained_columns"]} -> {fk["referred_table"]}.{fk["referred_columns"]}')