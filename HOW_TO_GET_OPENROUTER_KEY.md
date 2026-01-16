# How to Get OpenRouter API Key - 2 Minutes Setup

## Why OpenRouter?

✅ **FREE** - Multiple powerful models at $0 cost  
✅ **Best Quality** - Access to Llama 3.3 70B, Llama 3.1 405B  
✅ **High Rate Limits** - Much more generous than other providers  
✅ **Easy Setup** - One API key, multiple models  
✅ **No Subscription** - Unlike Grok, no monthly fees

## Step-by-Step Guide (2 minutes)

### Step 1: Go to OpenRouter

Visit: https://openrouter.ai/

### Step 2: Sign Up / Login

Click **"Sign In"** in top right corner

**Sign up options:**

- Google account (fastest)
- GitHub account
- Email

### Step 3: Get Your API Key

1. After login, click on your **profile icon** (top right)
2. Select **"Keys"** from dropdown
3. Click **"Create Key"** button
4. Give it a name (e.g., "Metadata Extractor")
5. Click **"Create"**
6. **Copy your API key** (starts with `sk-or-v1-...`)

### Step 4: Add to .env File

Open your `.env` file and add:

```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

### Step 5: Choose Your Model

In `.env`, set your preferred model:

```env
# Recommended: Llama 3.3 70B (best balance)
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# Or choose another free model:
# OPENROUTER_MODEL=meta-llama/llama-3.1-405b-instruct:free  # Most powerful
# OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free  # Fastest
```

### Step 6: Set as Primary Provider

```env
METADATA_LLM_PROVIDER=openrouter
METADATA_FALLBACK_PROVIDER=gemini
```

That's it! ✅

## Available FREE Models

### Recommended for Metadata Extraction:

#### 1. **Llama 3.3 70B Instruct** ⭐ BEST CHOICE

```env
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
```

- **Size:** 70B parameters
- **Context:** 131K tokens
- **Quality:** Excellent
- **Speed:** Fast
- **Best for:** Balanced performance

#### 2. **Llama 3.1 405B Instruct** 🚀 MOST POWERFUL

```env
OPENROUTER_MODEL=meta-llama/llama-3.1-405b-instruct:free
```

- **Size:** 405B parameters (HUGE!)
- **Context:** 131K tokens
- **Quality:** Best
- **Speed:** Slower
- **Best for:** Maximum accuracy

#### 3. **Gemini 2.0 Flash Experimental** ⚡ FASTEST

```env
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free
```

- **Context:** 1.05M tokens (massive!)
- **Quality:** Excellent
- **Speed:** Very fast
- **Note:** Deprecating Feb 6, 2026

#### 4. **DeepSeek R1T Chimera** 🧠 REASONING

```env
OPENROUTER_MODEL=tngtech/deepseek-r1t-chimera:free
```

- **Context:** 164K tokens
- **Quality:** Good reasoning
- **Speed:** Fast
- **Best for:** Complex analysis

## Pricing & Limits

### Cost: **$0** ✅

All models listed above are **completely FREE**!

### Rate Limits:

OpenRouter has **very generous rate limits** for free models:

- Much higher than Gemini (60/min)
- Much higher than Grok free tier
- Sufficient for scraping 10,000+ documents

**For 1000 documents:**

- Time: ~15-20 minutes
- Cost: $0
- Quality: Excellent

## Comparison

| Provider                       | Cost   | Quality    | Rate Limits | Setup Time |
| ------------------------------ | ------ | ---------- | ----------- | ---------- |
| **OpenRouter (Llama 3.3 70B)** | **$0** | ⭐⭐⭐⭐⭐ | Very High   | 2 min      |
| Gemini (Direct)                | $0     | ⭐⭐⭐⭐   | 60/min      | Done       |
| Grok                           | $16/mo | ⭐⭐⭐⭐   | 14,400/day  | 30 min     |

## Testing Your Setup

### Test 1: Verify API Key

```python
from langchain_openai import ChatOpenAI
import os

# Load your API key
openrouter_key = os.getenv("OPENROUTER_API_KEY")

# Test connection
llm = ChatOpenAI(
    model="meta-llama/llama-3.3-70b-instruct:free",
    api_key=openrouter_key,
    base_url="https://openrouter.ai/api/v1"
)

response = llm.invoke("Hello! Extract metadata from this: Policy Document 2024")
print(response.content)
```

### Test 2: Run Verification Script

```bash
python verify_grok_implementation.py
```

Should show:

```
✅ OpenRouter API key configured
✅ OpenRouter model set
```

### Test 3: Small Scrape Test

```bash
python test_fixed_scraping.py
```

Watch logs for:

```
INFO - Metadata extractor initialized with primary LLM: openrouter
INFO - Initializing OpenRouter with model: meta-llama/llama-3.3-70b-instruct:free
INFO - Primary LLM (openrouter) extraction successful
```

## Troubleshooting

### Error: "OPENROUTER_API_KEY not found"

**Solution:**

```env
# Make sure this is in your .env file
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

### Error: "Invalid API key"

**Possible causes:**

- API key is incorrect
- API key was deleted
- Typo in .env file

**Solution:**

1. Go to https://openrouter.ai/keys
2. Create new API key
3. Copy and paste carefully into .env

### Error: "Model not found"

**Solution:**
Check model name is correct:

```env
# Correct format:
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# Wrong (missing :free):
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct
```

### Error: "Rate limit exceeded"

**Solution:**

- Very rare with free models
- Wait a few minutes
- Or switch to another free model

## Advanced Configuration

### Multiple Models with Fallback

```env
# Primary: Llama 3.3 70B
METADATA_LLM_PROVIDER=openrouter
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# Fallback: Gemini (your existing setup)
METADATA_FALLBACK_PROVIDER=gemini
```

### Switch Models Easily

Just change the model in .env:

```env
# Try Llama 3.3 70B
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# Or try Llama 3.1 405B (more powerful)
OPENROUTER_MODEL=meta-llama/llama-3.1-405b-instruct:free

# Or try Gemini 2.0 Flash (faster)
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free
```

No code changes needed!

## Benefits for Your Use Case

### For 1000 Documents:

**With OpenRouter (Llama 3.3 70B):**

- ✅ Cost: $0
- ✅ Quality: Excellent (70B model)
- ✅ Time: ~15-20 minutes
- ✅ Rate limits: No issues
- ✅ Fallback: Gemini if needed

**vs Gemini Direct:**

- ✅ Cost: $0 (same)
- ⚠️ Quality: Good (smaller model)
- ✅ Time: ~17 minutes (similar)
- ⚠️ Rate limits: 60/min (may hit limits)
- ❌ Fallback: None

**vs Grok:**

- ❌ Cost: $16/month
- ✅ Quality: Good
- ✅ Time: ~10 minutes
- ✅ Rate limits: High
- ❌ Requires X Premium subscription

## Recommended Setup

```env
# Primary: OpenRouter with Llama 3.3 70B (FREE, excellent quality)
METADATA_LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# Fallback: Gemini (FREE, your existing setup)
METADATA_FALLBACK_PROVIDER=gemini
GOOGLE_API_KEY=your_existing_gemini_key

# Quality Control
DELETE_DOCS_WITHOUT_METADATA=true
REQUIRE_TITLE=true
REQUIRE_SUMMARY=true
```

This gives you:

- **Best quality** (70B model)
- **Zero cost**
- **Highest reliability** (two free providers)
- **Easy switching** between models

## FAQ

### Q: Is OpenRouter really free?

**A:** Yes! The models marked with `:free` are completely free.

### Q: Are there rate limits?

**A:** Yes, but very generous. Sufficient for 10,000+ documents.

### Q: Which model should I use?

**A:** Start with Llama 3.3 70B. It's the best balance of quality and speed.

### Q: Can I switch models anytime?

**A:** Yes! Just change `OPENROUTER_MODEL` in .env.

### Q: Do I need a credit card?

**A:** No! Free models don't require payment info.

### Q: What if OpenRouter is down?

**A:** The system automatically falls back to Gemini.

## Summary

**Setup Time:** 2 minutes  
**Cost:** $0  
**Quality:** Excellent (70B model)  
**Rate Limits:** Very generous  
**Recommended:** ✅ YES!

**Get started now:**

1. Visit https://openrouter.ai/
2. Sign up (2 minutes)
3. Get API key
4. Add to .env
5. Done! ✅

---

**Best Choice for Your Use Case:** OpenRouter with Llama 3.3 70B + Gemini fallback = FREE, excellent quality, high reliability!
