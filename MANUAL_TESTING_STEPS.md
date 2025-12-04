# Manual Testing Steps - Quick Guide

## Prerequisites

✅ Backend running: `uvicorn backend.main:app --reload`
✅ Frontend running: `cd frontend && npm run dev`
✅ Migrations applied: `alembic upgrade head`

---

## Step 1: Login as Developer

1. Open: http://localhost:5173/login
2. Login with:
   - Email: `root@beacon.system`
   - Password: `AR/SPt&_P^hhEI!8eHXWs1UO&wQGOtFA`

---

## Step 2: Create Ministries

1. Go to: **Admin → Institutions**
2. Click **Ministries** tab
3. Click **Add Ministry** button

Create these 3 ministries:

### Ministry 1:

```
Name: Ministry of Education
Location: New Delhi
```

### Ministry 2:

```
Name: Ministry of Health and Family Welfare
Location: New Delhi
```

### Ministry 3:

```
Name: Ministry of Defence
Location: New Delhi
```

**Expected Result:** ✅ 3 ministries created successfully

---

## Step 3: Verify Only 2 Tabs

**Check:** You should see only 2 tabs:

- ✅ **Institutions** tab
- ✅ **Ministries** tab
- ❌ **NO "Departments" tab**

---

## Step 4: Create Institutions

1. Click **Institutions** tab
2. Click **Add Institution** button

Create these institutions:

### Under Ministry of Education:

#### Institution 1:

```
Name: IIT Delhi
Location: Delhi
Ministry: Ministry of Education
```

#### Institution 2:

```
Name: IIT Mumbai
Location: Mumbai
Ministry: Ministry of Education
```

#### Institution 3:

```
Name: Delhi University
Location: Delhi
Ministry: Ministry of Education
```

### Under Ministry of Health:

#### Institution 4:

```
Name: AIIMS Delhi
Location: Delhi
Ministry: Ministry of Health and Family Welfare
```

#### Institution 5:

```
Name: AIIMS Mumbai
Location: Mumbai
Ministry: Ministry of Health and Family Welfare
```

### Under Ministry of Defence:

#### Institution 6:

```
Name: DRDO Bangalore
Location: Bangalore
Ministry: Ministry of Defence
```

#### Institution 7:

```
Name: National Defence Academy
Location: Pune
Ministry: Ministry of Defence
```

**Expected Result:** ✅ 7 institutions created successfully

---

## Step 5: Verify Hierarchy

1. Click **Ministries** tab
2. Check each ministry card shows:
   - Ministry name
   - Location
   - Number of child institutions

**Expected:**

- Ministry of Education: **3 institutions**
- Ministry of Health: **2 institutions**
- Ministry of Defence: **2 institutions**

---

## Step 6: Test Two-Step Registration

### Test 1: Ministry Admin (Single Step)

1. **Logout** from developer account
2. Go to: http://localhost:5173/register
3. Fill form:
   ```
   Name: Test Ministry Admin
   Email: ministry.admin@test.com
   Role: Ministry Admin
   ```
4. ✅ **Check:** Should see single dropdown "Ministry"
5. Select: **Ministry of Education**
6. Password: `test123456`
7. Confirm Password: `test123456`
8. Click **Create Account**

**Expected:** ✅ Registration successful

---

### Test 2: Student (Two-Step)

1. Go to: http://localhost:5173/register
2. Fill form:
   ```
   Name: Test Student
   Email: student@test.com
   Role: Student
   ```
3. ✅ **Check:** Should see **"Step 1: Select Ministry"**
4. Select Ministry: **Ministry of Education**
5. ✅ **Check:** Should see **"Step 2: Select Institution"** (now enabled)
6. ✅ **Check:** Dropdown should show only:
   - IIT Delhi - Delhi
   - IIT Mumbai - Mumbai
   - Delhi University - Delhi
7. Select: **IIT Delhi - Delhi**
8. Password: `test123456`
9. Confirm Password: `test123456`
10. Click **Create Account**

**Expected:** ✅ Registration successful

---

### Test 3: Document Officer at Hospital (Two-Step)

1. Go to: http://localhost:5173/register
2. Fill form:
   ```
   Name: Test Doctor
   Email: doctor@test.com
   Role: Document Officer
   ```
3. ✅ **Check:** Should see **"Step 1: Select Ministry"**
4. Select Ministry: **Ministry of Health and Family Welfare**
5. ✅ **Check:** Should see **"Step 2: Select Institution"** (now enabled)
6. ✅ **Check:** Dropdown should show only:
   - AIIMS Delhi - Delhi
   - AIIMS Mumbai - Mumbai
7. Select: **AIIMS Delhi - Delhi**
8. Password: `test123456`
9. Confirm Password: `test123456`
10. Click **Create Account**

**Expected:** ✅ Registration successful

---

### Test 4: University Admin at Defence Academy (Two-Step)

1. Go to: http://localhost:5173/register
2. Fill form:
   ```
   Name: Test Defence Admin
   Email: defence.admin@test.com
   Role: University Admin
   ```
3. ✅ **Check:** Should see **"Step 1: Select Ministry"**
4. Select Ministry: **Ministry of Defence**
5. ✅ **Check:** Should see **"Step 2: Select Institution"** (now enabled)
6. ✅ **Check:** Dropdown should show only:
   - DRDO Bangalore - Bangalore
   - National Defence Academy - Pune
7. Select: **National Defence Academy - Pune**
8. Password: `test123456`
9. Confirm Password: `test123456`
10. Click **Create Account**

**Expected:** ✅ Registration successful

---

### Test 5: Public Viewer (No Institution)

1. Go to: http://localhost:5173/register
2. Fill form:
   ```
   Name: Test Viewer
   Email: viewer@test.com
   Role: Public Viewer
   Password: test123456
   Confirm Password: test123456
   ```
3. ✅ **Check:** Should NOT see any institution fields
4. Click **Create Account**

**Expected:** ✅ Registration successful

---

## Step 7: Test Reset Logic

### Test A: Role Change Resets Selections

1. Go to: http://localhost:5173/register
2. Select Role: **Student**
3. Select Ministry: **Ministry of Education**
4. Select Institution: **IIT Delhi**
5. **Change Role to:** **Ministry Admin**
6. ✅ **Check:** Ministry and Institution selections should be reset
7. ✅ **Check:** Should see single ministry dropdown

---

### Test B: Ministry Change Resets Institution

1. Select Role: **Student**
2. Select Ministry: **Ministry of Education**
3. Select Institution: **IIT Delhi**
4. **Change Ministry to:** **Ministry of Health**
5. ✅ **Check:** Institution selection should be reset
6. ✅ **Check:** Should see new filtered list (AIIMS Delhi, AIIMS Mumbai)

---

## Step 8: Verify in Database (Optional)

If you want to verify in the database:

```sql
-- Check institution types (should be NO government_dept)
SELECT type, COUNT(*)
FROM institutions
GROUP BY type;

-- Expected:
-- ministry    | 3
-- university  | 7

-- Check hierarchy
SELECT
  i.name as institution,
  m.name as ministry
FROM institutions i
LEFT JOIN institutions m ON i.parent_ministry_id = m.id
WHERE i.type = 'university';

-- Expected: All 7 universities should have a ministry

-- Check registered users
SELECT
  u.name,
  u.role,
  i.name as institution,
  i.type as institution_type
FROM users u
LEFT JOIN institutions i ON u.institution_id = i.id
WHERE u.email LIKE '%@test.com'
ORDER BY u.created_at DESC;

-- Expected: 5 test users with correct institutions
```

---

## Success Checklist

### Institution Management:

- [ ] Only 2 tabs visible (Institutions | Ministries)
- [ ] Can create ministries
- [ ] Can create institutions with parent ministry
- [ ] Ministry cards show child institution count
- [ ] No "Departments" tab exists

### User Registration:

- [ ] Ministry Admin: Single dropdown works
- [ ] Student: Two-step selection works
- [ ] Document Officer: Two-step selection works
- [ ] University Admin: Two-step selection works
- [ ] Public Viewer: No institution field shown
- [ ] Institution dropdown disabled until ministry selected
- [ ] Institution list filtered by selected ministry
- [ ] Role change resets selections
- [ ] Ministry change resets institution

### Database:

- [ ] No government_dept types exist
- [ ] All universities have parent_ministry_id
- [ ] Users correctly linked to institutions

---

## Troubleshooting

### Issue: Backend not responding

**Solution:** Restart backend:

```bash
uvicorn backend.main:app --reload
```

### Issue: Frontend not loading

**Solution:** Restart frontend:

```bash
cd frontend
npm run dev
```

### Issue: Can't login as developer

**Solution:** Check credentials are correct:

- Email: `root@beacon.system`
- Password: `AR/SPt&_P^hhEI!8eHXWs1UO&wQGOtFA`

### Issue: Migrations not applied

**Solution:** Run migrations:

```bash
alembic upgrade head
```

---

## Summary

**What to Test:**

1. ✅ Create 3 ministries
2. ✅ Create 7 institutions under them
3. ✅ Verify only 2 tabs (no Departments)
4. ✅ Test 5 different user registrations
5. ✅ Verify two-step selection works
6. ✅ Verify filtering works
7. ✅ Verify reset logic works

**Expected Time:** 15-20 minutes

**Result:** Complete verification of government_dept removal and two-step registration! 🎉
