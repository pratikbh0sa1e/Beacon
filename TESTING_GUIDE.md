# Testing Guide - Institution Hierarchy & Two-Step Registration

## Quick Start

### Option 1: Automated Testing (Recommended)

```bash
# Make sure backend is running
cd backend
uvicorn main:app --reload

# In another terminal, run test script
python scripts/test_institution_hierarchy.py
```

This will automatically:

- ✅ Create test ministries
- ✅ Create test institutions under each ministry
- ✅ Verify government_dept is rejected
- ✅ Register test users with different roles
- ✅ Verify hierarchy is correct

---

### Option 2: Manual Testing

## Step 1: Start Backend & Frontend

```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

---

## Step 2: Login as Developer

1. Go to: http://localhost:5173/login
2. Login with:
   - Email: `dev@beacon.gov.in`
   - Password: `dev123456`

---

## Step 3: Test Institution Management

### 3.1 Verify Only 2 Tabs

1. Go to: **Admin → Institutions**
2. ✅ Should see only 2 tabs:
   - **Institutions**
   - **Ministries**
3. ❌ Should NOT see "Departments" tab

### 3.2 Create Ministries

1. Click **Ministries** tab
2. Click **Add Ministry**
3. Create these ministries:

   ```
   Name: Ministry of Education
   Location: New Delhi

   Name: Ministry of Health and Family Welfare
   Location: New Delhi

   Name: Ministry of Defence
   Location: New Delhi
   ```

### 3.3 Create Institutions

1. Click **Institutions** tab
2. Click **Add Institution**
3. Create these institutions:

   **Under Ministry of Education:**

   ```
   Name: IIT Delhi
   Location: Delhi
   Ministry: Ministry of Education

   Name: IIT Mumbai
   Location: Mumbai
   Ministry: Ministry of Education

   Name: Delhi University
   Location: Delhi
   Ministry: Ministry of Education
   ```

   **Under Ministry of Health:**

   ```
   Name: AIIMS Delhi
   Location: Delhi
   Ministry: Ministry of Health and Family Welfare

   Name: AIIMS Mumbai
   Location: Mumbai
   Ministry: Ministry of Health and Family Welfare
   ```

   **Under Ministry of Defence:**

   ```
   Name: DRDO Bangalore
   Location: Bangalore
   Ministry: Ministry of Defence

   Name: National Defence Academy
   Location: Pune
   Ministry: Ministry of Defence
   ```

### 3.4 Verify Hierarchy

1. Click **Ministries** tab
2. Each ministry card should show:
   - Ministry name
   - Location
   - Number of institutions (e.g., "3 institutions")

---

## Step 4: Test User Registration (Two-Step Selection)

### 4.1 Test Ministry Admin (Single Step)

1. Logout (if logged in)
2. Go to: http://localhost:5173/register
3. Fill form:
   ```
   Name: Test Ministry Admin
   Email: ministry.admin@test.com
   Role: Ministry Admin
   Ministry: Ministry of Education (single dropdown)
   Password: test123456
   Confirm Password: test123456
   ```
4. ✅ Should see single dropdown for ministry
5. ✅ Should register successfully

### 4.2 Test Student (Two-Step)

1. Go to: http://localhost:5173/register
2. Fill form:
   ```
   Name: Test Student
   Email: student@test.com
   Role: Student
   ```
3. ✅ Should see **Step 1: Select Ministry**
4. Select: **Ministry of Education**
5. ✅ Should see **Step 2: Select Institution** (now enabled)
6. ✅ Should see filtered list:
   - IIT Delhi - Delhi
   - IIT Mumbai - Mumbai
   - Delhi University - Delhi
7. Select: **IIT Delhi**
8. Complete password fields
9. ✅ Should register successfully

### 4.3 Test Document Officer (Two-Step)

1. Go to: http://localhost:5173/register
2. Fill form:
   ```
   Name: Test Doctor
   Email: doctor@test.com
   Role: Document Officer
   ```
3. ✅ Should see **Step 1: Select Ministry**
4. Select: **Ministry of Health and Family Welfare**
5. ✅ Should see **Step 2: Select Institution** (now enabled)
6. ✅ Should see filtered list:
   - AIIMS Delhi - Delhi
   - AIIMS Mumbai - Mumbai
7. Select: **AIIMS Delhi**
8. Complete password fields
9. ✅ Should register successfully

### 4.4 Test University Admin (Two-Step)

1. Go to: http://localhost:5173/register
2. Fill form:
   ```
   Name: Test Admin
   Email: admin@test.com
   Role: University Admin
   ```
3. ✅ Should see **Step 1: Select Ministry**
4. Select: **Ministry of Defence**
5. ✅ Should see **Step 2: Select Institution** (now enabled)
6. ✅ Should see filtered list:
   - DRDO Bangalore - Bangalore
   - National Defence Academy - Pune
7. Select: **DRDO Bangalore**
8. Complete password fields
9. ✅ Should register successfully

### 4.5 Test Public Viewer (No Institution)

1. Go to: http://localhost:5173/register
2. Fill form:
   ```
   Name: Test Viewer
   Email: viewer@test.com
   Role: Public Viewer
   Password: test123456
   ```
3. ✅ Should NOT see any institution fields
4. ✅ Should register successfully

---

## Step 5: Test Reset Logic

### 5.1 Test Role Change Reset

1. Go to: http://localhost:5173/register
2. Select Role: **Student**
3. Select Ministry: **Ministry of Education**
4. Select Institution: **IIT Delhi**
5. Change Role to: **Ministry Admin**
6. ✅ Ministry and Institution selections should reset
7. ✅ Should see single ministry dropdown

### 5.2 Test Ministry Change Reset

1. Select Role: **Student**
2. Select Ministry: **Ministry of Education**
3. Select Institution: **IIT Delhi**
4. Change Ministry to: **Ministry of Health**
5. ✅ Institution selection should reset
6. ✅ Should see new filtered list (AIIMS Delhi, AIIMS Mumbai)

---

## Step 6: Verify Database

### 6.1 Check Institution Types

```sql
-- Connect to your database
SELECT type, COUNT(*)
FROM institutions
GROUP BY type;

-- Expected result:
-- ministry    | 3
-- university  | 7
-- (NO government_dept!)
```

### 6.2 Check Hierarchy

```sql
-- Check institutions have parent ministries
SELECT
  i.name as institution,
  m.name as ministry
FROM institutions i
LEFT JOIN institutions m ON i.parent_ministry_id = m.id
WHERE i.type = 'university';

-- Expected: All universities should have a ministry
```

### 6.3 Check Users

```sql
-- Check registered users
SELECT
  u.name,
  u.role,
  i.name as institution,
  i.type as institution_type
FROM users u
LEFT JOIN institutions i ON u.institution_id = i.id
WHERE u.email LIKE '%@test.com';

-- Verify each user has correct institution
```

---

## Expected Results Summary

### ✅ Institution Management:

- [x] Only 2 tabs visible (Institutions | Ministries)
- [x] Can create ministries
- [x] Can create institutions with parent ministry
- [x] Cannot create government_dept type
- [x] Cannot create institution without parent ministry
- [x] Ministry cards show child institution count

### ✅ User Registration:

- [x] Ministry Admin: Single dropdown
- [x] University roles: Two-step selection
- [x] Public Viewer: No institution field
- [x] Institution dropdown disabled until ministry selected
- [x] Institution list filtered by selected ministry
- [x] Role change resets selections
- [x] Ministry change resets institution

### ✅ Database:

- [x] No government_dept types exist
- [x] All universities have parent_ministry_id
- [x] Users correctly linked to institutions

---

## Troubleshooting

### Issue: "government_dept" still appears

**Solution:** Run migration again:

```bash
alembic upgrade head
```

### Issue: Institution dropdown not filtering

**Solution:** Check browser console for errors, refresh page

### Issue: Can't create institution without ministry

**Solution:** This is correct! Create ministry first

### Issue: Test script fails

**Solution:**

1. Make sure backend is running
2. Make sure developer account exists
3. Check credentials in script

---

## Quick Test Commands

```bash
# Run automated tests
python scripts/test_institution_hierarchy.py

# Check database
psql -U postgres -d your_database -c "SELECT type, COUNT(*) FROM institutions GROUP BY type;"

# Restart backend
uvicorn backend.main:app --reload

# Restart frontend
cd frontend && npm run dev
```

---

## Success Criteria

✅ All tests pass
✅ No government_dept in database
✅ Two-step registration works smoothly
✅ Institution filtering works correctly
✅ Reset logic works as expected
✅ Users can register with all roles

---

**Happy Testing! 🚀**
