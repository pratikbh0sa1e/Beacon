# Local Model Setup with Ollama

## Why Use Local Models?

✅ **Completely FREE** - No API costs ever  
✅ **No rate limits** - Process unlimited documents  
✅ **Privacy** - All processing stays on your machine  
✅ **Offline** - Works without internet

## Step 1: Install Ollama

### Windows:

1. Download from https://ollama.ai/download
2. Run the installer
3. Open Command Prompt and verify: `ollama --version`

### Alternative (if download fails):

```bash
# Using curl
curl -fsSL https://ollama.ai/install.sh | sh
```

## Step 2: Download a Model

```bash
# Recommended: Llama 3.2 (3GB) - Good balance of speed/quality
ollama pull llama3.2

# Alternative: Smaller model (1.5GB) - Faster but lower quality
ollama pull llama3.2:1b

# Alternative: Larger model (7GB) - Better quality but slower
ollama pull llama3.1:8b
```

## Step 3: Test the Model

```bash
# Test if model works
ollama run llama3.2
# Type: "Hello, how are you?" and press Enter
# Type: "/bye" to exit
```

## Step 4: Configure Your System

Add to your `.env` file:

```env
# Use local Ollama instead of OpenRouter
METADATA_LLM_PROVIDER=ollama
RAG_LLM_PROVIDER=ollama
RERANKER_PROVIDER=ollama

# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

## Step 5: Update Code for Ollama Support

I'll create the Ollama integration for you:

### Add Ollama to MetadataExtractor:

```python
# In Agent/metadata/extractor.py, add this to _initialize_llm method:

elif provider == "ollama":
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")

    if not ollama_base_url:
        logger.warning("OLLAMA_BASE_URL not found - Ollama unavailable")
        return None

    logger.info(f"Initializing Ollama with model: {ollama_model}")
    return ChatOpenAI(
        model=ollama_model,
        base_url=f"{ollama_base_url}/v1",
        api_key="ollama",  # Ollama doesn't need real API key
        temperature=0.1,
        max_tokens=2000
    )
```

## Step 6: Test Your Setup

```bash
# Start Ollama service (if not auto-started)
ollama serve

# In another terminal, restart your backend
python -m uvicorn backend.main:app --reload

# Test scraping - should work with local model!
```

## Performance Comparison

| Model       | Size  | Speed     | Quality   | RAM Usage |
| ----------- | ----- | --------- | --------- | --------- |
| llama3.2:1b | 1.5GB | Very Fast | Good      | 2GB       |
| llama3.2    | 3GB   | Fast      | Very Good | 4GB       |
| llama3.1:8b | 7GB   | Medium    | Excellent | 8GB       |

## Troubleshooting

### Ollama not starting:

```bash
# Check if running
ollama list

# Start manually
ollama serve
```

### Model not downloading:

```bash
# Check available models
ollama list

# Re-download
ollama pull llama3.2
```

### Out of memory:

- Use smaller model: `ollama pull llama3.2:1b`
- Close other applications
- Restart computer

## Advantages of Local Setup

1. **No API costs** - Run unlimited scraping
2. **No rate limits** - Process 1000+ documents
3. **Better privacy** - Documents never leave your machine
4. **Consistent performance** - No network dependency
5. **Customizable** - Can fine-tune models for your domain

## Next Steps

Once Ollama is working:

1. Test with small scraping job (10 documents)
2. Monitor RAM usage and performance
3. Scale up to larger scraping jobs
4. Consider upgrading to larger model if needed

The local setup is perfect for your use case since you want to avoid API costs and have full control over the system.
