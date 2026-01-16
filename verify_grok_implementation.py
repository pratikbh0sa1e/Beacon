"""
Verify Grok integration implementation
This checks if all code changes were applied correctly
"""
import os
import re

def check_requirements():
    """Check if requirements.txt has OpenAI packages"""
    print("\n1. Checking requirements.txt...")
    
    with open('requirements.txt', 'r') as f:
        content = f.read()
    
    checks = []
    
    if 'openai>=' in content:
        print("   ✅ openai package added")
        checks.append(True)
    else:
        print("   ❌ openai package missing")
        checks.append(False)
    
    if 'langchain-openai' in content:
        print("   ✅ langchain-openai package added")
        checks.append(True)
    else:
        print("   ❌ langchain-openai package missing")
        checks.append(False)
    
    return all(checks)


def check_env_file():
    """Check if .env has LLM configuration"""
    print("\n2. Checking .env configuration...")
    
    with open('.env', 'r') as f:
        content = f.read()
    
    checks = []
    
    if 'METADATA_LLM_PROVIDER' in content:
        print("   ✅ METADATA_LLM_PROVIDER configured")
        checks.append(True)
    else:
        print("   ❌ METADATA_LLM_PROVIDER missing")
        checks.append(False)
    
    # Check for at least one API key
    has_api_key = False
    if 'OPENROUTER_API_KEY' in content:
        print("   ✅ OPENROUTER_API_KEY configured")
        has_api_key = True
    if 'XAI_API_KEY' in content:
        print("   ✅ XAI_API_KEY configured")
        has_api_key = True
    if 'GOOGLE_API_KEY' in content:
        print("   ✅ GOOGLE_API_KEY configured")
        has_api_key = True
    
    checks.append(has_api_key)
    
    if 'DELETE_DOCS_WITHOUT_METADATA' in content:
        print("   ✅ DELETE_DOCS_WITHOUT_METADATA configured")
        checks.append(True)
    else:
        print("   ❌ DELETE_DOCS_WITHOUT_METADATA missing")
        checks.append(False)
    
    return all(checks)


def check_metadata_extractor():
    """Check if metadata extractor has multi-provider support"""
    print("\n3. Checking Agent/metadata/extractor.py...")
    
    with open('Agent/metadata/extractor.py', 'r') as f:
        content = f.read()
    
    checks = []
    
    if 'from langchain_openai import ChatOpenAI' in content:
        print("   ✅ ChatOpenAI import added")
        checks.append(True)
    else:
        print("   ❌ ChatOpenAI import missing")
        checks.append(False)
    
    if 'openrouter' in content.lower():
        print("   ✅ OpenRouter support added")
        checks.append(True)
    else:
        print("   ❌ OpenRouter support missing")
        checks.append(False)
    
    if 'grok-beta' in content or 'openrouter' in content.lower():
        print("   ✅ Multi-provider support configured")
        checks.append(True)
    else:
        print("   ❌ Multi-provider support not found")
        checks.append(False)
    
    if 'validate_metadata_quality' in content:
        print("   ✅ Metadata validation method added")
        checks.append(True)
    else:
        print("   ❌ Metadata validation method missing")
        checks.append(False)
    
    if 'retry_with_fallback' in content:
        print("   ✅ Fallback retry logic added")
        checks.append(True)
    else:
        print("   ❌ Fallback retry logic missing")
        checks.append(False)
    
    return all(checks)


def check_enhanced_processor():
    """Check if enhanced processor has quality control"""
    print("\n4. Checking Agent/web_scraping/enhanced_processor.py...")
    
    with open('Agent/web_scraping/enhanced_processor.py', 'r') as f:
        content = f.read()
    
    checks = []
    
    if 'documents_failed_metadata' in content:
        print("   ✅ Failed metadata statistics added")
        checks.append(True)
    else:
        print("   ❌ Failed metadata statistics missing")
        checks.append(False)
    
    if 'validate_metadata_quality' in content:
        print("   ✅ Metadata quality check added")
        checks.append(True)
    else:
        print("   ❌ Metadata quality check missing")
        checks.append(False)
    
    if 'DELETE_DOCS_WITHOUT_METADATA' in content:
        print("   ✅ Document deletion logic added")
        checks.append(True)
    else:
        print("   ❌ Document deletion logic missing")
        checks.append(False)
    
    return all(checks)


def check_api_key_configured():
    """Check if any LLM API key is actually set"""
    print("\n5. Checking if LLM API keys are configured...")
    
    provider = os.getenv('METADATA_LLM_PROVIDER', 'gemini')
    
    if provider == 'openrouter':
        openrouter_key = os.getenv('OPENROUTER_API_KEY', '')
        if openrouter_key and openrouter_key != 'your_openrouter_api_key_here' and len(openrouter_key) > 10:
            print(f"   ✅ OPENROUTER_API_KEY is set (length: {len(openrouter_key)})")
            return True
        else:
            print("   ⚠️  OPENROUTER_API_KEY not set or using placeholder")
            print("   → Get your key from https://openrouter.ai/")
            return False
    
    elif provider == 'grok':
        xai_key = os.getenv('XAI_API_KEY', '')
        if xai_key and xai_key != 'your_grok_api_key_here' and len(xai_key) > 10:
            print(f"   ✅ XAI_API_KEY is set (length: {len(xai_key)})")
            return True
        else:
            print("   ⚠️  XAI_API_KEY not set or using placeholder")
            print("   → Get your key from https://x.ai/")
            return False
    
    elif provider == 'gemini':
        google_key = os.getenv('GOOGLE_API_KEY', '')
        if google_key and len(google_key) > 10:
            print(f"   ✅ GOOGLE_API_KEY is set (length: {len(google_key)})")
            return True
        else:
            print("   ⚠️  GOOGLE_API_KEY not set")
            return False
    
    else:
        print(f"   ⚠️  Unknown provider: {provider}")
        return False


def main():
    """Main verification function"""
    print("=" * 80)
    print("MULTI-PROVIDER LLM VERIFICATION (OpenRouter/Grok/Gemini)")
    print("=" * 80)
    
    results = []
    
    # Run all checks
    results.append(("Requirements", check_requirements()))
    results.append((".env Configuration", check_env_file()))
    results.append(("Metadata Extractor", check_metadata_extractor()))
    results.append(("Enhanced Processor", check_enhanced_processor()))
    results.append(("API Key", check_api_key_configured()))
    
    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:.<40} {status}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    # Get current provider
    provider = os.getenv('METADATA_LLM_PROVIDER', 'gemini')
    print(f"\nCurrent Provider: {provider.upper()}")
    
    if passed == total:
        print("\n✅ ALL CHECKS PASSED!")
        print(f"\nMulti-provider LLM support is complete with {provider.upper()} as primary.")
        print("\nNext steps:")
        
        if provider == 'openrouter':
            print("1. Get OpenRouter API key from https://openrouter.ai/")
            print("2. Add to .env: OPENROUTER_API_KEY=your_key_here")
            print("3. Test: python test_fixed_scraping.py")
        elif provider == 'grok':
            print("1. Get Grok API key from https://x.ai/")
            print("2. Add to .env: XAI_API_KEY=your_key_here")
            print("3. Test: python test_fixed_scraping.py")
        else:
            print("1. Your Gemini setup is ready!")
            print("2. Test: python test_fixed_scraping.py")
    else:
        print("\n❌ SOME CHECKS FAILED!")
        print("\nPlease review the failed checks above.")
        
        if not results[4][1]:  # API key check
            print(f"\n⚠️  Note: {provider.upper()} API key not configured.")
            if provider == 'openrouter':
                print("   Get it from https://openrouter.ai/ (FREE, 2 minutes)")
            elif provider == 'grok':
                print("   Get it from https://x.ai/ (requires X Premium)")
            else:
                print("   Check your GOOGLE_API_KEY in .env")
    
    print("\n" + "=" * 80)
    
    return passed == total


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = main()
    exit(0 if success else 1)
