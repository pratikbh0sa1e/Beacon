# 🗄️ Alembic in BEACON - Complete Explanation

## What is Alembic?

**Alembic** is a database migration tool for SQLAlchemy. Think of it as **"Git for your database"** - it tracks and manages changes to your database structure over time.

### Why Do We Need It?

**Without Alembic:**
```sql
-- Developer 1 manually adds a column
ALTER TABLE users ADD COLUMN email_verified BOOLEAN;

-- Developer 2 doesn't know about this
-- Production database is out of sync
-- Chaos! 😱
```

**With Alembic:**
```python
# Migration file tracks the change
def upgrade():
    op.add_column('users', sa.Column('email_verified', sa.Boolean()))

# Everyone runs: alembic upgrade head
# All databases stay in sync! ✅
```

---

## How Alembic Works in Your Project

### 1. Configuration Files

#### `alembic.ini` - Main Config
```ini
[alembic]
script_location = alembic          # Where migrations are stored
sqlalchemy.url =                   # Database URL (we use .env instead)
```

#### `alembic/env.py` - Environment Setup
```python
from backend.database import Base, DATABASE_URL

# Load from .env file
load_dotenv()

# Use our database URL
config.set_main_option('sqlalchemy.url', DATABASE_URL)

# Use our SQLAlchemy models
target_metadata = Base.metadata
```

**What it does:**
1. Loads your `.env` file
2. Gets database credentials
3. Connects Alembic to your database
4. Uses your SQLAlchemy models as the "source of truth"

---

### 2. Migration Files

**Location:** `alembic/y.org/
ic.sqlalchemembtps://al** hte:Mor

**Learn ablec_version` tbilemacking: `abase tr
- Dataions/`embic/vers `alions:at.py`
- Migr/env `alembicbic.ini`,on: `alematinfigurles:**
- Colembic Fi

**Your A-- safer.

-tsdeploymennd makes on, aatiaborenables collks changes, e. It trac databas for your Gitc ismbiAleay:** y Takeaw

**Kerrors  anual SQL ents m  
✅ Preveevolutiontabase  daDocuments 
✅  team a acrosses schem✅ Synchronizcks  
ollbaables safe r  
✅ Ene updatesates databas
✅ Automchanges  ma atabase scheracks 21+ dN:**

✅ T BEACOinbic lem
**Ary
# Summa

---

#ql
```de head --spgrambic ucuting
aleithout exew SQL w"

# Shoonticrip -m "desonc revision
alembitimigrampty eate e

# Cription"m "descrate -erutogen--aision alembic revct)
deteo-ation (autigr Create m1

#ade -ic downgrne
alembollback od

# Rpgrade heac ubilemrations
a mig Apply all

#ic historystory
alembw hiVieurrent

# embic c
alersionent vheck curr```bash
# Cnce

 Refere

## Quick``

---e head
`radalembic upg1
e -bic downgradly
alempp re-a andllback`bash
# Ron:**
``

**Solutiody exists"alrea: "Column ror## Er

#
```adade heupgr"
alembic chesbran -m "merge adsbic merge hetion
alemrge migrareate mebash
# C:**
```ution"

**Solevisionsple head rr: "MultiErro```

### tamp head

alembic srect versioncortamp to 

# S/versions/mbic
ls alees existiligration fCheck m``bash
# 
`on:**
**Solutin"
evisiot locate rCan'# Error: "ng

##tileshooroub
---

## Tion
ate a migratcreways 
   - Alrations**t migouabase withe daty changnuall. **Don't mastory

4r hifo Keep them 
   - files**igrationete m **Don't del3.er

 them in ord - Apply
  igrations** mipt sk**Don'
2. on instead
atie a new migr- Creat  tions**
  migraliedt edit app*Don''T:

1. *DON

### ❌ geschanback way to rolle a idov)**
   - Pr downgrade(deways inclu
4. **Al
   ```
date"on -m "upc revisid
   alembi   
   # Basers"
n to uverificatiol m "add emaivision - re alembicd
  # Gooh
    ```bas*
  ssages*ptive meite descri

3. **Wr ```upgrade
  ad    # Re-pgrade he  alembic u
  rollbackTest -1    # ic downgrade
   alembgradest up# Te    head bic upgradesh
   alem**
   ```bat firstenlopmst on deve

2. **Teing!
   ```applyle before eview the fipen and ron"
   # Ocriptides-m "e ogenerat --autrevisionmbic 
   alesh  ```baons**
 tirated migra auto-geneevieways r **Alw ✅ DO:

1.
###
cesactiBest Pr--

## 

-d more!
```.. antes

.personal no  └─ Added 
  Notesr seps

12. Utionshi relaFixed └─ es
   ixoreign Key F

11. Fse indexestabaAdded daes
    └─ exrmance Ind10. Perfotypes

institution ed  Simplifiept
   └─ernment Dmove Govy

9. Reierarchon htistitu└─ Added ininistry
   ent M

8. Parorkflowspproval w Added aields
   └─low FrkfWohat

7.  centded docum   └─ Adt System
. Chasystem

6cation rifi ve  └─ Addedfication
 eri5. Email V
ion
gratintea source  dat   └─ Added Sources
l Datana. Exter

4e supportstoragAdded S3 ge
   └─ se StoraabaSup
3. able
a ttadatdded me A  └─tadata
 ment Me
2. Docuutions)
 instit documents,(users,les sic tab   └─ Baup
SetInitial 

```
1. ase evolved:tab daON's BEAC's hows, herefiletion  migran your 21Based ovolution

ect's E Proj
## Your
``

---ion works
`icatfy appl 4. Veri
#ad
upgrade hec bi
alemationsy migrAppl

# 3. p.sqlE > backud DATABAST -U USER -h HOS -T!)
pg_dump(IMPORTANbase kup data# 2. Bac

inl origin ma pult code
git latesll
# 1. Pubash
```ployment
ion Dectodu# Pr

##eld"
```er fi phone numbdd"Am t -
git commie_number.pyonph_add_xxversions/xxxc/bipy alematabase.d/dt add backenes
giit both fil
# 5. Commd
 heac upgradeembi
altionigray m 4. Applpy

#number.dd_phone_xx_aions/xxxalembic/versck ile
# Cheerated fgeneview 
# 3. Rber"
dd phone num-m "agenerate -autovision -mbic re
aleigrationte menera2. G
# ELD
# NEW FIring(20))  mn(Stber = Colue_numonphBase):
    ass User(.py
cldatabasend/it backe
# Edhemy modelslcUpdate SQLA`bash
# 1. re

`` New Featung a## Addi

#! ✅
```up to dates now base i Dataead

#rade hic upg
alembationsly all migr
# 4. App
entialsredse cdatabanv with Create .e

# 3. ts.txtmenl -r requireinstales
pip ependenci dstall

# 2. In<repo>one t cl
gi repo
# 1. Cloneash``bup

`per Set New Develo
###es
 Examplow
## Workfl

---
ed.een applihave b migrations lembic which tells A`

Thisindexes
``nce__performa
add-----------------
---------sion_num``
ver:**
`
**Output;
```
bic_version FROM alem
SELECT *`sql

``n`embic_versiotable: `als a special embic create

Alionsacks Vers Tr Alembic--

## How

-om 3 to 2.s frution types institfieSimpli`

';
``rnment_dept= 'goveHERE type ersity'
W 'univtype =T s 
SEutioninstitl
UPDATE *
```sq data:*convertson ti
**Migraepartment
ment De Governe 3: Removmpl

### Exa
```iven
- is_act
- last_seeuser_idment_id
- - docu
- id
ipants:t_particcument_cha
dot
_aeated- crs (JSONB)
ationype
- cit
- message_tent.id)
- conters (FK → usser_id)
- uments.id→ docuK  (Fdocument_id id
- s:
-hat_messagement_cql
docu
```sables:**
ates 2 new t crerationt

**MigDocument Cha: ## Example 2
```

#res ← NEWpin_token_exicatio
- verif    ← NEWken  _toficationNEW
- veri          ← fiedail_veriord
- em- passw
- email
 name:
- id
-users table
ql
```s**elds.py`:tion_fifica_veri_emailrunning `add
**After `
ord
``
- passw
- emailid
- name table:
- `sql
users*
``gration:*
**Before min
 Verificatioe 1: Emailxampl# E
##
EACON Bmples from## Real Exa---


```

om index"dd custm "ac revision -
alembimigrationempty e # Or creatmber"

dd phone nuerate -m "a--autogension ic revidels
alemb moanges fromect ch-detAuto# ``bash
gration
`reate New Mi## Cation.

#of last migrrade()` ns `downg`
Ru
``wngrade -1ic dolemb```bash
ation
e MigraOnack ollb

### Rversiontest abase to ladates dation
4. Upmigrateach grade()` in uns `uptions
3. Rng migrandill pes an
2. Findse versiorent databaur1. Checks cppens:**
What ha
```
**dgrade hea
alembic upash```bons
gratiply All Mi
### Ap
 in order.tionsl migras al```
Showstory
c hi
alembi
```bash History
### View
 is at.r databasetion yougra miwhich
```
Shows c currentlembibash
a
```sionurrent Ver C## Check
#
ommandsmmon C--

## Cory.

-ion histoersing a vreatent, cnows its par kch migration`

Ea
``State]
[Current     ↓indexes
e_d_performanc
    ↓
adt_deptnmenverve_go    ↓
remoy
nistrd_parent_miadlds
    ↓
rkflow_fie
add_woles
    ↓at_tabnt_ch_docume
    ↓
addieldsrification_f_email_ve    ↓
addmetadata
t_ocumen ↓
add_d  
  Databaseial
Init```
s:
igrationhain** of ma **linked caintains ic m

Alembtory)ison Hersiain (VMigration Ch--

## 

-in)reates a chaigration (c**: Parent mn_revision
- **dowationthis migrD for que I*: Unievision*- **r(rollback)
nges ndoes chae()**: U- **downgradbase
s to datalies changepp Aade()**: **upgrs:**
- Partey

**K')
```verified 'email_n('users',columdrop_ op.)
   _token'ificationsers', 'verp_column('uop.drolumns
    ve co    # Remo')
    
usersfied', 'email_veriix_users_('index  op.drop_dex
  ove in Rem #"""
   k)s (rollbacgehan"Undo c  ""  ngrade():
ow
def d
])
_verified'', ['email 'users            ', 
       _verifiedailemx('ix_users_ate_inde
    op.creformance for perate index    # Cre)
    
(255))tringen', sa.Sn_tokiocatlumn('verifi     sa.Coers', 
   column('usd_ 
    op.adalse'))
   r_default='fe, servellable=Fals    nu              , 
olean()ed', sa.Boail_verifi.Column('em sa', 
       lumn('usersdd_cons
    op.add new colum"
    # A)""orwardhanges (f cply  """Ap():
   upgradedefion


at migr    # Parent    82b81'   9efcc1f = 'n_revision
dowration's IDis mig # Th    n'  verificatioil_emasion = 'add_s sa

reviy aemqlalch s
import import op alembic""
from-12-01
" 2024eate Date:tion
Cr migrarevious # P             b81      s: 9efcc1f82ID
Revisenique  # Uon     erificatidd_email_vID: a
Revision n fields
 verificatiodd email"""a

```python
eal example: at a r
Let's lookructure
ile Stgration F## 3. Mi
#

```

--- (and more)─ ...mization
└─optiSpeed   #          xes.py  nce_indeorma add_perf├──ypes
Simplified t  #           nt_dept.py  rnmemove_govehy
├── reion hierarc  # Institut       y.py        t_ministrparen
├── add_oval systemppr A    #y    ds.porkflow_fiel_document_wure
├── addt feat  # Cha          tables.pyent_chat__docum├── addn
atiol verific# Emaids.py       tion_fielrifical_vemai├── add_e/
ionsmbic/vers
ale
```
evolution:database  tracking files**ation s **21 migrject ha
Your pros/`
version