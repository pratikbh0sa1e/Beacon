"""
Quick script to check if Ollama is running and accessible
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("OLLAMA STATUS CHECK")
print("=" * 60)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

print(f"\n1. Checking Ollama at: {OLLAMA_BASE_URL}")

try:
    # Check if Ollama is running
    response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
    
    if response.status_code == 200:
        print("   ✅ Ollama is RUNNING")
        
        # Parse models
        data = response.json()
        models = data.get('models', [])
        
        print(f"\n2. Available Models: {len(models)}")
        for model in models:
            name = model.get('name', 'Unknown')
            size_gb = model.get('size', 0) / (1024**3)
            print(f"   ✅ {name} ({size_gb:.1f} GB)")
        
        # Check configured model
        configured_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        print(f"\n3. Configured Model: {configured_model}")
        
        model_names = [m.get('name', '') for m in models]
        if configured_model in model_names or f"{configured_model}:latest" in model_names:
            print(f"   ✅ Model '{configured_model}' is available")
        else:
            print(f"   ⚠️  Model '{configured_model}' NOT FOUND")
            print(f"   ℹ️  Run: ollama pull {configured_model}")
        
        # Test generation
        print(f"\n4. Testing Model Generation...")
        try:
            test_response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": configured_model,
                    "prompt": "Say 'Hello' in one word",
                    "stream": False
                },
                timeout=30
            )
            
            if test_response.status_code == 200:
                result = test_response.json()
                response_text = result.get('response', '').strip()
                print(f"   ✅ Model responded: '{response_text}'")
                print(f"   ✅ Ollama is WORKING PERFECTLY")
            else:
                print(f"   ⚠️  Model test failed: {test_response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Model test error: {e}")
        
        print("\n" + "=" * 60)
        print("✅ OLLAMA IS READY FOR SCRAPING!")
        print("=" * 60)
        
    else:
        print(f"   ❌ Ollama responded with status: {response.status_code}")
        print(f"   ℹ️  Try restarting: ollama serve")
        
except requests.exceptions.ConnectionError:
    print("   ❌ Cannot connect to Ollama")
    print(f"\n   Ollama is NOT running at {OLLAMA_BASE_URL}")
    print("\n   To start Ollama:")
    print("   1. Open a new terminal")
    print("   2. Run: ollama serve")
    print("   3. Or just run: ollama run llama3.2")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

print()
