# University Email Domain Solution

## Problem

We don't have university/college email domains yet, but we want email verification with domain validation.

---

## ✅ Solution Implemented

### **Approach: Flexible Domain Validation**

Domain validation is now **optional and configurable**:

1. **Initially Disabled** - Domain validation is OFF by default
2. **Gradually Enable** - Turn ON when you collect domains
3. **Admin Management** - Admins can add domains via API

---

## 🔧 Configuration

### In `backend/utils/email_validator.py`:

```python
# Enable/disable domain validation
ENABLE_DOMAIN_VALIDATION = False  # Set to True when ready
```

**Current Behavior:**

- ✅ Email format validation - ACTIVE
- ✅ Disposable email blocking - ACTIVE
- ✅ MX record checking - ACTIVE
- ⏸️ Domain validation - DISABLED (until you enable it)

---

## 📋 How to Collect University Domains

### **Option 1: Manual Collection**

When universities register, collect their email domain:

1. University admin signs up
2. Admin manually adds domain via API
3. Future admins from that university must use that domain

### **Option 2: Self-Service During Registration**

Add a field in registration form:

- "Official University Email Domain" (e.g., "university.edu")
- Store in Institution table
- Validate future registrations against it

### **Option 3: Bulk Import**

Create a CSV with university domains:

```csv
institution_id,domain
1,iitdelhi.ac.in
2,du.ac.in
3,jnu.ac.in
```

Import via bulk endpoint.

---

## 🔌 API Endpoints for Domain Management

### **1. List All Domains**

```http
GET /institution-domains/list
Authorization: Bearer {token}
```

**Response:**

```json
{
  "ministry_admin": ["moe.gov.in", "education.gov.in"],
  "university_admin": ["iitdelhi.ac.in", "du.ac.in"]
}
```

---

### **2. Add Single Domain**

```http
POST /institution-domains/add
Authorization: Bearer {token}
Content-Type: application/json

{
  "institution_id": 1,
  "domain": "iitdelhi.ac.in"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Domain iitdelhi.ac.in added for IIT Delhi",
  "role": "university_admin",
  "domain": "iitdelhi.ac.in"
}
```

---

### **3. Get Domains for Institution**

```http
GET /institution-domains/institution/1
Authorization: Bearer {token}
```

**Response:**

```json
{
  "institution": "IIT Delhi",
  "type": "university",
  "role": "university_admin",
  "domains": ["iitdelhi.ac.in"]
}
```

---

### **4. Bulk Add Domains**

```http
POST /institution-domains/bulk-add
Authorization: Bearer {token}
Content-Type: application/json

[
  {"institution_id": 1, "domain": "iitdelhi.ac.in"},
  {"institution_id": 2, "domain": "du.ac.in"},
  {"institution_id": 3, "domain": "jnu.ac.in"}
]
```

**Response:**

```json
{
  "status": "success",
  "added": [
    {
      "institution": "IIT Delhi",
      "domain": "iitdelhi.ac.in",
      "role": "university_admin"
    },
    {
      "institution": "Delhi University",
      "domain": "du.ac.in",
      "role": "university_admin"
    }
  ],
  "errors": [],
  "total_added": 2,
  "total_errors": 0
}
```

---

## 🚀 Recommended Workflow

### **Phase 1: Launch Without Domain Validation**

```python
ENABLE_DOMAIN_VALIDATION = False
```

- Users can register with any valid email
- Email verification still required
- MX records and disposable emails still blocked
- Collect university domains during registration

### **Phase 2: Collect Domains**

As universities register:

1. Note their email domain
2. Add via API: `POST /institution-domains/add`
3. Build your domain whitelist

### **Phase 3: Enable Domain Validation**

```python
ENABLE_DOMAIN_VALIDATION = True
```

- Now university admins MUST use official emails
- Existing users are grandfathered in
- New registrations are validated

---

## 📊 Current Status

### What's Working Now:

- ✅ Email verification (format, MX, disposable)
- ✅ Domain validation code (ready but disabled)
- ✅ API endpoints for domain management
- ✅ Flexible enable/disable toggle

### What's Disabled:

- ⏸️ Institution domain enforcement (until you enable it)

---

## 🎯 Quick Start Guide

### For Developers:

**1. Keep domain validation disabled initially:**

```python
# backend/utils/email_validator.py
ENABLE_DOMAIN_VALIDATION = False
```

**2. Add known domains (MoE, etc.):**

```python
INSTITUTION_DOMAINS = {
    "ministry_admin": [
        "moe.gov.in",
        "education.gov.in",
        "shiksha.gov.in"
    ],
    "university_admin": []  # Empty for now
}
```

**3. As universities register, add their domains:**

```bash
curl -X POST http://localhost:8000/institution-domains/add \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"institution_id": 1, "domain": "university.edu"}'
```

**4. When ready, enable validation:**

```python
ENABLE_DOMAIN_VALIDATION = True
```

---

## 🔐 Permissions

**Who can manage domains:**

- ✅ Developers - Full access (add, list, bulk)
- ✅ MoE Admins - Can add and list domains
- ❌ University Admins - Read-only for their institution
- ❌ Others - No access

---

## 💡 Alternative: No Domain Validation

If you decide domain validation is too restrictive:

1. Keep `ENABLE_DOMAIN_VALIDATION = False` permanently
2. Rely on:
   - Email verification (proves ownership)
   - Admin approval (manual verification)
   - MX record checking (real domains only)
   - Disposable email blocking

This is still secure! Many systems work this way.

---

## 📝 Summary

**Problem Solved:** ✅

- Domain validation is optional
- Can be enabled when ready
- Admins can manage domains via API
- System works perfectly without it

**Current State:**

- Email verification: ACTIVE
- Domain validation: DISABLED (configurable)
- Ready to enable when you have domains

**Next Steps:**

1. Launch with domain validation disabled
2. Collect university domains
3. Add domains via API
4. Enable validation when ready
