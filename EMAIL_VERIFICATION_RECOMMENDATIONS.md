# Email Verification Recommendations

## Overview

This document outlines strategies to verify email authenticity during user signup to prevent fake accounts and ensure legitimate users.

---

## Verification Approaches

### 1. Email Verification Link (Recommended - Most Common)

**How it works:**

- User signs up → Account created but `email_verified=False`
- System sends verification email with unique token/link
- User clicks link → Email verified → Account activated

**Pros:**

- Industry standard approach
- Confirms user owns the email address
- Prevents typos in email addresses
- Free to implement

**Implementation Requirements:**

- Add `email_verified` boolean field to User model
- Generate verification token (JWT or UUID)
- Send email via SMTP (Gmail, SendGrid, AWS SES)
- Create verification endpoint to validate token

---

### 2. Email Syntax & Domain Validation (Basic)

**How it works:**

- Check email format using regex
- Verify domain has MX records (mail server exists)
- Block known disposable email domains

**Pros:**

- Instant feedback to user
- No external service needed
- Catches obvious fake emails

**Cons:**

- Doesn't prove email ownership
- Can be bypassed with valid-looking fake emails

---

### 3. Third-Party Email Verification APIs (Advanced)

**Popular Services:**

- **ZeroBounce** - Checks if email exists, detects disposables
- **Hunter.io** - Email verification API
- **Abstract API** - Email validation service
- **Mailgun** - Email validation API

**Pros:**

- Detects fake/temporary emails
- Checks if mailbox actually exists
- Identifies role-based emails (info@, admin@)

**Cons:**

- Costs money (typically $0.001-0.01 per check)
- Requires API key management
- Adds latency to signup process

---

### 4. Institution Email Domain Restriction (For Government/Education)

**How it works:**

- University admins must use `@university.edu` emails
- MoE admins must use `@moe.gov` emails
- Validate domain against institution database

**Pros:**

- Perfect for government/education systems
- Ensures legitimacy of institutional users
- No external service needed

**Cons:**

- Requires maintaining domain whitelist
- Doesn't work for students with personal emails
- Needs regular updates as institutions change

---

## Recommended Implementation Strategy

### Combined Approach (Best for Your System)

**1. Email Verification Link (Must Have)**

- Prevents fake signups
- Confirms email ownership
- Required for all users

**2. Institution Domain Validation (For Admins)**

- University admins must use official university email domain
- MoE admins must use government email domain
- Students can use any verified email address

**3. Basic Domain Validation (Instant Feedback)**

- Check MX records exist for domain
- Block known disposable email providers
- Validate email format

---

## Implementation Components

### Backend Requirements:

- ✅ Add `email_verified` field to User model
- ✅ Token generation system (JWT or UUID)
- ✅ Email sending service (SMTP configuration)
- ✅ Verification endpoint (`/verify-email/{token}`)
- ✅ Domain validation logic
- ✅ MX record checking
- ✅ Disposable email blocklist

### Frontend Requirements:

- ✅ Verification pending UI state
- ✅ Resend verification email button
- ✅ Email verification success page
- ✅ Domain validation feedback

### Email Service Options:

1. **Gmail SMTP** (Free, 500 emails/day)
2. **SendGrid** (Free tier: 100 emails/day)
3. **AWS SES** (Pay as you go, very cheap)
4. **Mailgun** (Free tier: 5,000 emails/month)

---

## Security Considerations

- Tokens should expire (24-48 hours)
- Rate limit verification email requests
- Use secure token generation (cryptographically random)
- Log all verification attempts for audit
- Prevent account access until email verified
- Allow admin override for special cases

---

## User Experience Flow

1. User fills signup form
2. System validates email format and domain
3. Account created with `email_verified=False`
4. Verification email sent immediately
5. User receives email with verification link
6. User clicks link → redirected to success page
7. Account activated → user can login
8. If email not verified after 7 days → account deleted

---

## Next Steps

Choose implementation level:

- **Basic**: Email verification links only
- **Standard**: Email verification + domain validation
- **Advanced**: All of the above + third-party API validation

**Estimated Implementation Time:**

- Basic: 2-3 hours
- Standard: 4-5 hours
- Advanced: 6-8 hours
