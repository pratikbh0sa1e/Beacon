# How to Get Grok API Key - Complete Guide

## Overview

xAI's Grok API provides access to their powerful LLM models. Here's everything you need to know about getting access, pricing, and limits.

## ⚠️ Important: Requirements

To use Grok API, you need:

- **X (Twitter) Premium subscription** - Required for API access
- **X account** - Must be logged in

## Step-by-Step: Get Your Grok API Key

### Step 1: Subscribe to X Premium

You need an X Premium subscription to access Grok API:

**Subscription Options:**

- **Basic**: $3/month (limited features)
- **Premium**: $8/month (recommended for API access)
- **Premium+**: $16/month (higher rate limits)

**How to subscribe:**

1. Go to https://x.com/
2. Click on your profile
3. Select "Premium" or "Premium+"
4. Complete payment

### Step 2: Access Grok PromptIDE

1. Go to https://ide.x.ai/
2. Log in with your X account (the one with Premium subscription)
3. You'll see the Grok PromptIDE interface

### Step 3: Create API Key

1. Click on your **username** in the top right corner
2. Select **"API Keys"** from dropdown menu
3. Click **"Create API Key"** button
4. Set permissions (choose what the key can access):
   - Read access
   - Write access
   - Execute access
5. Click **"Save"**
6. **Copy your API key** immediately (you won't see it again!)

### Step 4: Add to Your .env File

```env
XAI_API_KEY=your_copied_api_key_here
```

## Pricing (As of January 2026)

### Subscription Costs

| Plan     | Monthly | Annual | API Access             |
| -------- | ------- | ------ | ---------------------- |
| Basic    | $3      | $32    | Limited                |
| Premium  | $8      | $84    | Yes ✅                 |
| Premium+ | $16     | $168   | Yes (Higher limits) ✅ |

### API Usage Costs

**Token Pricing:**

- **Input tokens**: $3 per million tokens
- **Output tokens**: $15 per million tokens
- **Cached tokens**: Reduced cost for repeated prompts

**For Metadata Extraction (Your Use Case):**

- Average document: ~2000 input tokens + ~500 output tokens
- Cost per document: ~$0.0006 + ~$0.0075 = **~$0.008 per document**
- **1000 documents**: ~$8 in API costs

**Tools Pricing (if used):**

- Web Search: $5 per 1,000 calls
- Code Execution: $5 per 1,000 calls
- Document Search: $2.50 per 1,000 calls

## Rate Limits

### Current Rate Limits (Subject to change)

**Based on X Premium tier:**

| Metric                  | Premium     | Premium+    |
| ----------------------- | ----------- | ----------- |
| Requests Per Day (RPD)  | 14,400      | Higher      |
| Tokens Per Minute (TPM) | 18,000      | Higher      |
| Context Window          | 256k tokens | 256k tokens |

**For Your Scraping Use Case:**

- 1000 documents at 2000 tokens each = 2M tokens
- At 18,000 TPM = ~111 minutes (~2 hours)
- Well within daily limits ✅

### Rate Limit Headers

When you make API calls, check these headers:

```
x-ratelimit-limit-requests: 14400  # Total requests per day
x-ratelimit-remaining-requests: 14370  # Remaining requests
x-ratelimit-limit-tokens: 18000  # Tokens per minute
x-ratelimit-remaining-tokens: 17997  # Remaining tokens
```

### If You Hit Rate Limit

You'll get a `429 Too Many Requests` error. The response will tell you how long to wait.

## Cost Comparison: Grok vs Gemini

### For 1000 Documents Metadata Extraction

| Provider   | Subscription | API Cost          | Total     | Rate Limit     |
| ---------- | ------------ | ----------------- | --------- | -------------- |
| **Grok**   | $8/month     | ~$8               | **$16**   | 14,400 req/day |
| **Gemini** | Free         | Free tier limited | **$0-15** | 60 req/min     |

**Recommendation:**

- Use **Grok** for bulk scraping (better rate limits)
- Use **Gemini** as fallback (free tier)
- Our implementation uses both! ✅

## Alternative: Use Gemini Only (Free)

If you don't want to pay for Grok, you can use Gemini only:

```env
# In .env file
METADATA_LLM_PROVIDER=gemini  # Use Gemini instead of Grok
METADATA_FALLBACK_PROVIDER=gemini
```

**Gemini Limits:**

- Free tier: 60 requests per minute
- 1000 documents = ~17 minutes
- Sufficient for your use case ✅

## Recommended Setup

### Option 1: Grok Primary (Best Performance)

```env
METADATA_LLM_PROVIDER=grok
METADATA_FALLBACK_PROVIDER=gemini
XAI_API_KEY=your_grok_key
GOOGLE_API_KEY=your_gemini_key
```

**Cost:** ~$16/month (subscription + API)  
**Speed:** Fast  
**Reliability:** Excellent (fallback to Gemini)

### Option 2: Gemini Only (Free)

```env
METADATA_LLM_PROVIDER=gemini
METADATA_FALLBACK_PROVIDER=gemini
GOOGLE_API_KEY=your_gemini_key
```

**Cost:** $0  
**Speed:** Good  
**Reliability:** Good

### Option 3: Hybrid (Recommended for Testing)

```env
METADATA_LLM_PROVIDER=gemini  # Start with free Gemini
METADATA_FALLBACK_PROVIDER=gemini
# Add Grok later when you need higher limits
```

## Common Errors & Solutions

### Error 1: "XAI_API_KEY not found"

**Solution:**

```env
# Make sure this is in your .env file
XAI_API_KEY=your_actual_key_here
```

### Error 2: "Authentication failed"

**Possible causes:**

- API key is incorrect
- X Premium subscription expired
- API key was deleted

**Solution:**

1. Check your X Premium subscription is active
2. Regenerate API key at https://ide.x.ai/
3. Update .env with new key

### Error 3: "429 Too Many Requests"

**Solution:**

- You hit rate limit
- Wait for the time specified in `retry-after` header
- Or upgrade to Premium+ for higher limits

### Error 4: "Missing Permissions"

**Solution:**

- Recreate API key with proper permissions
- Make sure you selected "Read" and "Execute" permissions

## Testing Your Setup

### Test 1: Verify API Key Works

```python
from langchain_openai import ChatOpenAI
import os

# Load your API key
xai_key = os.getenv("XAI_API_KEY")

# Test connection
llm = ChatOpenAI(
    model="grok-beta",
    api_key=xai_key,
    base_url="https://api.x.ai/v1"
)

response = llm.invoke("Hello, Grok!")
print(response.content)
```

### Test 2: Run Small Scrape

```bash
# Set to use Grok
# In .env: METADATA_LLM_PROVIDER=grok

# Run test with 10 documents
python test_fixed_scraping.py
```

## FAQ

### Q: Do I need X Premium to use Grok API?

**A:** Yes, X Premium ($8/month) or Premium+ ($16/month) is required.

### Q: Can I use Grok API without paying?

**A:** No, but you can use Gemini (free) instead. Our implementation supports both!

### Q: What if I run out of rate limits?

**A:** The system will automatically fallback to Gemini. Or upgrade to Premium+.

### Q: Is Grok better than Gemini for metadata extraction?

**A:** Both are excellent. Grok has better rate limits, Gemini is free. We use both!

### Q: How much will 1000 documents cost?

**A:**

- Grok: ~$8 subscription + ~$8 API = $16/month
- Gemini: $0 (free tier)

### Q: Should I use Grok or Gemini?

**A:**

- **For testing**: Use Gemini (free)
- **For production (1000+ docs)**: Use Grok (better limits)
- **Best**: Use both (our implementation does this!)

## Summary

### To Get Started:

**Option A: Use Grok (Paid, Better Limits)**

1. Subscribe to X Premium ($8/month)
2. Go to https://ide.x.ai/
3. Create API key
4. Add to .env: `XAI_API_KEY=your_key`
5. Set: `METADATA_LLM_PROVIDER=grok`

**Option B: Use Gemini Only (Free)**

1. Keep existing Gemini setup
2. Set: `METADATA_LLM_PROVIDER=gemini`
3. No additional cost!

**Option C: Use Both (Recommended)**

1. Set up Grok (Option A)
2. Keep Gemini as fallback
3. Best of both worlds!

---

**My Recommendation:** Start with **Gemini only** (free) for testing. If you need higher rate limits or faster processing, add Grok later. Our implementation supports both seamlessly!

**Cost for 1000 documents:**

- Gemini only: **$0** ✅
- Grok + Gemini: **~$16/month**

For your use case (scraping 1000+ documents), **Gemini's free tier is sufficient**! You don't need Grok unless you're scraping tens of thousands of documents.
