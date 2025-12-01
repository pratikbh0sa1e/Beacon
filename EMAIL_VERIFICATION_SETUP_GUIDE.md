# Email Verification Setup Guide

## 🚀 Quick Setup (5 Steps)

### Step 1: Install Dependencies

```bash
pip install dnspython==2.8.0
```

### Step 2: Run Database Migration

```bash
alembic upgrade head
```

### Step 3: Configure Email Service

Update your `.env` file with SMTP credentials:

#### Option A: Using Gmail (Recommended for Testing)

```env
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=BEACON System
FRONTEND_URL=http://localhost:3000

# Email Verification Settings
ENABLE_DOMAIN_VALIDATION=false
```

**Gmail Setup:**

1. Go to Google Account: https://myaccount.google.com/
2. Enable 2-Factor Authentication
3. Generate App Password: https://myaccount.google.com/apppasswords
4. Use the 16-character app password as `SMTP_PASSWORD`

#### Option B: Using Other SMTP Services

**SendGrid:**

```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

**Mailgun:**

```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=your-mailgun-password
```

**AWS SES:**

```env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
```

### Step 4: Configure Domain Validation

In `.env`:

```env
# Set to "false" initially (recommended)
ENABLE_DOMAIN_VALIDATION=false
```

**When to set to "true":**

- After you've collected university email domains
- When you want to enforce institutional emails for admins

### Step 5: Restart Backend Server

```bash
# Stop current server (Ctrl+C)
# Start again
uvicorn backend.main:app --reload
```

---

## 🧪 Testing the Setup

### Test 1: Register New User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "password123",
    "role": "student",
    "institution_id": 1
  }'
```

**Expected:**

- User created
- Verification email sent
- `email_verified: false`

### Test 2: Check Email

Check your inbox for verification email with subject:
"Verify Your Email - BEACON System"

### Test 3: Verify Email

Click the link in email or:

```bash
curl http://localhost:8000/auth/verify-email/{TOKEN_FROM_EMAIL}
```

**Expected:**

- `email_verified: true`
- Success confirmation email sent

### Test 4: Try to Login Before Verification

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

**Expected (if not verified):**

```json
{
  "detail": "Please verify your email address before logging in..."
}
```

### Test 5: Login After Verification

Same login request should succeed after verification.

---

## 🔧 Configuration Options

### Domain Validation Settings

#### Disabled (Default - Recommended)

```env
ENABLE_DOMAIN_VALIDATION=false
```

**Behavior:**

- ✅ Any valid email accepted
- ✅ MX records checked
- ✅ Disposable emails blocked
- ❌ No domain restrictions

**Use when:**

- Just starting out
- Don't have university domains yet
- Want maximum flexibility

#### Enabled

```env
ENABLE_DOMAIN_VALIDATION=true
```

**Behavior:**

- ✅ All above checks
- ✅ MoE admins must use gov.in emails
- ✅ University admins must use registered domains

**Use when:**

- You have collected university domains
- Want strict institutional email enforcement

---

## 📧 Email Templates

The system sends two types of emails:

### 1. Verification Email

- **Subject:** "Verify Your Email - BEACON System"
- **Contains:** Verification link (valid 24 hours)
- **Sent:** On registration

### 2. Success Email

- **Subject:** "Email Verified Successfully - BEACON System"
- **Contains:** Next steps (pending approval)
- **Sent:** After successful verification

Both emails are:

- ✅ Mobile-responsive
- ✅ HTML + plain text versions
- ✅ Branded with BEACON styling

---

## 🐛 Troubleshooting

### Issue: "Failed to send verification email"

**Causes:**

1. SMTP credentials not configured
2. Wrong SMTP host/port
3. Gmail app password not generated
4. Firewall blocking SMTP

**Solutions:**

1. Check `.env` file has correct SMTP settings
2. Verify Gmail app password (not regular password)
3. Check server logs for detailed error
4. Try different SMTP port (465 for SSL)

### Issue: "Email domain does not have valid mail servers"

**Cause:** Domain has no MX records

**Solutions:**

1. Check if email domain is correct
2. Verify domain actually exists
3. Temporarily disable MX checking (not recommended)

### Issue: "Disposable email addresses are not allowed"

**Cause:** User trying to use temporary email service

**Solution:** This is working as intended. User must use real email.

### Issue: Verification link expired

**Cause:** Token older than 24 hours

**Solution:** User can request new verification email via "Resend" button

---

## 🔐 Security Features

### Token Security

- ✅ Cryptographically secure (32 bytes)
- ✅ One-time use (cleared after verification)
- ✅ 24-hour expiration
- ✅ Unique per user

### Email Validation

- ✅ Format validation (regex)
- ✅ MX record checking
- ✅ Disposable email blocking
- ✅ Domain validation (optional)

### Audit Trail

- ✅ All verifications logged
- ✅ Includes timestamp and user info
- ✅ Tracks resend requests

---

## 📊 Monitoring

### Check Verification Status

```sql
-- Users pending verification
SELECT id, name, email, created_at
FROM users
WHERE email_verified = false;

-- Recently verified users
SELECT id, name, email, created_at
FROM users
WHERE email_verified = true
ORDER BY created_at DESC
LIMIT 10;

-- Expired tokens
SELECT id, name, email, verification_token_expires
FROM users
WHERE email_verified = false
  AND verification_token_expires < NOW();
```

### Audit Logs

```sql
-- Email verifications
SELECT * FROM audit_logs
WHERE action = 'email_verified'
ORDER BY created_at DESC;
```

---

## 🎯 Best Practices

### 1. Start with Domain Validation Disabled

```env
ENABLE_DOMAIN_VALIDATION=false
```

Enable later when you have domains.

### 2. Use App Passwords for Gmail

Never use your actual Gmail password.

### 3. Monitor Verification Rates

Track how many users complete verification.

### 4. Clean Up Expired Tokens

Periodically delete unverified accounts older than 7 days.

### 5. Test Email Delivery

Send test emails before going live.

---

## 📝 Summary

**Setup Steps:**

1. ✅ Install dnspython
2. ✅ Run migration
3. ✅ Configure SMTP in .env
4. ✅ Set domain validation (false initially)
5. ✅ Restart server

**What's Working:**

- Email verification with links
- Token-based security
- MX record validation
- Disposable email blocking
- Resend functionality
- Beautiful email templates

**What's Optional:**

- Domain validation (can enable later)

**Ready to go!** 🚀
