"""
Centralized speech-to-text configuration with cloud-only mode support
Change ACTIVE_ENGINE to switch between transcription engines
"""
from typing import Dict, Any
import os

# ============================================
# Available Speech-to-Text Engines
# ============================================

SPEECH_ENGINES = {
    # Local Whisper model (recommended)
    "whisper-local": {
        "engine_type": "whisper",
        "model_size": "base",  # tiny, base, small, medium, large
        "device": "cuda",  # cuda or cpu
        "languages": ["100+ languages including Hindi, Tamil, Telugu, etc."],
        "description": "OpenAI Whisper running locally on GPU",
        "use_case": "Privacy-focused, no API costs, works offline",
        "cost": "Free",
        "requires_api_key": False
    },
    
    # Google Cloud Speech-to-Text
    "google-cloud": {
        "engine_type": "google",
        "model": "default",
        "languages": ["125+ languages"],
        "description": "Google Cloud Speech-to-Text API",
        "use_case": "Cloud-based, high accuracy, pay per use",
        "cost": "$0.006 per 15 seconds (60 min/month free)",
        "requires_api_key": True,
        "api_key_env": "GOOGLE_API_KEY"
    },
    
    # Whisper via OpenAI API (cloud)
    "whisper-api": {
        "engine_type": "whisper-api",
        "model": "whisper-1",
        "languages": ["98 languages"],
        "description": "OpenAI Whisper via API",
        "use_case": "Cloud-based Whisper, no local GPU needed",
        "cost": "$0.006 per minute",
        "requires_api_key": True,
        "api_key_env": "OPENAI_API_KEY"
    }
}

# ============================================
# ACTIVE ENGINE CONFIGURATION
# ============================================
# Automatically use Google Cloud Speech in cloud-only mode, otherwise use local Whisper

def get_active_engine_key() -> str:
    """Get the active engine key based on cloud-only mode"""
    cloud_only = os.getenv("CLOUD_ONLY_MODE", "true").lower() == "true"
    
    if cloud_only:
        # Force Google Cloud Speech in cloud-only mode
        return "google-cloud"
    else:
        # Use local Whisper in development mode
        return "whisper-local"

# Get the active engine dynamically
ACTIVE_ENGINE = get_active_engine_key()

# ============================================
# Whisper Model Configuration
# ============================================
# Model sizes: tiny, base, small, medium, large
# Larger = more accurate but slower
WHISPER_MODEL_SIZE = "base"  # Good balance of speed and accuracy
# WHISPER_MODEL_SIZE = "small"  # Better accuracy, slower
# WHISPER_MODEL_SIZE = "medium"  # High accuracy, much slower

# ============================================
# Audio Processing Settings
# ============================================
AUDIO_CONFIG = {
    "supported_formats": ["mp3", "wav", "m4a", "ogg", "flac", "webm"],  # Added webm for browser recording
    "max_file_size_mb": 25,  # Maximum audio file size
    "sample_rate": 16000,  # Target sample rate for processing
    "enable_noise_reduction": True,  # Reduce background noise
    "enable_vad": True,  # Voice Activity Detection (remove silence)
}

# ============================================
# Language Settings
# ============================================
# Set to None for auto-detection, or specify language code
# Examples: "en" (English), "hi" (Hindi), "ta" (Tamil)
DEFAULT_LANGUAGE = None  # Auto-detect
# DEFAULT_LANGUAGE = "en"  # Force English
# DEFAULT_LANGUAGE = "hi"  # Force Hindi

# ============================================
# Helper Functions
# ============================================

def get_active_engine_config() -> Dict[str, Any]:
    """Get configuration for the currently active engine"""
    active_engine = get_active_engine_key()  # Always get fresh value
    
    if active_engine not in SPEECH_ENGINES:
        raise ValueError(f"Invalid ACTIVE_ENGINE: {active_engine}. Choose from {list(SPEECH_ENGINES.keys())}")
    
    return SPEECH_ENGINES[active_engine]


def get_engine_type() -> str:
    """Get the engine type for the active engine"""
    return get_active_engine_config()["engine_type"]


def requires_api_key() -> bool:
    """Check if active engine requires API key"""
    return get_active_engine_config().get("requires_api_key", False)


def get_api_key_env_var() -> str:
    """Get the environment variable name for API key"""
    config = get_active_engine_config()
    if not config.get("requires_api_key"):
        return None
    return config.get("api_key_env")


def validate_api_key() -> bool:
    """Validate that required API key is present"""
    if not requires_api_key():
        return True
    
    env_var = get_api_key_env_var()
    api_key = os.getenv(env_var)
    
    if not api_key:
        raise ValueError(f"API key required: Set {env_var} in .env file")
    
    return True


def get_engine_info() -> str:
    """Get human-readable info about the active engine"""
    active_engine = get_active_engine_key()
    config = get_active_engine_config()
    cloud_only = os.getenv("CLOUD_ONLY_MODE", "true").lower() == "true"
    
    info = f"""
Active Speech-to-Text Engine: {active_engine}
Cloud-Only Mode: {cloud_only}
Engine Type: {config['engine_type']}
Languages: {', '.join(config['languages'])}
Description: {config['description']}
Use Case: {config['use_case']}
Cost: {config['cost']}
Requires API Key: {config.get('requires_api_key', False)}
"""
    
    if active_engine == "whisper-local":
        info += f"Whisper Model Size: {WHISPER_MODEL_SIZE}\n"
    
    return info


def list_available_engines() -> None:
    """Print all available speech-to-text engines"""
    active_engine = get_active_engine_key()
    cloud_only = os.getenv("CLOUD_ONLY_MODE", "true").lower() == "true"
    
    print("\n" + "="*60)
    print("Available Speech-to-Text Engines")
    print(f"Cloud-Only Mode: {cloud_only}")
    print("="*60)
    
    for key, config in SPEECH_ENGINES.items():
        active_marker = "✅ ACTIVE" if key == active_engine else ""
        cloud_marker = "☁️ CLOUD" if config.get('requires_api_key') else "💻 LOCAL"
        print(f"\n{key} {active_marker} {cloud_marker}")
        print(f"  Type: {config['engine_type']}")
        print(f"  Languages: {', '.join(config['languages'])}")
        print(f"  Cost: {config['cost']}")
        print(f"  Use Case: {config['use_case']}")
        if config.get('requires_api_key'):
            print(f"  API Key: {config['api_key_env']}")
    
    print("\n" + "="*60)
    print(f"Active Engine: {active_engine} (auto-selected based on CLOUD_ONLY_MODE)")
    print("="*60 + "\n")


def get_supported_formats() -> list:
    """Get list of supported audio formats"""
    return AUDIO_CONFIG["supported_formats"]


def is_format_supported(file_extension: str) -> bool:
    """Check if audio format is supported"""
    return file_extension.lower() in AUDIO_CONFIG["supported_formats"]


if __name__ == "__main__":
    # Test the configuration
    print(get_engine_info())
    list_available_engines()
