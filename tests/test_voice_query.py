"""
Test voice query functionality
Tests speech-to-text transcription and RAG integration
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Agent.voice.speech_config import get_engine_info, list_available_engines, ACTIVE_ENGINE


def test_configuration():
    """Test voice configuration"""
    print("\n" + "="*60)
    print("Test 1: Voice Configuration")
    print("="*60)
    
    try:
        print(get_engine_info())
        print("✅ Configuration loaded successfully!")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        return False


def test_transcription_service():
    """Test transcription service initialization"""
    print("\n" + "="*60)
    print("Test 2: Transcription Service Initialization")
    print("="*60)
    
    try:
        from Agent.voice.transcription_service import get_transcription_service
        
        service = get_transcription_service()
        info = service.get_engine_info()
        
        print(f"✅ Service initialized!")
        print(f"   Active Engine: {info['active_engine']}")
        print(f"   Engine Type: {info['engine_type']}")
        
        return True
    except Exception as e:
        print(f"❌ Service initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_audio_format_validation():
    """Test audio format validation"""
    print("\n" + "="*60)
    print("Test 3: Audio Format Validation")
    print("="*60)
    
    from Agent.voice.speech_config import is_format_supported, get_supported_formats
    
    supported = get_supported_formats()
    print(f"Supported formats: {supported}")
    
    test_cases = [
        ("mp3", True),
        ("wav", True),
        ("m4a", True),
        ("ogg", True),
        ("flac", True),
        ("avi", False),
        ("mp4", False)
    ]
    
    all_passed = True
    for fmt, expected in test_cases:
        result = is_format_supported(fmt)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {fmt}: {result} (expected: {expected})")
        if result != expected:
            all_passed = False
    
    if all_passed:
        print("✅ All format validation tests passed!")
        return True
    else:
        print("❌ Some format validation tests failed")
        return False


def test_whisper_availability():
    """Test if Whisper is available (if using whisper-local)"""
    print("\n" + "="*60)
    print("Test 4: Whisper Availability")
    print("="*60)
    
    if ACTIVE_ENGINE != "whisper-local":
        print(f"⏭️  Skipping (active engine is {ACTIVE_ENGINE}, not whisper-local)")
        return True
    
    try:
        import whisper
        import torch
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"✅ Whisper is installed")
        print(f"   Device: {device}")
        
        # Check if CUDA is available for GPU acceleration
        if torch.cuda.is_available():
            print(f"   GPU: {torch.cuda.get_device_name(0)}")
        
        return True
    except ImportError as e:
        print(f"❌ Whisper not installed: {str(e)}")
        print(f"   Install with: pip install openai-whisper")
        return False


def test_google_cloud_availability():
    """Test if Google Cloud Speech is available (if using google-cloud)"""
    print("\n" + "="*60)
    print("Test 5: Google Cloud Speech Availability")
    print("="*60)
    
    if ACTIVE_ENGINE != "google-cloud":
        print(f"⏭️  Skipping (active engine is {ACTIVE_ENGINE}, not google-cloud)")
        return True
    
    try:
        from google.cloud import speech
        
        print(f"✅ Google Cloud Speech is installed")
        
        # Check for API key
        api_key = os.getenv("GOOGLE_CLOUD_API_KEY")
        if api_key:
            print(f"   API Key: Found in environment")
        else:
            print(f"   ⚠️  API Key: Not found (set GOOGLE_CLOUD_API_KEY in .env)")
        
        return True
    except ImportError as e:
        print(f"❌ Google Cloud Speech not installed: {str(e)}")
        print(f"   Install with: pip install google-cloud-speech")
        return False


def show_usage_examples():
    """Show usage examples"""
    print("\n" + "="*60)
    print("📚 Usage Examples")
    print("="*60)
    
    print("""
1. Voice Query (with RAG):
   curl -X POST "http://localhost:8000/voice/query" \\
     -F "audio=@question.mp3" \\
     -F "language=en" \\
     -H "Authorization: Bearer YOUR_TOKEN"

2. Transcribe Only (no RAG):
   curl -X POST "http://localhost:8000/voice/transcribe" \\
     -F "audio=@speech.mp3" \\
     -H "Authorization: Bearer YOUR_TOKEN"

3. Check Voice Service Health:
   curl "http://localhost:8000/voice/health"

4. Get Engine Info:
   curl "http://localhost:8000/voice/engine-info" \\
     -H "Authorization: Bearer YOUR_TOKEN"

5. Python Example:
   from Agent.voice.transcription_service import get_transcription_service
   
   service = get_transcription_service()
   result = service.transcribe_audio("audio.mp3", language="en")
   print(result["text"])
""")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎤 Voice Query Test Suite")
    print("="*60)
    
    # Show available engines
    list_available_engines()
    
    # Run tests
    results = []
    results.append(("Configuration", test_configuration()))
    results.append(("Transcription Service", test_transcription_service()))
    results.append(("Audio Format Validation", test_audio_format_validation()))
    results.append(("Whisper Availability", test_whisper_availability()))
    results.append(("Google Cloud Availability", test_google_cloud_availability()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    # Show usage examples
    show_usage_examples()
    
    if passed == total:
        print("\n✅ All tests passed! Voice query system is ready.")
        print(f"   Active Engine: {ACTIVE_ENGINE}")
        print(f"   Start your server and try the voice query endpoint!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        print(f"   Note: Some failures may be expected if dependencies aren't installed yet.")
        sys.exit(1)
