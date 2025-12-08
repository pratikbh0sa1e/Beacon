# 🗄️ Alembic Database Migrations - Complete Guide

## What is Alembic?

**Alembic** is a database migration tool for SQLAlchemy. Think of it as "Git for your database schema" - it tracks changes to your database structure over time and allows you to:

- ✅ Version control your database schema
- ✅ Apply changes incrementally
- ✅ Rollback changes if needed
- ✅ Share schema changes with team members
- ✅ Deploy database updates safely

---

## Why Use Alembic?

### Without Alembic (Manual Approach):
```sql
-- Developer 1 adds a column manually
ALTER TABLE users ADD COLUMN email_verified BOOLEAN;

-- Developer 2 doesn't know about this change
-- Production database is out of sync
-- Chaos ensues! 😱
```

### With Alembic (Automated Approach):
```python
# Migration file: add_email_verification_fields.py
def upgrade():
    op.add_column('users', sa.Column('email_verified', sa.Boolean()))

# Everyone runs: alembic upgrade head
# All databases stay in sync! ✅
```

---

## How Alembic Works in BEACON

### 1. Configuration Files

#### `alembic.ini` - Main Configuration
```ini
[alembic]
script_location = alembic          # Where migration files are stored
prepend_sys_path = .               # Add current directory to Python path
sqlalchemy.url =                   # Database URL (overridden by env.py)
```

**Key Settings:**
- `script_location`: Points to `alembic/` folder
- `sqlalchemy.url`: Left empty (we use .env instead)
- Logging configuration for debugging

#### `alembic/env.py` - Environment Setup
```python
from backend.database import Base, DATABASE_URL

# Load database URL from .env file
load_dotenv()

# Override sqlalchemy.url with our DATABASE_URL
config.set_main_option('sqlalchemy.url', DATABASE_URL)

# Use our SQLAlchemy models as the source of truth
target_metadata = Base.metadata
```

**What it does:**
1. Loads environment variables from `.env`
2. Constructs database URL from environment variables
3. Imports your SQLAlchemy models (`Base.metadata`)
4. Configures Alembic to use your database

---

## 2. Migration Files Structure

### Location: `alembic/versions/`

Your project has **21 migration files** that track the evolution of your database:

```
alembic/versions/
├── 002_add_document_metadata.py           # Added metadata table
├── add_email_verification_fields.py       # Email verification system
├── add_document_chat_tables.py            # Chat functionality
├── add_document_workflow_fields.py        # Approval workflows
├── add_parent_ministry.py                 # Institution hierarchy
├── remove_government_dept.py              # Simplified institution types
├── add_performance_indexes.py             # Database optimization
├── fix_foreign_key_constraints.py         # Fixed relationships
└── ... (and more)
```

### Migration File Anatomy

Let's break down a real migration file:

```python
"""add email verification fields

Revision ID: add_email_verification      # Unique identifier
Revises: 9efcc1f82b81                    # Previous migration
Create Date: 2024-12-01 00:00:00.000000  # When created

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_email_verification'       # This migration's ID
down_revision = '9efcc1f82b81'           # Parent migration
branch_labels = None                      # For branching (advanced)
depends_on = None                         # Dependencies (advanced)


def upgrade():
    """Apply changes to database"""
    # Add new columns
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), 
                                      nullable=False, server_default='false'))
    op.add_column('users', sa.Column('verification_token', sa.String(255), 
                                      nullable=True))
    op.add_column('users', sa.Column('verification_token_expires', 
                                      sa.DateTime(), nullable=True))
    
    # Create indexes for performance
    op.create_index('ix_users_email_verified', 'users', ['email_verified'])
    op.create_index('ix_users_verification_token', 'users', 
                    ['verification_token'], unique=True)


def downgrade():
    """Undo changes (rollback)"""
    # Remove indexes
    op.drop_index('ix_users_verification_token', 'users')
    op.drop_index('ix_users_email_verified', 'users')
    
    # Remove columns
    op.drop_column('users', 'verification_token_expires')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'email_verified')
```

**Key Components:**

1. **Docstring**: Human-readable description
2. **Revision IDs**: Unique identifiers for version tracking
3. **upgrade()**: Forward migration (apply changes)
4. **downgrade()**: Reverse migration (undo changes)

---

## 3. Migration Chain (Version History)

Alembic maintains a **chain of migrations** like Git commits:

```
Initial DB
    ↓
002_add_document_metadata
    ↓
add_email_verification_fields
    ↓
add_document_chat_tables
    ↓
add_document_workflow_fields
    ↓
add_parent_ministry
    ↓
remove_government_dept
    ↓
add_performance_indexes
    ↓
[Current State]
```

Each migration knows its **parent** (down_revision), creating a linked list.

---

## 4. Common Alembic Commands

### Check Current Version
```bash
alembic current
```
**Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
add_performance_indexes (head)
```

### View Migration History
```bash
alembic history
```
**Output:**
```
add_performance_indexes -> (head)
remove_government_dept -> add_performance_indexes
add_parent_ministry -> remove_government_dept
...
```

### Apply All Pending Migrations
```bash
alembic upgrade head
```
**What it does:**
1. Checks current database version
2. Finds all migrations between current and "head" (latest)
3. Runs `upgrade()` function in each migration
4. Updates `alembic_version` table

**Output:**
```
INFO  [alembic.runtime.migration] Running upgrade 9efcc1f82b81 -> add_email_verification
INFO  [alembic.runtime.migration] Running upgrade add_email_verification -> add_document_chat
```

### Rollback One Migration
```bash
alembic downgrade -1
```
**What it does:**
- Runs `downgrade()` function of the last migration
- Moves database back one version

### Rollback to Specific Version
```bash
alembic downgrade add_email_verification
```

### Upgrade to Specific Version
```bash
alembic upgrade add_document_chat
```

---

## 5. Creating New Migrations

### Method 1: Auto-generate from Models (Recommended)

```bash
# 1. Update your SQLAlchemy models in backend/database.py
# Example: Add a new field to User model
class User(Base):
    __tablename__ = "users"
    # ... existing fields
    phone_number = Column(String(20), nullable=True)  # NEW FIELD

# 2. Generate migration automatically
alembic revision --autogenerate -m "add phone number to users"
```

**What happens:**
1. Alembic compares your models (`Base.metadata`) with current database
2. Detects differences (new column)
3. Generates migration file with `upgrade()` and `downgrade()`
4. You review and edit if needed

**Generated file:**
```python
def upgrade():
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))

def downgrade():
    op.drop_column('users', 'phone_number')
```

### Method 2: Manual Migration

```bash
# Create empty migration file
alembic revision -m "add custom index"
```

**Then edit manually:**
```python
def upgrade():
    op.create_index('ix_custom_index', 'users', ['email', 'institution_id'])

def downgrade():
    op.drop_index('ix_custom_index', 'users')
```

---

## 6. Real Examples from BEACON

### Example 1: Adding Email Verification

**File:** `add_email_verification_fields.py`

**What it does:**
- Adds 3 new columns to `users` table
- Creates indexes for performance
- Enables email verification feature

**Before migration:**
```sql
users table:
- id
- name
- email
- password
```

**After migration:**
```sql
users table:
- id
- name
- email
- password
- email_verified          ← NEW
- verification_token      ← NEW
- verification_token_expires ← NEW
```

### Example 2: Adding Document Chat

**File:** `add_document_chat_tables.py`

**What it does:**
- Creates 2 new tables: `document_chat_messages` and `document_chat_participants`
- Sets up foreign keys
- Creates indexes

**Tables created:**
```sql
document_chat_messages:
- id
- document_id (FK → documents.id)
- user_id (FK → users.id)
- content
- message_type
- citations (JSONB)
- created_at

document_chat_participants:
- id
- document_id (FK → documents.id)
- user_id (FK → users.id)
- last_seen
- is_active
```

### Example 3: Removing Government Department Type

**File:** `remove_government_dept.py`

**What it does:**
- Converts all `government_dept` institutions to `university`
- Simplifies institution types to just 2: `ministry` and `university`

**SQL executed:**
```sql
UPDATE institutions 
SET type = 'university'
WHERE type = 'government_dept';
```

---

## 7. The `alembic_version` Table

Alembic creates a special table to track the current version:

```sql
SELECT * FROM alembic_version;
```

**Output:**
```
version_num
--------------------------
add_performance_indexes
```

This tells Alembic which migrations have been applied.

---

## 8. Migration Best Practices

### ✅ DO:

1. **Always review auto-generated migrations**
   ```bash
   alembic revision --autogenerate -m "description"
   # Open the generated file and review before applying!
   ```

2. **Test migrations on development database first**
   ```bash
   # Test upgrade
   alembic upgrade head
   
   # Test downgrade
   alembic downgrade -1
   
   # Re-upgrade
   alembic upgrade head
   ```

3. **Write descriptive migration messages**
   ```bash
   # Good
   alembic revision -m "add email verification fields to users table"
   
   # Bad
   alembic revision -m "update"
   ```

4. **Include both upgrade() and downgrade()**
   - Always provide a way to rollback changes

5. **Use transactions for data migrations**
   ```python
   def upgrade():
       connection = op.get_bind()
       connection.execute("""
           UPDATE users SET role = 'student' WHERE role IS NULL
       """)
   ```

### ❌ DON'T:

1. **Don't edit applied migrations**
   - Once a migration is applied, don't change it
   - Create a new migration instead

2. **Don't skip migrations**
   - Always apply migrations in order
   - Don't manually modify database and skip migrations

3. **Don't delete migration files**
   - Keep all migrations for history
   - Even if you rollback, keep the file

4. **Don't commit database changes without migrations**
   - If you change models, create a migration
   - Keep code and database in sync

---

## 9. Common Scenarios

### Scenario 1: New Developer Setup

```bash
# 1. Clone repository
git clone <repo>

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file with database credentials

# 4. Apply all migrations
alembic upgrade head

# Database is now up to date! ✅
```

### Scenario 2: Adding a New Feature

```bash
# 1. Update SQLAlchemy models
# Edit backend/database.py

# 2. Generate migration
alembic revision --autogenerate -m "add feature X"

# 3. Review generated migration file
# Edit alembic/versions/xxxxx_add_feature_x.py

# 4. Apply migration
alembic upgrade head

# 5. Commit both model changes and migration file
git add backend/database.py alembic/versions/xxxxx_add_feature_x.py
git commit -m "Add feature X with database migration"
```

### Scenario 3: Production Deployment

```bash
# 1. Pull latest code
git pull origin main

# 2. Check pending migrations
alembic current
alembic history

# 3. Backup database (IMPORTANT!)
pg_dump -h HOST -U USER -d DATABASE > backup.sql

# 4. Apply migrations
alembic upgrade head

# 5. Verify application works
# If issues, rollback:
# alembic downgrade -1
```

### Scenario 4: Fixing a Bad Migration

```bash
# If you just applied a bad migration:

# 1. Rollback
alembic downgrade -1

# 2. Edit the migration file
# Fix the issue in alembic/versions/xxxxx_bad_migration.py

# 3. Re-apply
alembic upgrade head

# If migration was already committed and pushed:

# 1. Create a new migration to fix it
alembic revision -m "fix previous migration issue"

# 2. Write corrective SQL in upgrade()
def upgrade():
    op.execute("ALTER TABLE users ALTER COLUMN email SET NOT NULL")

# 3. Apply
alembic upgrade head
```

---
env.py`alembic/c.ini` and `lembin: `anfiguratioons/`
- Coersiembic/vtions: `almigrar  Youemy.org/
-ic.sqlalchps://alembs: httc Doc Alembi?**
- Help
**Need
---
ther.
smooration m collabotear and oyments safe making deplhanges,s database cckic tranges, Alembe chacodracks e Git tm. Just lik syste controlse's versiontabais your da:** Alembic  Takeaways  

**Keyistencienss and incoQL error S manualvents**e  
✅ **Preyour databasvolution of ** the eocuments **D
✅mbers   meacross teame schema  databasonizes**
✅ **Synchrues occur  if isslbacks ** safe rolables  
✅ **Entsonmens envircrospdates aabase utes** datomaut✅ **Aes  
a changchembase ss** 21+ datarack
✅ **TEACON:**
embic in Bmary

**Al
## Sum-
--ead
```

 stamp h
alembicmigrations)ing thout runn version (wi specific top databasel

# Stamd --sqhearade ic upgng
alembexecutit SQL withouow Sh
# 
ion_id>de <revisc upgrabirsion
alem specific vepgrade toid>

# Uision_grade <revalembic downsion
verfic ck to speci
# Rollbaiption"
-m "descric revision 
alembanual)tion (mgrapty miCreate emion"

# cript -m "desgenerateion --autoic revis)
alembchangesetect on (auto-dmigratiate new Cre1

#  -ngradebic dowlemtion
ak one migra# Rollbac
 head
pgradec ualembigrations
 mily alle

# App--verbosy c historbistory
alemw hint

# Vieurren
alembic crent versioeck cur
# Chs

```bashCommand# Most Used ce

##ferenuick Re
## 12. Q
---
e!
```
.. and more

.es featurrsonal notd pedde └─ Apy)
   e.bl_ta_notess (add_user. User Noteaints

12strconationship  rel Fixed.py)
    └─ntsonstrai_key_ceigns (fix_for FixeForeign Keyd

11. or speee indexes fdatabasd     └─ Adde
xes.py)ndemance_irfor (add_pexesrmance Inde
10. Perfo types
titutioned ins└─ Simplifipt.py)
   ent_demove_governmt Dept (reGovernmen9. Remove 

n hierarchyd institutio Adde   └─nistry.py)
midd_parent_inistry (a MntPare
8. fields
w workflooval dded appr └─ Ads.py)
  ow_fielorkflocument_w_dadd Fields (7. Workflow

alityt function chaument└─ Added docles.py)
   hat_tabd_document_cadat System (
6. Chtem
ication syserifl vAdded emai
   └─ ds.py)on_fielficativeri_email_addn (Verificatiomail 5. Eation

grnte ita source danalded exter
   └─ Ad.py)rcesnal_data_souadd_exterc1f82b81_rces (9efc Sounal DataerExt
4. elds
 storage fiAdded S3.py)
   └─ rage_supportse_stopaba880_add_sud7a8orage (5b95a Supabase St
3. details
cumentle for doadata tab└─ Added met
   tadata.py)t_medd_documenta (002_aent MetadaDocum. )

2itutionsuments, inst doc (users, tablesBasic └─ p
  Initial Setu. 
```
1tabase:
N's daon of BEACOtie evoluhere's thtion files, n your migra

Based oetion Timelin Migrar Project'sou11. Y---

## d
```

stamp hea
alembic y, then:se manuall Fix databap version
#tamase and satably fix dManual# Option 2: head

ic upgrade alembde -1
gradown
alembic applyre-llback and on 1: Rosh
# Opti*
```baion:*olutfied

**Sodiually manabase was m or datally appliedrtias paation w** Migr

**Cause:" existsreadylumn al Error: "Co###ad
```

hebic upgrade 
alemge mer"

# Applyn branchesmigratioe s -m "mergerge head m
alembicgrationge miate merrebash
# Con:**
```

**Solutiltaneously)ns simud migratios createervelop(two deons  migraticonflict inrge Cause:** Me**nt"

reseions are pisad revMultiple he## Error: "
#ad
```
e heic upgradembd
algrade to hea
# Up current
on
alembicent versik curr
# Checpull
 code
git estll lat Pu
```bash
#**ion:*Solut

*ead of codebase is ah** DataCause:
**"
 to datee is not upt databasr: "Targe
### Erroead
```
 stamp hon
alembicect versiamp to corrpted, strru
# If coion"
embic_versM alLECT * FRO "SETABASE -cSER -d DAU Ul -h HOST -able
psqion tersck alembic_vChesions/

# ver alembic/xist
ls elesfimigration heck ash
# C*
```b:*tionh

**Solu ID mismatcrevisionng or simisis tion file ** Migra*Cause:"

*y 'xxxxx'tified bon idenate revisilocCan't  Error: "
###g
inoubleshoot

## 10. Tr