# Ollama Installation Guide for Windows

## Method 1: Official Installer (Recommended)

### Step 1: Download Ollama

1. Go to **https://ollama.ai/download**
2. Click **"Download for Windows"**
3. Download the `.exe` file (about 50MB)

### Step 2: Install Ollama

1. Run the downloaded `.exe` file
2. Click **"Yes"** when Windows asks for permission
3. Follow the installation wizard (just click Next → Next → Install)
4. Installation completes automatically

### Step 3: Verify Installation

Open Command Prompt (cmd) and run:

```cmd
ollama --version
```

You should see something like: `ollama version is 0.1.x`

## Method 2: Manual Installation (If download fails)

### Using PowerShell:

```powershell
# Open PowerShell as Administrator
# Run this command:
iwr -useb https://ollama.ai/install.sh | iex
```

### Using curl (if you have it):

```cmd
curl -fsSL https://ollama.ai/install.sh | sh
```

## Step 4: Download a Model

After installation, download a model:

```cmd
# Recommended: Llama 3.2 (3GB) - Good balance
ollama pull llama3.2

# Alternative: Smaller model (1.5GB) - Faster
ollama pull llama3.2:1b

# Alternative: Larger model (7GB) - Better quality
ollama pull llama3.1:8b
```

## Step 5: Test the Installation

```cmd
# Test if model works
ollama run llama3.2
```

You should see:

```
>>> Hello, how are you?
I'm doing well, thank you for asking! How can I help you today?

>>> /bye
```

## Step 6: Configure Your Project

Update your `.env` file:

```env
# Use Ollama instead of OpenRouter
METADATA_LLM_PROVIDER=ollama
RAG_LLM_PROVIDER=ollama
RERANKER_PROVIDER=ollama

# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Disable quality control initially for testing
DELETE_DOCS_WITHOUT_METADATA=false
```

## Step 7: Start Ollama Service

Ollama should start automatically, but if needed:

```cmd
# Start Ollama service
ollama serve
```

## Step 8: Test Your System

```cmd
# Restart your backend
python -m uvicorn backend.main:app --reload
```

Now test scraping - it should work with the local model!

## Troubleshooting

### Issue: "ollama command not found"

**Solution:** Restart Command Prompt or add to PATH:

1. Search "Environment Variables" in Windows
2. Add `C:\Users\YourName\AppData\Local\Programs\Ollama` to PATH
3. Restart Command Prompt

### Issue: Model download fails

**Solution:** Try different model:

```cmd
# Try smaller model first
ollama pull llama3.2:1b
```

### Issue: Out of memory

**Solution:** Use smaller model:

```cmd
ollama pull llama3.2:1b  # Only 1.5GB RAM needed
```

### Issue: Ollama not starting

**Solution:** Start manually:

```cmd
ollama serve
```

## Model Comparison

| Model       | Size  | RAM Needed | Speed     | Quality   |
| ----------- | ----- | ---------- | --------- | --------- |
| llama3.2:1b | 1.5GB | 2GB        | Very Fast | Good      |
| llama3.2    | 3GB   | 4GB        | Fast      | Very Good |
| llama3.1:8b | 7GB   | 8GB        | Medium    | Excellent |

## Next Steps

1. **Test with small scraping job** (10 documents)
2. **Monitor performance** - check RAM usage
3. **Scale up gradually** - try 100, then 500 documents
4. **Upgrade model if needed** - switch to larger model for better quality

## Benefits of Local Setup

✅ **Completely FREE** - No API costs ever  
✅ **No rate limits** - Process unlimited documents  
✅ **Privacy** - Documents never leave your machine  
✅ **Offline** - Works without internet  
✅ **Fast** - No network latency

Your scraping system will work perfectly with Ollama!
