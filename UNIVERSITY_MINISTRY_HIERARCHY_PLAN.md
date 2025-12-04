# University-Ministry Hierarchy Implementation Plan

## Overview

Link universities to their governing ministries to enable hierarchical approval workflows.

---

## 🎯 Goal

**Current:** Universities are independent entities
**Target:** Universities linked to parent ministries

### Example Hierarchy:

```
Ministry of Education
├── IIT Delhi
├── IIT Bombay
├── Delhi University
└── JNU

Ministry of Health
├── AIIMS Delhi
├── AIIMS Mumbai
└── NIMHANS

Ministry of Defence
├── National Defence Academy
└── Indian Military Academy
```

---

## 📊 Database Changes

### 1. Add `parent_ministry_id` to institutions table

```sql
ALTER TABLE institutions
ADD COLUMN parent_ministry_id INTEGER REFERENCES institutions(id);

-- Add index for performance
CREATE INDEX idx_institutions_parent_ministry ON institutions(parent_ministry_id);

-- Add constraint: only universities can have parent ministry
ALTER TABLE institutions
ADD CONSTRAINT check_parent_ministry
CHECK (
  (type = 'university' AND parent_ministry_id IS NOT NULL) OR
  (type != 'university' AND parent_ministry_id IS NULL)
);
```

### 2. Update Institution Model

```python
class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    location = Column(String(255), nullable=True)
    type = Column(String(50), nullable=False)
    parent_ministry_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="institution")
    parent_ministry = relationship("Institution", remote_side=[id], foreign_keys=[parent_ministry_id])
    child_universities = relationship("Institution", back_populates="parent_ministry")
```

---

## 🔄 Approval Workflow Changes

### Current Flow:

```
University Admin → Ministry Admin (all ministries)
```

### New Flow:

```
IIT Delhi Admin → Ministry of Education Admin (specific)
AIIMS Admin → Ministry of Health Admin (specific)
```

### Benefits:

1. ✅ Targeted notifications (only relevant ministry)
2. ✅ Clear hierarchy
3. ✅ Better organization
4. ✅ Scalable for multiple ministries

---

## 🎨 Frontend Changes

### 1. Institution Creation Form (Universities Tab)

**Add Ministry Selection:**

```javascript
{
  activeTab === "university" && (
    <div className="space-y-2">
      <Label htmlFor="parent_ministry">
        Governing Ministry <span className="text-destructive">*</span>
      </Label>
      <Select
        value={formData.parent_ministry_id}
        onValueChange={(v) =>
          setFormData({ ...formData, parent_ministry_id: v })
        }
        required
      >
        <SelectTrigger>
          <SelectValue placeholder="Select ministry" />
        </SelectTrigger>
        <SelectContent>
          {ministries.map((ministry) => (
            <SelectItem key={ministry.id} value={String(ministry.id)}>
              {ministry.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
```

### 2. Institution Cards

**Show Parent Ministry:**

```javascript
{
  inst.type === "university" && inst.parent_ministry && (
    <Badge variant="outline" className="text-xs">
      <Landmark className="h-3 w-3 mr-1" />
      {inst.parent_ministry.name}
    </Badge>
  );
}
```

### 3. Ministries Tab

**Show Child Universities:**

```javascript
{
  inst.type === "ministry" && (
    <div className="text-xs text-muted-foreground">
      {inst.child_universities?.length || 0} universities
    </div>
  );
}
```

---

## 🔔 Notification Changes

### Update notification_helper.py

**Before:**

```python
# Send to ALL ministry admins
ministry_admins = db.query(User).filter(User.role == "ministry_admin").all()
```

**After:**

```python
# Send to SPECIFIC ministry admins
university = db.query(Institution).filter(Institution.id == document.institution_id).first()
if university and university.parent_ministry_id:
    ministry_admins = db.query(User).filter(
        User.role == "ministry_admin",
        User.institution_id == university.parent_ministry_id
    ).all()
```

---

## 📝 Migration Script

```python
"""add parent ministry to institutions

Revision ID: add_parent_ministry_001
Revises: generalize_ministry_001
Create Date: 2024-12-03 22:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_parent_ministry_001'
down_revision = 'generalize_ministry_001'
branch_labels = None
depends_on = None


def upgrade():
    # Add parent_ministry_id column
    op.add_column('institutions',
        sa.Column('parent_ministry_id', sa.Integer(), nullable=True)
    )

    # Add foreign key
    op.create_foreign_key(
        'fk_institutions_parent_ministry',
        'institutions', 'institutions',
        ['parent_ministry_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add index
    op.create_index(
        'idx_institutions_parent_ministry',
        'institutions',
        ['parent_ministry_id']
    )

    # Link existing universities to Ministry of Education (if exists)
    op.execute("""
        UPDATE institutions
        SET parent_ministry_id = (
            SELECT id FROM institutions
            WHERE name = 'Ministry of Education'
            AND type = 'ministry'
            LIMIT 1
        )
        WHERE type = 'university'
        AND parent_ministry_id IS NULL
    """)


def downgrade():
    op.drop_constraint('fk_institutions_parent_ministry', 'institutions')
    op.drop_index('idx_institutions_parent_ministry', 'institutions')
    op.drop_column('institutions', 'parent_ministry_id')
```

---

## 🧪 Testing Scenarios

### Scenario 1: Create University

```
1. Admin clicks "Universities" tab
2. Clicks "+ Add University"
3. Form shows:
   - University Name: "IIT Delhi"
   - Location: "Delhi"
   - Governing Ministry: [Dropdown with ministries]
4. Selects "Ministry of Education"
5. Submits
6. University created with parent_ministry_id set
```

### Scenario 2: Approval Request

```
1. IIT Delhi admin uploads document
2. Submits for review
3. Notification sent ONLY to Ministry of Education admins
4. NOT sent to Health Ministry or other ministries
```

### Scenario 3: View Hierarchy

```
Ministries Tab:
- Ministry of Education (5 universities)
  Click to expand → Shows: IIT Delhi, IIT Bombay, etc.

Universities Tab:
- IIT Delhi
  Badge: "Ministry of Education"
```

---

## 🎯 API Changes

### 1. Institution Create Endpoint

**Update Request Body:**

```python
class InstitutionCreate(BaseModel):
    name: str
    location: Optional[str]
    type: str
    parent_ministry_id: Optional[int] = None  # NEW
```

**Add Validation:**

```python
# If type is university, parent_ministry_id is required
if data.type == "university" and not data.parent_ministry_id:
    raise HTTPException(400, "Universities must have a parent ministry")

# Validate parent is actually a ministry
if data.parent_ministry_id:
    parent = db.query(Institution).filter(Institution.id == data.parent_ministry_id).first()
    if not parent or parent.type != "ministry":
        raise HTTPException(400, "Parent must be a ministry")
```

### 2. Institution List Endpoint

**Include Parent Ministry:**

```python
return {
    "id": inst.id,
    "name": inst.name,
    "type": inst.type,
    "location": inst.location,
    "parent_ministry": {
        "id": inst.parent_ministry.id,
        "name": inst.parent_ministry.name
    } if inst.parent_ministry else None,
    "child_universities_count": len(inst.child_universities) if inst.type == "ministry" else 0
}
```

---

## 🔮 Future Enhancements

### 1. Multi-Level Hierarchy

```
Ministry of Education
└── Department of Higher Education
    ├── IIT Delhi
    ├── IIT Bombay
    └── Delhi University
```

### 2. Ministry Dashboard

- Show all child universities
- Aggregate statistics
- Bulk actions

### 3. Transfer Universities

- Move university from one ministry to another
- Update all related approvals

### 4. Approval Delegation

- Ministry can delegate approval to department
- Department can delegate to specific officer

---

## ✅ Implementation Checklist

### Backend:

- [ ] Create migration file
- [ ] Update Institution model
- [ ] Update institution_router.py (create/list endpoints)
- [ ] Update notification_helper.py (targeted notifications)
- [ ] Add validation for parent ministry

### Frontend:

- [ ] Update InstitutionsPage form (add ministry dropdown)
- [ ] Fetch ministries list for dropdown
- [ ] Show parent ministry badge on university cards
- [ ] Show child count on ministry cards
- [ ] Update institution creation logic

### Testing:

- [ ] Create university with ministry
- [ ] Create university without ministry (should fail)
- [ ] Create ministry (no parent needed)
- [ ] Submit document for approval
- [ ] Verify notification goes to correct ministry
- [ ] View hierarchy in UI

---

## 📊 Data Examples

### After Implementation:

```sql
-- Ministries
INSERT INTO institutions (name, type, location, parent_ministry_id) VALUES
('Ministry of Education', 'ministry', 'New Delhi', NULL),
('Ministry of Health', 'ministry', 'New Delhi', NULL);

-- Universities under Education
INSERT INTO institutions (name, type, location, parent_ministry_id) VALUES
('IIT Delhi', 'university', 'Delhi', 1),
('IIT Bombay', 'university', 'Mumbai', 1),
('Delhi University', 'university', 'Delhi', 1);

-- Universities under Health
INSERT INTO institutions (name, type, location, parent_ministry_id) VALUES
('AIIMS Delhi', 'university', 'Delhi', 2),
('NIMHANS', 'university', 'Bangalore', 2);
```

---

## 🎯 Summary

**What Changes:**

- Universities must select parent ministry
- Approval requests go to specific ministry
- Clear organizational hierarchy
- Better notification targeting

**Benefits:**

- ✅ Scalable for multiple ministries
- ✅ Clear responsibility
- ✅ Reduced notification noise
- ✅ Better organization

**Next Steps:**

1. Run migration
2. Update backend code
3. Update frontend form
4. Test approval workflow

---

**Status:** READY TO IMPLEMENT

**Estimated Time:** 2-3 hours
